import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ThreeLevelDrillDown from './ThreeLevelDrillDown';

vi.mock('framer-motion', () => ({
  motion: { div: ({ children }: any) => <div>{children}</div> },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
  BarChart: ({ children, data }: any) => <div data-testid="bar-chart" data-count={data?.length}>{children}</div>,
  Bar: ({ onClick, children }: any) => <div data-testid="bar" onClick={onClick}>{children}</div>,
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
  formatProductName: (s: any) => String(s || 'Unknown').replace(/_/g, ' '),
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

describe('ThreeLevelDrillDown', () => {
  const level0Data = [
    { stage: 1, total_ecl: 100000, name: 'Stage 1' },
    { stage: 2, total_ecl: 50000, name: 'Stage 2' },
    { stage: 3, total_ecl: 20000, name: 'Stage 3' },
  ];

  const defaultProps = {
    level0Data,
    level0Key: 'stage',
    level0Label: 'Stage',
    dataKey: 'total_ecl',
    title: 'ECL by Stage',
    fetchProductData: vi.fn().mockResolvedValue([
      { product_type: 'mortgage', total_ecl: 60000 },
      { product_type: 'personal_loan', total_ecl: 40000 },
    ]),
    fetchCohortData: vi.fn().mockResolvedValue([
      { cohort_id: 'C1', total_ecl: 30000 },
      { cohort_id: 'C2', total_ecl: 30000 },
    ]),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders breadcrumb with level0Label at top level', () => {
    render(<ThreeLevelDrillDown {...defaultProps} />);
    expect(screen.getByText('All Stages')).toBeInTheDocument();
  });

  it('renders bar chart with level0Data', () => {
    render(<ThreeLevelDrillDown {...defaultProps} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('shows drill-down hint at level0', () => {
    render(<ThreeLevelDrillDown {...defaultProps} />);
    expect(screen.getByText(/Click a stage to drill into products/i)).toBeInTheDocument();
  });

  it('does not show back button at level0', () => {
    render(<ThreeLevelDrillDown {...defaultProps} />);
    expect(screen.queryByText('Back')).toBeNull();
  });

  it('renders with custom colors', () => {
    render(<ThreeLevelDrillDown {...defaultProps} colors={['#FF0000', '#00FF00']} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('renders with level0Colors mapping', () => {
    render(<ThreeLevelDrillDown {...defaultProps} level0Colors={{ 1: '#10B981', 2: '#F59E0B', 3: '#EF4444' }} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('renders with custom formatValue', () => {
    const fmt = (v: number) => `$${v.toLocaleString()}`;
    render(<ThreeLevelDrillDown {...defaultProps} formatValue={fmt} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('renders with custom height', () => {
    render(<ThreeLevelDrillDown {...defaultProps} height={500} />);
    expect(screen.getByTestId('chart-container')).toBeInTheDocument();
  });

  it('loads drill-down dimensions on mount', async () => {
    const { api } = await import('../lib/api');
    render(<ThreeLevelDrillDown {...defaultProps} />);
    await waitFor(() => {
      expect(api.drillDownDimensions).toHaveBeenCalled();
    });
  });

  it('resets to level0 when level0Data changes', async () => {
    const { rerender } = render(<ThreeLevelDrillDown {...defaultProps} />);
    // Rerender with new data
    const newData = [{ stage: 1, total_ecl: 200000, name: 'Stage 1' }];
    rerender(<ThreeLevelDrillDown {...defaultProps} level0Data={newData} />);
    expect(screen.getByText('All Stages')).toBeInTheDocument();
  });

  it('handles empty level0Data', () => {
    render(<ThreeLevelDrillDown {...defaultProps} level0Data={[]} />);
    // Chart container should not render with empty data
    expect(screen.queryByTestId('chart-container')).toBeNull();
  });
});
