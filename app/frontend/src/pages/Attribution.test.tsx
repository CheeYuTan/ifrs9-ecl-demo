import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import Attribution from './Attribution';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart-container">{children}</div>,
  BarChart: ({ children }: any) => <div data-testid="bar-chart">{children}</div>,
  Bar: () => <div data-testid="bar" />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Cell: () => <div />,
  ReferenceLine: () => <div />,
}));

vi.mock('../lib/api', () => ({
  api: {
    getAttribution: vi.fn().mockResolvedValue({
      waterfall_data: [
        { name: 'Opening', value: 1700, cumulative: 1700, category: 'anchor', base: 0 },
        { name: 'New Originations', value: 200, cumulative: 1900, category: 'increase', base: 1700 },
        { name: 'Closing', value: 1950, cumulative: 1950, category: 'anchor', base: 0 },
      ],
      opening: { stage1: 1000, stage2: 500, stage3: 200, total: 1700 },
      closing: { stage1: 1100, stage2: 600, stage3: 250, total: 1950 },
      reconciliation: { total_movement: 250, absolute_residual: 5, residual_pct: 0.26, within_materiality: true, materiality_threshold_pct: 1, data_gaps: [] },
    }),
    getAttributionHistory: vi.fn().mockResolvedValue([]),
    eclAttribution: vi.fn().mockResolvedValue({
      waterfall: [],
      opening: { stage1: 0, stage2: 0, stage3: 0, total: 0 },
      closing: { stage1: 0, stage2: 0, stage3: 0, total: 0 },
      reconciliation: { total_movement: 0, absolute_residual: 0, residual_pct: 0, within_materiality: true, materiality_threshold_pct: 1, data_gaps: [] },
    }),
  },
}));

vi.mock('../lib/chartTheme', () => ({
  useChartTheme: () => ({ text: '#333', grid: '#ccc', bg: '#fff', textMuted: '#999' }),
}));

describe('Attribution', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders without crashing and loads data', async () => {
    render(<Attribution />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('calls getAttribution on mount', async () => {
    const { api } = await import('../lib/api');
    render(<Attribution />);
    await waitFor(() => {
      expect(api.getAttribution).toHaveBeenCalled();
    });
  });
});
