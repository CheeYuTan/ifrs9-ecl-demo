import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DrillDownChart from './DrillDownChart';

vi.mock('framer-motion', () => ({
  motion: { div: ({ children }: any) => <div>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
  BarChart: ({ children, data }: any) => (
    <div data-testid="bar-chart" data-count={data?.length}>{children}</div>
  ),
  Bar: ({ children }: any) => <div data-testid="bar">{children}</div>,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Cell: () => null,
}));

vi.mock('./ChartTooltip', () => ({
  default: () => <div data-testid="chart-tooltip" />,
}));

vi.mock('../lib/format', () => ({
  formatProductName: (s: string) => s?.replace(/_/g, ' ') || 'Unknown',
}));

vi.mock('../lib/chartUtils', () => ({
  sortChartData: (d: any[]) => d,
}));

vi.mock('../lib/chartTheme', () => ({
  useChartTheme: () => ({ grid: '#eee', axis: '#333', axisLight: '#999' }),
}));

vi.mock('../lib/api', () => ({
  api: {
    drillDownDimensions: vi.fn().mockResolvedValue([
      { key: 'risk_band', label: 'Risk Band' },
      { key: 'segment', label: 'Segment' },
    ]),
  },
}));

const makeData = () => ({
  totalData: [
    { product_type: 'mortgage', total_ecl: 50000 },
    { product_type: 'personal_loan', total_ecl: 30000 },
  ],
  productData: {
    mortgage: [{ cohort_id: 'C1', total_ecl: 20000 }, { cohort_id: 'C2', total_ecl: 30000 }],
    personal_loan: [{ cohort_id: 'C3', total_ecl: 30000 }],
  },
  cohortData: {},
});

describe('DrillDownChart', () => {
  const defaultProps = {
    data: makeData(),
    dataKey: 'total_ecl',
    title: 'ECL by Product',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders with role=figure and aria-label', () => {
    render(<DrillDownChart {...defaultProps} />);
    expect(screen.getByRole('figure')).toHaveAttribute('aria-label', 'ECL by Product');
  });

  it('shows "All Products" breadcrumb at top level', () => {
    render(<DrillDownChart {...defaultProps} />);
    expect(screen.getByText('All Products')).toBeInTheDocument();
  });

  it('renders bar chart with data', () => {
    render(<DrillDownChart {...defaultProps} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('shows drill-down hint at top level', () => {
    render(<DrillDownChart {...defaultProps} />);
    expect(screen.getByText('Click a bar to drill down by dimension')).toBeInTheDocument();
  });

  it('renders with custom formatValue', () => {
    const fmt = (v: number) => `$${v}`;
    render(<DrillDownChart {...defaultProps} formatValue={fmt} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('renders with custom height', () => {
    render(<DrillDownChart {...defaultProps} height={500} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('applies custom colors', () => {
    render(<DrillDownChart {...defaultProps} colors={['#FF0000', '#00FF00']} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('renders empty product data without chart', () => {
    const emptyData = { totalData: [], productData: {}, cohortData: {} };
    render(<DrillDownChart {...defaultProps} data={emptyData} />);
    // No chart rendered when totalData is empty but level is 'total'
    // The component still renders the figure container
    expect(screen.getByRole('figure')).toBeInTheDocument();
  });

  it('loads drill-down dimensions on mount', async () => {
    const { api } = await import('../lib/api');
    render(<DrillDownChart {...defaultProps} />);
    await waitFor(() => {
      expect(api.drillDownDimensions).toHaveBeenCalled();
    });
  });

  it('supports fetchByDimension callback', async () => {
    const fetchByDimension = vi.fn().mockResolvedValue([{ cohort_id: 'C99', total_ecl: 5000 }]);
    render(<DrillDownChart {...defaultProps} fetchByDimension={fetchByDimension} />);
    // Component renders successfully with the prop
    expect(screen.getByRole('figure')).toBeInTheDocument();
  });
});
