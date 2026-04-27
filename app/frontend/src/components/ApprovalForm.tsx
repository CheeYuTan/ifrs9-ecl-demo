import { useState } from 'react';

interface Props {
  onApprove: (comment: string) => Promise<void>;
  onReject?: (comment: string) => Promise<void>;
  approveLabel?: string;
  rejectLabel?: string;
  placeholder?: string;
  title?: string;
  description?: string;
  requireCommentForReject?: boolean;
  disabled?: boolean;
}

export default function ApprovalForm({
  onApprove,
  onReject,
  approveLabel = '✓ Approve',
  rejectLabel = '✗ Reject',
  placeholder = 'Review comments (required for rejection)...',
  title,
  description,
  requireCommentForReject = true,
  disabled = false,
}: Props) {
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  const handleAction = async (type: 'approve' | 'reject') => {
    if (type === 'reject' && requireCommentForReject && !comment) return;
    setActing(true);
    try {
      if (type === 'approve') { await onApprove(comment); } else { await onReject?.(comment); }
    } finally {
      setActing(false);
    }
  };

  return (
    <div>
      {title && <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-2">{title}</h3>}
      {description && <p className="text-xs text-slate-400 mb-3">{description}</p>}
      <label htmlFor="approval-comment" className="sr-only">Review comments</label>
      <textarea
        id="approval-comment"
        value={comment}
        onChange={e => setComment(e.target.value)}
        rows={2}
        placeholder={placeholder}
        className="form-input resize-none mb-3"
      />
      <div className="flex gap-3">
        <button
          onClick={() => handleAction('approve')}
          disabled={acting || disabled}
          className="btn-primary shadow-sm"
        >
          {acting ? 'Processing...' : approveLabel}
        </button>
        {onReject && (
          <button
            onClick={() => handleAction('reject')}
            disabled={acting || disabled || (requireCommentForReject && !comment)}
            className="px-5 py-2.5 bg-white dark:bg-slate-800 text-red-500 text-sm font-semibold rounded-lg border border-red-200 dark:border-red-800 hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-40 transition"
          >
            {rejectLabel}
          </button>
        )}
      </div>
    </div>
  );
}
