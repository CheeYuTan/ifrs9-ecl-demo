import { useState, useCallback, useEffect } from 'react';
import { ChevronUp, ChevronDown, Download, Search } from 'lucide-react';

interface Column {
  key: string;
  label: React.ReactNode;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  format?: (v: any, row: any) => string | React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

interface Props {
  columns: Column[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: any[];
  pageSize?: number;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onRowClick?: (row: any) => void;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  selectedRow?: any;
  compact?: boolean;
  exportName?: string;
}

export default function DataTable({ columns, data, pageSize = 15, onRowClick, selectedRow, compact, exportName }: Props) {
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [search, setSearch] = useState('');

  // Reset page when data changes
  useEffect(() => { setPage(0); }, [data]);

  const filtered = search
    ? data.filter(row => columns.some(c => { const v = row[c.key]; return v != null && String(v).toLowerCase().includes(search.toLowerCase()); }))
    : data;

  const sorted = sortKey
    ? [...filtered].sort((a, b) => {
        const av = a[sortKey], bv = b[sortKey];
        const cmp = typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv));
        return sortDir === 'asc' ? cmp : -cmp;
      })
    : filtered;

  const totalPages = Math.ceil(sorted.length / pageSize);
  const paged = sorted.slice(page * pageSize, (page + 1) * pageSize);

  const toggleSort = (key: string) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('asc'); }
  };

  const py = compact ? 'py-2' : 'py-3';

  const exportCsv = useCallback(() => {
    const header = columns.map(c => typeof c.label === 'string' ? c.label : c.key).join(',');
    const rows = sorted.map(row =>
      columns.map(c => {
        const v = row[c.key];
        const s = v == null ? '' : (typeof v === 'object' ? JSON.stringify(v) : String(v));
        return s.includes(',') || s.includes('"') || s.includes('\n') ? `"${s.replace(/"/g, '""')}"` : s;
      }).join(',')
    );
    const csv = '\uFEFF' + [header, ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `${exportName || 'export'}_${new Date().toISOString().slice(0, 10)}.csv`; a.click();
    URL.revokeObjectURL(url);
  }, [columns, data, sorted, exportName]);

  return (
    <div>
      {(data.length > 5 || exportName) && (
        <div className="flex items-center justify-between mb-3 gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" />
            <label htmlFor={`table-search-${exportName || 'default'}`} className="sr-only">Search table</label>
            <input id={`table-search-${exportName || 'default'}`} value={search} onChange={e => { setSearch(e.target.value); setPage(0); }} placeholder="Search..."
              className="form-input pl-10 text-xs" />
          </div>
          <button onClick={exportCsv} aria-label={`Export ${exportName || 'data'} as CSV`}
            className="btn-secondary text-xs shadow-sm">
            <Download size={12} /> Export CSV
          </button>
        </div>
      )}
      <div className="overflow-x-auto rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gradient-to-r from-slate-100 to-slate-50 text-slate-700 dark:from-slate-700/80 dark:to-slate-600/60 dark:text-slate-100">
              {columns.map(c => (
                <th key={c.key} onClick={() => toggleSort(c.key)}
                  className={`${py} px-4 text-[11px] font-bold uppercase tracking-wider cursor-pointer select-none whitespace-nowrap ${c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : 'text-left'}`}
                  scope="col" aria-sort={sortKey === c.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}
                  tabIndex={0} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleSort(c.key); } }}>
                  <span className="inline-flex items-center gap-1 hover:opacity-80 transition">
                    {c.label}
                    {sortKey === c.key && (sortDir === 'asc' ? <ChevronUp size={11} /> : <ChevronDown size={11} />)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((row, ri) => (
              <tr key={ri} onClick={() => onRowClick?.(row)}
                role="row"
                tabIndex={onRowClick ? 0 : undefined}
                onKeyDown={onRowClick ? (e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onRowClick(row); } }) : undefined}
                className={`border-b border-slate-50 transition-colors ${
                  onRowClick ? 'cursor-pointer hover:bg-brand/5' : 'hover:bg-slate-50/80 dark:hover:bg-white/[0.04]'
                } ${ri % 2 === 1 ? 'bg-slate-50/40 dark:bg-white/[0.02]' : 'bg-white dark:bg-transparent'} ${
                  selectedRow && JSON.stringify(selectedRow) === JSON.stringify(row) ? 'bg-brand/8 ring-1 ring-brand/20' : ''
                }`}>
                {columns.map(c => (
                  <td key={c.key} className={`${py} px-4 ${c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : 'text-left'} ${c.className || ''}`}>
                    {c.format ? c.format(row[c.key], row) : row[c.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-3 text-xs text-slate-400">
          <span>{sorted.length} rows</span>
          <div className="flex gap-1">
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} aria-label="Previous page"
              className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition shadow-sm focus-visible:ring-2 focus-visible:ring-brand">Prev</button>
            <span className="px-3 py-1.5 font-semibold text-slate-600 dark:text-slate-300" aria-live="polite">Page {page + 1} of {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} aria-label="Next page"
              className="px-3 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 transition shadow-sm focus-visible:ring-2 focus-visible:ring-brand">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
