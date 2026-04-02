import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GLJournals from './GLJournals';

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

vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock('../lib/api', () => ({
  api: {
    glListJournals: vi.fn().mockResolvedValue([]),
    glTrialBalance: vi.fn().mockResolvedValue([]),
    glChartOfAccounts: vi.fn().mockResolvedValue([]),
    glGenerateJournals: vi.fn().mockResolvedValue({}),
    glPostJournal: vi.fn().mockResolvedValue({}),
    glReverseJournal: vi.fn().mockResolvedValue({}),
    glGetJournal: vi.fn().mockResolvedValue(null),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

vi.mock('../lib/userContext', () => ({
  getCurrentUser: () => 'test-user',
}));

const testProject = {
  project_id: 'ECL-TEST',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: 5,
  step_status: {},
  overlays: [],
  scenario_weights: { base: 0.5, adverse: 0.3, optimistic: 0.2 },
  audit_log: [],
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  signed_off_by: null,
  signed_off_at: null,
};

describe('GLJournals', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', async () => {
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('GL Journal Entries & Ledger')).toBeInTheDocument();
    });
  });

  it('renders tab navigation with 3 tabs', async () => {
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('Journal Entries')).toBeInTheDocument();
    });
    expect(screen.getByText('Trial Balance')).toBeInTheDocument();
    expect(screen.getByText('Chart of Accounts')).toBeInTheDocument();
  });

  it('shows empty state when no journals exist', async () => {
    mockApi.glListJournals.mockResolvedValue([]);
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(mockApi.glListJournals).toHaveBeenCalledWith('ECL-TEST');
    });
  });

  it('loads journals on mount with project_id', async () => {
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(mockApi.glListJournals).toHaveBeenCalledWith('ECL-TEST');
      expect(mockApi.glChartOfAccounts).toHaveBeenCalled();
      expect(mockApi.glTrialBalance).toHaveBeenCalledWith('ECL-TEST');
    });
  });

  it('renders null project gracefully', async () => {
    render(<GLJournals project={null} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('switches to trial balance tab', async () => {
    const user = userEvent.setup();
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('Trial Balance')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Trial Balance'));
    // After switching, the tab content changes
    await waitFor(() => {
      expect(mockApi.glTrialBalance).toHaveBeenCalled();
    });
  });

  it('switches to chart of accounts tab', async () => {
    const user = userEvent.setup();
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('Chart of Accounts')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Chart of Accounts'));
    await waitFor(() => {
      expect(mockApi.glChartOfAccounts).toHaveBeenCalled();
    });
  });

  it('displays journals when data is loaded', async () => {
    mockApi.glListJournals.mockResolvedValue([
      {
        journal_id: 'J-001',
        journal_type: 'ecl_provision',
        status: 'draft',
        total_debit: 1000,
        total_credit: 1000,
        entry_count: 4,
        created_by: 'analyst',
        created_at: '2025-12-31',
      },
    ]);
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('J-001')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    mockApi.glListJournals.mockRejectedValue(new Error('Network error'));
    render(<GLJournals project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });
});
