import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import ChartTooltip from './ChartTooltip';

describe('ChartTooltip', () => {
  it('returns null when not active', () => {
    const { container } = render(<ChartTooltip active={false} payload={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when payload is empty', () => {
    const { container } = render(<ChartTooltip active={true} payload={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it('returns null when payload is undefined', () => {
    const { container } = render(<ChartTooltip active={true} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders tooltip with name and value', () => {
    const payload = [{ payload: { name: 'Stage 1' }, name: 'ecl', value: 50000, fill: '#10B981' }];
    render(<ChartTooltip active={true} payload={payload} />);
    expect(screen.getByText('Stage 1')).toBeInTheDocument();
    expect(screen.getByText('50,000')).toBeInTheDocument();
  });

  it('uses fallback name from payload entry when payload.name missing', () => {
    const payload = [{ payload: {}, name: 'ECL Amount', value: 1234, color: '#3B82F6' }];
    render(<ChartTooltip active={true} payload={payload} />);
    expect(screen.getByText('ECL Amount')).toBeInTheDocument();
  });

  it('uses custom formatValue function', () => {
    const payload = [{ payload: { name: 'Test' }, name: 'x', value: 0.75, fill: '#000' }];
    render(<ChartTooltip active={true} payload={payload} formatValue={(v) => `${(v * 100).toFixed(0)}%`} />);
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('applies fill color as inline style', () => {
    const payload = [{ payload: { name: 'A' }, name: 'x', value: 100, fill: '#FF0000' }];
    const { container } = render(<ChartTooltip active={true} payload={payload} />);
    const valueEl = container.querySelector('p[style]');
    expect(valueEl?.getAttribute('style')).toContain('color');
    expect(valueEl?.getAttribute('style')).toContain('rgb(255, 0, 0)');
  });

  it('uses color when fill is not present', () => {
    const payload = [{ payload: { name: 'A' }, name: 'x', value: 100, color: '#00FF00' }];
    const { container } = render(<ChartTooltip active={true} payload={payload} />);
    const valueEl = container.querySelector('p[style]');
    expect(valueEl?.getAttribute('style')).toContain('color');
  });
});
