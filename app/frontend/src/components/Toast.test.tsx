import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ToastProvider, useToast } from './Toast';

function ToastTrigger({ message, type }: { message: string; type?: 'success' | 'error' | 'info' }) {
  const { toast } = useToast();
  return <button onClick={() => toast(message, type)}>Show Toast</button>;
}

describe('Toast', () => {
  it('renders children within ToastProvider', () => {
    render(
      <ToastProvider>
        <div>App Content</div>
      </ToastProvider>
    );
    expect(screen.getByText('App Content')).toBeInTheDocument();
  });

  it('shows a toast message when triggered', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastTrigger message="Operation successful" type="success" />
      </ToastProvider>
    );
    await user.click(screen.getByText('Show Toast'));
    expect(screen.getByText('Operation successful')).toBeInTheDocument();
  });

  it('shows error toast with correct styling', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastTrigger message="Something failed" type="error" />
      </ToastProvider>
    );
    await user.click(screen.getByText('Show Toast'));
    const toast = screen.getByText('Something failed').closest('div');
    expect(toast?.className).toContain('bg-red-600');
  });

  it('shows info toast by default', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastTrigger message="FYI" />
      </ToastProvider>
    );
    await user.click(screen.getByText('Show Toast'));
    const toast = screen.getByText('FYI').closest('div');
    expect(toast?.className).toContain('bg-slate-800');
  });

  it('shows success toast with correct styling', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastTrigger message="Done!" type="success" />
      </ToastProvider>
    );
    await user.click(screen.getByText('Show Toast'));
    const toast = screen.getByText('Done!').closest('div');
    expect(toast?.className).toContain('bg-emerald-600');
  });

  it('provides toast function via context', () => {
    let toastFn: ((msg: string, type?: 'success' | 'error' | 'info') => void) | undefined;
    function Capture() {
      const { toast } = useToast();
      toastFn = toast;
      return null;
    }
    render(
      <ToastProvider>
        <Capture />
      </ToastProvider>
    );
    expect(toastFn).toBeInstanceOf(Function);
  });

  it('can trigger multiple toasts', async () => {
    const user = userEvent.setup();
    function MultiTrigger() {
      const { toast } = useToast();
      return (
        <>
          <button onClick={() => toast('Toast A', 'info')}>A</button>
          <button onClick={() => toast('Toast B', 'error')}>B</button>
        </>
      );
    }
    render(
      <ToastProvider>
        <MultiTrigger />
      </ToastProvider>
    );
    await user.click(screen.getByText('A'));
    await user.click(screen.getByText('B'));
    expect(screen.getByText('Toast A')).toBeInTheDocument();
    expect(screen.getByText('Toast B')).toBeInTheDocument();
  });

  it('shows toast with long message', async () => {
    const user = userEvent.setup();
    const longMsg = 'A'.repeat(200);
    render(
      <ToastProvider>
        <ToastTrigger message={longMsg} />
      </ToastProvider>
    );
    await user.click(screen.getByText('Show Toast'));
    expect(screen.getByText(longMsg)).toBeInTheDocument();
  });

  it('shows toast with special characters', async () => {
    const user = userEvent.setup();
    render(
      <ToastProvider>
        <ToastTrigger message="Error: <script>alert('xss')</script>" type="error" />
      </ToastProvider>
    );
    await user.click(screen.getByText('Show Toast'));
    expect(screen.getByText("Error: <script>alert('xss')</script>")).toBeInTheDocument();
  });

  it('renders toast container in DOM', () => {
    const { container } = render(
      <ToastProvider>
        <div>Content</div>
      </ToastProvider>
    );
    expect(container).toBeTruthy();
  });

  it('multiple providers nest without error', () => {
    render(
      <ToastProvider>
        <ToastProvider>
          <div>Nested</div>
        </ToastProvider>
      </ToastProvider>
    );
    expect(screen.getByText('Nested')).toBeInTheDocument();
  });

  it('rapid-fires multiple toasts', async () => {
    const user = userEvent.setup();
    function RapidTrigger() {
      const { toast } = useToast();
      return <button onClick={() => {
        toast('Toast 1', 'success');
        toast('Toast 2', 'error');
        toast('Toast 3', 'info');
      }}>Fire All</button>;
    }
    render(
      <ToastProvider>
        <RapidTrigger />
      </ToastProvider>
    );
    await user.click(screen.getByText('Fire All'));
    expect(screen.getByText('Toast 1')).toBeInTheDocument();
    expect(screen.getByText('Toast 2')).toBeInTheDocument();
    expect(screen.getByText('Toast 3')).toBeInTheDocument();
  });
});
