import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, CheckCircle2, XCircle, AlertTriangle,
  ChevronDown, ChevronRight,
  RefreshCw, Eye, Wand2, Loader2, CheckCheck,
  GitBranch, LayoutGrid,
} from 'lucide-react';
import Card from '../../components/Card';
import { useToast } from '../../components/Toast';
import { fetchJson, inputCls, labelCls } from './types';
import type { AdminConfig } from './types';
import ColumnMappingRow, { Badge } from './ColumnMappingRow';
import VisualDataMapper from './VisualDataMapper';

// ── Data Mapping Tab ────────────────────────────────────────────────────

export interface AdminDataMappingsProps {
  config: AdminConfig;
  onChange: (c: AdminConfig) => void;
}

export default function AdminDataMappings({ config, onChange }: AdminDataMappingsProps) {
  const { toast } = useToast();
  const [viewMode, setViewMode] = useState<'table' | 'graph'>('table');
  const [expanded, setExpanded] = useState<string | null>('loan_tape');
  const [validating, setValidating] = useState<string | null>(null);
  const [validatingAll, setValidatingAll] = useState(false);
  const [validationResults, setValidationResults] = useState<Record<string, any>>({});
  const [schemas, setSchemas] = useState<string[]>([]);
  const [loadingSchemas, setLoadingSchemas] = useState(false);
  const [tableColumns, setTableColumns] = useState<Record<string, any[]>>({});
  const [suggestions, setSuggestions] = useState<Record<string, any>>({});
  const [previews, setPreviews] = useState<Record<string, any>>({});
  const [loadingColumns, setLoadingColumns] = useState<string | null>(null);
  const [loadingPreview, setLoadingPreview] = useState<string | null>(null);
  const [availableTables, setAvailableTables] = useState<any[]>([]);
  const [tableRowCounts, setTableRowCounts] = useState<Record<string, number | null>>({});

  const tables = config.data_sources.tables;
  const tableEntries = Object.entries(tables);

  const loadSchemas = useCallback(async () => {
    setLoadingSchemas(true);
    try { setSchemas(await fetchJson<string[]>('/api/admin/schemas')); } catch { /* */ }
    finally { setLoadingSchemas(false); }
  }, []);

  const loadAvailableTables = useCallback(async () => {
    try { setAvailableTables(await fetchJson<any[]>('/api/admin/available-tables')); } catch { /* */ }
  }, []);

  useEffect(() => { loadSchemas(); loadAvailableTables(); }, [loadSchemas, loadAvailableTables]);

  const loadColumnsForTable = useCallback(async (tableKey: string) => {
    const tbl = tables[tableKey];
    if (!tbl) return;
    setLoadingColumns(tableKey);
    const prefix = config.data_sources.lakebase_prefix || 'lb_';
    const tableName = prefix + tbl.source_table;
    try {
      const [cols, sugg] = await Promise.all([
        fetchJson<any[]>(`/api/admin/table-columns/${tableName}`),
        fetchJson<any>(`/api/admin/suggest-mappings/${tableKey}`),
      ]);
      setTableColumns(prev => ({ ...prev, [tableKey]: cols }));
      setSuggestions(prev => ({ ...prev, [tableKey]: sugg }));
    } catch {
      setTableColumns(prev => ({ ...prev, [tableKey]: [] }));
    } finally { setLoadingColumns(null); }
  }, [config.data_sources.lakebase_prefix, tables]);

  useEffect(() => {
    if (!expanded || tableColumns[expanded]) return;
    loadColumnsForTable(expanded);
  }, [expanded, loadColumnsForTable, tableColumns]);

  const loadRowCount = useCallback(async (tableKey: string) => {
    const tbl = tables[tableKey];
    if (!tbl) return;
    const prefix = config.data_sources.lakebase_prefix || 'lb_';
    try {
      const data = await fetchJson<any>(`/api/admin/table-preview/${prefix}${tbl.source_table}?limit=1`);
      if (data.total_rows !== undefined) setTableRowCounts(prev => ({ ...prev, [tableKey]: data.total_rows }));
    } catch { /* */ }
  }, [config.data_sources.lakebase_prefix, tables]);

  useEffect(() => { tableEntries.forEach(([key]) => loadRowCount(key)); }, []); // eslint-disable-line

  const handleMappingChange = (tableKey: string, colName: string, mappedTo: string) => {
    const updated = { ...config };
    const mappings = { ...updated.data_sources.tables[tableKey].column_mappings };
    if (mappedTo && mappedTo !== colName) mappings[colName] = mappedTo;
    else delete mappings[colName];
    updated.data_sources.tables[tableKey] = { ...updated.data_sources.tables[tableKey], column_mappings: mappings };
    onChange(updated);
  };

  const handleSourceTableChange = (tableKey: string, newSourceTable: string) => {
    const updated = { ...config };
    updated.data_sources.tables[tableKey] = { ...updated.data_sources.tables[tableKey], source_table: newSourceTable };
    onChange(updated);
    setTableColumns(prev => { const n = { ...prev }; delete n[tableKey]; return n; });
    setSuggestions(prev => { const n = { ...prev }; delete n[tableKey]; return n; });
    setValidationResults(prev => { const n = { ...prev }; delete n[tableKey]; return n; });
  };

  const handleAutoDetect = (tableKey: string) => {
    const sugg = suggestions[tableKey];
    if (!sugg?.suggestions) { toast('No suggestions available', 'info'); return; }
    const updated = { ...config };
    const mappings: Record<string, string> = {};
    let count = 0;
    for (const [expected, info] of Object.entries(sugg.suggestions) as [string, any][]) {
      if (info.mapped && info.mapped !== expected) mappings[expected] = info.mapped;
      count++;
    }
    updated.data_sources.tables[tableKey] = { ...updated.data_sources.tables[tableKey], column_mappings: mappings };
    onChange(updated);
    toast(`Auto-detected ${count} column mappings`, 'success');
  };

  const handlePreview = async (tableKey: string) => {
    const tbl = tables[tableKey];
    const prefix = config.data_sources.lakebase_prefix || 'lb_';
    setLoadingPreview(tableKey);
    try {
      const data = await fetchJson<any>(`/api/admin/table-preview/${prefix}${tbl.source_table}?limit=5`);
      setPreviews(prev => ({ ...prev, [tableKey]: data }));
    } catch (e: any) { toast(`Preview failed: ${e.message}`, 'error'); }
    finally { setLoadingPreview(null); }
  };

  const handleValidate = async (tableKey: string) => {
    setValidating(tableKey);
    try {
      const result = await fetchJson<any>('/api/admin/validate-mapping', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ table_key: tableKey, mappings: tables[tableKey].column_mappings }),
      });
      setValidationResults(prev => ({ ...prev, [tableKey]: result }));
      if (result.valid && (!result.warnings || result.warnings.length === 0)) toast('All columns validated', 'success');
      else if (result.valid) toast(`Valid with ${result.warnings.length} warning(s)`, 'success');
      else toast(`${result.errors.length} error(s) found`, 'error');
    } catch (e: any) { toast(`Validation failed: ${e.message}`, 'error'); }
    finally { setValidating(null); }
  };

  const handleValidateAll = async () => {
    setValidatingAll(true);
    let totalErrors = 0, totalWarnings = 0, totalValid = 0;
    for (const [key] of tableEntries) {
      try {
        const result = await fetchJson<any>('/api/admin/validate-mapping', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ table_key: key, mappings: tables[key].column_mappings }),
        });
        setValidationResults(prev => ({ ...prev, [key]: result }));
        if (result.valid) totalValid++;
        totalErrors += result.errors?.length || 0;
        totalWarnings += result.warnings?.length || 0;
      } catch { totalErrors++; }
    }
    if (totalErrors === 0 && totalWarnings === 0) toast(`All ${tableEntries.length} tables validated`, 'success');
    else if (totalErrors === 0) toast(`${totalValid}/${tableEntries.length} valid, ${totalWarnings} warning(s)`, 'info');
    else toast(`${totalErrors} error(s), ${totalWarnings} warning(s)`, 'error');
    setValidatingAll(false);
  };

  const handleSourceChange = (field: string, value: string) => {
    const updated = { ...config, data_sources: { ...config.data_sources, [field]: value } };
    onChange(updated);
    if (field === 'lakebase_schema' || field === 'lakebase_prefix') {
      setTableColumns({}); setSuggestions({}); setValidationResults({}); setPreviews({}); setTableRowCounts({});
    }
  };

  const validationSummary = useMemo(() => {
    let errors = 0, warnings = 0, valid = 0;
    for (const vr of Object.values(validationResults)) {
      if (vr?.valid) valid++;
      errors += vr?.errors?.length || 0;
      warnings += vr?.warnings?.length || 0;
    }
    return { errors, warnings, valid, total: tableEntries.length };
  }, [validationResults, tableEntries.length]);

  const lbTableNames = useMemo(() => {
    const prefix = config.data_sources.lakebase_prefix || 'lb_';
    return availableTables.filter(t => t.table_name?.startsWith(prefix)).map(t => t.table_name.slice(prefix.length));
  }, [availableTables, config.data_sources.lakebase_prefix]);

  return (
    <div className="space-y-4">
      <Card accent="brand" icon={<Database size={16} />} title="Data Source Connection" subtitle="Unity Catalog and Lakebase connection settings">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className={labelCls}>Unity Catalog</label>
            <input value={config.data_sources.catalog} onChange={e => handleSourceChange('catalog', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>UC Schema</label>
            <input value={config.data_sources.schema} onChange={e => handleSourceChange('schema', e.target.value)} className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Lakebase Schema</label>
            <div className="flex gap-2">
              {schemas.length > 0 ? (
                <select value={config.data_sources.lakebase_schema} onChange={e => handleSourceChange('lakebase_schema', e.target.value)} className={`${inputCls} flex-1`}>
                  <option value="">-- select --</option>
                  {schemas.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              ) : (
                <input value={config.data_sources.lakebase_schema} onChange={e => handleSourceChange('lakebase_schema', e.target.value)} className={`${inputCls} flex-1`} />
              )}
              <button onClick={loadSchemas} disabled={loadingSchemas} className="px-2.5 py-2 rounded-xl border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition text-slate-500 dark:text-slate-400 disabled:opacity-40" title="Refresh schemas">
                <RefreshCw size={14} className={loadingSchemas ? 'animate-spin' : ''} />
              </button>
            </div>
          </div>
          <div>
            <label className={labelCls}>Table Prefix</label>
            <input value={config.data_sources.lakebase_prefix} onChange={e => handleSourceChange('lakebase_prefix', e.target.value)} className={inputCls} />
          </div>
        </div>
      </Card>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex bg-slate-100 dark:bg-slate-800 rounded-xl p-0.5">
            <button onClick={() => setViewMode('table')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                viewMode === 'table' ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-700 dark:text-white' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
              }`}>
              <LayoutGrid size={12} /> Table View
            </button>
            <button onClick={() => setViewMode('graph')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                viewMode === 'graph' ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-700 dark:text-white' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
              }`}>
              <GitBranch size={12} /> Lineage View
            </button>
          </div>
          <div className="h-4 w-px bg-slate-200 dark:bg-slate-700" />
          {validationSummary.valid > 0 && <Badge variant="green"><CheckCircle2 size={10} /> {validationSummary.valid} valid</Badge>}
          {validationSummary.errors > 0 && <Badge variant="red"><XCircle size={10} /> {validationSummary.errors} error(s)</Badge>}
          {validationSummary.warnings > 0 && <Badge variant="yellow"><AlertTriangle size={10} /> {validationSummary.warnings} warning(s)</Badge>}
        </div>
        {viewMode === 'table' && (
          <button onClick={handleValidateAll} disabled={validatingAll}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold gradient-navy text-white rounded-xl hover:opacity-90 transition disabled:opacity-50 shadow-sm">
            {validatingAll ? <Loader2 size={14} className="animate-spin" /> : <CheckCheck size={14} />}
            {validatingAll ? 'Validating...' : 'Validate All Tables'}
          </button>
        )}
      </div>

      {viewMode === 'graph' ? (
        <VisualDataMapper config={config} />
      ) : tableEntries.map(([key, tbl]) => (
        <TableCard key={key} tableKey={key} tbl={tbl} expanded={expanded} setExpanded={setExpanded}
          validationResults={validationResults} tableColumns={tableColumns} loadingColumns={loadingColumns}
          tableRowCounts={tableRowCounts} lbTableNames={lbTableNames} suggestions={suggestions}
          previews={previews} loadingPreview={loadingPreview} validating={validating}
          onMappingChange={handleMappingChange} onSourceTableChange={handleSourceTableChange}
          onAutoDetect={handleAutoDetect} onValidate={handleValidate} onPreview={handlePreview}
          onRefresh={loadColumnsForTable} onClosePreview={(k) => setPreviews(prev => { const n = { ...prev }; delete n[k]; return n; })} />
      ))}
    </div>
  );
}

// ── Table Card ──────────────────────────────────────────────────────────

function TableCard({ tableKey, tbl, expanded, setExpanded, validationResults, tableColumns,
  loadingColumns, tableRowCounts, lbTableNames, suggestions, previews, loadingPreview,
  validating, onMappingChange, onSourceTableChange, onAutoDetect, onValidate, onPreview,
  onRefresh, onClosePreview,
}: {
  tableKey: string; tbl: any; expanded: string | null; setExpanded: (k: string | null) => void;
  validationResults: Record<string, any>; tableColumns: Record<string, any[]>;
  loadingColumns: string | null; tableRowCounts: Record<string, number | null>;
  lbTableNames: string[]; suggestions: Record<string, any>; previews: Record<string, any>;
  loadingPreview: string | null; validating: string | null;
  onMappingChange: (k: string, c: string, v: string) => void;
  onSourceTableChange: (k: string, v: string) => void;
  onAutoDetect: (k: string) => void; onValidate: (k: string) => void;
  onPreview: (k: string) => void; onRefresh: (k: string) => void;
  onClosePreview: (k: string) => void;
}) {
  const isOpen = expanded === tableKey;
  const vr = validationResults[tableKey];
  const cols = tableColumns[tableKey] || [];
  const isLoadingCols = loadingColumns === tableKey;
  const rowCount = tableRowCounts[tableKey];

  return (
    <Card>
      <button onClick={() => setExpanded(isOpen ? null : tableKey)} className="w-full flex items-center justify-between group">
        <div className="flex items-center gap-3">
          {isOpen ? <ChevronDown size={16} className="text-brand" /> : <ChevronRight size={16} className="text-slate-400" />}
          <div className="text-left">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200">{tableKey.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
              {tbl.required !== false
                ? <span className="text-[9px] font-bold uppercase tracking-wider text-red-500 bg-red-50 px-1.5 py-0.5 rounded-full">Required</span>
                : <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded-full">Optional</span>
              }
            </div>
            {tbl.description && !isOpen && <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1 max-w-2xl">{tbl.description}</p>}
            <p className="text-xs text-slate-400 mt-0.5">
              Source: <span className="font-mono">{tbl.source_table}</span> &middot; {tbl.mandatory_columns.length} mandatory, {tbl.optional_columns.length} optional
              {cols.length > 0 && <span className="text-emerald-500 ml-1">&middot; {cols.length} columns loaded</span>}
              {rowCount != null && <span className="text-blue-500 ml-1">&middot; {rowCount.toLocaleString()} rows</span>}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {vr && (vr.valid ? <Badge variant="green"><CheckCircle2 size={10} /> Valid</Badge> : <Badge variant="red"><XCircle size={10} /> {vr.errors?.length || 0} error(s)</Badge>)}
        </div>
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
            <div className="mt-4 border-t border-slate-100 dark:border-slate-700 pt-4">
              {tbl.description && (
                <div className="mb-4 p-3 bg-brand/5 rounded-xl border border-brand/10">
                  <p className="text-xs text-brand-dark leading-relaxed">{tbl.description}</p>
                </div>
              )}
              <div className="mb-4 flex items-center gap-3">
                <label className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase whitespace-nowrap">Source Table:</label>
                {lbTableNames.length > 0 ? (
                  <select value={tbl.source_table} onChange={e => onSourceTableChange(tableKey, e.target.value)}
                    className="form-input flex-1 max-w-xs text-xs font-mono py-1.5">
                    <option value={tbl.source_table}>{tbl.source_table}</option>
                    {lbTableNames.filter(n => n !== tbl.source_table).map(n => <option key={n} value={n}>{n}</option>)}
                  </select>
                ) : (
                  <input value={tbl.source_table} onChange={e => onSourceTableChange(tableKey, e.target.value)}
                    className="flex-1 max-w-xs px-2 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none" />
                )}
              </div>

              {isLoadingCols && (
                <div className="flex items-center gap-2 mb-4 px-3 py-2 bg-brand/5 rounded-xl border border-brand/10">
                  <Loader2 size={14} className="animate-spin text-brand" />
                  <span className="text-xs text-brand-dark">Loading columns and suggestions...</span>
                </div>
              )}

              <div className="grid grid-cols-12 gap-3 items-center mb-2 px-0">
                <div className="col-span-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Expected Column</div>
                <div className="col-span-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Type</div>
                <div className="col-span-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Description</div>
                <div className="col-span-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Mapped To</div>
                <div className="col-span-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">Actual Type</div>
              </div>

              <div className="mb-2"><Badge variant="brand">Required</Badge></div>
              <div className="space-y-0.5">
                {tbl.mandatory_columns.map((col: any) => (
                  <ColumnMappingRow key={col.name} col={col} tableKey={tableKey} tbl={tbl} tableColumns={cols} validationResult={vr} isMandatory={true} onChange={onMappingChange} />
                ))}
              </div>

              {tbl.optional_columns.length > 0 && (
                <>
                  <div className="mt-4 mb-2"><Badge variant="gray">Optional</Badge></div>
                  <div className="space-y-0.5">
                    {tbl.optional_columns.map((col: any) => (
                      <ColumnMappingRow key={col.name} col={col} tableKey={tableKey} tbl={tbl} tableColumns={cols} validationResult={vr} isMandatory={false} onChange={onMappingChange} />
                    ))}
                  </div>
                </>
              )}

              <div className="mt-4 flex items-center gap-3 flex-wrap">
                {suggestions[tableKey]?.suggestions && (
                  <button onClick={() => onAutoDetect(tableKey)} className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-gradient-to-r from-purple to-indigo text-white rounded-xl hover:opacity-90 transition shadow-sm">
                    <Wand2 size={14} /> Auto-Detect
                  </button>
                )}
                <button onClick={() => onValidate(tableKey)} disabled={validating === tableKey}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-blue text-white rounded-xl hover:opacity-90 transition disabled:opacity-50 shadow-sm">
                  {validating === tableKey ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                  {validating === tableKey ? 'Validating...' : 'Validate'}
                </button>
                <button onClick={() => onPreview(tableKey)} disabled={loadingPreview === tableKey}
                  className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition disabled:opacity-50">
                  {loadingPreview === tableKey ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
                  Preview
                </button>
                <button onClick={() => onRefresh(tableKey)} disabled={isLoadingCols}
                  className="flex items-center gap-1.5 px-3 py-2 text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition disabled:opacity-40">
                  <RefreshCw size={12} className={isLoadingCols ? 'animate-spin' : ''} /> Refresh
                </button>
              </div>

              {vr?.errors?.length > 0 && (
                <div className="mt-3 p-3 bg-red-50 rounded-xl border border-red-200">
                  {vr.errors.map((e: string, i: number) => <p key={i} className="text-xs text-red-700 flex items-center gap-1.5"><XCircle size={12} /> {e}</p>)}
                </div>
              )}
              {vr?.warnings?.length > 0 && (
                <div className="mt-2 p-3 bg-amber-50 rounded-xl border border-amber-200">
                  {vr.warnings.map((w: string, i: number) => <p key={i} className="text-xs text-amber-700 flex items-center gap-1.5"><AlertTriangle size={12} /> {w}</p>)}
                </div>
              )}

              {previews[tableKey] && (
                <div className="mt-3 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                  <div className="bg-slate-50 dark:bg-slate-800 px-3 py-2 text-xs font-bold text-slate-600 dark:text-slate-300 flex justify-between items-center">
                    <span>Data Preview &mdash; {previews[tableKey].table}</span>
                    <button onClick={() => onClosePreview(tableKey)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition"><XCircle size={12} /></button>
                  </div>
                  <div className="overflow-x-auto max-h-48">
                    <table className="w-full text-xs">
                      <thead><tr className="bg-slate-100 dark:bg-slate-800">{previews[tableKey].columns?.map((c: any) => <th key={c.name} className="py-1.5 px-2 text-left font-semibold text-slate-600 dark:text-slate-300 whitespace-nowrap">{c.name}</th>)}</tr></thead>
                      <tbody>{previews[tableKey].rows?.map((row: any, i: number) => <tr key={i} className="border-t border-slate-50 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-800/50">{previews[tableKey].columns?.map((c: any) => <td key={c.name} className="py-1 px-2 font-mono text-slate-600 dark:text-slate-300 whitespace-nowrap max-w-[200px] truncate">{String(row[c.name] ?? '')}</td>)}</tr>)}</tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}
