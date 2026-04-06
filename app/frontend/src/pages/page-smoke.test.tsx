/**
 * Smoke tests for all pages — verifies each page renders without crashing
 * and shows expected content.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, waitFor } from '@testing-library/react';

// Mock framer-motion globally
vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_target, _prop) => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, style, ...rest } = props;
        // Only pass valid DOM props
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'ref' || k === 'key' || k === 'disabled' || k === 'href' || k === 'target') {
            domProps[k] = v;
          }
        }
        return <div style={style} {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
  useAnimation: () => ({ start: vi.fn(), stop: vi.fn() }),
  useMotionValue: (v: number) => ({ get: () => v, set: vi.fn() }),
  useTransform: () => 0,
}));

// Mock recharts
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div data-testid="chart">{children}</div>,
  BarChart: ({ children }: any) => <div>{children}</div>,
  LineChart: ({ children }: any) => <div>{children}</div>,
  PieChart: ({ children }: any) => <div>{children}</div>,
  AreaChart: ({ children }: any) => <div>{children}</div>,
  ComposedChart: ({ children }: any) => <div>{children}</div>,
  RadarChart: ({ children }: any) => <div>{children}</div>,
  ScatterChart: ({ children }: any) => <div>{children}</div>,
  Treemap: () => <div />,
  Bar: () => null,
  Line: () => null,
  Pie: () => null,
  Area: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  Cell: () => null,
  ReferenceLine: () => null,
  Radar: () => null,
  PolarGrid: () => null,
  PolarAngleAxis: () => null,
  PolarRadiusAxis: () => null,
  Scatter: () => null,
}));

// Mock Toast context
vi.mock('../components/Toast', () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

// Mock api
vi.mock('../lib/api', () => ({
  api: {
    listProjects: vi.fn().mockResolvedValue([]),
    eclByProduct: vi.fn().mockResolvedValue([]),
    eclByCohort: vi.fn().mockResolvedValue([]),
    eclSummary: vi.fn().mockResolvedValue({ total_ecl: 0, total_gca: 0, coverage_ratio: 0 }),
    portfolioSummary: vi.fn().mockResolvedValue([]),
    portfolioByCohort: vi.fn().mockResolvedValue([]),
    stageDistribution: vi.fn().mockResolvedValue([]),
    scenarioSummary: vi.fn().mockResolvedValue([]),
    mcDistribution: vi.fn().mockResolvedValue([]),
    concentration: vi.fn().mockResolvedValue([]),
    migration: vi.fn().mockResolvedValue([]),
    sensitivity: vi.fn().mockResolvedValue([]),
    vintage: vi.fn().mockResolvedValue([]),
    eclAttribution: vi.fn().mockResolvedValue({ waterfall: [], opening: { stage1: 0, stage2: 0, stage3: 0, total: 0 }, closing: { stage1: 0, stage2: 0, stage3: 0, total: 0 }, reconciliation: { total_movement: 0, absolute_residual: 0, residual_pct: 0, within_materiality: true, materiality_threshold_pct: 1, data_gaps: [] } }),
    drillDownDimensions: vi.fn().mockResolvedValue([]),
    listModels: vi.fn().mockResolvedValue([]),
    modelComparison: vi.fn().mockResolvedValue([]),
    modelAudit: vi.fn().mockResolvedValue([]),
    backtestResults: vi.fn().mockResolvedValue([]),
    backtestTrend: vi.fn().mockResolvedValue([]),
    markovMatrices: vi.fn().mockResolvedValue([]),
    markovListMatrices: vi.fn().mockResolvedValue([]),
    markovForecast: vi.fn().mockResolvedValue([]),
    markovLifetimePd: vi.fn().mockResolvedValue([]),
    hazardModels: vi.fn().mockResolvedValue([]),
    hazardSurvivalCurve: vi.fn().mockResolvedValue([]),
    hazardTermStructure: vi.fn().mockResolvedValue([]),
    glJournals: vi.fn().mockResolvedValue([]),
    chartOfAccounts: vi.fn().mockResolvedValue([]),
    trialBalance: vi.fn().mockResolvedValue({ rows: [], total_debit: 0, total_credit: 0, balanced: true }),
    reportsList: vi.fn().mockResolvedValue([]),
    listApprovals: vi.fn().mockResolvedValue([]),
    approvalHistory: vi.fn().mockResolvedValue([]),
    rbacUsers: vi.fn().mockResolvedValue([]),
    rbacPermissions: vi.fn().mockResolvedValue([]),
    adminConfig: vi.fn().mockResolvedValue({}),
    setupStatus: vi.fn().mockResolvedValue({ status: 'complete' }),
    dataMappingStatus: vi.fn().mockResolvedValue({ status: 'not_started' }),
    dataMappingCatalogs: vi.fn().mockResolvedValue([]),
    cureRates: vi.fn().mockResolvedValue([]),
    ccfData: vi.fn().mockResolvedValue([]),
    collateralData: vi.fn().mockResolvedValue([]),
    periodCloseHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
    dqResults: vi.fn().mockResolvedValue([]),
    glReconciliation: vi.fn().mockResolvedValue([]),
    jobsConfig: vi.fn().mockResolvedValue({ job_ids: {} }),
    satelliteModelComparison: vi.fn().mockResolvedValue([]),
    satelliteModelSelected: vi.fn().mockResolvedValue([]),
    satelliteModelRuns: vi.fn().mockResolvedValue([]),
    satelliteCohortSummary: vi.fn().mockResolvedValue([]),
    cohortSummary: vi.fn().mockResolvedValue([]),
    modelRuns: vi.fn().mockResolvedValue([]),
    jobRuns: vi.fn().mockResolvedValue([]),
    simulationDefaults: vi.fn().mockResolvedValue({ n_simulations: 500, pd_lgd_correlation: 0.3, aging_factor: 1.0, pd_floor: 0.001, pd_cap: 0.999, lgd_floor: 0.05, lgd_cap: 0.95, scenario_weights: {}, products: [] }),
    lossAllowanceByStage: vi.fn().mockResolvedValue([]),
    eclByScenarioProduct: vi.fn().mockResolvedValue([]),
    simulationValidate: vi.fn().mockResolvedValue({ errors: [], warnings: [] }),
    projectAuditTrail: vi.fn().mockResolvedValue([]),
    configChanges: vi.fn().mockResolvedValue([]),
    getMyProjectRole: vi.fn().mockResolvedValue({ user_id: 'test-user', project_role: 'owner', rbac_role: 'admin' }),
    authMe: vi.fn().mockResolvedValue({ user_id: 'test-user', email: 'test@test.com', display_name: 'Test', role: 'admin', permissions: [] }),
  },
}));

vi.mock('../lib/chartTheme', () => ({
  useChartTheme: () => ({ text: '#333', grid: '#ccc', bg: '#fff', textMuted: '#999' }),
}));

vi.mock('../lib/chartUtils', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    chartAxisProps: () => ({}),
    sortChartData: (d: any[]) => d,
  };
});

vi.mock('../lib/config', () => ({
  config: {
    bankName: 'Test Bank',
    defaultReportingDate: '2025-12-31',
    projectTypes: ['ifrs9'],
    scenarios: { base: { label: 'Base', color: '#10B981' } },
    governance: { glReconciliationTolerancePct: 1, dqScoreThresholdPct: 90, cfoName: 'CFO' },
    currency: 'USD',
    currencyLocale: 'en-US',
    workflowSteps: [],
  },
}));

// Mock all sub-components that use complex dependencies
vi.mock('../components/SimulationPanel', () => ({
  default: () => <div data-testid="sim-panel">Simulation Panel</div>,
}));

vi.mock('../components/HelpPanel', () => ({
  default: () => <div data-testid="help-panel">Help</div>,
}));

vi.mock('../components/DrillDownChart', () => ({
  default: () => <div data-testid="drill-down">DrillDown</div>,
}));

vi.mock('../components/ThreeLevelDrillDown', () => ({
  default: () => <div data-testid="three-level">ThreeLevelDrillDown</div>,
}));

vi.mock('../components/ScenarioProductBarChart', () => ({
  default: () => <div data-testid="scenario-bar">ScenarioBarChart</div>,
}));

vi.mock('../components/NotebookLink', () => ({
  default: () => <div data-testid="notebook-link">NotebookLink</div>,
}));

vi.mock('../components/SetupWizard', () => ({
  default: () => <div data-testid="setup-wizard">SetupWizard</div>,
}));

vi.mock('../hooks/useEclData', () => ({
  useEclProductData: () => ({ eclProduct: [], eclCohortByProduct: {}, loading: false }),
  useCohortsByProduct: () => ({}),
}));

beforeEach(() => {
  vi.clearAllMocks();
  // Mock global fetch for pages that call fetch() directly
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  }));
});

const nullProject = {
  project_id: 'ECL-TEST',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: 3,
  step_status: {},
  overlays: [],
  scenario_weights: { base: 0.5, adverse: 0.3, optimistic: 0.2 },
  audit_log: [],
  created_at: '2025-01-01',
  updated_at: '2025-01-01',
  signed_off_by: null,
  signed_off_at: null,
};

describe('Page smoke tests — AdvancedFeatures', () => {
  it('renders without crashing', async () => {
    const { default: AdvancedFeatures } = await import('./AdvancedFeatures');
    render(<AdvancedFeatures />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — ApprovalWorkflow', () => {
  it('renders without crashing', async () => {
    const { default: ApprovalWorkflow } = await import('./ApprovalWorkflow');
    render(<ApprovalWorkflow />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — Backtesting', () => {
  it('renders without crashing', async () => {
    const { default: Backtesting } = await import('./Backtesting');
    render(<Backtesting />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — DataControl', () => {
  it('renders without crashing', async () => {
    const { default: DataControl } = await import('./DataControl');
    render(<DataControl project={nullProject} onApprove={vi.fn()} onReject={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — DataMapping', () => {
  it('renders without crashing', async () => {
    const { default: DataMapping } = await import('./DataMapping');
    render(<DataMapping />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — DataProcessing', () => {
  it('renders without crashing', async () => {
    const { default: DataProcessing } = await import('./DataProcessing');
    render(<DataProcessing project={nullProject} onComplete={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — GLJournals', () => {
  it('renders without crashing', async () => {
    const { default: GLJournals } = await import('./GLJournals');
    render(<GLJournals project={nullProject} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — HazardModels', () => {
  it('renders without crashing', async () => {
    const { default: HazardModels } = await import('./HazardModels');
    render(<HazardModels />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — MarkovChains', () => {
  it('renders without crashing', async () => {
    const { default: MarkovChains } = await import('./MarkovChains');
    render(<MarkovChains />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — ModelExecution', () => {
  it('renders without crashing', async () => {
    const { default: ModelExecution } = await import('./ModelExecution');
    render(<ModelExecution project={nullProject} onApprove={vi.fn()} onReject={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — ModelRegistry', () => {
  it('renders without crashing', async () => {
    const { default: ModelRegistry } = await import('./ModelRegistry');
    render(<ModelRegistry />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — Overlays', () => {
  it('renders without crashing', async () => {
    const { default: Overlays } = await import('./Overlays');
    render(<Overlays project={nullProject} onSubmit={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — RegulatoryReports', () => {
  it('renders without crashing', async () => {
    const { default: RegulatoryReports } = await import('./RegulatoryReports');
    render(<RegulatoryReports project={nullProject} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — SatelliteModel', () => {
  it('renders without crashing', async () => {
    const { default: SatelliteModel } = await import('./SatelliteModel');
    render(<SatelliteModel project={nullProject} onApprove={vi.fn()} onReject={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — SignOff', () => {
  it('renders without crashing', async () => {
    const { default: SignOff } = await import('./SignOff');
    render(<SignOff project={nullProject} onSignOff={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});

describe('Page smoke tests — StressTesting', () => {
  it('renders without crashing', async () => {
    const { default: StressTesting } = await import('./StressTesting');
    render(<StressTesting project={nullProject} onApprove={vi.fn()} onReject={vi.fn()} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });
});
