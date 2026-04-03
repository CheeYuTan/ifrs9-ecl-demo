import { motion } from 'framer-motion';
import { Table2, ArrowRight, Loader2 } from 'lucide-react';
import type { MappingStatus } from './types';

interface StatusCardsProps {
  status: Record<string, MappingStatus>;
  loadingStatus: boolean;
  onStartWizard: (tableKey: string) => void;
}

export default function StatusCards({ status, loadingStatus, onStartWizard }: StatusCardsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {Object.entries(status).map(([key, s]) => (
        <motion.div key={key} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
          className={`relative rounded-2xl border p-5 cursor-pointer transition hover:border-brand/40 ${
            s.has_data ? 'border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/5' : s.required ? 'border-slate-200 dark:border-white/10 bg-white dark:bg-white/[0.02]' : 'border-slate-100 dark:border-white/5 bg-white dark:bg-white/[0.01]'
          }`}
          onClick={() => onStartWizard(key)}>
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <Table2 size={16} className={s.has_data ? 'text-emerald-400' : 'text-slate-500'} />
              <span className="text-sm font-bold text-slate-800 dark:text-white">{key.replace(/_/g, ' ')}</span>
            </div>
            <div className="flex items-center gap-1.5">
              {s.required && (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-red-500/10 text-red-400 border border-red-500/20">
                  Required
                </span>
              )}
              {s.has_data ? (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {s.row_count.toLocaleString()} rows
                </span>
              ) : (
                <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-slate-500/10 text-slate-500 border border-slate-500/20">
                  No data
                </span>
              )}
            </div>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed mb-3 line-clamp-2">{s.description}</p>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3 text-[10px] text-slate-600 dark:text-slate-500">
              <span>{s.mandatory_columns} mandatory</span>
              <span>{s.optional_columns} optional</span>
            </div>
            <ArrowRight size={14} className="text-slate-500" />
          </div>
          {s.source_uc_table && (
            <div className="mt-2 pt-2 border-t border-slate-100 dark:border-white/5 text-[10px] text-slate-600 dark:text-slate-500 truncate">
              Source: {s.source_uc_table}
            </div>
          )}
        </motion.div>
      ))}

      {loadingStatus && Object.keys(status).length === 0 && (
        <div className="col-span-full flex items-center justify-center py-12 text-slate-500">
          <Loader2 size={20} className="animate-spin mr-2" /> Loading table status...
        </div>
      )}
    </div>
  );
}
