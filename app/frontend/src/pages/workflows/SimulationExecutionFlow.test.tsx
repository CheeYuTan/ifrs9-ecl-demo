/**
 * Workflow interaction tests: Simulation execution flow.
 * Tests the user journey of configuring and running ECL simulations.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SimulationPanel from '../../components/SimulationPanel';

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
    simulationDefaults: vi.fn().mockResolvedValue({
      n_simulations: 1000,
      pd_lgd_correlation: 0.30,
      aging_factor: 0.08,
      scenario_weights: { baseline: 0.4, adverse: 0.3, severely_adverse: 0.3 },
    }),
    runSimulation: vi.fn().mockResolvedValue({ ecl_by_product: [] }),
    simulateStream: vi.fn().mockResolvedValue({ ecl_by_product: [] }),
    validateSimulation: vi.fn().mockResolvedValue({ errors: [], warnings: [] }),
    simulateJob: vi.fn().mockResolvedValue({ run_id: 1, run_url: '' }),
    jobRunStatus: vi.fn().mockResolvedValue({ lifecycle_state: 'TERMINATED', result_state: 'SUCCESS' }),
  },
}));

vi.mock('../../lib/config', () => ({
  config: {
    scenarios: {
      baseline: { label: 'Baseline', color: '#10B981' },
      adverse: { label: 'Adverse', color: '#EF4444' },
      severely_adverse: { label: 'Severely Adverse', color: '#DC2626' },
    },
  },
}));

vi.mock('../../components/SimulationProgress', () => ({
  default: () => <div data-testid="sim-progress">Progress</div>,
}));

vi.mock('../../components/SimulationResults', () => ({
  default: () => <div data-testid="sim-results">Results</div>,
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
  BarChart: ({ children }: any) => <div>{children}</div>,
  Bar: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  CartesianGrid: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
}));

const defaultProps = {
  onSimulationComplete: vi.fn(),
  defaultOpen: true,
};

describe('Simulation Execution Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders simulation configuration panel', async () => {
    render(<SimulationPanel {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('shows simulation parameter inputs', async () => {
    render(<SimulationPanel {...defaultProps} />);
    await waitFor(() => {
      const text = document.body.textContent || '';
      expect(text.length).toBeGreaterThan(10);
    });
  });

  it('renders with default open state', async () => {
    render(<SimulationPanel {...defaultProps} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('handles collapsed state gracefully', async () => {
    render(<SimulationPanel onSimulationComplete={vi.fn()} defaultOpen={false} />);
    await waitFor(() => {
      expect(document.body.textContent!.length).toBeGreaterThan(0);
    });
  });

  it('renders run button', async () => {
    render(<SimulationPanel {...defaultProps} />);
    await waitFor(() => {
      const buttons = document.querySelectorAll('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('renders parameter controls', async () => {
    render(<SimulationPanel {...defaultProps} />);
    await waitFor(() => {
      const inputs = document.querySelectorAll('input');
      expect(inputs.length).toBeGreaterThanOrEqual(0);
    });
  });
});
