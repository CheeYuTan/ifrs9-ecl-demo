import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ErrorBoundary from './ErrorBoundary';

function ThrowingComponent({ error }: { error: Error }): React.ReactNode {
  throw error;
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Safe content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Safe content')).toBeInTheDocument();
  });

  it('shows default fallback when child throws', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error('Test crash')} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Test crash')).toBeInTheDocument();
  });

  it('shows custom fallback when provided', () => {
    render(
      <ErrorBoundary fallback={<div>Custom error UI</div>}>
        <ThrowingComponent error={new Error('Oops')} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Custom error UI')).toBeInTheDocument();
    expect(screen.queryByText('Something went wrong')).toBeNull();
  });

  it('shows Reload Page button in default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error('Crash')} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Reload Page')).toBeInTheDocument();
  });

  it('shows generic message when error has no message', () => {
    const error = new Error();
    error.message = '';
    render(
      <ErrorBoundary>
        <ThrowingComponent error={error} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
  });

  it('shows Try Again button in default fallback', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error('Crash')} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('renders error message text', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent error={new Error('Detailed error: fetch failed')} />
      </ErrorBoundary>
    );
    expect(screen.getByText('Detailed error: fetch failed')).toBeInTheDocument();
  });

  it('catches deeply nested errors', () => {
    function Wrapper() {
      return (
        <div>
          <div>
            <ThrowingComponent error={new Error('Deep crash')} />
          </div>
        </div>
      );
    }
    render(
      <ErrorBoundary>
        <Wrapper />
      </ErrorBoundary>
    );
    expect(screen.getByText('Deep crash')).toBeInTheDocument();
  });

  it('does not show fallback content when child renders normally', () => {
    render(
      <ErrorBoundary fallback={<div>Fallback</div>}>
        <div>Normal content</div>
      </ErrorBoundary>
    );
    expect(screen.queryByText('Fallback')).toBeNull();
    expect(screen.getByText('Normal content')).toBeInTheDocument();
  });

  it('renders multiple children when no error', () => {
    render(
      <ErrorBoundary>
        <div>Child 1</div>
        <div>Child 2</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Child 1')).toBeInTheDocument();
    expect(screen.getByText('Child 2')).toBeInTheDocument();
  });

  it('catches TypeError', () => {
    function TypeErrorComponent(): React.ReactNode {
      throw new TypeError('Cannot read properties of undefined');
    }
    render(
      <ErrorBoundary>
        <TypeErrorComponent />
      </ErrorBoundary>
    );
    expect(screen.getByText('Cannot read properties of undefined')).toBeInTheDocument();
  });
});
