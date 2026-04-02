import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CollapsibleSection from './CollapsibleSection';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
    span: ({ children, ...props }: any) => {
      const { animate, transition, ...rest } = props;
      return <span {...rest}>{children}</span>;
    },
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('CollapsibleSection', () => {
  it('renders title', () => {
    render(<CollapsibleSection title="Advanced Options">Content here</CollapsibleSection>);
    expect(screen.getByText('Advanced Options')).toBeInTheDocument();
  });

  it('hides content by default', () => {
    render(<CollapsibleSection title="Section">Hidden content</CollapsibleSection>);
    expect(screen.queryByText('Hidden content')).toBeNull();
  });

  it('shows content when defaultOpen is true', () => {
    render(<CollapsibleSection title="Section" defaultOpen>Visible content</CollapsibleSection>);
    expect(screen.getByText('Visible content')).toBeInTheDocument();
  });

  it('toggles content on button click', async () => {
    const user = userEvent.setup();
    render(<CollapsibleSection title="Section">Toggle me</CollapsibleSection>);
    expect(screen.queryByText('Toggle me')).toBeNull();
    await user.click(screen.getByRole('button'));
    expect(screen.getByText('Toggle me')).toBeInTheDocument();
  });

  it('sets aria-expanded correctly', async () => {
    const user = userEvent.setup();
    render(<CollapsibleSection title="Section">Content</CollapsibleSection>);
    const btn = screen.getByRole('button');
    expect(btn).toHaveAttribute('aria-expanded', 'false');
    await user.click(btn);
    expect(btn).toHaveAttribute('aria-expanded', 'true');
  });

  it('renders icon when provided', () => {
    render(
      <CollapsibleSection title="Section" icon={<span data-testid="icon">★</span>}>
        Content
      </CollapsibleSection>
    );
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });
});
