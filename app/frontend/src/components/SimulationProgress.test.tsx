import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SimulationProgress from './SimulationProgress';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, style, ...rest } = props;
      return <div style={style} {...rest}>{children}</div>;
    },
  },
}));

vi.mock('./ScenarioChecklist', () => ({
  default: ({ scenarios }: any) => <div data-testid="scenario-checklist">{scenarios.length} scenarios</div>,
}));

describe('SimulationProgress', () => {
  const defaultProps = {
    elapsedSeconds: 5.3,
    progressPct: 45,
    currentPhase: 'monte_carlo',
    currentMessage: 'Processing scenario 2 of 3',
    scenarioResults: [],
    runningEcl: 500000,
    loanCount: 1000,
    scenarioCount: 3,
    nSimulations: 500,
    onCancel: vi.fn(),
  };

  it('renders simulation running header', () => {
    render(<SimulationProgress {...defaultProps} />);
    expect(screen.getByText('Monte Carlo Simulation Running')).toBeInTheDocument();
  });

  it('displays elapsed time', () => {
    render(<SimulationProgress {...defaultProps} />);
    expect(screen.getByText('5.3s')).toBeInTheDocument();
  });

  it('displays progress percentage', () => {
    render(<SimulationProgress {...defaultProps} />);
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('displays current phase', () => {
    render(<SimulationProgress {...defaultProps} />);
    expect(screen.getByText('Phase: monte_carlo')).toBeInTheDocument();
  });

  it('displays current message', () => {
    render(<SimulationProgress {...defaultProps} />);
    expect(screen.getByText('Processing scenario 2 of 3')).toBeInTheDocument();
  });

  it('displays loan and simulation counts', () => {
    render(<SimulationProgress {...defaultProps} />);
    expect(screen.getByText((t) => t.includes('1,000 loans'))).toBeInTheDocument();
    expect(screen.getByText((t) => t.includes('3 scenarios'))).toBeInTheDocument();
    expect(screen.getByText((t) => t.includes('500 paths'))).toBeInTheDocument();
  });

  it('calls onCancel when cancel button clicked', async () => {
    const user = userEvent.setup();
    const onCancel = vi.fn();
    render(<SimulationProgress {...defaultProps} onCancel={onCancel} />);
    await user.click(screen.getByText('Cancel'));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it('caps progress at 100%', () => {
    render(<SimulationProgress {...defaultProps} progressPct={150} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders scenario checklist when results present', () => {
    const props = {
      ...defaultProps,
      scenarioResults: [{ key: 'base', label: 'Base', color: '#000', weightPct: 50, status: 'done' as const }],
    };
    render(<SimulationProgress {...props} />);
    expect(screen.getByTestId('scenario-checklist')).toBeInTheDocument();
  });

  it('formats elapsed time in minutes when > 60s', () => {
    render(<SimulationProgress {...defaultProps} elapsedSeconds={125} />);
    expect(screen.getByText('2m 5s')).toBeInTheDocument();
  });
});
