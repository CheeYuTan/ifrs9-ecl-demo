import { ExternalLink, Play, CheckCircle2, XCircle, Loader2, Clock } from 'lucide-react';

interface JobRun {
  run_id: number;
  job_id: number;
  lifecycle_state: string;
  result_state: string | null;
  state_message?: string;
  run_url: string;
  start_time?: number;
  end_time?: number;
  run_duration_ms?: number;
  tasks?: {
    task_key: string;
    lifecycle_state: string;
    result_state: string | null;
    run_url: string;
    execution_duration_ms: number;
  }[];
}

interface Props {
  run: JobRun | null;
  label?: string;
  compact?: boolean;
}

function StatusIcon({ state, result }: { state: string; result: string | null }) {
  if (state === 'TERMINATED' && result === 'SUCCESS')
    return <CheckCircle2 size={14} className="text-emerald-500" />;
  if (state === 'TERMINATED' && result === 'FAILED')
    return <XCircle size={14} className="text-red-500" />;
  if (state === 'RUNNING' || state === 'PENDING')
    return <Loader2 size={14} className="text-blue-500 animate-spin" />;
  return <Clock size={14} className="text-slate-400" />;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  const s = Math.round(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  return `${m}m ${s % 60}s`;
}

export default function JobRunLink({ run, label = 'Databricks Job Run', compact }: Props) {
  if (!run) return null;

  const isRunning = run.lifecycle_state === 'RUNNING' || run.lifecycle_state === 'PENDING';
  const isSuccess = run.result_state === 'SUCCESS';
  const isFailed = run.result_state === 'FAILED';

  if (compact) {
    return (
      <a
        href={run.run_url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-brand hover:underline"
      >
        <StatusIcon state={run.lifecycle_state} result={run.result_state} />
        {label}
        <ExternalLink size={10} />
      </a>
    );
  }

  return (
    <div className={`flex items-start gap-3 p-3 rounded-lg border ${
      isRunning ? 'bg-blue-50/50 border-blue-200' :
      isSuccess ? 'bg-emerald-50/50 border-emerald-100' :
      isFailed ? 'bg-red-50/50 border-red-100' :
      'bg-slate-50/50 dark:bg-slate-800/50 border-slate-100 dark:border-slate-700'
    }`}>
      <Play size={16} className={`mt-0.5 flex-shrink-0 ${
        isRunning ? 'text-blue-500' : isSuccess ? 'text-emerald-500' : isFailed ? 'text-red-500' : 'text-slate-400'
      }`} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <p className="text-[10px] font-semibold text-slate-400 uppercase mb-1">{label}</p>
          <a
            href={run.run_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-[10px] font-semibold text-brand hover:underline"
          >
            Open in Databricks <ExternalLink size={9} />
          </a>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <StatusIcon state={run.lifecycle_state} result={run.result_state} />
            <span className="font-semibold">
              {isRunning ? 'Running...' : run.result_state || run.lifecycle_state}
            </span>
          </span>
          {run.run_duration_ms ? (
            <span className="text-slate-400">{formatDuration(run.run_duration_ms)}</span>
          ) : null}
          {run.start_time ? (
            <span className="text-slate-400">{new Date(run.start_time).toLocaleString()}</span>
          ) : null}
        </div>
        {run.tasks && run.tasks.length > 0 && (
          <div className="mt-2 space-y-1">
            {run.tasks.map(t => (
              <a
                key={t.task_key}
                href={t.run_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between group text-[11px]"
              >
                <span className="flex items-center gap-1.5">
                  <StatusIcon state={t.lifecycle_state} result={t.result_state} />
                  <span className="text-slate-600 dark:text-slate-300 group-hover:underline">{t.task_key}</span>
                </span>
                <span className="text-slate-400">
                  {t.execution_duration_ms > 0 ? formatDuration(t.execution_duration_ms) : '—'}
                </span>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
