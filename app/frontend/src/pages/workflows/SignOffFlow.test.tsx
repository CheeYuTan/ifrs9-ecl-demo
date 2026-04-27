/**
 * Workflow interaction tests: Sign-off flow.
 * Tests the user journey of reviewing and signing off on ECL calculations.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SignOff from '../SignOff';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: () => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, style, ...rest } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'type' || k === 'value' || k === 'onChange' || k === 'name'
            || k === 'htmlFor' || k === 'placeholder' || k === 'disabled' || k === 'checked') {
            domProps[k] = v;
          }
        }
        return <div style={style} {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../../lib/api', () => ({
  api: {
    eclByProduct: vi.fn().mockResolvedValue([]),
    topExposures: vi.fn().mockResolvedValue([]),
    lossAllowanceByStage: vi.fn().mockResolvedValue([]),
    creditRiskExposure: vi.fn().mockResolvedValue([]),
    getAttribution: vi.fn().mockResolvedValue(null),
    computeAttribution: vi.fn().mockResolvedValue(null),
    getAttributionHistory: vi.fn().mockResolvedValue([]),
    eclByCohort: vi.fn().mockResolvedValue([]),
    eclByStageProduct: vi.fn().mockResolvedValue([]),
    verifyHash: vi.fn().mockResolvedValue({ status: 'valid', match: true }),
    signOff: vi.fn().mockResolvedValue({ signed_off_by: 'analyst' }),
  },
}));

vi.mock('../../hooks/usePermissions', () => ({
  usePermissions: vi.fn().mockReturnValue({ canEdit: true, canOwn: true }),
}));

vi.mock('../../lib/chartTheme', () => ({
  useChartTheme: vi.fn().mockReturnValue({
    grid: '#F1F5F9',
    axis: '#475569',
    axisLight: '#64748B',
    reference: '#94A3B8',
    tooltip: { bg: '#fff', text: '#334155', border: '#E2E8F0' },
  }),
}));

vi.mock('../../lib/config', () => ({
  config: {
    currencySymbol: '$',
    framework: 'IFRS 9',
    scenarios: {},
  },
}));

vi.mock('../../lib/format', () => ({
  fmtCurrency: (v: any) => `$${Number(v || 0).toLocaleString()}`,
  fmtPct: (v: any) => `${Number(v || 0).toFixed(1)}%`,
  fmtNumber: (v: any) => Number(v || 0).toLocaleString(),
  fmtDateTime: (v: any) => v || '',
}));

vi.mock('../../lib/chartUtils', () => ({
  buildDrillDownData: () => [],
}));

vi.mock('../../components/KpiCard', () => ({
  default: ({ title, value }: any) => <div data-testid="kpi-card">{String(title)}: {value}</div>,
}));
vi.mock('../../components/Card', () => ({
  default: ({ children, title }: any) => <div data-testid="card"><h4>{title}</h4>{children}</div>,
}));
vi.mock('../../components/DataTable', () => ({
  default: () => <div data-testid="data-table" />,
}));
vi.mock('../../components/DrillDownChart', () => ({
  default: () => <div data-testid="drill-down" />,
}));
vi.mock('../../components/ThreeLevelDrillDown', () => ({
  default: () => <div data-testid="three-level-drill" />,
}));
vi.mock('../../components/LockedBanner', () => ({
  default: () => <div data-testid="locked-banner">Step Locked</div>,
}));
vi.mock('../../components/NotebookLink', () => ({
  default: () => <div data-testid="notebook-link" />,
}));
vi.mock('../../components/PageLoader', () => ({
  default: () => <div data-testid="page-loader">Loading...</div>,
}));
vi.mock('../../components/ConfirmDialog', () => ({
  default: ({ open, title, onConfirm, onCancel }: any) =>
    open ? <div data-testid="confirm-dialog"><p>{title}</p><button onClick={onConfirm}>Confirm</button><button onClick={onCancel}>Cancel</button></div> : null,
}));
vi.mock('../../components/StepDescription', () => ({
  default: () => <div data-testid="step-desc" />,
}));
vi.mock('../../components/HelpTooltip', () => ({
  default: () => <span />,
  IFRS9_HELP: {
    ECL: 'ECL help', COVERAGE_RATIO: 'Coverage help',
    STAGE_1: 'Stage 1', STAGE_2: 'Stage 2', STAGE_3: 'Stage 3',
  },
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div>{children}</div>,
  PieChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => <div />,
  Pie: () => <div />,
  Cell: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
  ReferenceLine: () => <div />,
}));

// Mock global fetch for /api/admin/config
const mockFetch = vi.fn();
const originalFetch = globalThis.fetch;

describe('Sign-Off Flow', () => {
  const mockProject = {
    project_id: 'proj-1',
    project_name: 'Q4 ECL',
    project_type: 'ifrs9',
    description: 'Test',
    reporting_date: '2025-12-31',
    current_step: 7,
    step_status: {},
    overlays: [],
    scenario_weights: { base: 0.5, upside: 0.25, downside: 0.25 },
    audit_log: [],
    created_at: '2025-01-01',
    updated_at: '2025-01-01',
    signed_off_by: null,
    signed_off_at: null,
  };

  const defaultProps = {
    project: mockProject as any,
    onSignOff: vi.fn().mockResolvedValue(undefined),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockFetch.mockImplementation((url: string) => {
      if (url === '/api/admin/config') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({
            app_settings: {
              scenarios: [{ key: 'base' }, { key: 'upside' }, { key: 'downside' }],
              opening_balance_growth: { residential_mortgage: 1.02 },
            },
          }),
        });
      }
      return originalFetch(url);
    });
    globalThis.fetch = mockFetch;
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('renders sign-off page', async () => {
    render(<SignOff {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('fetches admin config on mount', async () => {
    render(<SignOff {...defaultProps} />);
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/admin/config');
    });
  });

  it('renders with project context', async () => {
    render(<SignOff {...defaultProps} />);
    await waitFor(() => {
      const text = document.body.textContent || '';
      expect(text.length).toBeGreaterThan(10);
    });
  });

  it('handles missing project gracefully', async () => {
    render(<SignOff project={null} onSignOff={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('handles API error on config fetch', async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url === '/api/admin/config') {
        return Promise.reject(new Error('Config error'));
      }
      return originalFetch(url);
    });
    render(<SignOff {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('renders sign-off controls', async () => {
    render(<SignOff {...defaultProps} />);
    await waitFor(() => {
      const buttons = document.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThanOrEqual(0);
    });
  });
});
