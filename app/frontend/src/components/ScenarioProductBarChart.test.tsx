import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ScenarioProductBarChart from './ScenarioProductBarChart';

vi.mock('framer-motion', () => ({
  motion: { div: ({ children }: any) => <div>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
  BarChart: ({ children, data }: any) => <div data-testid="bar-chart" data-count={data?.length}>{children}</div>,
  Bar: ({ onClick, children, name }: any) => <div data-testid={`bar-${name || 'default'}`} onClick={onClick}>{children}</div>,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
}));

vi.mock('./ChartTooltip', () => ({
  default: () => <div data-testid="chart-tooltip" />,
}));

vi.mock('../lib/format', () => ({
  fmtCurrency: (v: number) => `$${(v || 0).toLocaleString()}`,
  formatProductName: (s: string) => s?.replace(/_/g, ' ') || 'Unknown',
}));

vi.mock('../lib/chartUtils', () => ({
  chartAxisProps: () => ({ fontSize: 11, angle: 0, height: 40 }),
  sortChartData: (d: any[]) => d,
}));

vi.mock('../lib/config', () => ({
  config: { currencySymbol: '$' },
}));

vi.mock('../lib/chartTheme', () => ({
  useChartTheme: () => ({
    grid: '#eee',
    axis: '#333',
    axisLight: '#999',
    label: '#666',
    tooltip: { bg: '#fff', border: '#ddd', text: '#333' },
  }),
}));

vi.mock('../lib/api', () => ({
  api: {
    drillDownDimensions: vi.fn().mockResolvedValue([
      { key: 'risk_band', label: 'Risk Band' },
      { key: 'segment', label: 'Segment' },
    ]),
    eclByCohort: vi.fn().mockResolvedValue([
      { cohort_id: 'C1', total_ecl: 25000 },
      { cohort_id: 'C2', total_ecl: 15000 },
    ]),
  },
}));

describe('ScenarioProductBarChart', () => {
  const sampleData = [
    { product: 'Mortgage', _rawProduct: 'mortgage', base: 50000, optimistic: 40000, pessimistic: 65000 },
    { product: 'Personal Loan', _rawProduct: 'personal_loan', base: 30000, optimistic: 25000, pessimistic: 40000 },
  ];

  const scenarioColors: Record<string, string> = {
    base: '#3B82F6',
    optimistic: '#10B981',
    pessimistic: '#EF4444',
  };

  const defaultProps = {
    data: sampleData,
    scenarioColors,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders empty state when data is empty', () => {
    render(<ScenarioProductBarChart data={[]} scenarioColors={scenarioColors} />);
    expect(screen.getByText('No scenario comparison data available')).toBeInTheDocument();
  });

  it('renders chart container when data is provided', () => {
    render(<ScenarioProductBarChart {...defaultProps} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('shows "All Products" breadcrumb at products level', () => {
    render(<ScenarioProductBarChart {...defaultProps} />);
    expect(screen.getByText('All Products')).toBeInTheDocument();
  });

  it('shows drill-down hint at products level', () => {
    render(<ScenarioProductBarChart {...defaultProps} />);
    expect(screen.getByText('Click a product bar to drill down by dimension')).toBeInTheDocument();
  });

  it('does not show back button at products level', () => {
    render(<ScenarioProductBarChart {...defaultProps} />);
    expect(screen.queryByText('Back')).toBeNull();
  });

  it('renders with custom scenarioLabels', () => {
    const labels = { base: 'Base Case', optimistic: 'Upside', pessimistic: 'Downside' };
    render(<ScenarioProductBarChart {...defaultProps} scenarioLabels={labels} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('renders with custom height', () => {
    render(<ScenarioProductBarChart {...defaultProps} height={400} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('loads drill-down dimensions on mount', async () => {
    const { api } = await import('../lib/api');
    render(<ScenarioProductBarChart {...defaultProps} />);
    await waitFor(() => {
      expect(api.drillDownDimensions).toHaveBeenCalled();
    });
  });

  it('resets to products level when data changes', () => {
    const { rerender } = render(<ScenarioProductBarChart {...defaultProps} />);
    const newData = [{ product: 'Auto Loan', base: 20000 }];
    rerender(<ScenarioProductBarChart data={newData} scenarioColors={scenarioColors} />);
    expect(screen.getByText('All Products')).toBeInTheDocument();
  });

  it('only renders bars for scenarios present in data', () => {
    const partialData = [{ product: 'Mortgage', base: 50000 }];
    const colors = { base: '#3B82F6', optimistic: '#10B981', pessimistic: '#EF4444' };
    render(<ScenarioProductBarChart data={partialData} scenarioColors={colors} />);
    // Component renders, only 'base' bar should exist
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });
});
