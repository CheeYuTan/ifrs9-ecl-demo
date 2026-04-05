import { Columns3, Wand2, ArrowRight, Search } from 'lucide-react';
import { TypeBadge, StatusIcon } from './types';

interface ColumnMapperProps {
  mappings: Record<string, string>;
  allEclColumns: any[];
  filteredEclColumns: any[];
  columnFilter: string;
  sourceColNames: string[];
  onSetMappings: (updater: (prev: Record<string, string>) => Record<string, string>) => void;
  onSetColumnFilter: (filter: string) => void;
  onAutoSuggest: () => void;
  onValidateAndAdvance: () => void;
}

export default function ColumnMapper({
  mappings,
  allEclColumns,
  filteredEclColumns,
  columnFilter,
  sourceColNames,
  onSetMappings,
  onSetColumnFilter,
  onAutoSuggest,
  onValidateAndAdvance,
}: ColumnMapperProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-white">
          <Columns3 size={16} className="text-brand" />
          Column Mapping
          <span className="text-[10px] text-slate-400 font-normal ml-2">
            {Object.keys(mappings).length} / {allEclColumns.length} mapped
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={onAutoSuggest}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand/10 text-brand text-xs font-semibold hover:bg-brand/20 transition">
            <Wand2 size={12} /> Auto-Detect
          </button>
          <button onClick={onValidateAndAdvance}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:opacity-90 transition">
            Validate <ArrowRight size={12} />
          </button>
        </div>
      </div>

      {/* Search filter */}
      <div className="relative">
        <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" />
        <input type="text" placeholder="Filter columns..." value={columnFilter} onChange={(e) => onSetColumnFilter(e.target.value)}
          className="w-full pl-10 pr-3 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-brand" />
      </div>

      {/* Column mapping table */}
      <div className="rounded-2xl border border-slate-200 dark:border-white/10 overflow-hidden">
        <div className="grid grid-cols-[auto_1fr_14px_1fr_auto] gap-0 items-center px-4 py-2 bg-slate-50 dark:bg-slate-700/50 text-[11px] font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider">
          <span className="w-6" />
          <span>ECL Column</span>
          <span />
          <span>Source Column</span>
          <span className="w-16 text-center">Type</span>
        </div>
        <div className="max-h-[50vh] overflow-y-auto divide-y divide-slate-100 dark:divide-white/5">
          {filteredEclColumns.map((col: any) => {
            const mapped = mappings[col.name] || '';
            return (
              <div key={col.name}
                className={`grid grid-cols-[auto_1fr_14px_1fr_auto] gap-0 items-center px-4 py-2.5 transition ${
                  col.is_mandatory && !mapped ? 'bg-red-500/5' : 'hover:bg-slate-50/50 dark:hover:bg-white/[0.02]'
                }`}>
                <div className="w-6 flex items-center">
                  {col.is_mandatory ? (
                    <span className="w-1.5 h-1.5 rounded-full bg-red-400" title="Mandatory" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" title="Optional" />
                  )}
                </div>
                <div className="pr-3">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-semibold text-slate-800 dark:text-white">{col.name}</span>
                    <TypeBadge type={col.type} />
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5 line-clamp-1">{col.description}</p>
                </div>
                <ArrowRight size={12} className="text-slate-400 dark:text-slate-500" />
                <div className="pl-3">
                  <select value={mapped}
                    onChange={(e) => {
                      const v = e.target.value;
                      onSetMappings(prev => {
                        const n = { ...prev };
                        if (v) n[col.name] = v;
                        else delete n[col.name];
                        return n;
                      });
                    }}
                    className="w-full px-2.5 py-1.5 rounded-lg bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-brand">
                    <option value="">-- not mapped --</option>
                    {sourceColNames.map(name => (
                      <option key={name} value={name}>{name}</option>
                    ))}
                  </select>
                </div>
                <div className="w-16 flex justify-center">
                  {mapped ? (
                    <StatusIcon status="ok" />
                  ) : col.is_mandatory ? (
                    <StatusIcon status="unmapped" />
                  ) : (
                    <StatusIcon status="unmapped_optional" />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
