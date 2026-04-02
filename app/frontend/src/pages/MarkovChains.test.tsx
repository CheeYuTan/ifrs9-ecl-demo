import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import MarkovChains from './MarkovChains';

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
  AreaChart: ({ children }: any) => <div>{children}</div>,
  Area: () => null,
  LineChart: ({ children }: any) => <div>{children}</div>,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
}));

vi.mock('../lib/chartTheme', () => ({
  useChartTheme: () => ({
    grid: '#F1F5F9',
    axis: '#475569',
    axisLight: '#64748B',
    label: '#475569',
    tooltip: { bg: 'rgba(255,255,255,0.95)', border: 'rgba(0,0,0,0.06)', text: '#0F172A' },
    reference: '#E5E7EB',
  }),
}));

vi.mock('../lib/api', () => ({
  api: {
    markovListMatrices: vi.fn().mockResolvedValue([]),
    markovEstimate: vi.fn().mockResolvedValue({}),
    markovGetMatrix: vi.fn().mockResolvedValue({}),
    markovForecast: vi.fn().mockResolvedValue({}),
    markovLifetimePd: vi.fn().mockResolvedValue({}),
    markovCompare: vi.fn().mockResolvedValue([]),
    portfolioSummary: vi.fn().mockResolvedValue([]),
    stageDistribution: vi.fn().mockResolvedValue([]),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

describe('MarkovChains', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.markovListMatrices.mockResolvedValue([]);
    mockApi.portfolioSummary.mockResolvedValue([]);
  });

  it('renders page header', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('Markov Chain Transition Models')).toBeInTheDocument();
    });
  });

  it('renders 4 sub-tabs', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('Transition Matrix')).toBeInTheDocument();
    });
    expect(screen.getByText('Stage Forecast')).toBeInTheDocument();
    expect(screen.getByText('Lifetime PD')).toBeInTheDocument();
    expect(screen.getByText('Compare')).toBeInTheDocument();
  });

  it('renders estimate controls', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getAllByText('Estimate All Products').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('loads matrices on mount', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(mockApi.markovListMatrices).toHaveBeenCalled();
    });
  });

  it('loads portfolio summary for products', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(mockApi.portfolioSummary).toHaveBeenCalled();
    });
  });

  it('shows empty state when no matrices', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('No transition matrices estimated')).toBeInTheDocument();
    });
  });

  it('displays matrix list when data exists', async () => {
    mockApi.markovListMatrices.mockResolvedValue([
      { matrix_id: 'M-001', model_name: 'Markov All', product_type: null, segment: null, matrix_type: 'annual', methodology: 'cohort', n_observations: 1000, computed_at: '2025-12-31' },
    ]);
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('Markov All')).toBeInTheDocument();
    });
  });

  it('handles API error on load', async () => {
    mockApi.markovListMatrices.mockRejectedValue(new Error('Load failed'));
    mockApi.portfolioSummary.mockRejectedValue(new Error('Load failed'));
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText(/Load failed/)).toBeInTheDocument();
    });
  });

  it('renders horizon selector', async () => {
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('60 months')).toBeInTheDocument();
    });
  });

  it('renders KPI cards when a matrix is selected', async () => {
    mockApi.markovListMatrices.mockResolvedValue([
      {
        matrix_id: 'M-001', model_name: 'Test',
        matrix_data: { matrix: [[0.9, 0.08, 0.02, 0], [0.1, 0.8, 0.1, 0], [0, 0.05, 0.7, 0.25], [0, 0, 0, 1]], states: ['Stage 1', 'Stage 2', 'Stage 3', 'Default'] },
        product_type: 'All', n_observations: 500, computed_at: '2025-12-31',
      },
    ]);
    mockApi.markovGetMatrix.mockResolvedValue({
      matrix_id: 'M-001', model_name: 'Test',
      matrix_data: { matrix: [[0.9, 0.08, 0.02, 0], [0.1, 0.8, 0.1, 0], [0, 0.05, 0.7, 0.25], [0, 0, 0, 1]], states: ['Stage 1', 'Stage 2', 'Stage 3', 'Default'] },
      product_type: 'All', n_observations: 500,
    });

    const user = userEvent.setup();
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('Test')).toBeInTheDocument();
    });
    // Click on matrix row to select it
    await user.click(screen.getByText('Test'));
    await waitFor(() => {
      expect(screen.getByText('SICR Probability')).toBeInTheDocument();
    });
    expect(screen.getByText('Cure Rate')).toBeInTheDocument();
    expect(screen.getByText('Default Probability')).toBeInTheDocument();
    expect(screen.getByText('Stage 1 Retention')).toBeInTheDocument();
  });

  it('switches to forecast tab', async () => {
    const user = userEvent.setup();
    render(<MarkovChains />);
    await waitFor(() => {
      expect(screen.getByText('Stage Forecast')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Stage Forecast'));
    await waitFor(() => {
      expect(screen.getByText(/No forecast generated/)).toBeInTheDocument();
    });
  });
});
