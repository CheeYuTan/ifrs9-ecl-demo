import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import KpiCard from './KpiCard';

describe('KpiCard', () => {
  it('renders title', () => {
    render(<KpiCard title="Total ECL" value="$1,234" />);
    expect(screen.getByText('Total ECL')).toBeInTheDocument();
  });

  it('renders value', () => {
    render(<KpiCard title="Total ECL" value="$1,234" />);
    expect(screen.getByText('$1,234')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<KpiCard title="Total ECL" value="$1,234" subtitle="vs prior quarter" />);
    expect(screen.getByText('vs prior quarter')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    const { container } = render(<KpiCard title="Total ECL" value="$1,234" />);
    const subtitleEls = container.querySelectorAll('.text-xs.text-slate-400.mt-1');
    expect(subtitleEls.length).toBe(0);
  });

  it('renders icon when provided', () => {
    render(<KpiCard title="Title" value="Value" icon={<span data-testid="icon">★</span>} />);
    expect(screen.getByTestId('icon')).toBeInTheDocument();
  });

  it('applies gradient based on color prop', () => {
    const { container } = render(<KpiCard title="Title" value="Value" color="green" />);
    const card = container.firstElementChild;
    expect(card?.className).toContain('from-emerald-50');
  });

  it('defaults to blue gradient', () => {
    const { container } = render(<KpiCard title="Title" value="Value" />);
    const card = container.firstElementChild;
    expect(card?.className).toContain('from-blue-50');
  });
});
