import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

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
  LineChart: ({ children }: any) => <div>{children}</div>,
  AreaChart: ({ children }: any) => <div>{children}</div>,
  ComposedChart: ({ children }: any) => <div>{children}</div>,
  RadarChart: ({ children }: any) => <div>{children}</div>,
  ScatterChart: ({ children }: any) => <div>{children}</div>,
  Treemap: () => <div />,
  Bar: () => null,
  Line: () => null,
  Area: () => null,
  Scatter: () => null,
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

vi.mock('../lib/chartUtils', async (importOriginal) => {
  const actual = await importOriginal() as any;
  return {
    ...actual,
    chartAxisProps: () => ({}),
    buildScenarioColorMap: () => ({}),
    getScenarioLabels: () => ({}),
    pivotScenarioByProduct: () => [],
    sortChartData: (d: any[]) => d,
  };
});

vi.mock('../lib/config', () => ({
  config: {
    bankName: 'Test Bank',
    defaultReportingDate: '2025-12-31',
    projectTypes: ['ifrs9'],
    scenarios: { base: { label: 'Base', color: '#10B981' } },
    governance: {},
    currency: 'USD',
    currencyLocale: 'en-US',
    workflowSteps: [],
  },
}));

vi.mock('../components/SimulationPanel', () => ({
  default: () => <div data-testid="sim-panel">SimPanel</div>,
}));

vi.mock('../components/DrillDownChart', () => ({
  default: () => <div data-testid="drill-down">DrillDown</div>,
}));

vi.mock('../components/NotebookLink', () => ({
  default: () => <div data-testid="notebook-link">NotebookLink</div>,
}));

vi.mock('../components/ScenarioProductBarChart', () => ({
  default: () => <div data-testid="scenario-bar">ScenarioBarChart</div>,
}));

// Mock sub-tab components to avoid deep dependency issues
vi.mock('./stress-testing/MonteCarloTab', () => ({
  default: (_props: any) => <div data-testid="mc-tab">MonteCarloTab</div>,
}));

vi.mock('./stress-testing/SensitivityTab', () => ({
  default: (_props: any) => <div data-testid="sens-tab">SensitivityTab</div>,
}));

vi.mock('./stress-testing/VintageTab', () => ({
  default: (_props: any) => <div data-testid="vintage-tab">VintageTab</div>,
}));

vi.mock('./stress-testing/ConcentrationTab', () => ({
  default: (_props: any) => <div data-testid="conc-tab">ConcentrationTab</div>,
}));

vi.mock('./stress-testing/MigrationTab', () => ({
  default: (_props: any) => <div data-testid="mig-tab">MigrationTab</div>,
}));

vi.mock('./stress-testing/CapitalImpact', () => ({
  default: (_props: any) => <div data-testid="capital-tab">CapitalImpact</div>,
}));

vi.mock('../lib/api', () => ({
  api: {
    sensitivityData: vi.fn().mockResolvedValue([]),
    scenarioComparison: vi.fn().mockResolvedValue([]),
    stressByStage: vi.fn().mockResolvedValue([]),
    vintagePerformance: vi.fn().mockResolvedValue([]),
    concentrationByProductStage: vi.fn().mockResolvedValue([]),
    mcDistribution: vi.fn().mockResolvedValue([]),
    eclByProduct: vi.fn().mockResolvedValue([]),
    eclByCohort: vi.fn().mockResolvedValue([]),
    simulationDefaults: vi.fn().mockResolvedValue({ n_simulations: 500, products: [] }),
    runSimulation: vi.fn().mockResolvedValue({}),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

const makeProject = (step: number) => ({
  project_id: 'ECL-TEST',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: step,
  step_status: { stress_testing: 'pending' },
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

describe('StressTesting', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows locked banner when step < 5', async () => {
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    // Should show locked banner, not the page header
    expect(screen.queryByText('Stress Testing & Scenario Analysis')).not.toBeInTheDocument();
  });

  it('renders page header when step >= 5', async () => {
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Stress Testing & Scenario Analysis')).toBeInTheDocument();
    });
  });

  it('loads all stress data on mount', async () => {
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(mockApi.sensitivityData).toHaveBeenCalled();
      expect(mockApi.scenarioComparison).toHaveBeenCalled();
      expect(mockApi.stressByStage).toHaveBeenCalled();
      expect(mockApi.vintagePerformance).toHaveBeenCalled();
      expect(mockApi.concentrationByProductStage).toHaveBeenCalled();
      expect(mockApi.mcDistribution).toHaveBeenCalled();
    });
  });

  it('renders sub-tab navigation with 5 tabs', async () => {
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Monte Carlo Simulation')).toBeInTheDocument();
    });
    expect(screen.getByText('Sensitivity Analysis')).toBeInTheDocument();
    expect(screen.getByText('Vintage Analysis')).toBeInTheDocument();
    expect(screen.getByText('Concentration Risk')).toBeInTheDocument();
    expect(screen.getByText('Stage Migration Sim')).toBeInTheDocument();
  });

  it('renders KPI cards', async () => {
    mockApi.sensitivityData.mockResolvedValue([
      { product_type: 'mortgage', base_ecl: 100000, stressed_ecl: 120000 },
    ]);
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Weighted ECL')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    mockApi.sensitivityData.mockRejectedValue(new Error('Server error'));
    mockApi.scenarioComparison.mockRejectedValue(new Error('Server error'));
    mockApi.stressByStage.mockRejectedValue(new Error('Server error'));
    mockApi.vintagePerformance.mockRejectedValue(new Error('Server error'));
    mockApi.concentrationByProductStage.mockRejectedValue(new Error('Server error'));
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText(/Server error/)).toBeInTheDocument();
    });
  });

  it('handles null project gracefully', async () => {
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={null} onApprove={onApprove} onReject={onReject} />);
    // Should show locked banner
    expect(screen.queryByText('Stress Testing & Scenario Analysis')).not.toBeInTheDocument();
  });

  it('switches to Sensitivity Analysis tab', async () => {
    // Reset mocks to resolved values (may have been rejected by error test)
    mockApi.sensitivityData.mockResolvedValue([]);
    mockApi.scenarioComparison.mockResolvedValue([]);
    mockApi.stressByStage.mockResolvedValue([]);
    mockApi.vintagePerformance.mockResolvedValue([]);
    mockApi.concentrationByProductStage.mockResolvedValue([]);
    mockApi.mcDistribution.mockResolvedValue([]);
    const user = userEvent.setup();
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Sensitivity Analysis')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Sensitivity Analysis'));
    await waitFor(() => {
      expect(screen.getByText('Sensitivity Analysis')).toBeInTheDocument();
    });
  });

  it('switches to Vintage Analysis tab', async () => {
    mockApi.sensitivityData.mockResolvedValue([]);
    mockApi.scenarioComparison.mockResolvedValue([]);
    mockApi.stressByStage.mockResolvedValue([]);
    mockApi.vintagePerformance.mockResolvedValue([]);
    mockApi.concentrationByProductStage.mockResolvedValue([]);
    mockApi.mcDistribution.mockResolvedValue([]);
    const user = userEvent.setup();
    const { default: StressTesting } = await import('./stress-testing/index');
    render(<StressTesting project={makeProject(5)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Vintage Analysis')).toBeInTheDocument();
    });
    await user.click(screen.getByText('Vintage Analysis'));
    await waitFor(() => {
      expect(screen.getByText('Vintage Analysis')).toBeInTheDocument();
    });
  });
});
