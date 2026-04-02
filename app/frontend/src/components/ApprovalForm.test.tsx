import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ApprovalForm from './ApprovalForm';

describe('ApprovalForm', () => {
  it('renders approve button', () => {
    render(<ApprovalForm onApprove={vi.fn()} />);
    expect(screen.getByText('✓ Approve')).toBeInTheDocument();
  });

  it('renders reject button when onReject provided', () => {
    render(<ApprovalForm onApprove={vi.fn()} onReject={vi.fn()} />);
    expect(screen.getByText('✗ Reject')).toBeInTheDocument();
  });

  it('does not render reject button when onReject not provided', () => {
    render(<ApprovalForm onApprove={vi.fn()} />);
    expect(screen.queryByText('✗ Reject')).toBeNull();
  });

  it('renders custom labels', () => {
    render(<ApprovalForm onApprove={vi.fn()} onReject={vi.fn()} approveLabel="Accept" rejectLabel="Decline" />);
    expect(screen.getByText('Accept')).toBeInTheDocument();
    expect(screen.getByText('Decline')).toBeInTheDocument();
  });

  it('renders title and description when provided', () => {
    render(<ApprovalForm onApprove={vi.fn()} title="Review" description="Please review carefully" />);
    expect(screen.getByText('Review')).toBeInTheDocument();
    expect(screen.getByText('Please review carefully')).toBeInTheDocument();
  });

  it('calls onApprove with comment on approve click', async () => {
    const user = userEvent.setup();
    const onApprove = vi.fn().mockResolvedValue(undefined);
    render(<ApprovalForm onApprove={onApprove} />);
    const textarea = screen.getByLabelText('Review comments');
    await user.type(textarea, 'Looks good');
    await user.click(screen.getByText('✓ Approve'));
    expect(onApprove).toHaveBeenCalledWith('Looks good');
  });

  it('disables reject when requireCommentForReject and comment empty', () => {
    render(<ApprovalForm onApprove={vi.fn()} onReject={vi.fn()} requireCommentForReject />);
    const rejectBtn = screen.getByText('✗ Reject').closest('button');
    expect(rejectBtn).toBeDisabled();
  });

  it('enables reject when comment is typed', async () => {
    const user = userEvent.setup();
    render(<ApprovalForm onApprove={vi.fn()} onReject={vi.fn()} requireCommentForReject />);
    await user.type(screen.getByLabelText('Review comments'), 'Need changes');
    const rejectBtn = screen.getByText('✗ Reject').closest('button');
    expect(rejectBtn).not.toBeDisabled();
  });

  it('calls onReject with comment on reject click', async () => {
    const user = userEvent.setup();
    const onReject = vi.fn().mockResolvedValue(undefined);
    render(<ApprovalForm onApprove={vi.fn()} onReject={onReject} />);
    await user.type(screen.getByLabelText('Review comments'), 'Rejected reason');
    await user.click(screen.getByText('✗ Reject'));
    expect(onReject).toHaveBeenCalledWith('Rejected reason');
  });

  it('shows Processing... while acting', async () => {
    const user = userEvent.setup();
    let resolveApprove: () => void;
    const onApprove = vi.fn(() => new Promise<void>(r => { resolveApprove = r; }));
    render(<ApprovalForm onApprove={onApprove} />);
    await user.click(screen.getByText('✓ Approve'));
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    resolveApprove!();
  });

  it('renders textarea with custom placeholder', () => {
    render(<ApprovalForm onApprove={vi.fn()} placeholder="Enter notes..." />);
    expect(screen.getByPlaceholderText('Enter notes...')).toBeInTheDocument();
  });
});
