import clsx from 'clsx';

const styles: Record<string, string> = {
  completed: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  in_progress: 'bg-amber-50 text-amber-700 ring-amber-200',
  pending: 'bg-slate-50 text-slate-500 ring-slate-200',
  rejected: 'bg-red-50 text-red-700 ring-red-200',
  PASS: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  FAIL: 'bg-red-50 text-red-700 ring-red-200',
};

const labels: Record<string, string> = {
  completed: 'Completed',
  in_progress: 'In Progress',
  pending: 'Pending',
  rejected: 'Rejected',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ring-1', styles[status] || styles.pending)}>
      {labels[status] || status}
    </span>
  );
}
