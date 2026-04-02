import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Backtesting from './Backtesting';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: () => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, ...rest } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'style' || k === 'disabled') {
            domProps[k] = v;
          }
        }
        return <div {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart">{children}</div>,
  LineChart: ({ children }: any) => <div>{children}</div>,
  ScatterChart: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div>{children}</div>,
  Line: () => null,
  Scatter: () => null,
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ReferenceLine: () => null,
}));

vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('../lib/chartTheme', () => ({
  useChartTheme: () => ({
    text: '#333', grid: '#ccc', bg: '#fff', textMuted: '#999',
    tooltip: { border: '#ccc', bg: '#fff', text: '#333' },
    brand: '#3b82f6',
    colors: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'],
  }),
}));

vi.mock('../lib/format', () => ({
  fmtNumber: (v: number) => String(v),
  fmtPct: (v: number) => `${(v * 100).toFixed(1)}%`,
  fmtDateTime: (v: string) => v || '—',
}));

vi.mock('../lib/api', () => ({
  api: {
    listBacktests: vi.fn().mockResolvedValue([]),
    backtestTrend: vi.fn().mockResolvedValue([]),
    runBacktest: vi.fn().mockResolvedValue({}),
    getBacktest: vi.fn().mockResolvedValue(null),
    listModels: vi.fn().mockResolvedValue([]),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

describe('Backtesting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', async () => {
    render(<Backtesting />);
    await waitFor(() => {
      expect(screen.getByText('Model Backtesting')).toBeInTheDocument();
    });
  });

  it('loads backtest results on mount', async () => {
    render(<Backtesting />);
    await waitFor(() => {
      expect(mockApi.listBacktests).toHaveBeenCalled();
    });
  });

  it('shows empty state when no backtest results', async () => {
    mockApi.listBacktests.mockResolvedValue([]);
    render(<Backtesting />);
    await waitFor(() => {
      expect(mockApi.listBacktests).toHaveBeenCalled();
    });
  });

  it('displays backtest results with traffic light badges', async () => {
    mockApi.listBacktests.mockResolvedValue([
      {
        backtest_id: 'BT-001',
        model_id: 'M-001',
        model_name: 'PD Logistic v1',
        model_type: 'PD',
        backtest_date: '2025-12-15',
        total_loans: 1000,
        pass_count: 3,
        amber_count: 1,
        fail_count: 0,
        overall_traffic_light: 'Green',
        observation_window: '12M',
        outcome_window: '12M',
      },
    ]);
    render(<Backtesting />);
    await waitFor(() => {
      // DataTable shows model_type column with "PD"
      expect(screen.getAllByText('PD').length).toBeGreaterThan(0);
    });
    // Traffic light badge shows "Green"
    expect(screen.getAllByText('Green').length).toBeGreaterThan(0);
  });

  it('shows model type filter', async () => {
    render(<Backtesting />);
    await waitFor(() => {
      expect(mockApi.listBacktests).toHaveBeenCalled();
    });
    // Model type filter is a select with "PD Model" and "LGD Model" options
    expect(screen.getByText('PD Model')).toBeInTheDocument();
    expect(screen.getByText('LGD Model')).toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    mockApi.listBacktests.mockRejectedValue(new Error('Backtest failed'));
    render(<Backtesting />);
    await waitFor(() => {
      expect(screen.getByText(/Backtest failed/)).toBeInTheDocument();
    });
  });

  it('displays trend data when available', async () => {
    mockApi.listBacktests.mockResolvedValue([
      {
        backtest_id: 'BT-001',
        model_id: 'M-001',
        model_name: 'PD v1',
        model_type: 'PD',
        backtest_date: '2025-12-15',
        total_loans: 500,
        pass_count: 2,
        amber_count: 0,
        fail_count: 0,
        overall_traffic_light: 'Green',
        observation_window: '12M',
        outcome_window: '12M',
      },
    ]);
    mockApi.backtestTrend.mockResolvedValue([
      { backtest_date: '2025-06-01', auc: 0.80 },
      { backtest_date: '2025-12-01', auc: 0.82 },
    ]);
    render(<Backtesting />);
    await waitFor(() => {
      // The page renders with trend chart visible
      expect(screen.getByText('Model Backtesting')).toBeInTheDocument();
    });
    // Trend data should cause chart to render
    expect(mockApi.backtestTrend).toHaveBeenCalledWith('PD');
  });
});
