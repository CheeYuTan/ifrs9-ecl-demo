import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdvancedFeatures from './AdvancedFeatures';

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
  BarChart: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => null,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
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
    listCureAnalyses: vi.fn().mockResolvedValue([]),
    getCureAnalysis: vi.fn().mockResolvedValue(null),
    computeCureRates: vi.fn().mockResolvedValue({}),
    listCCFAnalyses: vi.fn().mockResolvedValue([]),
    getCCFAnalysis: vi.fn().mockResolvedValue(null),
    computeCCF: vi.fn().mockResolvedValue({}),
    listCollateralAnalyses: vi.fn().mockResolvedValue([]),
    getCollateralAnalysis: vi.fn().mockResolvedValue(null),
    computeCollateral: vi.fn().mockResolvedValue({}),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

describe('AdvancedFeatures', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page heading', async () => {
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getByText('Advanced ECL Features')).toBeInTheDocument();
    });
  });

  it('renders subtitle text', async () => {
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getByText(/Cure rate modeling/)).toBeInTheDocument();
    });
  });

  it('renders 3 tab buttons', async () => {
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getByText('Cure Rates')).toBeInTheDocument();
    });
    expect(screen.getByText('CCF Analysis')).toBeInTheDocument();
    expect(screen.getByText('Collateral Haircuts')).toBeInTheDocument();
  });

  it('loads cure analyses on mount (default tab)', async () => {
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(mockApi.listCureAnalyses).toHaveBeenCalled();
    });
  });

  it('shows compute button for cure rates', async () => {
    mockApi.listCureAnalyses.mockResolvedValue([]);
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getAllByText('Compute Cure Rates').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('switches to CCF Analysis tab', async () => {
    const user = userEvent.setup();
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getByText('CCF Analysis')).toBeInTheDocument();
    });
    await user.click(screen.getByText('CCF Analysis'));
    await waitFor(() => {
      expect(mockApi.listCCFAnalyses).toHaveBeenCalled();
    });
  });

  it('switches to Collateral Haircuts tab', async () => {
    const user = userEvent.setup();
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getByText('Collateral Haircuts')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Collateral Haircuts'));
    await waitFor(() => {
      expect(mockApi.listCollateralAnalyses).toHaveBeenCalled();
    });
  });

  it('shows analysis count when analyses exist', async () => {
    mockApi.listCureAnalyses.mockResolvedValue([
      { analysis_id: 'CURE-001', created_at: '2025-12-01' },
      { analysis_id: 'CURE-002', created_at: '2025-12-15' },
    ]);
    mockApi.getCureAnalysis.mockResolvedValue({
      cure_by_dpd: [{ dpd_bucket: '30', cure_rate: 0.15 }],
      cure_by_product: [],
      cure_trend: [],
      time_to_cure: [],
    });
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getByText('2 analysis run(s)')).toBeInTheDocument();
    });
  });

  it('displays cure rate data when loaded', async () => {
    mockApi.listCureAnalyses.mockResolvedValue([
      { analysis_id: 'CURE-001', created_at: '2025-12-01' },
    ]);
    mockApi.getCureAnalysis.mockResolvedValue({
      cure_by_dpd: [{ dpd_bucket: '30-60', cure_rate: 0.15 }],
      cure_by_product: [{ product_type: 'mortgage', cure_rate: 0.12 }],
      cure_trend: [],
      time_to_cure: [],
    });
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(mockApi.getCureAnalysis).toHaveBeenCalledWith('CURE-001');
    });
  });

  it('handles compute error gracefully', async () => {
    mockApi.listCureAnalyses.mockResolvedValue([]);
    mockApi.computeCureRates.mockRejectedValue(new Error('Computation timeout'));
    const user = userEvent.setup();
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(screen.getAllByText('Compute Cure Rates').length).toBeGreaterThanOrEqual(1);
    });
    await user.click(screen.getAllByText('Compute Cure Rates')[0]);
    await waitFor(() => {
      expect(screen.getByText(/Computation timeout/)).toBeInTheDocument();
    });
  });
});
