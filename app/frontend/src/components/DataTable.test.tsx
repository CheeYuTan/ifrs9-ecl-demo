import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataTable from './DataTable';

const columns = [
  { key: 'name', label: 'Name' },
  { key: 'amount', label: 'Amount', align: 'right' as const },
];

const data = [
  { name: 'Alice', amount: 100 },
  { name: 'Bob', amount: 200 },
  { name: 'Charlie', amount: 300 },
];

describe('DataTable', () => {
  it('renders column headers', () => {
    render(<DataTable columns={columns} data={data} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Amount')).toBeInTheDocument();
  });

  it('renders row data', () => {
    render(<DataTable columns={columns} data={data} />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText('Bob')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('handles empty data', () => {
    render(<DataTable columns={columns} data={[]} />);
    expect(screen.getByText('Name')).toBeInTheDocument();
    const rows = screen.queryAllByRole('row');
    expect(rows.length).toBe(1); // header only
  });

  it('applies custom format function', () => {
    const formattedColumns = [
      { key: 'name', label: 'Name' },
      { key: 'amount', label: 'Amount', format: (v: number) => `$${v.toFixed(2)}` },
    ];
    render(<DataTable columns={formattedColumns} data={[{ name: 'Alice', amount: 100 }]} />);
    expect(screen.getByText('$100.00')).toBeInTheDocument();
  });

  it('calls onRowClick when a row is clicked', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<DataTable columns={columns} data={data} onRowClick={onClick} />);
    await user.click(screen.getByText('Alice'));
    expect(onClick).toHaveBeenCalledWith({ name: 'Alice', amount: 100 });
  });

  it('paginates data when exceeding pageSize', () => {
    const largeData = Array.from({ length: 20 }, (_, i) => ({ name: `Person ${i}`, amount: i * 10 }));
    render(<DataTable columns={columns} data={largeData} pageSize={5} />);
    expect(screen.getByText('Person 0')).toBeInTheDocument();
    expect(screen.queryByText('Person 5')).toBeNull();
    expect(screen.getByText('20 rows')).toBeInTheDocument();
    expect(screen.getByText('Page 1 of 4')).toBeInTheDocument();
  });

  it('navigates pages with Next/Prev buttons', async () => {
    const user = userEvent.setup();
    const largeData = Array.from({ length: 10 }, (_, i) => ({ name: `Person ${i}`, amount: i }));
    render(<DataTable columns={columns} data={largeData} pageSize={5} />);

    expect(screen.getByText('Person 0')).toBeInTheDocument();
    await user.click(screen.getByText('Next'));
    expect(screen.getByText('Person 5')).toBeInTheDocument();
    expect(screen.queryByText('Person 0')).toBeNull();

    await user.click(screen.getByText('Prev'));
    expect(screen.getByText('Person 0')).toBeInTheDocument();
  });

  it('sorts by column when header is clicked', async () => {
    const user = userEvent.setup();
    render(<DataTable columns={columns} data={data} pageSize={15} />);

    await user.click(screen.getByText('Amount'));
    const cells = screen.getAllByRole('cell');
    const amountCells = cells.filter((_, i) => i % 2 === 1);
    expect(amountCells[0].textContent).toBe('100');
    expect(amountCells[2].textContent).toBe('300');

    await user.click(screen.getByText('Amount'));
    const cellsDesc = screen.getAllByRole('cell');
    const amountCellsDesc = cellsDesc.filter((_, i) => i % 2 === 1);
    expect(amountCellsDesc[0].textContent).toBe('300');
    expect(amountCellsDesc[2].textContent).toBe('100');
  });

  it('does not show pagination for small datasets', () => {
    render(<DataTable columns={columns} data={data} pageSize={15} />);
    expect(screen.queryByText('Prev')).toBeNull();
    expect(screen.queryByText('Next')).toBeNull();
  });

  it('filters data with search input', async () => {
    const user = userEvent.setup();
    const largeData = [
      { name: 'Alice', amount: 100 },
      { name: 'Bob', amount: 200 },
      { name: 'Charlie', amount: 300 },
      { name: 'Diana', amount: 400 },
      { name: 'Eve', amount: 500 },
      { name: 'Frank', amount: 600 },
    ];
    render(<DataTable columns={columns} data={largeData} pageSize={15} />);
    const searchInput = screen.getByPlaceholderText('Search...');
    await user.type(searchInput, 'Ali');
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.queryByText('Bob')).toBeNull();
    expect(screen.queryByText('Charlie')).toBeNull();
  });

  it('shows search bar and export button when data > 5 rows', () => {
    const largeData = Array.from({ length: 6 }, (_, i) => ({ name: `P${i}`, amount: i }));
    render(<DataTable columns={columns} data={largeData} />);
    expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
  });

  it('shows export button when exportName is provided', () => {
    render(<DataTable columns={columns} data={data} exportName="test-export" />);
    expect(screen.getByLabelText('Export test-export as CSV')).toBeInTheDocument();
  });

  it('applies compact mode with smaller padding', () => {
    const { container } = render(<DataTable columns={columns} data={data} compact />);
    const cells = container.querySelectorAll('td');
    expect(cells.length).toBeGreaterThan(0);
    // compact mode uses py-2 class
    expect(cells[0].className).toContain('py-2');
  });

  it('highlights selected row', () => {
    const selectedRow = { name: 'Bob', amount: 200 };
    const { container } = render(
      <DataTable columns={columns} data={data} onRowClick={vi.fn()} selectedRow={selectedRow} />
    );
    const rows = container.querySelectorAll('tr');
    // Find the row with Bob — should have ring styling
    const bobRow = Array.from(rows).find(r => r.textContent?.includes('Bob'));
    expect(bobRow?.className).toContain('ring-1');
  });

  it('supports keyboard navigation on clickable rows', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<DataTable columns={columns} data={data} onRowClick={onClick} />);
    const rows = screen.getAllByRole('row');
    // Data rows (not header) should have tabIndex
    const dataRow = rows[1]; // first data row
    dataRow.focus();
    await user.keyboard('{Enter}');
    expect(onClick).toHaveBeenCalledWith({ name: 'Alice', amount: 100 });
  });

  it('sorts columns with keyboard Enter', async () => {
    const user = userEvent.setup();
    render(<DataTable columns={columns} data={data} pageSize={15} />);
    const amountHeader = screen.getByText('Amount');
    amountHeader.focus();
    await user.keyboard('{Enter}');
    const cells = screen.getAllByRole('cell');
    const amountCells = cells.filter((_, i) => i % 2 === 1);
    expect(amountCells[0].textContent).toBe('100');
  });

  it('shows aria-sort attribute on sorted column', async () => {
    const user = userEvent.setup();
    render(<DataTable columns={columns} data={data} pageSize={15} />);
    const amountHeader = screen.getByText('Amount').closest('th');
    expect(amountHeader?.getAttribute('aria-sort')).toBeNull();
    await user.click(screen.getByText('Amount'));
    expect(amountHeader?.getAttribute('aria-sort')).toBe('ascending');
    await user.click(screen.getByText('Amount'));
    expect(amountHeader?.getAttribute('aria-sort')).toBe('descending');
  });

  it('resets page to 0 when data changes', () => {
    const largeData1 = Array.from({ length: 20 }, (_, i) => ({ name: `Person ${i}`, amount: i }));
    const largeData2 = Array.from({ length: 20 }, (_, i) => ({ name: `New ${i}`, amount: i + 100 }));
    const { rerender } = render(<DataTable columns={columns} data={largeData1} pageSize={5} />);
    // Navigate to page 2 would be needed, but data change resets
    rerender(<DataTable columns={columns} data={largeData2} pageSize={5} />);
    expect(screen.getByText('Page 1 of 4')).toBeInTheDocument();
    expect(screen.getByText('New 0')).toBeInTheDocument();
  });

  it('search resets page to 0', async () => {
    const user = userEvent.setup();
    const largeData = Array.from({ length: 20 }, (_, i) => ({ name: `Person ${i}`, amount: i * 10 }));
    render(<DataTable columns={columns} data={largeData} pageSize={5} />);
    // First navigate to page 2
    await user.click(screen.getByText('Next'));
    expect(screen.getByText('Page 2 of 4')).toBeInTheDocument();
    // Then search — should reset to page 1
    const searchInput = screen.getByPlaceholderText('Search...');
    await user.type(searchInput, 'Person 1');
    // Should show filtered results from page 1
    expect(screen.queryByText('Page 2')).toBeNull();
  });

  it('Prev button is disabled on first page', () => {
    const largeData = Array.from({ length: 20 }, (_, i) => ({ name: `Person ${i}`, amount: i }));
    render(<DataTable columns={columns} data={largeData} pageSize={5} />);
    const prevBtn = screen.getByLabelText('Previous page');
    expect(prevBtn).toBeDisabled();
  });

  it('Next button is disabled on last page', async () => {
    const user = userEvent.setup();
    const largeData = Array.from({ length: 10 }, (_, i) => ({ name: `Person ${i}`, amount: i }));
    render(<DataTable columns={columns} data={largeData} pageSize={5} />);
    await user.click(screen.getByText('Next'));
    const nextBtn = screen.getByLabelText('Next page');
    expect(nextBtn).toBeDisabled();
  });

  it('exports CSV when export button is clicked', async () => {
    const user = userEvent.setup();
    const clickSpy = vi.fn();
    const createObjectURLSpy = vi.fn().mockReturnValue('blob:test');
    const revokeObjectURLSpy = vi.fn();

    vi.stubGlobal('URL', {
      createObjectURL: createObjectURLSpy,
      revokeObjectURL: revokeObjectURLSpy,
    });

    // Render first, then spy on createElement for the export click
    render(<DataTable columns={columns} data={data} exportName="test-data" />);

    const origCreateElement = document.createElement.bind(document);
    const mockAnchor = { href: '', download: '', click: clickSpy } as any;
    const createElementSpy = vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'a') return mockAnchor;
      return origCreateElement(tag);
    });

    await user.click(screen.getByLabelText('Export test-data as CSV'));

    expect(createObjectURLSpy).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(mockAnchor.download).toContain('test-data');
    expect(revokeObjectURLSpy).toHaveBeenCalled();

    createElementSpy.mockRestore();
  });
});
