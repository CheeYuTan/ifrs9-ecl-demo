import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SimulationResults from './SimulationResults';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, style, ...rest } = props;
      const domProps: Record<string, any> = {};
      for (const [k, v] of Object.entries(rest)) {
        if (typeof v !== 'object' || v === null || k === 'className' || k === 'onClick') {
          domProps[k] = v;
        }
      }
      return <div style={style} {...domProps}>{children}</div>;
    },
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

vi.mock('../lib/format', () => ({
  fmtCurrency: (v: number) => `$${(v || 0).toLocaleString()}`,
}));

// Mock scrollIntoView (not available in jsdom)
Element.prototype.scrollIntoView = vi.fn();

describe('SimulationResults', () => {
  const defaultProps = {
    totalEcl: 1500000,
    coverage: 3.45,
    durationMs: 12500,
    loanCount: 5000,
    scenarioCount: 3,
    nSimulations: 1000,
    completedTiming: null,
    convergenceInfo: null,
    progressEvents: [],
    startTime: Date.now() - 12500,
    onApply: vi.fn(),
    onDiscard: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders "Simulation Complete" header', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.getByText('Simulation Complete')).toBeInTheDocument();
  });

  it('displays total ECL formatted', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.getByText('$1,500,000')).toBeInTheDocument();
  });

  it('displays coverage percentage', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.getByText('3.45%')).toBeInTheDocument();
  });

  it('displays duration formatted', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.getByText('12.5s')).toBeInTheDocument();
  });

  it('displays loan/scenario/simulation counts', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.getByText(/5,000 loans/)).toBeInTheDocument();
    expect(screen.getByText(/3 scenarios/)).toBeInTheDocument();
    expect(screen.getByText(/1,000 paths/)).toBeInTheDocument();
  });

  it('calls onApply when Apply Results clicked', async () => {
    const user = userEvent.setup();
    const onApply = vi.fn();
    render(<SimulationResults {...defaultProps} onApply={onApply} />);
    await user.click(screen.getByText('Apply Results'));
    expect(onApply).toHaveBeenCalledTimes(1);
  });

  it('calls onDiscard when Discard clicked', async () => {
    const user = userEvent.setup();
    const onDiscard = vi.fn();
    render(<SimulationResults {...defaultProps} onDiscard={onDiscard} />);
    await user.click(screen.getByText('Discard'));
    expect(onDiscard).toHaveBeenCalledTimes(1);
  });

  it('shows timing breakdown when completedTiming provided', () => {
    const timing = { loading: 2.0, compute: 8.5, aggregation: 2.0 };
    render(<SimulationResults {...defaultProps} completedTiming={timing} />);
    expect(screen.getByText('Timing Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Data loading:')).toBeInTheDocument();
    expect(screen.getByText('Scenario compute:')).toBeInTheDocument();
    expect(screen.getByText('Aggregation:')).toBeInTheDocument();
  });

  it('does not show timing breakdown when completedTiming is null', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.queryByText('Timing Breakdown')).toBeNull();
  });

  it('shows convergence info when provided', () => {
    const convergence = { pct: 0.5, at: 800 };
    render(<SimulationResults {...defaultProps} convergenceInfo={convergence} />);
    expect(screen.getByText(/Convergence/)).toBeInTheDocument();
    expect(screen.getByText(/±0.5%/)).toBeInTheDocument();
    expect(screen.getByText(/800/)).toBeInTheDocument();
  });

  it('does not show convergence info when null', () => {
    render(<SimulationResults {...defaultProps} />);
    expect(screen.queryByText(/Convergence/)).toBeNull();
  });

  it('toggles log view on button click', async () => {
    const user = userEvent.setup();
    const events = [
      { type: 'progress', phase: 'loading', message: 'Loading data', _ts: defaultProps.startTime + 1000 },
      { type: 'progress', phase: 'monte_carlo', message: 'Running simulation', _ts: defaultProps.startTime + 5000 },
      { type: 'complete', phase: 'done', message: 'Done', ecl: 1500000, _ts: defaultProps.startTime + 12000 },
    ];
    render(<SimulationResults {...defaultProps} progressEvents={events} />);
    expect(screen.getByText('View Full Log')).toBeInTheDocument();
    await user.click(screen.getByText('View Full Log'));
    expect(screen.getByText('Hide Log')).toBeInTheDocument();
    // Log entries contain the message text with icons
    expect(screen.getByText(/Loading data/)).toBeInTheDocument();
    expect(screen.getByText(/Running simulation/)).toBeInTheDocument();
  });

  it('formats duration as minutes when >= 60s', () => {
    render(<SimulationResults {...defaultProps} durationMs={125000} />);
    expect(screen.getByText('2m 5s')).toBeInTheDocument();
  });

  it('handles zero loanCount gracefully', () => {
    render(<SimulationResults {...defaultProps} loanCount={0} />);
    // Should not show "0 loans" in the header line
    expect(screen.getByText(/3 scenarios/)).toBeInTheDocument();
  });

  it('shows timing percentages in breakdown', () => {
    const timing = { loading: 2.5, compute: 5.0, aggregation: 2.5 };
    render(<SimulationResults {...defaultProps} completedTiming={timing} />);
    // loading = 2.5/10 = 25%, compute = 50%, agg = 25%
    // Use getAllByText since '2.5s' appears twice (loading + aggregation)
    expect(screen.getAllByText('2.5s')).toHaveLength(2);
    expect(screen.getByText('5.0s')).toBeInTheDocument();
    expect(screen.getAllByText('(25%)')).toHaveLength(2);
    expect(screen.getByText('(50%)')).toBeInTheDocument();
  });
});
