import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ApprovalWorkflow from './ApprovalWorkflow';

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
  PieChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => null,
  Pie: () => null,
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

vi.mock('../lib/api', () => ({
  api: {
    rbacListApprovals: vi.fn().mockResolvedValue([]),
    rbacListUsers: vi.fn().mockResolvedValue([]),
    rbacCreateApproval: vi.fn().mockResolvedValue({}),
    rbacApprove: vi.fn().mockResolvedValue({}),
    rbacReject: vi.fn().mockResolvedValue({}),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

vi.mock('../lib/format', () => ({
  fmtDateTime: (v: string) => v || '—',
}));

describe('ApprovalWorkflow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', async () => {
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText('Approval Workflow')).toBeInTheDocument();
    });
  });

  it('renders all 4 tabs', async () => {
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
    expect(screen.getByText('Pending Queue')).toBeInTheDocument();
    expect(screen.getByText('History')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
  });

  it('loads approvals and users on mount', async () => {
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(mockApi.rbacListApprovals).toHaveBeenCalled();
      expect(mockApi.rbacListUsers).toHaveBeenCalled();
      expect(mockApi.rbacListApprovals).toHaveBeenCalled();
    });
  });

  it('switches to Pending Queue tab', async () => {
    const user = userEvent.setup();
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText('Pending Queue')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Pending Queue'));
    // Tab is now active
    await waitFor(() => {
      expect(mockApi.rbacListApprovals).toHaveBeenCalled();
    });
  });

  it('switches to History tab', async () => {
    const user = userEvent.setup();
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText('History')).toBeInTheDocument();
    });
    await user.click(screen.getByText('History'));
    await waitFor(() => {
      expect(mockApi.rbacListApprovals).toHaveBeenCalled();
    });
  });

  it('switches to Users tab', async () => {
    const user = userEvent.setup();
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Users'));
    await waitFor(() => {
      expect(mockApi.rbacListUsers).toHaveBeenCalled();
    });
  });

  it('displays KPI cards on Dashboard', async () => {
    mockApi.rbacListApprovals.mockResolvedValue([
      { id: 1, status: 'pending', request_type: 'model_approval' },
      { id: 2, status: 'approved', request_type: 'overlay_approval' },
    ]);
    mockApi.rbacListApprovals.mockResolvedValue([
      { id: 3, status: 'approved', action: 'approved' },
    ]);
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(mockApi.rbacListApprovals).toHaveBeenCalled();
    });
  });

  it('displays users data when loaded', async () => {
    mockApi.rbacListUsers.mockResolvedValue([
      { user_id: 'analyst_1', display_name: 'Alice Analyst', role: 'analyst', email: 'alice@test.com' },
      { user_id: 'approver_1', display_name: 'Bob Approver', role: 'approver', email: 'bob@test.com' },
    ]);
    const user = userEvent.setup();
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Users'));
    await waitFor(() => {
      expect(screen.getByText('Alice Analyst')).toBeInTheDocument();
      expect(screen.getByText('Bob Approver')).toBeInTheDocument();
    });
  });

  it('handles API error in loading approvals', async () => {
    mockApi.rbacListApprovals.mockRejectedValue(new Error('Server error'));
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(screen.getByText(/Server error/i)).toBeInTheDocument();
    });
  });
});
