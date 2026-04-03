import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Card from './Card';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Hello World</Card>);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });

  it('renders title when provided', () => {
    render(<Card title="Test Title">Content</Card>);
    expect(screen.getByText('Test Title')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(<Card title="Title" subtitle="Sub">Content</Card>);
    expect(screen.getByText('Sub')).toBeInTheDocument();
  });

  it('does not render title section when no title', () => {
    const { container } = render(<Card>Content</Card>);
    expect(container.querySelector('h3')).toBeNull();
  });

  it('applies custom className', () => {
    const { container } = render(<Card className="custom-class">Content</Card>);
    const wrapper = container.firstElementChild;
    expect(wrapper?.className).toContain('custom-class');
  });

  it('applies padding by default', () => {
    const { container } = render(<Card>Padded Content</Card>);
    const divs = container.querySelectorAll('div');
    const paddedDiv = Array.from(divs).find(d => d.className.includes('pb-5'));
    expect(paddedDiv).toBeDefined();
    expect(paddedDiv?.className).toContain('px-6');
  });

  it('removes padding when noPad is true', () => {
    const { container } = render(<Card noPad>Unpadded Content</Card>);
    const divs = container.querySelectorAll('div');
    const hasPadding = Array.from(divs).some(d => d.className.includes('px-6'));
    expect(hasPadding).toBe(false);
  });
});
