import { CheckCircle2, Loader2, Circle } from 'lucide-react';
import { fmtCurrency } from '../lib/format';

export interface ScenarioProgress {
  key: string;
  label: string;
  color: string;
  weightPct: number;
  status: 'pending' | 'running' | 'done';
  ecl?: number;
  durationMs?: number;
}

interface Props {
  scenarios: ScenarioProgress[];
}

export default function ScenarioChecklist({ scenarios }: Props) {
  return (
    <div className="bg-slate-50 rounded-lg border border-slate-200 divide-y divide-slate-100 overflow-hidden">
      {scenarios.map(sr => (
        <div key={sr.key} className="flex items-center gap-3 px-3 py-2 text-xs">
          <div className="flex-shrink-0">
            {sr.status === 'done' && <CheckCircle2 size={14} className="text-emerald-500" />}
            {sr.status === 'running' && <Loader2 size={14} className="text-indigo-500 animate-spin" />}
            {sr.status === 'pending' && <Circle size={14} className="text-slate-300" />}
          </div>
          <div className="flex items-center gap-1.5 w-40 flex-shrink-0">
            <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: sr.color }} />
            <span className="font-medium text-slate-700 truncate">{sr.label}</span>
            <span className="text-slate-400">({Math.round(sr.weightPct)}%)</span>
          </div>
          <div className="flex-1 text-right font-mono text-slate-600">
            {sr.status === 'done' && sr.ecl != null
              ? <span className="text-slate-800 font-semibold">{fmtCurrency(sr.ecl)}</span>
              : sr.status === 'running'
              ? <span className="text-indigo-500 italic">Computing…</span>
              : <span className="text-slate-300">Pending</span>
            }
          </div>
          <div className="w-14 text-right font-mono text-slate-400 text-[10px]">
            {sr.status === 'done' && sr.durationMs != null
              ? `${(sr.durationMs / 1000).toFixed(1)}s`
              : '—'
            }
          </div>
        </div>
      ))}
    </div>
  );
}
