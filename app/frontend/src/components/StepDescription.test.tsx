import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';
import StepDescription from './StepDescription';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
}));

describe('StepDescription', () => {
  it('renders description text', () => {
    render(<StepDescription description="Review your loan portfolio data" />);
    expect(screen.getByText('Review your loan portfolio data')).toBeInTheDocument();
  });

  it('renders IFRS reference when provided', () => {
    render(<StepDescription description="Test" ifrsRef="IFRS 9.5.5.1" />);
    expect(screen.getByText('IFRS 9.5.5.1')).toBeInTheDocument();
  });

  it('does not render IFRS reference when not provided', () => {
    const { container } = render(<StepDescription description="Test" />);
    expect(container.textContent).not.toContain('IFRS');
  });

  it('renders tips as list items', () => {
    render(<StepDescription description="Test" tips={['Tip one', 'Tip two']} />);
    expect(screen.getByText('Tip one')).toBeInTheDocument();
    expect(screen.getByText('Tip two')).toBeInTheDocument();
  });

  it('does not render tips section when tips not provided', () => {
    const { container } = render(<StepDescription description="Test" />);
    expect(container.querySelectorAll('li').length).toBe(0);
  });

  it('renders custom icon when provided', () => {
    render(<StepDescription description="Test" icon={<span data-testid="icon">★</span>} />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });
});
