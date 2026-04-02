import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Overlays from './Overlays';

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
    jobsConfig: vi.fn().mockResolvedValue({ job_ids: {} }),
    drillDownDimensions: vi.fn().mockResolvedValue([]),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

const makeProject = (step: number, overlays?: any[]) => ({
  project_id: 'PROJ-001',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: step,
  step_status: { overlays: 'pending' },
  overlays: overlays || [],
  scenario_weights: { base: 0.5, adverse: 0.3, optimistic: 0.2 },
  audit_log: [],
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  signed_off_by: null,
  signed_off_at: null,
});

const onSubmit = vi.fn().mockResolvedValue(undefined);

describe('Overlays', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApi.eclByProduct.mockResolvedValue([
      { product_type: 'Credit Card', total_ecl: 5000000 },
    ]);
    mockApi.eclByCohort.mockResolvedValue([]);
  });

  it('shows locked banner when step < 6', () => {
    render(<Overlays project={makeProject(5)} onSubmit={onSubmit} />);
    // LockedBanner renders — page header should not appear
    expect(screen.queryByText('Management Overlays')).not.toBeInTheDocument();
  });

  it('renders page header when step >= 6', async () => {
    render(<Overlays project={makeProject(6)} onSubmit={onSubmit} />);
    await waitFor(() => {
      expect(screen.getByText('Management Overlays')).toBeInTheDocument();
    });
  });

  it('renders KPI cards', async () => {
    render(<Overlays project={makeProject(6)} onSubmit={onSubmit} />);
    await waitFor(() => {
      expect(screen.getByText('Active Overlays')).toBeInTheDocument();
    });
    expect(screen.getByText('Net Impact')).toBeInTheDocument();
    expect(screen.getByText('Adjusted ECL')).toBeInTheDocument();
  });

  it('loads ECL by product on mount', async () => {
    render(<Overlays project={makeProject(6)} onSubmit={onSubmit} />);
    await waitFor(() => {
      expect(mockApi.eclByProduct).toHaveBeenCalled();
    });
  });

  it('renders default overlays when project has none', async () => {
    render(<Overlays project={makeProject(6)} onSubmit={onSubmit} />);
    await waitFor(() => {
      expect(screen.getByText(/OVL-001/)).toBeInTheDocument();
    });
  });

  it('shows null project as locked', () => {
    render(<Overlays project={null} onSubmit={onSubmit} />);
    expect(screen.queryByText('Management Overlays')).not.toBeInTheDocument();
  });

  it('renders step description with IFRS reference', async () => {
    render(<Overlays project={makeProject(6)} onSubmit={onSubmit} />);
    await waitFor(() => {
      expect(screen.getAllByText(/B5.5.17/).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders overlay entries with IDs', async () => {
    render(<Overlays project={makeProject(6)} onSubmit={onSubmit} />);
    await waitFor(() => {
      expect(screen.getByText('OVL-001')).toBeInTheDocument();
    });
    expect(screen.getByText('OVL-002')).toBeInTheDocument();
    expect(screen.getByText('OVL-003')).toBeInTheDocument();
  });
});
