import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Sidebar, type ViewType } from './Sidebar';

vi.mock('framer-motion', () => ({
  motion: new Proxy({}, {
    get: (_target: any, prop: string) => {
      const tag = prop === 'aside' ? 'aside' : prop === 'button' ? 'button' : 'div';
      return ({ children, ...props }: any) => {
        const {
          initial, animate, exit, transition, layout, whileHover, whileTap,
          variants, layoutId, onMouseEnter, onMouseLeave,
          ...rest
        } = props;
        const domProps: Record<string, any> = {};
        for (const [k, v] of Object.entries(rest)) {
          if (
            typeof v !== 'object' || v === null ||
            k === 'className' || k === 'onClick' || k === 'id' ||
            k === 'role' || k.startsWith('aria-') || k.startsWith('data-') ||
            k === 'tabIndex' || k === 'style' || k === 'disabled'
          ) {
            domProps[k] = v;
          }
        }
        if (onMouseEnter) domProps.onMouseEnter = onMouseEnter;
        if (onMouseLeave) domProps.onMouseLeave = onMouseLeave;
        if (tag === 'aside') return <aside {...domProps}>{children}</aside>;
        if (tag === 'button') return <button {...domProps}>{children}</button>;
        return <div {...domProps}>{children}</div>;
      };
    },
  }),
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('Sidebar', () => {
  let onNavigate: any;

  beforeEach(() => {
    onNavigate = vi.fn();
    // Default to a wide viewport so desktop sidebar renders
    Object.defineProperty(window, 'innerWidth', { value: 1440, writable: true });
    window.matchMedia = vi.fn().mockReturnValue({
      matches: true,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
  });

  it('renders ECL Workspace branding', () => {
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    expect(screen.getAllByText('ECL Workspace').length).toBeGreaterThan(0);
  });

  it('renders all navigation group titles', () => {
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    // Group titles appear in both mobile and desktop, check at least one
    expect(screen.getAllByText('Workflow').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Analytics').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Operations').length).toBeGreaterThan(0);
  });

  it('renders all navigation items', () => {
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    const labels = [
      'ECL Workflow', 'Data Mapping', 'Attribution', 'Models',
      'Backtesting', 'Markov Chains', 'Hazard Models',
      'GL Journals', 'Reports', 'Approvals', 'Advanced', 'Admin',
    ];
    for (const label of labels) {
      expect(screen.getAllByText(label).length).toBeGreaterThan(0);
    }
  });

  it('marks the active view with aria-current="page"', () => {
    render(<Sidebar activeView="models" onNavigate={onNavigate} />);
    const activeButtons = screen.getAllByRole('button', { current: 'page' });
    expect(activeButtons.length).toBeGreaterThan(0);
  });

  it('calls onNavigate when a nav item is clicked', async () => {
    const user = userEvent.setup();
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    const modelsButtons = screen.getAllByText('Models');
    await user.click(modelsButtons[0]);
    expect(onNavigate).toHaveBeenCalledWith('models');
  });

  it('calls onNavigate with correct view for each nav item', async () => {
    const user = userEvent.setup();
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);

    const navMap: Record<string, ViewType> = {
      'ECL Workflow': 'workflow',
      'Data Mapping': 'data-mapping',
      'Attribution': 'attribution',
      'Backtesting': 'backtesting',
      'Markov Chains': 'markov',
      'Hazard Models': 'hazard',
      'GL Journals': 'gl-journals',
      'Reports': 'reports',
      'Approvals': 'approvals',
      'Advanced': 'advanced',
      'Admin': 'admin',
    };

    for (const [label, view] of Object.entries(navMap)) {
      onNavigate.mockClear();
      const elements = screen.getAllByText(label);
      await user.click(elements[0]);
      expect(onNavigate).toHaveBeenCalledWith(view);
    }
  });

  it('renders collapse/expand button with correct aria-label', () => {
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    expect(screen.getByLabelText('Collapse sidebar')).toBeInTheDocument();
  });

  it('renders mobile menu button', () => {
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    expect(screen.getByLabelText('Open navigation menu')).toBeInTheDocument();
  });

  it('renders navigation landmark', () => {
    render(<Sidebar activeView="workflow" onNavigate={onNavigate} />);
    const navElements = screen.getAllByRole('navigation', { name: 'Main navigation' });
    expect(navElements.length).toBeGreaterThan(0);
  });

  it('renders settings/admin item at the bottom', () => {
    render(<Sidebar activeView="admin" onNavigate={onNavigate} />);
    const adminButtons = screen.getAllByText('Admin');
    expect(adminButtons.length).toBeGreaterThan(0);
  });

  it('highlights different active views correctly', () => {
    const views: ViewType[] = ['workflow', 'models', 'admin', 'reports'];
    for (const view of views) {
      const { unmount } = render(<Sidebar activeView={view} onNavigate={onNavigate} />);
      const activeButtons = screen.getAllByRole('button', { current: 'page' });
      expect(activeButtons.length).toBeGreaterThan(0);
      unmount();
    }
  });
});
