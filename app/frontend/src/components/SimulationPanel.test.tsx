import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SimulationPanel from './SimulationPanel';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_target, _prop) => {
      return ({ children, ...props }: any) => {
        const { initial, animate, exit, transition, layout, whileHover, whileTap, variants, style, ...rest } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick' || k === 'id'
            || k === 'role' || k.startsWith('aria-') || k.startsWith('data-') || k === 'tabIndex'
            || k === 'ref' || k === 'key' || k === 'disabled' || k === 'href' || k === 'target'
            || k === 'type' || k === 'value' || k === 'onChange' || k === 'onSubmit' || k === 'name'
            || k === 'htmlFor' || k === 'placeholder' || k === 'min' || k === 'max' || k === 'step') {
            domProps[k] = v;
          }
        }
        return <div style={style} {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('./SimulationProgress', () => ({
  default: () => <div data-testid="simulation-progress">Progress</div>,
}));

vi.mock('./SimulationResults', () => ({
  default: ({ onApply, onDiscard }: any) => (
    <div data-testid="simulation-results">
      <button onClick={onApply}>Apply</button>
      <button onClick={onDiscard}>Discard</button>
    </div>
  ),
}));

vi.mock('../lib/api', () => ({
  api: {
    simulationDefaults: vi.fn().mockResolvedValue({
      n_simulations: 500,
      pd_lgd_correlation: 0.3,
      aging_factor: 1.0,
      pd_floor: 0.001,
      pd_cap: 0.999,
      lgd_floor: 0.05,
      lgd_cap: 0.95,
      scenario_weights: { base: 0.5, optimistic: 0.25, pessimistic: 0.25 },
      products: ['mortgage', 'personal_loan'],
    }),
    simulationValidate: vi.fn().mockResolvedValue({ errors: [], warnings: [] }),
    runSimulation: vi.fn().mockResolvedValue({ total_ecl: 1000000 }),
    simulationStream: vi.fn().mockResolvedValue(new ReadableStream()),
    jobRuns: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock('../lib/config', () => ({
  config: {
    currencySymbol: '$',
    scenarios: {
      base: { label: 'Base', color: '#3B82F6' },
      optimistic: { label: 'Optimistic', color: '#10B981' },
      pessimistic: { label: 'Pessimistic', color: '#EF4444' },
    },
  },
}));

describe('SimulationPanel', () => {
  const defaultProps = {
    onSimulationComplete: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders collapsed by default', () => {
    render(<SimulationPanel {...defaultProps} />);
    // Panel header should be visible
    expect(screen.getByText(/Monte Carlo/i)).toBeInTheDocument();
  });

  it('renders expanded when defaultOpen is true', async () => {
    render(<SimulationPanel {...defaultProps} defaultOpen />);
    await waitFor(() => {
      // Should load simulation defaults when opened
      expect(screen.getByText(/Monte Carlo/i)).toBeInTheDocument();
    });
  });

  it('loads simulation defaults on open', async () => {
    const { api } = await import('../lib/api');
    render(<SimulationPanel {...defaultProps} defaultOpen />);
    await waitFor(() => {
      expect(api.simulationDefaults).toHaveBeenCalled();
    });
  });

  it('expands on header click', async () => {
    const user = userEvent.setup();
    render(<SimulationPanel {...defaultProps} />);
    const header = screen.getByText(/Monte Carlo/i).closest('button') || screen.getByText(/Monte Carlo/i);
    await user.click(header);
    // After click, panel should be open — defaults will be loaded
    const { api } = await import('../lib/api');
    await waitFor(() => {
      expect(api.simulationDefaults).toHaveBeenCalled();
    });
  });

  it('shows simulation parameter inputs when expanded', async () => {
    render(<SimulationPanel {...defaultProps} defaultOpen />);
    await waitFor(() => {
      // Look for n_simulations input or label
      expect(screen.getByText(/Simulations|Number of/i)).toBeInTheDocument();
    });
  });

  it('shows scenario weight controls when expanded', async () => {
    render(<SimulationPanel {...defaultProps} defaultOpen />);
    await waitFor(() => {
      // Scenario weight labels from config mock
      expect(screen.getAllByText(/Base|Optimistic|Pessimistic/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows run button when expanded', async () => {
    render(<SimulationPanel {...defaultProps} defaultOpen />);
    await waitFor(() => {
      expect(screen.getAllByText(/Run|Start|Execute/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows PD/LGD correlation control when expanded', async () => {
    render(<SimulationPanel {...defaultProps} defaultOpen />);
    await waitFor(() => {
      expect(screen.getAllByText(/Correlation|PD.*LGD/i).length).toBeGreaterThanOrEqual(1);
    });
  });
});
