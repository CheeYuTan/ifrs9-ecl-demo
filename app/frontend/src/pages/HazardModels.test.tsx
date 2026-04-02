import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HazardModels from './HazardModels';

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
  Line: () => null,
  BarChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => null,
  Cell: () => null,
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
    hazardListModels: vi.fn().mockResolvedValue([]),
    hazardEstimate: vi.fn().mockResolvedValue({}),
    hazardGetModel: vi.fn().mockResolvedValue(null),
    hazardTermStructure: vi.fn().mockResolvedValue(null),
    hazardCompare: vi.fn().mockResolvedValue(null),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

describe('HazardModels', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.hazardListModels.mockResolvedValue([]);
  });

  it('renders page header after loading', async () => {
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('Hazard Models')).toBeInTheDocument();
    });
  });

  it('renders 6 sub-tabs', async () => {
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('Overview')).toBeInTheDocument();
    });
    expect(screen.getByText('Survival Curves')).toBeInTheDocument();
    expect(screen.getByText('Hazard Rates')).toBeInTheDocument();
    expect(screen.getByText('PD Term Structure')).toBeInTheDocument();
    expect(screen.getByText('Coefficients')).toBeInTheDocument();
    expect(screen.getByText('Compare')).toBeInTheDocument();
  });

  it('renders estimate button', async () => {
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('Estimate Model')).toBeInTheDocument();
    });
  });

  it('renders model type selector', async () => {
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByLabelText('Hazard model type')).toBeInTheDocument();
    });
  });

  it('loads models on mount', async () => {
    render(<HazardModels />);
    await waitFor(() => {
      expect(mockApi.hazardListModels).toHaveBeenCalled();
    });
  });

  it('shows empty state when no models', async () => {
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText(/No hazard models/i)).toBeInTheDocument();
    });
  });

  it('displays model list when data exists', async () => {
    mockApi.hazardListModels.mockResolvedValue([
      {
        model_id: 'HZ-001', model_type: 'cox_ph', concordance_index: 0.72,
        n_observations: 5000, estimation_date: '2025-12-31', created_at: '2025-12-31',
      },
    ]);
    mockApi.hazardGetModel.mockResolvedValue({
      model_id: 'HZ-001', model_type: 'cox_ph', concordance_index: 0.72,
      curves: [], coefficients: { covariates: [] },
    });
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('HZ-001')).toBeInTheDocument();
    });
  });

  it('handles estimation error', async () => {
    mockApi.hazardEstimate.mockRejectedValue(new Error('Estimation failed'));
    const user = userEvent.setup();
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('Estimate Model')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Estimate Model'));
    await waitFor(() => {
      expect(screen.getAllByText(/Estimation failed/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('switches between tabs', async () => {
    const user = userEvent.setup();
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('Survival Curves')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Survival Curves'));
    // Tab switched — no crash
    await waitFor(() => {
      expect(screen.getByText('Survival Curves')).toBeInTheDocument();
    });
  });

  it('renders KPI cards with model data', async () => {
    mockApi.hazardListModels.mockResolvedValue([
      {
        model_id: 'HZ-001', model_type: 'cox_ph', concordance_index: 0.72,
        n_observations: 5000, estimation_date: '2025-12-31', created_at: '2025-12-31',
      },
    ]);
    mockApi.hazardGetModel.mockResolvedValue({
      model_id: 'HZ-001', model_type: 'cox_ph', concordance_index: 0.72,
      curves: [], coefficients: { covariates: [] },
    });
    render(<HazardModels />);
    await waitFor(() => {
      expect(screen.getByText('Best Concordance')).toBeInTheDocument();
    });
  });
});
