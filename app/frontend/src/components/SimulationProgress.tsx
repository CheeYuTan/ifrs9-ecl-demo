import { motion } from 'framer-motion';
import { Loader2, Timer, Ban } from 'lucide-react';
import { fmtCurrency } from '../lib/format';
import ScenarioChecklist, { type ScenarioProgress } from './ScenarioChecklist';

interface Props {
  elapsedSeconds: number;
  progressPct: number;
  currentPhase: string;
  currentMessage: string;
  scenarioResults: ScenarioProgress[];
  runningEcl: number;
  loanCount: number;
  scenarioCount: number;
  nSimulations: number;
  onCancel: () => void;
}

function formatElapsed(s: number) {
  if (s < 60) return `${s.toFixed(1)}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}m ${rem.toFixed(0)}s`;
}

export default function SimulationProgress({
  elapsedSeconds, progressPct, currentPhase, currentMessage,
  scenarioResults, runningEcl, loanCount, scenarioCount,
  nSimulations, onCancel,
}: Props) {
  const pct = Math.min(progressPct, 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4 pt-4"
    >
      <div className="bg-indigo-50 border-2 border-indigo-200 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Loader2 size={18} className="text-indigo-600 animate-spin" />
            <h4 className="text-sm font-bold text-indigo-900">Monte Carlo Simulation Running</h4>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-mono text-indigo-600">
            <Timer size={13} />
            <span>{formatElapsed(elapsedSeconds)}</span>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full rounded-full"
              style={{ background: 'linear-gradient(90deg, #6366F1, #10B981)' }}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px]">
            <span className="font-semibold text-indigo-700">{Math.round(pct)}%</span>
            <span className="text-indigo-500">{currentPhase && `Phase: ${currentPhase}`}</span>
          </div>
        </div>

        {currentMessage && (
          <p className="text-xs text-indigo-700 bg-indigo-100/60 rounded-lg px-3 py-2 font-medium">
            {currentMessage}
          </p>
        )}

        {scenarioResults.length > 0 && <ScenarioChecklist scenarios={scenarioResults} />}

        <div className="flex items-center justify-between text-xs text-indigo-700">
          <div className="space-y-0.5">
            {runningEcl > 0 && (
              <p className="font-semibold">Running ECL: {fmtCurrency(runningEcl)} <span className="font-normal text-indigo-500">(weighted so far)</span></p>
            )}
            <p className="text-[10px] text-indigo-500">
              {loanCount > 0 ? `${loanCount.toLocaleString()} loans` : '—'} × {scenarioCount} scenarios × {nSimulations.toLocaleString()} paths
            </p>
          </div>
        </div>

        <button
          onClick={onCancel}
          className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-white border border-red-200 text-red-600 text-xs font-semibold rounded-lg hover:bg-red-50 transition"
        >
          <Ban size={14} />
          Cancel
        </button>
      </div>
    </motion.div>
  );
}
