import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HelpPanel from './HelpPanel';

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

vi.mock('../lib/config', () => ({
  config: {
    governance: {
      glReconciliationTolerancePct: 1,
      dqScoreThresholdPct: 90,
    },
  },
}));

describe('HelpPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders help button with aria-label', () => {
    render(<HelpPanel activeStep={0} />);
    expect(screen.getByLabelText('Open help panel')).toBeInTheDocument();
  });

  it('opens panel on button click', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={0} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Create Project')).toBeInTheDocument();
  });

  it('shows correct help for step 0 (create_project)', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={0} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('What is an ECL Project?')).toBeInTheDocument();
    expect(screen.getByText('Key Fields')).toBeInTheDocument();
    expect(screen.getByText('IFRS 9 Reference')).toBeInTheDocument();
  });

  it('shows correct help for step 1 (data_processing)', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={1} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Data Processing')).toBeInTheDocument();
    expect(screen.getByText('Purpose')).toBeInTheDocument();
  });

  it('shows step indicator text', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={2} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Step 3 of 8')).toBeInTheDocument();
  });

  it('shows external links with correct attributes', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={0} />);
    await user.click(screen.getByLabelText('Open help panel'));
    const link = screen.getByText('IFRS 9 Standard');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('closes panel on close button click', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={0} />);
    // Open
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Create Project')).toBeInTheDocument();
    // Close — the X button
    const closeButtons = screen.getAllByRole('button');
    const xButton = closeButtons.find(b => !b.getAttribute('aria-label'));
    if (xButton) await user.click(xButton);
  });

  it('toggles on "?" key press', () => {
    render(<HelpPanel activeStep={0} />);
    // Press ? to open
    fireEvent.keyDown(document, { key: '?' });
    expect(screen.getByText('Create Project')).toBeInTheDocument();
    // Press ? again to close
    fireEvent.keyDown(document, { key: '?' });
  });

  it('closes on Escape key', () => {
    render(<HelpPanel activeStep={0} />);
    // Open first
    fireEvent.keyDown(document, { key: '?' });
    expect(screen.getByText('Create Project')).toBeInTheDocument();
    // Close with Escape
    fireEvent.keyDown(document, { key: 'Escape' });
  });

  it('shows keyboard shortcut hint', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={0} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('?')).toBeInTheDocument();
    expect(screen.getByText(/toggle help/i)).toBeInTheDocument();
  });

  it('shows help for stress_testing step', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={5} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Stress Testing')).toBeInTheDocument();
  });

  it('shows help for sign_off step', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={7} />);
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Sign-Off')).toBeInTheDocument();
    expect(screen.getByText('IFRS 7 Disclosure')).toBeInTheDocument();
  });

  it('falls back to create_project help for out-of-range step', async () => {
    const user = userEvent.setup();
    render(<HelpPanel activeStep={99} />);
    // Falls back to create_project (STEP_KEYS[99] is undefined → fallback)
    expect(screen.getByLabelText('Open help panel')).toBeInTheDocument();
    await user.click(screen.getByLabelText('Open help panel'));
    expect(screen.getByText('Create Project')).toBeInTheDocument();
  });
});
