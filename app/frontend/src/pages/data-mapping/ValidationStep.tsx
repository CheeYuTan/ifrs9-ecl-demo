import { CheckCircle2, XCircle, AlertTriangle, Loader2, RefreshCw, ArrowRight } from 'lucide-react';
import { TypeBadge, StatusIcon } from './types';
import type { ColumnMapping } from './types';

interface ValidationStepProps {
  validationResult: any;
  validating: boolean;
  onRunValidation: () => void;
  onAdvanceToApply: () => void;
}

export default function ValidationStep({
  validationResult,
  validating,
  onRunValidation,
  onAdvanceToApply,
}: ValidationStepProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-white">
          <CheckCircle2 size={16} className="text-brand" />
          Validation Results
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onRunValidation} disabled={validating}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs font-semibold text-slate-700 dark:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition disabled:opacity-50">
            {validating ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            Re-validate
          </button>
          {validationResult?.valid && (
            <button onClick={onAdvanceToApply}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:opacity-90 transition">
              Apply <ArrowRight size={12} />
            </button>
          )}
        </div>
      </div>

      {validating && (
        <div className="flex items-center gap-2 text-xs text-slate-400 py-8 justify-center">
          <Loader2 size={16} className="animate-spin" /> Validating mapping...
        </div>
      )}

      {validationResult && !validating && (
        <>
          {/* Summary */}
          <div className={`rounded-2xl border p-4 ${
            validationResult.valid ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-red-500/30 bg-red-500/5'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              {validationResult.valid ? (
                <CheckCircle2 size={16} className="text-emerald-400" />
              ) : (
                <XCircle size={16} className="text-red-400" />
              )}
              <span className="text-sm font-bold text-slate-800 dark:text-white">
                {validationResult.valid ? 'Validation Passed' : 'Validation Failed'}
              </span>
              <span className="text-[10px] text-slate-500 dark:text-slate-400 ml-2">
                {validationResult.mandatory_mapped}/{validationResult.mandatory_count} mandatory columns mapped
              </span>
            </div>
            {validationResult.errors?.length > 0 && (
              <div className="space-y-1 mt-2">
                {validationResult.errors.map((e: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-red-600 dark:text-red-300">
                    <XCircle size={12} className="flex-shrink-0 mt-0.5" /> {e}
                  </div>
                ))}
              </div>
            )}
            {validationResult.warnings?.length > 0 && (
              <div className="space-y-1 mt-2">
                {validationResult.warnings.map((w: string, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-xs text-amber-600 dark:text-amber-300">
                    <AlertTriangle size={12} className="flex-shrink-0 mt-0.5" /> {w}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Column details */}
          <div className="rounded-2xl border border-slate-200 dark:border-white/10 overflow-hidden">
            <div className="px-4 py-2 bg-slate-50 dark:bg-white/5 text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Column Details
            </div>
            <div className="divide-y divide-slate-100 dark:divide-white/5 max-h-96 overflow-y-auto">
              {(validationResult.columns || []).map((col: ColumnMapping) => (
                <div key={col.ecl_column} className="flex items-center gap-3 px-4 py-2 text-xs">
                  <StatusIcon status={col.status} />
                  <div className="flex-1 min-w-0">
                    <span className="font-semibold text-slate-800 dark:text-white">{col.ecl_column}</span>
                    {col.is_mandatory && <span className="ml-1.5 text-[9px] text-red-400 font-bold">REQ</span>}
                  </div>
                  <ArrowRight size={10} className="text-slate-400 dark:text-slate-500" />
                  <div className="flex-1 min-w-0">
                    {col.source_column ? (
                      <span className="text-slate-600 dark:text-slate-300">{col.source_column}</span>
                    ) : (
                      <span className="text-slate-400 dark:text-slate-500 italic">not mapped</span>
                    )}
                  </div>
                  <TypeBadge type={col.ecl_type} />
                  {col.source_type && <TypeBadge type={col.source_type} />}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
