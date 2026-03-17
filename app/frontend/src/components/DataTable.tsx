import { useState, useCallback } from 'react';
import { ChevronUp, ChevronDown, Download, Search } from 'lucide-react';

interface Column {
  key: string;
  label: string;
  format?: (v: any, row: any) => string | React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

interface Props {
  columns: Column[];
  data: any[];
  pageSize?: number;
  onRowClick?: (row: any) => void;
  selectedRow?: any;
  compact?: boolean;
  exportName?: string;
}

export default function DataTable({ columns, data, pageSize = 15, onRowClick, selectedRow, compact, exportName }: Props) {
  const [page, setPage] = useState(0);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [search, setSearch] = useState('');

  const filtered = search
    ? data.filter(row =>
        columns.some(c => {
          const v = row[c.key];
          return v != null && String(v).toLowerCase().includes(search.toLowerCase());
        })
      )
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

  const py = compact ? 'py-2' : 'py-2.5';

  const exportCsv = useCallback(() => {
    const header = columns.map(c => c.label).join(',');
    const rows = data.map(row =>
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
    a.href = url;
    a.download = `${exportName || 'export'}_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [columns, data, exportName]);

  return (
    <div>
      {(data.length > 5 || exportName) && (
        <div className="flex items-center justify-between mb-3 gap-3">
          <div className="relative flex-1 max-w-xs">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300" />
            <input
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(0); }}
              placeholder="Search..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:ring-2 focus:ring-brand focus:border-transparent outline-none transition"
            />
          </div>
          <button onClick={exportCsv} className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-500 bg-slate-100 rounded-lg hover:bg-slate-200 transition" title="Export to CSV">
            <Download size={12} /> CSV
          </button>
        </div>
      )}
      <div className="overflow-x-auto rounded-lg border border-slate-100">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-navy text-white">
              {columns.map(c => (
                <th
                  key={c.key}
                  onClick={() => toggleSort(c.key)}
                  className={`${py} px-3 text-[11px] font-semibold uppercase tracking-wider cursor-pointer select-none whitespace-nowrap ${c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : 'text-left'}`}
                >
                  <span className="inline-flex items-center gap-1">
                    {c.label}
                    {sortKey === c.key && (sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />)}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paged.map((row, ri) => (
              <tr
                key={ri}
                onClick={() => onRowClick?.(row)}
                className={`border-b border-slate-50 transition-colors ${
                  onRowClick ? 'cursor-pointer hover:bg-blue-50' : ''
                } ${ri % 2 === 1 ? 'bg-slate-50/50' : ''} ${
                  selectedRow && JSON.stringify(selectedRow) === JSON.stringify(row) ? 'bg-blue-50 ring-1 ring-blue-200' : ''
                }`}
              >
                {columns.map(c => (
                  <td key={c.key} className={`${py} px-3 ${c.align === 'right' ? 'text-right' : c.align === 'center' ? 'text-center' : 'text-left'} ${c.className || ''}`}>
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
            <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 disabled:opacity-40">Prev</button>
            <span className="px-2 py-1">{page + 1} / {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 disabled:opacity-40">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
