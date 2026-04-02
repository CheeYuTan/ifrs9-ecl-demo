import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ErrorDisplay from './ErrorDisplay';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => {
      const { initial, animate, exit, transition, ...rest } = props;
      return <div {...rest}>{children}</div>;
    },
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('ErrorDisplay', () => {
  it('renders title and message', () => {
    render(<ErrorDisplay message="Connection failed" />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText('Connection failed')).toBeInTheDocument();
  });

  it('renders custom title', () => {
    render(<ErrorDisplay title="Data Error" message="Invalid format" />);
    expect(screen.getByText('Data Error')).toBeInTheDocument();
  });

  it('renders retry button when onRetry provided', async () => {
    const user = userEvent.setup();
    const onRetry = vi.fn();
    render(<ErrorDisplay message="Fail" onRetry={onRetry} />);
    const btn = screen.getByText('Retry');
    await user.click(btn);
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it('does not render retry button when onRetry not provided', () => {
    render(<ErrorDisplay message="Fail" />);
    expect(screen.queryByText('Retry')).toBeNull();
  });

  it('renders Report Issue link', () => {
    render(<ErrorDisplay message="Fail" />);
    expect(screen.getByText('Report Issue')).toBeInTheDocument();
  });

  it('shows technical details when toggled', async () => {
    const user = userEvent.setup();
    render(<ErrorDisplay message="Fail" technicalDetails="Stack trace here" />);
    expect(screen.queryByText('Stack trace here')).toBeNull();
    await user.click(screen.getByText('Show Details'));
    expect(screen.getByText('Stack trace here')).toBeInTheDocument();
  });

  it('hides details toggle when no technicalDetails', () => {
    render(<ErrorDisplay message="Fail" />);
    expect(screen.queryByText('Show Details')).toBeNull();
  });

  it('renders dismiss button when onDismiss provided', async () => {
    const user = userEvent.setup();
    const onDismiss = vi.fn();
    render(<ErrorDisplay message="Fail" onDismiss={onDismiss} />);
    await user.click(screen.getByText('Dismiss'));
    expect(onDismiss).toHaveBeenCalledOnce();
  });
});
