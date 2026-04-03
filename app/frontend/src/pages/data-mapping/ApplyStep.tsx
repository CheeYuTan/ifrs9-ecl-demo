import { Play, AlertTriangle, Loader2, CheckCircle2, XCircle } from 'lucide-react';

interface ApplyStepProps {
  selectedSourceTable: string;
  selectedTableKey: string;
  mappings: Record<string, string>;
  applyMode: 'overwrite' | 'append';
  applying: boolean;
  applyResult: any;
  onSetApplyMode: (mode: 'overwrite' | 'append') => void;
  onRunApply: () => void;
}

export default function ApplyStep({
  selectedSourceTable,
  selectedTableKey,
  mappings,
  applyMode,
  applying,
  applyResult,
  onSetApplyMode,
  onRunApply,
}: ApplyStepProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-white">
        <Play size={16} className="text-brand" />
        Apply Data Mapping
      </div>

      <div className="rounded-2xl border border-slate-200 dark:border-white/10 p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-500 dark:text-slate-400">Source Table</span>
            <p className="text-slate-800 dark:text-white font-semibold mt-1">{selectedSourceTable}</p>
          </div>
          <div>
            <span className="text-slate-500 dark:text-slate-400">Target Table</span>
            <p className="text-slate-800 dark:text-white font-semibold mt-1">{selectedTableKey.replace(/_/g, ' ')}</p>
          </div>
          <div>
            <span className="text-slate-500 dark:text-slate-400">Columns Mapped</span>
            <p className="text-slate-800 dark:text-white font-semibold mt-1">{Object.keys(mappings).length}</p>
          </div>
          <div>
            <span className="text-slate-500 dark:text-slate-400">Write Mode</span>
            <div className="flex items-center gap-2 mt-1">
              <button onClick={() => onSetApplyMode('overwrite')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  applyMode === 'overwrite' ? 'bg-brand text-white' : 'bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
                }`}>
                Overwrite
              </button>
              <button onClick={() => onSetApplyMode('append')}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  applyMode === 'append' ? 'bg-brand text-white' : 'bg-slate-100 dark:bg-white/5 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
                }`}>
                Append
              </button>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-300">
          <AlertTriangle size={14} className="flex-shrink-0" />
          {applyMode === 'overwrite'
            ? 'This will replace all existing data in the target table.'
            : 'This will append data to the existing target table.'}
        </div>

        <button onClick={onRunApply} disabled={applying}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand text-white text-sm font-bold hover:opacity-90 transition disabled:opacity-50">
          {applying ? <Loader2 size={16} className="animate-spin" /> : <Play size={16} />}
          {applying ? 'Ingesting data...' : 'Apply Mapping'}
        </button>
      </div>

      {/* Result */}
      {applyResult && (
        <div className={`rounded-2xl border p-4 ${
          applyResult.status === 'success' ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            {applyResult.status === 'success' ? (
              <CheckCircle2 size={16} className="text-emerald-400" />
            ) : (
              <XCircle size={16} className="text-red-400" />
            )}
            <span className="text-sm font-bold text-slate-800 dark:text-white">
              {applyResult.status === 'success' ? 'Data Ingested Successfully' : 'Ingestion Failed'}
            </span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-300">{applyResult.message}</p>
          {applyResult.rows_written > 0 && (
            <div className="mt-2 grid grid-cols-3 gap-3 text-xs">
              <div className="rounded-xl bg-slate-50 dark:bg-white/5 p-3 text-center">
                <div className="text-lg font-bold text-emerald-400">{applyResult.rows_written.toLocaleString()}</div>
                <div className="text-slate-400">Rows Written</div>
              </div>
              <div className="rounded-xl bg-slate-50 dark:bg-white/5 p-3 text-center">
                <div className="text-lg font-bold text-slate-800 dark:text-white">{applyResult.columns_mapped}</div>
                <div className="text-slate-400">Columns</div>
              </div>
              <div className="rounded-xl bg-slate-50 dark:bg-white/5 p-3 text-center">
                <div className="text-lg font-bold text-slate-800 dark:text-white capitalize">{applyResult.mode}</div>
                <div className="text-slate-400">Mode</div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
