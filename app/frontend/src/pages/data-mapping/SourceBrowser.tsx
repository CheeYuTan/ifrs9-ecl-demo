import { FolderOpen, Loader2, Eye, ArrowRight } from 'lucide-react';
import { TypeBadge } from './types';

interface SourceBrowserProps {
  catalogs: any[];
  selectedCatalog: string;
  schemas: any[];
  selectedSchema: string;
  tables: any[];
  selectedSourceTable: string;
  loadingBrowse: boolean;
  loadingPreview: boolean;
  showPreview: boolean;
  previewData: any;
  onSelectCatalog: (catalog: string) => void;
  onSelectSchema: (schema: string) => void;
  onSelectSourceTable: (table: string) => void;
  onLoadPreview: (sourceTable: string) => void;
  onContinueToMapColumns: () => void;
}

export default function SourceBrowser({
  catalogs,
  selectedCatalog,
  schemas,
  selectedSchema,
  tables,
  selectedSourceTable,
  loadingBrowse,
  loadingPreview,
  showPreview,
  previewData,
  onSelectCatalog,
  onSelectSchema,
  onSelectSourceTable,
  onLoadPreview,
  onContinueToMapColumns,
}: SourceBrowserProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-800 dark:text-white mb-2">
        <FolderOpen size={16} className="text-brand" />
        Browse Unity Catalog
      </div>

      {/* Catalog selector */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Catalog</label>
          <select value={selectedCatalog}
            onChange={(e) => onSelectCatalog(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-brand">
            <option value="">-- Select catalog --</option>
            {catalogs.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Schema</label>
          <select value={selectedSchema} disabled={!selectedCatalog}
            onChange={(e) => onSelectSchema(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-brand disabled:opacity-40">
            <option value="">-- Select schema --</option>
            {schemas.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Table</label>
          <select value={selectedSourceTable} disabled={!selectedSchema}
            onChange={(e) => onSelectSourceTable(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-brand disabled:opacity-40">
            <option value="">-- Select table --</option>
            {tables.map(t => <option key={t.name} value={t.full_name}>{t.name} ({t.table_type})</option>)}
          </select>
        </div>
      </div>

      {/* Or enter manually */}
      <div className="flex items-center gap-3 text-[11px] text-slate-500">
        <div className="flex-1 h-px bg-slate-200 dark:bg-white/5" />
        <span>or enter full table path</span>
        <div className="flex-1 h-px bg-slate-200 dark:bg-white/5" />
      </div>
      <input
        type="text"
        placeholder="catalog.schema.table_name"
        value={selectedSourceTable}
        onChange={(e) => onSelectSourceTable(e.target.value)}
        className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-800 dark:text-white text-xs focus:outline-none focus:ring-2 focus:ring-brand"
      />

      {loadingBrowse && (
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <Loader2 size={14} className="animate-spin" /> Loading...
        </div>
      )}

      {/* Preview button */}
      {selectedSourceTable && (
        <div className="flex items-center gap-3">
          <button onClick={() => onLoadPreview(selectedSourceTable)} disabled={loadingPreview}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-xs font-semibold text-slate-700 dark:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition disabled:opacity-50">
            {loadingPreview ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
            Preview Data
          </button>
          <button onClick={onContinueToMapColumns}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-brand text-white text-xs font-semibold hover:opacity-90 transition">
            Continue <ArrowRight size={14} />
          </button>
        </div>
      )}

      {/* Preview table */}
      {showPreview && previewData && (
        <div className="mt-4 rounded-2xl border border-slate-200 dark:border-white/10 overflow-hidden">
          <div className="px-4 py-2 bg-slate-50 dark:bg-white/5 flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-800 dark:text-white">
              Preview: {previewData.table} ({previewData.total_rows?.toLocaleString()} total rows)
            </span>
            <span className="text-[10px] text-slate-400">Showing {previewData.row_count} rows</span>
          </div>
          <div className="overflow-x-auto max-h-64">
            <table className="w-full text-[11px]">
              <thead>
                <tr className="border-b border-slate-100 dark:border-white/5">
                  {(previewData.columns || []).map((c: any) => (
                    <th key={c.name} className="px-3 py-2 text-left font-semibold text-slate-500 dark:text-slate-400 whitespace-nowrap">
                      {c.name} <TypeBadge type={c.type} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(previewData.rows || []).map((row: any, i: number) => (
                  <tr key={i} className="border-b border-slate-50 dark:border-white/5 hover:bg-slate-50/50 dark:hover:bg-white/[0.02]">
                    {(previewData.columns || []).map((c: any) => (
                      <td key={c.name} className="px-3 py-1.5 text-slate-600 dark:text-slate-300 whitespace-nowrap max-w-[200px] truncate">
                        {row[c.name] ?? <span className="text-slate-400 dark:text-slate-500 italic">null</span>}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
