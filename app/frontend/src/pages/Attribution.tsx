import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, ReferenceLine,
} from 'recharts';
import {
  BarChart3, RefreshCw, CheckCircle2, AlertTriangle,
  Clock, ChevronDown, Info,
} from 'lucide-react';
import { api } from '../lib/api';
import { fmtCurrency, fmtPct, fmtDateTime } from '../lib/format';
import { useChartTheme } from '../lib/chartTheme';

interface StageData {
  stage1: number;
  stage2: number;
  stage3: number;
  total: number;
  status?: string;
  reason?: string;
  note?: string;
}

interface WaterfallItem {
  name: string;
  value: number;
  cumulative: number;
  category: string;
  base: number;
}

interface Reconciliation {
  total_movement: number;
  absolute_residual: number;
  residual_pct: number;
  within_materiality: boolean;
  materiality_threshold_pct: number;
  data_gaps: string[];
}

interface AttributionData {
  attribution_id: string;
  project_id: string;
  reporting_date: string;
  opening_ecl: StageData;
  closing_ecl: StageData;
  new_originations: StageData;
  derecognitions: StageData;
  stage_transfers: StageData;
  model_changes: StageData;
  macro_changes: StageData;
  management_overlays: StageData;
  write_offs: StageData;
  unwind_discount: StageData;
  fx_changes: StageData;
  residual: StageData;
  waterfall_data: WaterfallItem[];
  reconciliation: Reconciliation;
  computed_at?: string;
}

const COMPONENT_LABELS: Record<string, string> = {
  new_originations: 'New Originations',
  derecognitions: 'Derecognitions',
  stage_transfers: 'Stage Transfers',
  model_changes: 'Model Parameter Changes',
  macro_changes: 'Macro Scenario Changes',
  management_overlays: 'Management Overlays',
  write_offs: 'Write-offs',
  unwind_discount: 'Unwind of Discount',
  fx_changes: 'FX Changes',
  residual: 'Residual',
};

const WATERFALL_COLORS: Record<string, string> = {
  anchor: '#6366F1',
  increase: '#22C55E',
  decrease: '#EF4444',
  change: '#F59E0B',
};

export default function Attribution() {
  const [data, setData] = useState<AttributionData | null>(null);
  const [history, setHistory] = useState<AttributionData[]>([]);
  const [loading, setLoading] = useState(true);
  const [computing, setComputing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedHistoryIdx, setSelectedHistoryIdx] = useState(0);
  const [showHistory, setShowHistory] = useState(false);
  const chart = useChartTheme();

  const projectId = 'demo_2025q1';

  const loadAttribution = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const attr = await api.getAttribution(projectId);
      setData(attr);
    } catch (e: any) {
      setError(e.message || 'Failed to load attribution');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const loadHistory = useCallback(async () => {
    try {
      const h = await api.getAttributionHistory(projectId);
      setHistory(h);
    } catch {
      // History is optional — don't block on failure
    }
  }, [projectId]);

  useEffect(() => {
    loadAttribution();
    loadHistory();
  }, [loadAttribution, loadHistory]);

  const handleCompute = async () => {
    setComputing(true);
    setError(null);
    try {
      const attr = await api.computeAttribution(projectId);
      setData(attr);
      await loadHistory();
    } catch (e: any) {
      setError(e.message || 'Failed to compute attribution');
    } finally {
      setComputing(false);
    }
  };

  const handleHistorySelect = (idx: number) => {
    setSelectedHistoryIdx(idx);
    if (history[idx]) {
      setData(history[idx]);
    }
    setShowHistory(false);
  };

  if (loading) return <LoadingSkeleton />;

  if (error && !data) {
    return (
      <div className="space-y-6">
        <PageHeader onCompute={handleCompute} computing={computing} />
        <ErrorCard message={error} onRetry={loadAttribution} />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="space-y-6">
        <PageHeader onCompute={handleCompute} computing={computing} />
        <EmptyState onCompute={handleCompute} computing={computing} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader onCompute={handleCompute} computing={computing} />

      {error && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="glass-card rounded-2xl p-4 border-l-4 border-amber-400 flex items-center gap-3">
          <AlertTriangle size={16} className="text-amber-500 flex-shrink-0" />
          <p className="text-xs text-slate-600 dark:text-slate-300">{error}</p>
        </motion.div>
      )}

      {/* History selector */}
      {history.length > 1 && (
        <HistorySelector
          history={history}
          selectedIdx={selectedHistoryIdx}
          open={showHistory}
          onToggle={() => setShowHistory(!showHistory)}
          onSelect={handleHistorySelect}
        />
      )}

      {/* Reconciliation Status */}
      <ReconciliationCard recon={data.reconciliation} />

      {/* Waterfall Chart */}
      <WaterfallChart waterfall={data.waterfall_data} chartTheme={chart} />

      {/* Stage Breakdown Table */}
      <BreakdownTable data={data} />
    </div>
  );
}

