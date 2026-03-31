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
});
