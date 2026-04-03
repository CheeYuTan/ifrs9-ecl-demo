import { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, XCircle, Network } from 'lucide-react';
import type { AdminConfig } from './types';

// ── Types ──────────────────────────────────────────────────────────────

interface LineageNode {
  id: string;
  label: string;
  type: 'source' | 'transform' | 'target';
  columns: { name: string; mapped?: boolean; type?: string }[];
  x: number;
  y: number;
}

// ── Node Color Helper ──────────────────────────────────────────────────

function nodeColor(type: string) {
  if (type === 'source') return { bg: '#EFF6FF', border: '#3B82F6', text: '#1E40AF', accent: '#3B82F6' };
  if (type === 'transform') return { bg: '#F5F3FF', border: '#8B5CF6', text: '#5B21B6', accent: '#8B5CF6' };
  return { bg: '#ECFDF5', border: '#10B981', text: '#065F46', accent: '#10B981' };
}

// ── Edge Renderer ──────────────────────────────────────────────────────

function Edge({ srcX, srcY, tgtX, tgtY, edgeId, hoveredEdge, setHoveredEdge, label }: {
  srcX: number; srcY: number; tgtX: number; tgtY: number;
  edgeId: string; hoveredEdge: string | null;
  setHoveredEdge: (id: string | null) => void; label?: string;
}) {
  const isHovered = hoveredEdge === edgeId;
  return (
    <g onMouseEnter={() => setHoveredEdge(edgeId)} onMouseLeave={() => setHoveredEdge(null)}>
      <path
        d={`M ${srcX} ${srcY} C ${srcX + 50} ${srcY}, ${tgtX - 50} ${tgtY}, ${tgtX} ${tgtY}`}
        fill="none" stroke={isHovered ? 'url(#edgeGrad)' : '#CBD5E1'} strokeWidth={isHovered ? 2.5 : 1.5}
        strokeDasharray={isHovered ? '' : '4 4'} markerEnd={isHovered ? 'url(#arrowhead-active)' : 'url(#arrowhead)'}
        className="transition-all duration-200"
      />
      {isHovered && label && (
        <text x={(srcX + tgtX) / 2} y={Math.min(srcY, tgtY) - 8} textAnchor="middle" fontSize="9" fill="#8B5CF6" fontWeight="600">
          {label}
        </text>
      )}
    </g>
  );
}

// ── Node Renderer ──────────────────────────────────────────────────────