function PageHeader({ onCompute, computing }: { onCompute: () => void; computing: boolean }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-2xl gradient-brand flex items-center justify-center shadow-lg">
          <BarChart3 size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-lg font-extrabold text-slate-800 dark:text-white">ECL Attribution Analysis</h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">IFRS 7.35I Loss Allowance Reconciliation</p>
        </div>
      </div>
      <button onClick={onCompute} disabled={computing}
        className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white gradient-brand rounded-xl shadow-lg hover:opacity-90 transition disabled:opacity-50">
        <RefreshCw size={14} className={computing ? 'animate-spin' : ''} />
        {computing ? 'Computing...' : 'Recompute'}
      </button>
    </div>
  );
}

function ReconciliationCard({ recon }: { recon: Reconciliation }) {
  const passed = recon.within_materiality;
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200">Reconciliation Check</h3>
        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
          passed
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
            : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
        }`}>
          {passed ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
          {passed ? 'Within Materiality' : 'Materiality Breach'}
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <MetricCell label="Total Movement" value={fmtCurrency(recon.total_movement)} />
        <MetricCell label="Residual" value={fmtCurrency(recon.absolute_residual)} />
        <MetricCell label="Residual %" value={fmtPct(recon.residual_pct, 4)} />
        <MetricCell label="Threshold" value={fmtPct(recon.materiality_threshold_pct)} />
      </div>
      {recon.data_gaps.length > 0 && (
        <div className="mt-3 flex items-start gap-2 p-3 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/30">
          <Info size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-semibold text-amber-700 dark:text-amber-400">Data Gaps Detected</p>
            <p className="text-[11px] text-amber-600 dark:text-amber-300 mt-0.5">
              Unavailable: {recon.data_gaps.join(', ')}
            </p>
          </div>
        </div>
      )}
    </motion.div>
  );
}

function MetricCell({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-300">{label}</p>
      <p className="text-sm font-extrabold text-slate-800 dark:text-white mt-0.5">{value}</p>
    </div>
  );
}

function WaterfallChart({ waterfall, chartTheme }: { waterfall: WaterfallItem[]; chartTheme: ReturnType<typeof useChartTheme> }) {
  const chartData = waterfall.map(item => ({
    ...item,
    // For anchors: full bar from 0. For changes: floating bar from base.
    invisible: item.category === 'anchor' ? 0 : item.base,
    visible: item.category === 'anchor' ? item.value : item.value,
  }));

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}
      className="glass-card rounded-2xl p-5">
      <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-4">ECL Waterfall — Opening to Closing</h3>
      <ResponsiveContainer width="100%" height={380}>
        <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 60, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.grid} vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 10, fill: chartTheme.axis }}
            angle={-35}
            textAnchor="end"
            interval={0}
            height={60}
          />
          <YAxis
            tick={{ fontSize: 10, fill: chartTheme.axis }}
            tickFormatter={(v: number) => fmtCurrency(v)}
          />
          <Tooltip content={<WaterfallTooltip />} />
          <ReferenceLine y={0} stroke={chartTheme.reference} />
          <Bar dataKey="invisible" stackId="waterfall" fill="transparent" />
          <Bar dataKey="visible" stackId="waterfall" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, idx) => {
              const color = entry.category === 'anchor'
                ? WATERFALL_COLORS.anchor
                : entry.value >= 0
                  ? WATERFALL_COLORS.increase
                  : WATERFALL_COLORS.decrease;
              return <Cell key={idx} fill={color} />;
            })}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  );
}

function WaterfallTooltip({ active, payload }: { active?: boolean; payload?: any[] }) {
  if (!active || !payload?.length) return null;
  const item = payload[1]?.payload || payload[0]?.payload;
  if (!item) return null;

  return (
    <div className="glass-card rounded-xl px-3 py-2 shadow-lg border border-slate-100 dark:border-slate-700">
      <p className="text-xs font-bold text-slate-700 dark:text-slate-200 mb-1">{item.name}</p>
      <p className="text-sm font-extrabold" style={{
        color: item.category === 'anchor'
          ? WATERFALL_COLORS.anchor
          : item.value >= 0 ? WATERFALL_COLORS.increase : WATERFALL_COLORS.decrease,
      }}>
        {fmtCurrency(item.value)}
      </p>
      {item.category !== 'anchor' && (
        <p className="text-[11px] text-slate-500 dark:text-slate-300 mt-0.5">Cumulative: {fmtCurrency(item.cumulative)}</p>
      )}
    </div>
  );
}

function BreakdownTable({ data }: { data: AttributionData }) {
  const components = [
    { key: 'opening_ecl', label: 'Opening ECL', isAnchor: true },
    ...Object.entries(COMPONENT_LABELS).map(([key, label]) => ({ key, label, isAnchor: false })),
    { key: 'closing_ecl', label: 'Closing ECL', isAnchor: true },
  ];

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}
      className="glass-card rounded-2xl overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 dark:border-slate-700/50">
        <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200">Stage-Level Breakdown</h3>
        <p className="text-[11px] text-slate-500 dark:text-slate-300 mt-0.5">All amounts by impairment stage</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-slate-50 dark:bg-slate-800/40">
              <th className="text-left px-5 py-3 font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider">Component</th>
              <th className="text-right px-4 py-3 font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider">Stage 1</th>
              <th className="text-right px-4 py-3 font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider">Stage 2</th>
              <th className="text-right px-4 py-3 font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider">Stage 3</th>
              <th className="text-right px-5 py-3 font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider">Total</th>
              <th className="px-4 py-3 font-bold text-slate-600 dark:text-slate-200 uppercase tracking-wider text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-700/30">
            {components.map(({ key, label, isAnchor }) => {
              const comp = (data as any)[key] as StageData | undefined;
              if (!comp) return null;
              const isUnavailable = comp.status === 'data_unavailable';
              const rowClass = isAnchor
                ? 'bg-indigo-50/50 dark:bg-indigo-900/10 font-bold'
                : 'hover:bg-slate-50 dark:hover:bg-slate-800/20';
              return (
                <tr key={key} className={rowClass}>
                  <td className="px-5 py-3 text-slate-700 dark:text-slate-200 font-semibold">{label}</td>
                  <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-300 font-mono">
                    {isUnavailable ? '—' : fmtCurrency(comp.stage1)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-300 font-mono">
                    {isUnavailable ? '—' : fmtCurrency(comp.stage2)}
                  </td>
                  <td className="px-4 py-3 text-right text-slate-600 dark:text-slate-300 font-mono">
                    {isUnavailable ? '—' : fmtCurrency(comp.stage3)}
                  </td>
                  <td className={`px-5 py-3 text-right font-mono ${isAnchor ? 'text-indigo-600 dark:text-indigo-400 font-extrabold' : 'text-slate-800 dark:text-slate-100 font-bold'}`}>
                    {isUnavailable ? '—' : fmtCurrency(comp.total)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ComponentStatus comp={comp} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  );
}

function ComponentStatus({ comp }: { comp: StageData }) {
  if (comp.status === 'data_unavailable') {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
        title={comp.reason || 'Data unavailable'}>
        <AlertTriangle size={10} /> Unavailable
      </span>
    );
  }
  if (comp.note) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
        title={comp.note}>
        <Info size={10} /> Estimated
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
      <CheckCircle2 size={10} /> Computed
    </span>
  );
}

function HistorySelector({
  history, selectedIdx, open, onToggle, onSelect,
}: {
  history: AttributionData[];
  selectedIdx: number;
  open: boolean;
  onToggle: () => void;
  onSelect: (idx: number) => void;
}) {
  const current = history[selectedIdx];
  return (
    <div className="relative">
      <button onClick={onToggle}
        className="flex items-center gap-2 px-4 py-2 glass-card rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-300 hover:shadow-md transition">
        <Clock size={14} className="text-brand" />
        <span>{current ? fmtDateTime(current.computed_at) : 'Latest'}</span>
        <span className="text-slate-500 dark:text-slate-300">({history.length} runs)</span>
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={onToggle} />
          <div className="absolute top-full left-0 mt-2 w-72 glass-card rounded-2xl z-50 overflow-hidden shadow-xl">
            <div className="max-h-60 overflow-y-auto p-1.5">
              {history.map((h, idx) => (
                <button key={h.attribution_id} onClick={() => onSelect(idx)}
                  className={`w-full text-left px-3 py-2.5 rounded-xl text-xs transition ${
                    idx === selectedIdx ? 'bg-brand/10 ring-1 ring-brand/20' : 'hover:bg-slate-50 dark:hover:bg-slate-800/30'
                  }`}>
                  <p className="font-semibold text-slate-700 dark:text-slate-200">{fmtDateTime(h.computed_at)}</p>
                  <p className="text-[11px] text-slate-500 dark:text-slate-300 mt-0.5">
                    Total ECL: {fmtCurrency(h.closing_ecl?.total)} &middot;
                    {h.reconciliation?.within_materiality ? ' Reconciled' : ' Unreconciled'}
                  </p>
                </button>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-slate-200 dark:bg-slate-700" />
          <div>
            <div className="h-5 w-48 bg-slate-200 dark:bg-slate-700 rounded" />
            <div className="h-3 w-64 bg-slate-100 dark:bg-slate-800 rounded mt-1" />
          </div>
        </div>
        <div className="h-9 w-28 bg-slate-200 dark:bg-slate-700 rounded-xl" />
      </div>
      <div className="glass-card rounded-2xl p-5 h-24" />
      <div className="glass-card rounded-2xl p-5 h-96" />
      <div className="glass-card rounded-2xl p-5 h-64" />
    </div>
  );
}

function EmptyState({ onCompute, computing }: { onCompute: () => void; computing: boolean }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-12 text-center">
      <div className="w-16 h-16 rounded-3xl gradient-brand flex items-center justify-center mx-auto mb-4 shadow-lg">
        <BarChart3 size={28} className="text-white" />
      </div>
      <h3 className="text-base font-bold text-slate-700 dark:text-slate-200 mb-2">No Attribution Data</h3>
      <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-6">
        Compute an ECL attribution analysis to decompose the loss allowance movement
        into IFRS 7.35I waterfall components.
      </p>
      <button onClick={onCompute} disabled={computing}
        className="px-6 py-2.5 text-sm font-bold text-white gradient-brand rounded-xl shadow-lg hover:opacity-90 transition disabled:opacity-50">
        {computing ? 'Computing...' : 'Compute Attribution'}
      </button>
    </motion.div>
  );
}

function ErrorCard({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      className="glass-card rounded-2xl p-8 text-center">
      <AlertTriangle size={32} className="text-red-400 mx-auto mb-3" />
      <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-1">Failed to Load Attribution</h3>
      <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 max-w-md mx-auto">{message}</p>
      <button onClick={onRetry}
        className="px-5 py-2 text-xs font-bold text-white gradient-brand rounded-xl shadow-lg hover:opacity-90 transition">
        Retry
      </button>
    </motion.div>
  );
}
