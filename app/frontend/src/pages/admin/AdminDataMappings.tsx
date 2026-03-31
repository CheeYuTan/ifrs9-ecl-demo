import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, CheckCircle2, XCircle, AlertTriangle,
  ChevronDown, ChevronRight,
  RefreshCw, Eye, Wand2, Loader2, CheckCheck,
  HelpCircle, GitBranch, Network,
  LayoutGrid,
} from 'lucide-react';
import Card from '../../components/Card';
import { useToast } from '../../components/Toast';
import { fetchJson, isTypeCompatible, inputCls, labelCls } from './types';
import type { AdminConfig, ColumnDef, TableConfig } from './types';

// ── Badge & Tooltip ──────────────────────────────────────────────────────────

function Badge({ variant, children }: { variant: 'green' | 'yellow' | 'red' | 'gray' | 'brand'; children: React.ReactNode }) {
  const cls = {
    green: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    yellow: 'bg-amber-50 text-amber-700 border-amber-200',
    red: 'bg-red-50 text-red-700 border-red-200',
    gray: 'bg-slate-50 dark:bg-slate-800 text-slate-500 border-slate-200 dark:border-slate-700',
    brand: 'bg-brand/10 text-brand-dark border-brand/20',
  }[variant];
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${cls}`}>{children}</span>;
}

function Tooltip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex ml-1 cursor-help">
      <HelpCircle size={11} className="text-slate-300 group-hover:text-slate-500 dark:group-hover:text-slate-400 transition" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 text-[10px] leading-tight bg-slate-800 text-white rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition pointer-events-none w-52 z-50 text-center">
        {text}
      </span>
    </span>
  );
}

// ── Column Mapping Row ─────────────────────────────────────────────────────

function ColumnMappingRow({
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
      <div className="col-span-3 text-[11px] text-slate-400 leading-tight pt-0.5">
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
          <span className={`text-[10px] font-mono flex items-center gap-0.5 ${compatible ? 'text-emerald-600' : 'text-amber-600'}`}>
            {compatible ? <CheckCircle2 size={10} /> : <AlertTriangle size={10} />}
            {actualCol.data_type}
          </span>
        ) : mapped && tableColumns.length > 0 ? (
          <span className="text-[10px] text-red-400 font-mono">not found</span>
        ) : (
          <span className="text-xs text-slate-300">&mdash;</span>
        )}
      </div>
    </div>
  );
}

// ── Visual Data Mapper (Lineage Graph) ─────────────────────────────────────

interface LineageNode {
  id: string;
  label: string;
  type: 'source' | 'transform' | 'target';
  columns: { name: string; mapped?: boolean; type?: string }[];
  x: number;
  y: number;
}

function VisualDataMapper({ config }: { config: AdminConfig }) {
  const tables = config.data_sources.tables;
  const tableEntries = Object.entries(tables);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const sourceNodes: LineageNode[] = tableEntries.map(([key, tbl], i) => {
    const allCols = [...tbl.mandatory_columns, ...tbl.optional_columns];
    return {
      id: `src-${key}`,
      label: tbl.source_table,
      type: 'source' as const,
      columns: allCols.map(c => ({
        name: tbl.column_mappings[c.name] || c.name,
        mapped: !!tbl.column_mappings[c.name],
        type: c.type,
      })),
      x: 40,
      y: 40 + i * 180,
    };
  });

  const transformNode: LineageNode = {
    id: 'transform',
    label: 'ECL Engine',
    type: 'transform',
    columns: [
      { name: 'PD Calculation', type: 'PROCESS' },
      { name: 'LGD Assignment', type: 'PROCESS' },
      { name: 'EAD Computation', type: 'PROCESS' },
      { name: 'Stage Classification', type: 'PROCESS' },
      { name: 'Monte Carlo Sim', type: 'PROCESS' },
    ],
    x: 420,
    y: 40 + ((tableEntries.length - 1) * 180) / 2 - 40,
  };

  const targetNodes: LineageNode[] = [
    { id: 'tgt-ecl', label: 'ECL Results', type: 'target', columns: [{ name: 'ecl_amount' }, { name: 'stage' }, { name: 'pd_lifetime' }, { name: 'lgd' }], x: 780, y: 40 + ((tableEntries.length - 1) * 180) / 2 - 80 },
    { id: 'tgt-report', label: 'Reports', type: 'target', columns: [{ name: 'summary' }, { name: 'drill_down' }, { name: 'audit_trail' }], x: 780, y: 40 + ((tableEntries.length - 1) * 180) / 2 + 80 },
  ];

  const allNodes = [...sourceNodes, transformNode, ...targetNodes];
  const svgHeight = Math.max(500, tableEntries.length * 180 + 80);

  const nodeColor = (type: string) => {
    if (type === 'source') return { bg: '#EFF6FF', border: '#3B82F6', text: '#1E40AF', accent: '#3B82F6' };
    if (type === 'transform') return { bg: '#F5F3FF', border: '#8B5CF6', text: '#5B21B6', accent: '#8B5CF6' };
    return { bg: '#ECFDF5', border: '#10B981', text: '#065F46', accent: '#10B981' };
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 mb-2">
        <div className="flex items-center gap-2 text-xs">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-blue-500" /> Source Tables</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-purple" /> Processing</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded bg-emerald-500" /> Output</span>
        </div>
      </div>

      <div className="glass-card rounded-2xl overflow-hidden border border-slate-100 dark:border-slate-700">
        <svg width="100%" viewBox={`0 0 1000 ${svgHeight}`} className="select-none">
          <defs>
            <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="#94A3B8" />
            </marker>
            <marker id="arrowhead-active" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
              <polygon points="0 0, 8 3, 0 6" fill="var(--color-brand)" />
            </marker>
            <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
              <feDropShadow dx="0" dy="2" stdDeviation="4" floodOpacity="0.08" />
            </filter>
            <linearGradient id="edgeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.4" />
              <stop offset="50%" stopColor="#8B5CF6" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#10B981" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {sourceNodes.map(src => {
            const srcRight = src.x + 300;
            const srcMidY = src.y + 20 + (src.columns.length * 10);
            const tgtLeft = transformNode.x;
            const tgtMidY = transformNode.y + 20 + (transformNode.columns.length * 10);
            const edgeId = `${src.id}-transform`;
            const isHovered = hoveredEdge === edgeId;
            return (
              <g key={edgeId} onMouseEnter={() => setHoveredEdge(edgeId)} onMouseLeave={() => setHoveredEdge(null)}>
                <path
                  d={`M ${srcRight} ${srcMidY} C ${srcRight + 50} ${srcMidY}, ${tgtLeft - 50} ${tgtMidY}, ${tgtLeft} ${tgtMidY}`}
                  fill="none" stroke={isHovered ? 'url(#edgeGrad)' : '#CBD5E1'} strokeWidth={isHovered ? 2.5 : 1.5}
                  strokeDasharray={isHovered ? '' : '4 4'} markerEnd={isHovered ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
                  className="transition-all duration-200"
                />
                {isHovered && (
                  <text x={(srcRight + tgtLeft) / 2} y={Math.min(srcMidY, tgtMidY) - 8} textAnchor="middle" fontSize="9" fill="#8B5CF6" fontWeight="600">
                    {src.columns.length} columns
                  </text>
                )}
              </g>
            );
          })}

          {targetNodes.map(tgt => {
            const srcRight = transformNode.x + 300;
            const srcMidY = transformNode.y + 20 + (transformNode.columns.length * 10);
            const tgtLeft = tgt.x;
            const tgtMidY = tgt.y + 20 + (tgt.columns.length * 10);
            const edgeId = `transform-${tgt.id}`;
            const isHovered = hoveredEdge === edgeId;
            return (
              <g key={edgeId} onMouseEnter={() => setHoveredEdge(edgeId)} onMouseLeave={() => setHoveredEdge(null)}>
                <path
                  d={`M ${srcRight} ${srcMidY} C ${srcRight + 50} ${srcMidY}, ${tgtLeft - 50} ${tgtMidY}, ${tgtLeft} ${tgtMidY}`}
                  fill="none" stroke={isHovered ? 'url(#edgeGrad)' : '#CBD5E1'} strokeWidth={isHovered ? 2.5 : 1.5}
                  strokeDasharray={isHovered ? '' : '4 4'} markerEnd={isHovered ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
                  className="transition-all duration-200"
                />
              </g>
            );
          })}

          {allNodes.map(node => {
            const c = nodeColor(node.type);
            const isSelected = selectedNode === node.id;
            const nodeWidth = 300;
            const headerHeight = 36;
            const colHeight = 22;
            const nodeHeight = headerHeight + node.columns.length * colHeight + 8;

            return (
              <g key={node.id} onClick={() => setSelectedNode(isSelected ? null : node.id)} className="cursor-pointer">
                <rect x={node.x} y={node.y} width={nodeWidth} height={nodeHeight} rx={12} ry={12}
                  fill={c.bg} stroke={isSelected ? c.accent : c.border} strokeWidth={isSelected ? 2 : 1}
                  filter="url(#shadow)" className="transition-all duration-200" />

                <rect x={node.x} y={node.y} width={nodeWidth} height={headerHeight} rx={12} ry={12} fill={c.accent} />
                <rect x={node.x} y={node.y + headerHeight - 12} width={nodeWidth} height={12} fill={c.accent} />

                <text x={node.x + 12} y={node.y + 22} fontSize="11" fontWeight="700" fill="white" fontFamily="Inter, sans-serif">
                  {node.type === 'source' ? '📊' : node.type === 'transform' ? '⚙️' : '📈'} {node.label}
                </text>

                {node.columns.map((col, ci) => {
                  const cy = node.y + headerHeight + 4 + ci * colHeight;
                  return (
                    <g key={col.name}>
                      <rect x={node.x + 4} y={cy} width={nodeWidth - 8} height={colHeight - 2} rx={4} ry={4}
                        fill={col.mapped ? 'rgba(16,185,129,0.08)' : 'transparent'}
                        className="hover:fill-[rgba(0,0,0,0.03)] transition-colors" />
                      {col.mapped && <circle cx={node.x + 14} cy={cy + 10} r={3} fill="#10B981" />}
                      {!col.mapped && node.type === 'source' && <circle cx={node.x + 14} cy={cy + 10} r={3} fill="#CBD5E1" />}
                      <text x={node.x + 24} y={cy + 14} fontSize="10" fill={c.text} fontFamily="'JetBrains Mono', monospace">
                        {col.name}
                      </text>
                      {col.type && (
                        <text x={node.x + nodeWidth - 12} y={cy + 14} fontSize="8" fill="#94A3B8" textAnchor="end" fontFamily="Inter, sans-serif">
                          {col.type}
                        </text>
                      )}
                    </g>
                  );
                })}
              </g>
            );
          })}
        </svg>
      </div>

      {selectedNode && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-2xl p-4">
          <div className="flex items-center gap-2 mb-2">
            <Network size={14} className="text-brand" />
            <span className="text-sm font-bold text-slate-700 dark:text-slate-200">
              {allNodes.find(n => n.id === selectedNode)?.label}
            </span>
            <button onClick={() => setSelectedNode(null)} className="ml-auto text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition">
              <XCircle size={14} />
            </button>
          </div>
          <div className="grid grid-cols-3 gap-2">
            {allNodes.find(n => n.id === selectedNode)?.columns.map(col => (
              <div key={col.name} className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${col.mapped ? 'bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700'}`}>
                {col.mapped ? <CheckCircle2 size={10} className="text-emerald-500" /> : <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-600" />}
                <span className="font-mono">{col.name}</span>
                {col.type && <span className="ml-auto text-[9px] text-slate-400">{col.type}</span>}
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}

