import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SignOff from './SignOff';

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
  ReferenceLine: () => null,
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
    eclByProduct: vi.fn().mockResolvedValue([]),
    eclByCohort: vi.fn().mockResolvedValue([]),
    topExposures: vi.fn().mockResolvedValue([]),
    lossAllowanceByStage: vi.fn().mockResolvedValue([]),
    creditRiskExposure: vi.fn().mockResolvedValue([]),
    getAttribution: vi.fn().mockResolvedValue(null),
    computeAttribution: vi.fn().mockResolvedValue(null),
    verifyHash: vi.fn().mockResolvedValue({ status: 'ok', match: true }),
    jobsConfig: vi.fn().mockResolvedValue({ job_ids: {} }),
    drillDownDimensions: vi.fn().mockResolvedValue([]),
    getMyProjectRole: vi.fn().mockResolvedValue({ user_id: 'test-user', project_role: 'owner', rbac_role: 'admin' }),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

const makeProject = (step: number, signedOff = false) => ({
  project_id: 'PROJ-001',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: step,
  step_status: { sign_off: 'pending' },
  overlays: [],
  scenario_weights: { base: 0.5, adverse: 0.3, optimistic: 0.2 },
  audit_log: [],
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  signed_off_by: signedOff ? 'J. Smith' : null,
  signed_off_at: signedOff ? '2025-12-31T10:00:00' : null,
});

const onSignOff = vi.fn().mockResolvedValue(undefined);

describe('SignOff', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.eclByProduct.mockResolvedValue([]);
    mockApi.topExposures.mockResolvedValue([]);
    mockApi.lossAllowanceByStage.mockResolvedValue([]);
    mockApi.creditRiskExposure.mockResolvedValue([]);
    mockApi.getAttribution.mockResolvedValue(null);
  });

  it('shows locked banner when step < 7', () => {
    render(<SignOff project={makeProject(6)} onSignOff={onSignOff} />);
    expect(screen.queryByText('Final ECL: Awaiting Sign-Off')).not.toBeInTheDocument();
  });

  it('renders page header when step >= 7', async () => {
    render(<SignOff project={makeProject(7)} onSignOff={onSignOff} />);
    await waitFor(() => {
      expect(screen.getByText('Final ECL: Awaiting Sign-Off')).toBeInTheDocument();
    });
  });

  it('loads ECL data on mount', async () => {
    render(<SignOff project={makeProject(7)} onSignOff={onSignOff} />);
    await waitFor(() => {
      expect(mockApi.eclByProduct).toHaveBeenCalled();
      expect(mockApi.topExposures).toHaveBeenCalledWith(10);
    });
  });

  it('loads attribution on mount', async () => {
    render(<SignOff project={makeProject(7)} onSignOff={onSignOff} />);
    await waitFor(() => {
      expect(mockApi.getAttribution).toHaveBeenCalledWith('PROJ-001');
    });
  });

  it('shows null project as locked', () => {
    render(<SignOff project={null} onSignOff={onSignOff} />);
    expect(screen.queryByText(/Sign-Off|Executive Summary/i)).not.toBeInTheDocument();
  });

  it('verifies hash when project is signed off', async () => {
    render(<SignOff project={makeProject(7, true)} onSignOff={onSignOff} />);
    await waitFor(() => {
      expect(mockApi.verifyHash).toHaveBeenCalledWith('PROJ-001');
    });
  });

  it('renders ECL product data when available', async () => {
    mockApi.eclByProduct.mockResolvedValue([
      { product_type: 'Credit Card', total_ecl: 5000000, loan_count: 100 },
    ]);
    render(<SignOff project={makeProject(7)} onSignOff={onSignOff} />);
    await waitFor(() => {
      expect(screen.getByText(/Credit Card/)).toBeInTheDocument();
    });
  });

  it('renders attestation checkboxes', async () => {
    render(<SignOff project={makeProject(7)} onSignOff={onSignOff} />);
    await waitFor(() => {
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes.length).toBeGreaterThanOrEqual(4);
    });
  });
});
