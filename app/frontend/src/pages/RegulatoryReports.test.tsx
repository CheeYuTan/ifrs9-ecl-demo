import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegulatoryReports from './RegulatoryReports';

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

vi.mock('../lib/api', () => ({
  api: {
    listReports: vi.fn().mockResolvedValue([]),
    generateReport: vi.fn().mockResolvedValue({}),
    getReport: vi.fn().mockResolvedValue(null),
    finalizeReport: vi.fn().mockResolvedValue({}),
    exportReportCsv: vi.fn().mockResolvedValue(new Blob()),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

const testProject = {
  project_id: 'PROJ-001',
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

describe('RegulatoryReports', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.listReports.mockResolvedValue([]);
  });

  it('renders page header', async () => {
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('Regulatory Reports')).toBeInTheDocument();
    });
  });

  it('renders KPI cards', async () => {
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('Total Reports')).toBeInTheDocument();
    });
    expect(screen.getByText('Draft')).toBeInTheDocument();
    expect(screen.getByText('Final')).toBeInTheDocument();
    expect(screen.getByText('Submitted')).toBeInTheDocument();
  });

  it('renders 5 report type generate buttons', async () => {
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      // Text appears in both generate buttons and filter dropdown
      expect(screen.getAllByText('IFRS 7 Disclosure').length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getAllByText('ECL Movement').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Stage Migration').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Sensitivity Analysis').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Concentration Risk').length).toBeGreaterThanOrEqual(1);
  });

  it('shows empty state when no reports exist', async () => {
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('No reports generated')).toBeInTheDocument();
    });
  });

  it('loads reports on mount', async () => {
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(mockApi.listReports).toHaveBeenCalled();
    });
  });

  it('displays report list when data exists', async () => {
    mockApi.listReports.mockResolvedValue([
      {
        report_id: 'RPT-001',
        report_type: 'ifrs7_disclosure',
        report_date: '2025-12-31',
        status: 'draft',
        generated_by: 'analyst',
        created_at: '2025-12-31T10:00:00',
      },
    ]);
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('RPT-001')).toBeInTheDocument();
    });
  });

  it('renders type filter dropdown', async () => {
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('All Types')).toBeInTheDocument();
    });
  });

  it('handles API error gracefully', async () => {
    mockApi.listReports.mockRejectedValue(new Error('Server error'));
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText(/Server error/)).toBeInTheDocument();
    });
  });

  it('shows warning when no project selected', async () => {
    render(<RegulatoryReports project={null} />);
    await waitFor(() => {
      expect(screen.getByText(/Select a project first/)).toBeInTheDocument();
    });
  });

  it('renders report status badges correctly', async () => {
    mockApi.listReports.mockResolvedValue([
      { report_id: 'RPT-001', report_type: 'ifrs7_disclosure', status: 'final', report_date: '2025-12-31', generated_by: 'analyst', created_at: '2025-12-31' },
    ]);
    render(<RegulatoryReports project={testProject} />);
    await waitFor(() => {
      expect(screen.getByText('Final')).toBeInTheDocument();
    });
  });
});
