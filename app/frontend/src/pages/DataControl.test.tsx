import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import DataControl from './DataControl';

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

vi.mock('../lib/api', () => ({
  api: {
    dqResults: vi.fn().mockResolvedValue([]),
    glReconciliation: vi.fn().mockResolvedValue([]),
    jobsConfig: vi.fn().mockResolvedValue({ job_ids: {} }),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

const makeProject = (step: number) => ({
  project_id: 'PROJ-001',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: step,
  step_status: { data_control: 'pending' },
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

describe('DataControl', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.dqResults.mockResolvedValue([]);
    mockApi.glReconciliation.mockResolvedValue([]);
  });

  it('shows locked banner when step < 2', () => {
    render(<DataControl project={makeProject(1)} onApprove={onApprove} onReject={onReject} />);
    // LockedBanner renders when step < 2
    expect(screen.queryByText('Data Control')).not.toBeInTheDocument();
  });

  it('renders page header when step >= 2', async () => {
    render(<DataControl project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Data Control')).toBeInTheDocument();
    });
  });

  it('loads DQ results and GL reconciliation', async () => {
    render(<DataControl project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(mockApi.dqResults).toHaveBeenCalled();
      expect(mockApi.glReconciliation).toHaveBeenCalled();
    });
  });

  it('renders KPI cards', async () => {
    mockApi.dqResults.mockResolvedValue([
      { check_id: 'DQ-001', passed: true, severity: 'high', category: 'completeness', description: 'test', failures: 0 },
      { check_id: 'DQ-002', passed: false, severity: 'critical', category: 'accuracy', description: 'test', failures: 3 },
    ]);
    mockApi.glReconciliation.mockResolvedValue([
      { product_type: 'mortgage', gl_balance: 1000, loan_tape_balance: 1000, variance: 0, variance_pct: 0, status: 'PASS' },
    ]);

    render(<DataControl project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('DQ Score')).toBeInTheDocument();
    });
    expect(screen.getAllByText('GL Reconciliation').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Critical Failures')).toBeInTheDocument();
    expect(screen.getByText('Step Status')).toBeInTheDocument();
  });

  it('shows error state on API failure', async () => {
    mockApi.dqResults.mockRejectedValue(new Error('Network error'));
    render(<DataControl project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it('renders null for null project', () => {
    render(<DataControl project={null} onApprove={onApprove} onReject={onReject} />);
    expect(screen.queryByText('Data Control')).not.toBeInTheDocument();
  });

  it('renders DQ checks table heading', async () => {
    mockApi.dqResults.mockResolvedValue([
      { check_id: 'DQ-001', passed: true, severity: 'high', category: 'completeness', description: 'No nulls', failures: 0 },
    ]);
    render(<DataControl project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Data Quality Checks')).toBeInTheDocument();
    });
  });

  it('renders GL reconciliation table heading', async () => {
    render(<DataControl project={makeProject(2)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getAllByText(/GL Reconciliation/).length).toBeGreaterThanOrEqual(1);
    });
  });
});
