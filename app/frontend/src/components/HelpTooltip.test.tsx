import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import HelpTooltip, { IFRS9_HELP } from './HelpTooltip';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, style, ref: _, ...rest } = props;
      return <div style={style} {...rest}>{children}</div>;
    },
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('HelpTooltip', () => {
  it('renders help circle button by default', () => {
    render(<HelpTooltip content="Help text" />);
    expect(screen.getByLabelText('Help')).toBeInTheDocument();
  });

  it('renders term text when term provided', () => {
    render(<HelpTooltip content="Explanation" term="ECL" />);
    expect(screen.getByText('ECL')).toBeInTheDocument();
  });

  it('shows tooltip on mouse enter', async () => {
    const user = userEvent.setup();
    const { container } = render(<HelpTooltip content={<span>Tooltip content</span>} />);
    await user.hover(container.firstElementChild!);
    expect(screen.getByText('Tooltip content')).toBeInTheDocument();
  });

  it('hides tooltip on mouse leave', async () => {
    const user = userEvent.setup();
    const { container } = render(<HelpTooltip content={<span>Tooltip content</span>} />);
    await user.hover(container.firstElementChild!);
    expect(screen.getByText('Tooltip content')).toBeInTheDocument();
    await user.unhover(container.firstElementChild!);
    expect(screen.queryByText('Tooltip content')).toBeNull();
  });

  it('toggles on click via mouseEnter then shows content', async () => {
    const { container } = render(<HelpTooltip content={<span>Click tooltip</span>} />);
    // Hover to open
    fireEvent.mouseEnter(container.firstElementChild!);
    expect(screen.getByText('Click tooltip')).toBeInTheDocument();
  });

  it('has close button in tooltip when open', async () => {
    const { container } = render(<HelpTooltip content={<span>Content</span>} />);
    fireEvent.mouseEnter(container.firstElementChild!);
    expect(screen.getByLabelText('Close')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<HelpTooltip content="Test" className="my-class" />);
    expect(container.firstElementChild?.className).toContain('my-class');
  });
});

describe('IFRS9_HELP constants', () => {
  it('has ECL help text', () => {
    const { container } = render(<>{IFRS9_HELP.ECL}</>);
    expect(container.textContent).toContain('Expected Credit Loss');
  });

  it('has PD help text', () => {
    const { container } = render(<>{IFRS9_HELP.PD}</>);
    expect(container.textContent).toContain('Probability of Default');
  });

  it('has LGD help text', () => {
    const { container } = render(<>{IFRS9_HELP.LGD}</>);
    expect(container.textContent).toContain('Loss Given Default');
  });

  it('has EAD help text', () => {
    const { container } = render(<>{IFRS9_HELP.EAD}</>);
    expect(container.textContent).toContain('Exposure at Default');
  });

  it('has SICR help text', () => {
    const { container } = render(<>{IFRS9_HELP.SICR}</>);
    expect(container.textContent).toContain('Significant Increase in Credit Risk');
  });

  it('has STAGE_1 help text', () => {
    const { container } = render(<>{IFRS9_HELP.STAGE_1}</>);
    expect(container.textContent).toContain('12-month ECL');
  });

  it('has STAGE_2 help text', () => {
    const { container } = render(<>{IFRS9_HELP.STAGE_2}</>);
    expect(container.textContent).toContain('Lifetime ECL');
  });

  it('has STAGE_3 help text', () => {
    const { container } = render(<>{IFRS9_HELP.STAGE_3}</>);
    expect(container.textContent).toContain('credit-impaired');
  });

  it('has GCA help text', () => {
    const { container } = render(<>{IFRS9_HELP.GCA}</>);
    expect(container.textContent).toContain('Gross Carrying Amount');
  });

  it('has COVERAGE_RATIO help text', () => {
    const { container } = render(<>{IFRS9_HELP.COVERAGE_RATIO}</>);
    expect(container.textContent).toContain('Coverage Ratio');
  });

  it('has GL_RECON help text', () => {
    const { container } = render(<>{IFRS9_HELP.GL_RECON}</>);
    expect(container.textContent).toContain('GL Reconciliation');
  });
});
