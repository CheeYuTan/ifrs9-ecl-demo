import { CheckCircle2, Clock, XCircle, Loader2 } from 'lucide-react';

const styles: Record<string, { bg: string; icon: any }> = {
  completed: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  in_progress: { bg: 'bg-amber-50 text-amber-700 border-amber-200', icon: Loader2 },
  pending: { bg: 'bg-slate-50 text-slate-500 border-slate-200', icon: Clock },
  rejected: { bg: 'bg-red-50 text-red-700 border-red-200', icon: XCircle },
  PASS: { bg: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  FAIL: { bg: 'bg-red-50 text-red-700 border-red-200', icon: XCircle },
};

const labels: Record<string, string> = {
  completed: 'Completed',
  in_progress: 'In Progress',
  pending: 'Pending',
  rejected: 'Rejected',
};

export default function StatusBadge({ status }: { status: string }) {
  const s = styles[status] || styles.pending;
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${s.bg}`}>
      <Icon size={12} className={status === 'in_progress' ? 'animate-spin' : ''} />
      {labels[status] || status}
    </span>
  );
}