// ── Data Mapping Tab ────────────────────────────────────────────────────────

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
      ) : tableEntries.map(([key, tbl]) => {
        const isOpen = expanded === key;
        const vr = validationResults[key];
        const cols = tableColumns[key] || [];
        const isLoadingCols = loadingColumns === key;
        const rowCount = tableRowCounts[key];

        return (
          <Card key={key}>
            <button onClick={() => setExpanded(isOpen ? null : key)} className="w-full flex items-center justify-between group">
              <div className="flex items-center gap-3">
                {isOpen ? <ChevronDown size={16} className="text-brand" /> : <ChevronRight size={16} className="text-slate-400" />}
                <div className="text-left">
                  <div className="flex items-center gap-2">
                    <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</h4>
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
                        <select value={tbl.source_table} onChange={e => handleSourceTableChange(key, e.target.value)}
                          className="form-input flex-1 max-w-xs text-xs font-mono py-1.5">
                          <option value={tbl.source_table}>{tbl.source_table}</option>
                          {lbTableNames.filter(n => n !== tbl.source_table).map(n => <option key={n} value={n}>{n}</option>)}
                        </select>
                      ) : (
                        <input value={tbl.source_table} onChange={e => handleSourceTableChange(key, e.target.value)}
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
                      {tbl.mandatory_columns.map(col => (
                        <ColumnMappingRow key={col.name} col={col} tableKey={key} tbl={tbl} tableColumns={cols} validationResult={vr} isMandatory={true} onChange={handleMappingChange} />
                      ))}
                    </div>

                    {tbl.optional_columns.length > 0 && (
                      <>
                        <div className="mt-4 mb-2"><Badge variant="gray">Optional</Badge></div>
                        <div className="space-y-0.5">
                          {tbl.optional_columns.map(col => (
                            <ColumnMappingRow key={col.name} col={col} tableKey={key} tbl={tbl} tableColumns={cols} validationResult={vr} isMandatory={false} onChange={handleMappingChange} />
                          ))}
                        </div>
                      </>
                    )}

                    <div className="mt-4 flex items-center gap-3 flex-wrap">
                      {suggestions[key]?.suggestions && (
                        <button onClick={() => handleAutoDetect(key)} className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-gradient-to-r from-purple to-indigo text-white rounded-xl hover:opacity-90 transition shadow-sm">
                          <Wand2 size={14} /> Auto-Detect
                        </button>
                      )}
                      <button onClick={() => handleValidate(key)} disabled={validating === key}
                        className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-blue text-white rounded-xl hover:opacity-90 transition disabled:opacity-50 shadow-sm">
                        {validating === key ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle2 size={14} />}
                        {validating === key ? 'Validating...' : 'Validate'}
                      </button>
                      <button onClick={() => handlePreview(key)} disabled={loadingPreview === key}
                        className="flex items-center gap-1.5 px-4 py-2 text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-200 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition disabled:opacity-50">
                        {loadingPreview === key ? <Loader2 size={14} className="animate-spin" /> : <Eye size={14} />}
                        Preview
                      </button>
                      <button onClick={() => loadColumnsForTable(key)} disabled={isLoadingCols}
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

                    {previews[key] && (
                      <div className="mt-3 border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden">
                        <div className="bg-slate-50 dark:bg-slate-800 px-3 py-2 text-xs font-bold text-slate-600 dark:text-slate-300 flex justify-between items-center">
                          <span>Data Preview &mdash; {previews[key].table}</span>
                          <button onClick={() => setPreviews(prev => { const n = { ...prev }; delete n[key]; return n; })} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition"><XCircle size={12} /></button>
                        </div>
                        <div className="overflow-x-auto max-h-48">
                          <table className="w-full text-xs">
                            <thead><tr className="bg-slate-100 dark:bg-slate-800">{previews[key].columns?.map((c: any) => <th key={c.name} className="py-1.5 px-2 text-left font-semibold text-slate-600 dark:text-slate-300 whitespace-nowrap">{c.name}</th>)}</tr></thead>
                            <tbody>{previews[key].rows?.map((row: any, i: number) => <tr key={i} className="border-t border-slate-50 dark:border-slate-800 hover:bg-slate-50/50 dark:hover:bg-slate-800/50">{previews[key].columns?.map((c: any) => <td key={c.name} className="py-1 px-2 font-mono text-slate-600 dark:text-slate-300 whitespace-nowrap max-w-[200px] truncate">{String(row[c.name] ?? '')}</td>)}</tr>)}</tbody>
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
      })}
    </div>
  );
}
