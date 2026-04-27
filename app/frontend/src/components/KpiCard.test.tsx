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

  it('renders amber gradient', () => {
    const { container } = render(<KpiCard title="Title" value="Value" color="amber" />);
    const card = container.firstElementChild;
    expect(card?.className).toContain('from-amber-50');
  });

  it('renders red gradient', () => {
    const { container } = render(<KpiCard title="Title" value="Value" color="red" />);
    const card = container.firstElementChild;
    expect(card?.className).toContain('from-red-50');
  });

  it('renders purple gradient', () => {
    const { container } = render(<KpiCard title="Title" value="Value" color="purple" />);
    const card = container.firstElementChild;
    expect(card?.className).toContain('from-purple-50');
  });

  it('falls back to blue for unknown color', () => {
    const { container } = render(<KpiCard title="Title" value="Value" color="magenta" />);
    const card = container.firstElementChild;
    expect(card?.className).toContain('from-blue-50');
  });

  it('renders large numeric values', () => {
    render(<KpiCard title="Total GCA" value="$1,234,567,890" />);
    expect(screen.getByText('$1,234,567,890')).toBeInTheDocument();
  });

  it('renders zero value', () => {
    render(<KpiCard title="ECL" value="$0" />);
    expect(screen.getByText('$0')).toBeInTheDocument();
  });

  it('renders empty value string', () => {
    render(<KpiCard title="N/A" value="" />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('renders ReactNode as title', () => {
    render(<KpiCard title={<span data-testid="custom-title">Custom</span>} value="123" />);
    expect(screen.getByTestId('custom-title')).toBeInTheDocument();
  });

  it('renders icon inside icon container', () => {
    const { container } = render(
      <KpiCard title="Title" value="Value" icon={<span>📊</span>} color="green" />
    );
    const iconContainer = container.querySelector('.rounded-xl');
    expect(iconContainer).toBeTruthy();
    expect(iconContainer?.className).toContain('bg-emerald-500/10');
  });
});
