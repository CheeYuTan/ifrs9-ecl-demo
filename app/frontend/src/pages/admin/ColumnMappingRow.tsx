import {
  CheckCircle2, XCircle, AlertTriangle, HelpCircle,
} from 'lucide-react';
import { isTypeCompatible } from './types';
import type { ColumnDef, TableConfig } from './types';

// ── Badge ──────────────────────────────────────────────────────────────

export function Badge({ variant, children }: { variant: 'green' | 'yellow' | 'red' | 'gray' | 'brand'; children: React.ReactNode }) {
  const cls = {
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    yellow: 'bg-amber-50 text-amber-700 border-amber-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-slate-50 dark:bg-slate-800 text-slate-500 border-slate-200 dark:border-slate-700',
    brand: 'bg-brand/10 text-brand-dark border-brand/20',
  }[variant];
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold border ${cls}`}>{children}</span>;
}

// ── Tooltip ────────────────────────────────────────────────────────────

function Tooltip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex ml-1 cursor-help">
      <HelpCircle size={11} className="text-slate-300 group-hover:text-slate-500 dark:group-hover:text-slate-400 transition" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 text-[11px] leading-tight bg-slate-800 text-white rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition pointer-events-none w-52 z-50 text-center">
        {text}
      </span>
    </span>
  );
}

// ── Column Mapping Row ─────────────────────────────────────────────────

export default function ColumnMappingRow({
  col, tableKey, tbl, tableColumns, validationResult, isMandatory, onChange,
}: {
  col: ColumnDef;
  tableKey: string;
  tbl: TableConfig;
  tableColumns: any[];
  validationResult: any;
  isMandatory: boolean;
  onChange: (tableKey: string, colName: string, mappedTo: string) => void;
}) {
  const mapped = tbl.column_mappings[col.name] || col.name;
  const vrCol = validationResult?.columns?.find((c: any) => c.expected === col.name);
  const actualCol = tableColumns.find((c: any) => c.column_name === mapped);
  const compatible = actualCol ? isTypeCompatible(col.type, actualCol.data_type) : true;

  const tooltipParts: string[] = [];
  if (col.description) tooltipParts.push(col.description);
  if (col.constraints) tooltipParts.push(`Constraints: ${col.constraints}`);
  if (col.example) tooltipParts.push(`Example: ${col.example}`);
  if (col.default) tooltipParts.push(`Default: ${col.default}`);
  const tooltipText = tooltipParts.join(' | ');

  return (
    <div className="grid grid-cols-12 gap-3 items-start py-2 hover:bg-brand/3 dark:hover:bg-brand/5 rounded-lg -mx-1 px-1 transition">
      <div className="col-span-3 flex items-start gap-2 min-w-0">
        <div className="mt-0.5 flex-shrink-0">
          {vrCol ? (
            vrCol.status === 'ok'
              ? <CheckCircle2 size={14} className="text-emerald-500" />
              : isMandatory
                ? <XCircle size={14} className="text-red-500" />
                : <AlertTriangle size={14} className="text-amber-500" />
          ) : <div className="w-3.5" />}
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1">
            <span className={`text-xs font-mono truncate ${isMandatory ? 'font-semibold text-slate-700 dark:text-slate-200' : 'text-slate-500 dark:text-slate-400'}`}>{col.name}</span>
            {tooltipText && <Tooltip text={tooltipText} />}
          </div>
          {col.example && (
            <p className="text-[9px] text-slate-300 dark:text-slate-500 font-mono truncate mt-0.5" title={col.example}>e.g. {col.example}</p>
          )}
        </div>
      </div>
      <div className="col-span-1 pt-0.5">
        <Badge variant={isMandatory ? 'brand' : 'gray'}>{col.type}</Badge>
      </div>
      <div className="col-span-3 text-[11px] text-slate-500 dark:text-slate-300 leading-tight pt-0.5">
        <span className="line-clamp-2" title={col.description}>{col.description}</span>
        {col.default && <span className="block text-[9px] text-slate-300 mt-0.5">Default: {col.default}</span>}
      </div>
      <div className="col-span-3 pt-0.5">
        {tableColumns.length > 0 ? (
          <select
            value={mapped}
            onChange={e => onChange(tableKey, col.name, e.target.value)}
            className={`w-full px-2 py-1.5 rounded-lg border text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none bg-white/80 dark:bg-slate-800/80 ${
              isMandatory ? 'border-slate-200 dark:border-slate-700' : 'border-dashed border-slate-200 dark:border-slate-700'
            }`}
          >
            <option value="">-- unmapped --</option>
            {tableColumns.map((c: any) => (
              <option key={c.column_name} value={c.column_name}>{c.column_name}</option>
            ))}
          </select>
        ) : (
          <input
            value={tbl.column_mappings[col.name] || ''}
            onChange={e => onChange(tableKey, col.name, e.target.value)}
            placeholder={col.name}
            className={`w-full px-2 py-1.5 rounded-lg border text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none ${
              isMandatory ? 'border-slate-200 dark:border-slate-700' : 'border-dashed border-slate-200 dark:border-slate-700'
            }`}
          />
        )}
      </div>
      <div className="col-span-2 flex items-center gap-1 pt-1">
        {actualCol ? (
          <span className={`text-[11px] font-mono flex items-center gap-0.5 ${compatible ? 'text-emerald-600' : 'text-amber-600'}`}>
            {compatible ? <CheckCircle2 size={10} /> : <AlertTriangle size={10} />}
            {actualCol.data_type}
          </span>
        ) : mapped && tableColumns.length > 0 ? (
          <span className="text-[11px] text-red-400 font-mono">not found</span>
        ) : (
          <span className="text-xs text-slate-300">&mdash;</span>
        )}
      </div>
    </div>
  );
}
