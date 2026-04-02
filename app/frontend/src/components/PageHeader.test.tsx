import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import PageHeader from './PageHeader';

describe('PageHeader', () => {
  it('renders title and subtitle', () => {
    render(<PageHeader title="Dashboard" subtitle="Overview of metrics" />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Overview of metrics')).toBeInTheDocument();
  });

  it('renders status badge when status provided', () => {
    render(<PageHeader title="Test" subtitle="Sub" status="completed" />);
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('does not render status badge when no status', () => {
    const { container } = render(<PageHeader title="Test" subtitle="Sub" />);
    expect(container.textContent).not.toContain('Completed');
  });

  it('renders children in the right section', () => {
    render(
      <PageHeader title="Test" subtitle="Sub">
        <button>Action</button>
      </PageHeader>
    );
    expect(screen.getByText('Action')).toBeInTheDocument();
  });

  it('renders title as h2 element', () => {
    render(<PageHeader title="My Title" subtitle="Sub" />);
    const heading = screen.getByText('My Title');
    expect(heading.tagName).toBe('H2');
  });
});
