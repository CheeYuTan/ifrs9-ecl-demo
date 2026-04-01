import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, FileText, ArrowRight, XCircle } from 'lucide-react';
import { fmtCurrency } from '../lib/format';

interface ProgressEvent {
  type: string;
  phase?: string;
  message?: string;
  ecl?: number;
  [key: string]: any;
}

interface Props {
  totalEcl: number;
  coverage: number;
  durationMs: number;
  loanCount: number;
  scenarioCount: number;
  nSimulations: number;
  completedTiming: { loading: number; compute: number; aggregation: number } | null;
  convergenceInfo: { pct: number; at: number } | null;
  progressEvents: ProgressEvent[];
  startTime: number;
  onApply: () => void;
  onDiscard: () => void;
}

function formatElapsed(s: number) {
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}m ${rem.toFixed(0)}s`;
}

function formatLogTime(ms: number) {
  const totalSec = ms / 1000;
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, '0')}:${s.toFixed(1).padStart(4, '0')}`;
}

export default function SimulationResults({
  totalEcl, coverage, durationMs, loanCount, scenarioCount, nSimulations,
  completedTiming, convergenceInfo, progressEvents, startTime,
  onApply, onDiscard,
}: Props) {
  const [showLog, setShowLog] = useState(false);
  const logEndRef = useRef<HTMLDivElement | null>(null);
  const durationSec = durationMs / 1000;
  const totalTimingSec = completedTiming
    ? completedTiming.loading + completedTiming.compute + completedTiming.aggregation
    : 0;

  useEffect(() => {
    if (showLog && logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [progressEvents, showLog]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4 pt-4"
    >
      <div className="bg-emerald-50 border-2 border-emerald-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-2">
          <CheckCircle2 size={18} className="text-emerald-600" />
          <h4 className="text-sm font-bold text-emerald-900">Simulation Complete</h4>
          <span className="ml-auto text-[10px] text-emerald-600 font-mono">
            {loanCount > 0 ? `${loanCount.toLocaleString()} loans` : ''} × {scenarioCount} scenarios × {nSimulations.toLocaleString()} paths
          </span>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-emerald-200 dark:border-emerald-800">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Total ECL</p>
            <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">{fmtCurrency(totalEcl)}</p>
          </div>
          <div className="bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-emerald-200 dark:border-emerald-800">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Coverage</p>
            <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">{coverage.toFixed(2)}%</p>
          </div>
          <div className="bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-emerald-200 dark:border-emerald-800">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Duration</p>
            <p className="text-lg font-bold text-slate-800 dark:text-slate-100 font-mono">{formatElapsed(durationSec)}</p>
          </div>
        </div>

        {completedTiming && totalTimingSec > 0 && (
          <div className="text-xs text-slate-600 dark:text-slate-300 space-y-1 bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-emerald-200 dark:border-emerald-800">
            <p className="font-semibold text-slate-700 dark:text-slate-200 mb-1.5">Timing Breakdown</p>
            {[
              { label: 'Data loading', sec: completedTiming.loading },
              { label: 'Scenario compute', sec: completedTiming.compute },
              { label: 'Aggregation', sec: completedTiming.aggregation },
            ].map(t => {
              const pct = totalTimingSec > 0 ? (t.sec / totalTimingSec) * 100 : 0;
              return (
                <div key={t.label} className="flex items-center gap-2">
                  <span className="w-32 text-slate-500">{t.label}:</span>
                  <div className="flex-1 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="w-16 text-right font-mono">{t.sec.toFixed(1)}s</span>
                  <span className="w-10 text-right font-mono text-slate-400">({pct.toFixed(0)}%)</span>
                </div>
              );
            })}
          </div>
        )}

        {convergenceInfo && (
          <p className="text-xs text-emerald-700 bg-emerald-100/60 rounded-lg px-3 py-2">
            Convergence: ECL stable within ±{convergenceInfo.pct.toFixed(1)}% at {convergenceInfo.at.toLocaleString()} sims
          </p>
        )}

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowLog(!showLog)}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition"
          >
            <FileText size={13} />
            {showLog ? 'Hide Log' : 'View Full Log'}
          </button>
          <button
            onClick={onApply}
            className="btn-primary flex-1 py-2.5 text-xs shadow-lg"
          >
            <ArrowRight size={14} />
            Apply Results
          </button>
          <button
            onClick={onDiscard}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-red-600 bg-white dark:bg-slate-800 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition"
          >
            <XCircle size={13} />
            Discard
          </button>
        </div>
      </div>

      <AnimatePresence>
        {showLog && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="bg-slate-100 dark:bg-slate-900 rounded-lg p-4 max-h-64 overflow-y-auto font-mono text-[11px] text-slate-600 dark:text-slate-300 space-y-0.5">
              {progressEvents.map((evt, i) => {
                const ts = startTime
                  ? formatLogTime(
                      (evt as any)._ts
                        ? (evt as any)._ts - startTime
                        : i * 1000
                    )
                  : `${i}`;
                const icon = evt.phase === 'done' || (evt.ecl != null)
                  ? '✓'
                  : evt.phase === 'error'
                  ? '✗'
                  : '›';
                return (
                  <div key={i} className="flex gap-2">
                    <span className="text-slate-500 flex-shrink-0">[{ts}]</span>
                    <span className={evt.ecl != null ? 'text-emerald-400' : evt.phase === 'error' ? 'text-red-400' : 'text-slate-300'}>
                      {icon} {evt.message || evt.phase || '…'}
                    </span>
                  </div>
                );
              })}
              <div ref={logEndRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
