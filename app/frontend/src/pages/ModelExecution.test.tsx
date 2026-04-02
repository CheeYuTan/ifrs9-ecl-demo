import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ModelExecution from './ModelExecution';

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
    scenarioGridClass: () => '',
    pivotScenarioByProduct: () => [],
    buildDrillDownData: () => [],
    sortChartData: (d: any[]) => d,
  };
});

vi.mock('../lib/config', () => ({
  config: {
    bankName: 'Test Bank',
    defaultReportingDate: '2025-12-31',
    projectTypes: ['ifrs9'],
    scenarios: { base: { label: 'Base', color: '#10B981' }, adverse: { label: 'Adverse', color: '#EF4444' } },
    governance: {},
    currency: 'USD',
    currencyLocale: 'en-US',
    workflowSteps: [],
  },
  type: {} as any,
}));

vi.mock('../components/SimulationPanel', () => ({
  default: (_props: any) => <div data-testid="sim-panel">SimPanel</div>,
}));

vi.mock('../components/DrillDownChart', () => ({
  default: () => <div data-testid="drill-down">DrillDown</div>,
}));

vi.mock('../components/ThreeLevelDrillDown', () => ({
  default: () => <div data-testid="three-level">ThreeLevelDrillDown</div>,
}));

vi.mock('../components/NotebookLink', () => ({
  default: () => <div data-testid="notebook-link">NotebookLink</div>,
}));

vi.mock('../components/ScenarioProductBarChart', () => ({
  default: () => <div data-testid="scenario-bar">ScenarioBarChart</div>,
}));

vi.mock('../lib/api', () => ({
  api: {
    eclByProduct: vi.fn().mockResolvedValue([]),
    scenarioSummary: vi.fn().mockResolvedValue([]),
    lossAllowanceByStage: vi.fn().mockResolvedValue([]),
    eclByScenarioProduct: vi.fn().mockResolvedValue([]),
    eclByCohort: vi.fn().mockResolvedValue([]),
    simulationDefaults: vi.fn().mockResolvedValue({ n_simulations: 500, products: [] }),
  },
}));

import { api } from '../lib/api';
const mockApi = api as any;

const makeProject = (step: number, stepStatus: Record<string, string> = {}) => ({
  project_id: 'ECL-TEST',
  project_name: 'Test Project',
  project_type: 'ifrs9',
  description: 'Test',
  reporting_date: '2025-12-31',
  current_step: step,
  step_status: { model_execution: 'pending', model_control: 'pending', ...stepStatus },
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
    json: () => Promise.resolve({}),
  }));
});

describe('ModelExecution', () => {
  it('shows locked banner when step < 4', () => {
    render(<ModelExecution project={makeProject(3)} onApprove={onApprove} onReject={onReject} />);
    expect(screen.queryByText('Model Execution & Control')).not.toBeInTheDocument();
  });

  it('renders page header when step >= 4', async () => {
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Model Execution & Control')).toBeInTheDocument();
    });
  });

  it('loads ECL data on mount', async () => {
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(mockApi.eclByProduct).toHaveBeenCalled();
      expect(mockApi.scenarioSummary).toHaveBeenCalled();
      expect(mockApi.lossAllowanceByStage).toHaveBeenCalled();
      expect(mockApi.eclByScenarioProduct).toHaveBeenCalled();
    });
  });

  it('renders KPI cards with ECL data', async () => {
    mockApi.eclByProduct.mockResolvedValue([
      { product_type: 'mortgage', total_ecl: 500000, total_gca: 10000000 },
    ]);
    mockApi.scenarioSummary.mockResolvedValue([
      { scenario: 'base', total_ecl: 500000, weight: 0.5 },
    ]);
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText('Total ECL')).toBeInTheDocument();
    });
    expect(screen.getByText('Coverage')).toBeInTheDocument();
    expect(screen.getByText('Scenarios')).toBeInTheDocument();
    expect(screen.getByText('Products')).toBeInTheDocument();
  });

  it('renders SimulationPanel component', async () => {
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByTestId('sim-panel')).toBeInTheDocument();
    });
  });

  it('renders step description', async () => {
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText(/ECL calculation engine/)).toBeInTheDocument();
    });
  });

  it('handles null project gracefully', () => {
    render(<ModelExecution project={null} onApprove={onApprove} onReject={onReject} />);
    expect(screen.queryByText('Model Execution & Control')).not.toBeInTheDocument();
  });

  it('renders drill-down chart components', async () => {
    mockApi.eclByProduct.mockResolvedValue([
      { product_type: 'mortgage', total_ecl: 500000, total_gca: 10000000 },
    ]);
    mockApi.scenarioSummary.mockResolvedValue([{ scenario: 'base', total_ecl: 500000 }]);
    mockApi.lossAllowanceByStage.mockResolvedValue([{ assessed_stage: 1, total_ecl: 400000 }]);
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      const drillDowns = screen.getAllByTestId('drill-down');
      expect(drillDowns.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('loads simulation defaults', async () => {
    render(<ModelExecution project={makeProject(4)} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(mockApi.simulationDefaults).toHaveBeenCalled();
    });
  });

  it('renders approval form for pending step', async () => {
    mockApi.eclByProduct.mockResolvedValue([]);
    render(<ModelExecution project={makeProject(4, { model_execution: 'pending' })} onApprove={onApprove} onReject={onReject} />);
    await waitFor(() => {
      expect(screen.getByText(/Approve Model Results/)).toBeInTheDocument();
    });
  });
});
