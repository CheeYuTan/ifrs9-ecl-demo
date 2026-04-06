import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SatelliteModel from './SatelliteModel';

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
  Bar: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
}));

vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
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
    satelliteModelComparison: vi.fn().mockResolvedValue([]),
    satelliteModelSelected: vi.fn().mockResolvedValue([]),
    cohortSummary: vi.fn().mockResolvedValue([]),
    modelRuns: vi.fn().mockResolvedValue([]),
    triggerJob: vi.fn().mockResolvedValue({ run_id: 'JOB-001' }),
    jobRunStatus: vi.fn().mockResolvedValue({ status: 'completed' }),
    jobRuns: vi.fn().mockResolvedValue([]),
    getMyProjectRole: vi.fn().mockResolvedValue({ user_id: 'test-user', project_role: 'owner', rbac_role: 'admin' }),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

vi.mock('../lib/config', () => ({
  config: {
    bankName: 'Test Bank',
    defaultReportingDate: '2025-12-31',
    projectTypes: ['ifrs9'],
    scenarios: {},
    governance: {},
    currency: 'USD',
    currencyLocale: 'en-US',
    workflowSteps: [],
  },
}));

const makeProject = (step: number, stepStatus: Record<string, string> = {}) => ({
  project_id: 'ECL-TEST',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: step,
  step_status: stepStatus,
  overlays: [],
  scenario_weights: { base: 0.5, adverse: 0.3, optimistic: 0.2 },
  audit_log: [],
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  signed_off_by: null,
  signed_off_at: null,
});

const onApprove = vi.fn().mockResolvedValue(undefined);
const onReject = vi.fn().mockResolvedValue(undefined);

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({ model: { satellite_models: {} } }),
  }));
});

describe('SatelliteModel', () => {
  it('shows locked banner when step < 3', () => {
    render(<SatelliteModel project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    expect(screen.queryByText('Satellite Model Selection')).not.toBeInTheDocument();
  });

  it('renders page content when step >= 3', async () => {
    render(<SatelliteModel project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Satellite Model Selection')).toBeInTheDocument();
    });
  });

  it('loads comparison data on mount', async () => {
    render(<SatelliteModel project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(mockApi.satelliteModelComparison).toHaveBeenCalled();
      expect(mockApi.satelliteModelSelected).toHaveBeenCalled();
      expect(mockApi.cohortSummary).toHaveBeenCalled();
    });
  });

  it('loads model runs history', async () => {
    render(<SatelliteModel project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(mockApi.modelRuns).toHaveBeenCalledWith('satellite_model');
    });
  });

  it('renders model checkboxes for pipeline trigger', async () => {
    render(<SatelliteModel project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Satellite Model Selection')).toBeInTheDocument();
    });
    // Default model labels should appear as checkboxes
    expect(screen.getByText('Linear Regression')).toBeInTheDocument();
  });

  it('shows Run History button', async () => {
    render(<SatelliteModel project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Run History')).toBeInTheDocument();
    });
  });

  it('shows approval form when not completed', async () => {
    render(<SatelliteModel project={makeProject(3, { satellite_model: 'pending' })} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText(/Approve Satellite Model/)).toBeInTheDocument();
    });
  });

  it('shows completion banner when step is completed', async () => {
    render(<SatelliteModel project={makeProject(3, { satellite_model: 'completed' })} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText(/Satellite model selection approved/)).toBeInTheDocument();
    });
  });

  it('handles null project gracefully', () => {
    render(<SatelliteModel project={null} onApprove={onApprove} onReject={onReject} />);
    // Should show locked banner
    expect(screen.queryByText('Satellite Model Selection')).not.toBeInTheDocument();
  });

  it('displays model comparison data when loaded', async () => {
    mockApi.satelliteModelComparison.mockResolvedValue([
      { product_type: 'mortgage', cohort: 'A', model_type: 'linear_regression', r2: 0.85, rmse: 0.02, aic: 120 },
    ]);
    mockApi.satelliteModelSelected.mockResolvedValue([
      { product_type: 'mortgage', cohort: 'A', selected_model: 'linear_regression' },
    ]);
    render(<SatelliteModel project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Mortgage')).toBeInTheDocument();
    });
  });
});