function NodeBox({ node, isSelected, onClick }: {
  node: LineageNode; isSelected: boolean; onClick: () => void;
}) {
  const c = nodeColor(node.type);
  const nodeWidth = 300;
  const headerHeight = 36;
  const colHeight = 22;
  const nodeHeight = headerHeight + node.columns.length * colHeight + 8;
  const icon = node.type === 'source' ? '📊' : node.type === 'transform' ? '⚙️' : '📈';

  return (
    <g onClick={onClick} className="cursor-pointer">
      <rect x={node.x} y={node.y} width={nodeWidth} height={nodeHeight} rx={12} ry={12}
        fill={c.bg} stroke={isSelected ? c.accent : c.border} strokeWidth={isSelected ? 2 : 1}
        filter="url(#shadow)" className="transition-all duration-200" />
      <rect x={node.x} y={node.y} width={nodeWidth} height={headerHeight} rx={12} ry={12} fill={c.accent} />
      <rect x={node.x} y={node.y + headerHeight - 12} width={nodeWidth} height={12} fill={c.accent} />
      <text x={node.x + 12} y={node.y + 22} fontSize="11" fontWeight="700" fill="white" fontFamily="Inter, sans-serif">
        {icon} {node.label}
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
}

// ── Node Detail Panel ──────────────────────────────────────────────────

function NodeDetail({ node, onClose }: { node: LineageNode; onClose: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="glass-card rounded-2xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <Network size={14} className="text-brand" />
        <span className="text-sm font-bold text-slate-700 dark:text-slate-200">{node.label}</span>
        <button onClick={onClose} className="ml-auto text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition">
          <XCircle size={14} />
        </button>
      </div>
      <div className="grid grid-cols-3 gap-2">
        {node.columns.map(col => (
          <div key={col.name} className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs ${col.mapped ? 'bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800' : 'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700'}`}>
            {col.mapped ? <CheckCircle2 size={10} className="text-emerald-500" /> : <div className="w-2.5 h-2.5 rounded-full bg-slate-300 dark:bg-slate-600" />}
            <span className="font-mono">{col.name}</span>
            {col.type && <span className="ml-auto text-[9px] text-slate-400">{col.type}</span>}
          </div>
        ))}
      </div>
    </motion.div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────

export default function VisualDataMapper({ config }: { config: AdminConfig }) {
  const tables = config.data_sources.tables;
  const tableEntries = Object.entries(tables);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  const sourceNodes: LineageNode[] = tableEntries.map(([key, tbl], i) => {
    const allCols = [...tbl.mandatory_columns, ...tbl.optional_columns];
    return {
      id: `src-${key}`, label: tbl.source_table, type: 'source' as const,
      columns: allCols.map(c => ({ name: tbl.column_mappings[c.name] || c.name, mapped: !!tbl.column_mappings[c.name], type: c.type })),
      x: 40, y: 40 + i * 180,
    };
  });

  const transformNode: LineageNode = {
    id: 'transform', label: 'ECL Engine', type: 'transform',
    columns: [
      { name: 'PD Calculation', type: 'PROCESS' }, { name: 'LGD Assignment', type: 'PROCESS' },
      { name: 'EAD Computation', type: 'PROCESS' }, { name: 'Stage Classification', type: 'PROCESS' },
      { name: 'Monte Carlo Sim', type: 'PROCESS' },
    ],
    x: 420, y: 40 + ((tableEntries.length - 1) * 180) / 2 - 40,
  };

  const targetNodes: LineageNode[] = [
    { id: 'tgt-ecl', label: 'ECL Results', type: 'target', columns: [{ name: 'ecl_amount' }, { name: 'stage' }, { name: 'pd_lifetime' }, { name: 'lgd' }], x: 780, y: 40 + ((tableEntries.length - 1) * 180) / 2 - 80 },
    { id: 'tgt-report', label: 'Reports', type: 'target', columns: [{ name: 'summary' }, { name: 'drill_down' }, { name: 'audit_trail' }], x: 780, y: 40 + ((tableEntries.length - 1) * 180) / 2 + 80 },
  ];

  const allNodes = [...sourceNodes, transformNode, ...targetNodes];
  const svgHeight = Math.max(500, tableEntries.length * 180 + 80);

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
            const tgtMidY = transformNode.y + 20 + (transformNode.columns.length * 10);
            return (
              <Edge key={`${src.id}-transform`} edgeId={`${src.id}-transform`}
                srcX={srcRight} srcY={srcMidY} tgtX={transformNode.x} tgtY={tgtMidY}
                hoveredEdge={hoveredEdge} setHoveredEdge={setHoveredEdge}
                label={`${src.columns.length} columns`} />
            );
          })}

          {targetNodes.map(tgt => {
            const srcRight = transformNode.x + 300;
            const srcMidY = transformNode.y + 20 + (transformNode.columns.length * 10);
            const tgtMidY = tgt.y + 20 + (tgt.columns.length * 10);
            return (
              <Edge key={`transform-${tgt.id}`} edgeId={`transform-${tgt.id}`}
                srcX={srcRight} srcY={srcMidY} tgtX={tgt.x} tgtY={tgtMidY}
                hoveredEdge={hoveredEdge} setHoveredEdge={setHoveredEdge} />
            );
          })}

          {allNodes.map(node => (
            <NodeBox key={node.id} node={node} isSelected={selectedNode === node.id}
              onClick={() => setSelectedNode(selectedNode === node.id ? null : node.id)} />
          ))}
        </svg>
      </div>

      {selectedNode && (() => {
        const node = allNodes.find(n => n.id === selectedNode);
        return node ? <NodeDetail node={node} onClose={() => setSelectedNode(null)} /> : null;
      })()}
    </div>
  );
}
