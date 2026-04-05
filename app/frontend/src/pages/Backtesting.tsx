import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FlaskConical, Play, CheckCircle2, AlertTriangle, XCircle,
  TrendingUp, Eye, X, BarChart3, Target, Activity, Users,
  RefreshCw, ChevronRight,
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ScatterChart, Scatter, BarChart, Bar,
  ReferenceLine,
} from 'recharts';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import KpiCard from '../components/KpiCard';
import PageHeader from '../components/PageHeader';
import PageLoader from '../components/PageLoader';
import { useChartTheme } from '../lib/chartTheme';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import { api, type BacktestResult, type BacktestMetric, type BacktestTrendPoint } from '../lib/api';
import { fmtNumber, fmtPct, fmtDateTime } from '../lib/format';

const MODEL_TYPES = ['PD', 'LGD'] as const;

const LIGHT_COLORS: Record<string, { bg: string; text: string; dot: string; border: string }> = {
  Green: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500', border: 'border-emerald-200' },
  Amber: { bg: 'bg-amber-50', text: 'text-amber-700', dot: 'bg-amber-500', border: 'border-amber-200' },
  Red:   { bg: 'bg-red-50', text: 'text-red-700', dot: 'bg-red-500', border: 'border-red-200' },
};

function TrafficLightBadge({ light }: { light: string }) {
  const cfg = LIGHT_COLORS[light] || LIGHT_COLORS.Green;
  const Icon = light === 'Green' ? CheckCircle2 : light === 'Amber' ? AlertTriangle : XCircle;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${cfg.bg} ${cfg.text} ${cfg.border}`}>
      <Icon size={12} /> {light}
    </span>
  );
}

function TrafficLightDot({ light }: { light: string }) {
  const cfg = LIGHT_COLORS[light] || LIGHT_COLORS.Green;
  return <div className={`w-3 h-3 rounded-full ${cfg.dot}`} />;
}

function MetricCard({ metric }: { metric: BacktestMetric }) {
  const cfg = LIGHT_COLORS[metric.pass_fail] || LIGHT_COLORS.Green;
  const isLowerBetter = metric.metric_name === 'PSI' || metric.metric_name === 'Brier';
  return (
    <div className={`p-4 rounded-xl border ${cfg.border} ${cfg.bg} transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-300">{metric.metric_name}</span>
        <TrafficLightDot light={metric.pass_fail} />
      </div>
      <p className={`text-2xl font-extrabold ${cfg.text}`}>{fmtNumber(metric.metric_value, 4)}</p>
      <p className="text-[11px] text-slate-500 dark:text-slate-300 mt-1">
        {isLowerBetter ? '≤' : '≥'} {fmtNumber(metric.threshold_green, 2)} Green
        {' · '}
        {isLowerBetter ? '≤' : '≥'} {fmtNumber(metric.threshold_amber, 2)} Amber
      </p>
    </div>
  );
}

interface DetailPanelProps {
  backtest: BacktestResult;
  onClose: () => void;
}

function DetailPanel({ backtest, onClose }: DetailPanelProps) {
  const ct = useChartTheme();
  const metrics = backtest.metrics || [];
  const cohorts = backtest.cohort_results || [];

  const scatterData = cohorts.map(c => ({
    name: c.cohort_name,
    predicted: c.predicted_rate * 100,
    actual: c.actual_rate * 100,
    count: c.count,
  }));

  const cohortBarData = cohorts.map(c => ({
    name: c.cohort_name.length > 20 ? c.cohort_name.slice(0, 18) + '…' : c.cohort_name,
    predicted: +(c.predicted_rate * 100).toFixed(2),
    actual: +(c.actual_rate * 100).toFixed(2),
    count: c.count,
  }));

  return (
    <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 40 }}
      className="fixed inset-y-0 right-0 w-full max-w-2xl bg-white dark:bg-slate-800 shadow-2xl z-50 overflow-y-auto border-l border-slate-200 dark:border-slate-700">
      <div className="sticky top-0 bg-white dark:bg-slate-800 z-10 px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center">
            <FlaskConical size={18} className="text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">Backtest Detail</h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-300">{backtest.backtest_id} · {backtest.model_type}</p>
          </div>
        </div>
        <button onClick={onClose} className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition"><X size={18} className="text-slate-400" /></button>
      </div>

      <div className="p-6 space-y-6">
        <div className="flex items-center gap-3">
          <TrafficLightBadge light={backtest.overall_traffic_light} />
          <span className="text-xs text-slate-500 dark:text-slate-300">{fmtDateTime(backtest.backtest_date)}</span>
          <span className="text-xs text-slate-500 dark:text-slate-300">· {fmtNumber(backtest.total_loans)} loans</span>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase">Observation Window</p>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{backtest.observation_window}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase">Outcome Window</p>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{backtest.outcome_window}</p>
          </div>
        </div>

        {metrics.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-3">Metrics — Traffic Light Assessment</p>
            <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
              {metrics.map(m => <MetricCard key={m.metric_id} metric={m} />)}
            </div>
          </div>
        )}

        {cohortBarData.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-3">Predicted vs Actual by Cohort</p>
            <div className="h-64 bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3 border border-slate-100 dark:border-slate-700">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={cohortBarData} barGap={2}>
                  <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: ct.axisLight }} angle={-30} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={v => `${v}%`} />
                  <Tooltip
                    contentStyle={{ fontSize: 11, borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }}
                    formatter={(v: any) => `${Number(v).toFixed(2)}%`}
                  />
                  <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
                  <Bar dataKey="predicted" name="Predicted" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="actual" name="Actual" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {scatterData.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-3">Calibration Plot</p>
            <div className="h-64 bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3 border border-slate-100 dark:border-slate-700">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart>
                  <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                  <XAxis dataKey="predicted" name="Predicted %" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={v => `${v}%`} />
                  <YAxis dataKey="actual" name="Actual %" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={v => `${v}%`} />
                  <Tooltip
                    contentStyle={{ fontSize: 11, borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }}
                    formatter={(v: any) => `${Number(v).toFixed(2)}%`}
                  />
                  <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 100, y: 100 }]} stroke="#94a3b8" strokeDasharray="5 5" />
                  <Scatter data={scatterData} fill="#6366f1" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {cohorts.length > 0 && (
          <div>
            <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider mb-3">Cohort Analysis</p>
            <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-700">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-gradient-to-r from-slate-100 to-slate-50 text-slate-700 dark:from-slate-800 dark:to-slate-700 dark:bg-slate-700/50 dark:text-slate-200">
                    <th className="py-2 px-3 text-left text-[11px] font-bold uppercase">Cohort</th>
                    <th className="py-2 px-3 text-right text-[11px] font-bold uppercase">Predicted</th>
                    <th className="py-2 px-3 text-right text-[11px] font-bold uppercase">Actual</th>
                    <th className="py-2 px-3 text-right text-[11px] font-bold uppercase">Diff</th>
                    <th className="py-2 px-3 text-right text-[11px] font-bold uppercase">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {cohorts.map((c, i) => (
                    <tr key={c.cohort_id} className={`border-b border-slate-50 dark:border-slate-700 ${i % 2 === 1 ? 'bg-slate-50/40 dark:bg-white/[0.02]' : ''}`}>
                      <td className="py-2 px-3 font-semibold text-slate-700 dark:text-slate-200">{c.cohort_name}</td>
                      <td className="py-2 px-3 text-right font-mono">{fmtPct(c.predicted_rate * 100, 2)}</td>
                      <td className="py-2 px-3 text-right font-mono">{fmtPct(c.actual_rate * 100, 2)}</td>
                      <td className="py-2 px-3 text-right font-mono">
                        <span className={c.abs_diff > 0.05 ? 'text-red-600 font-bold' : c.abs_diff > 0.02 ? 'text-amber-600' : 'text-emerald-600'}>
                          {fmtPct(c.abs_diff * 100, 2)}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right">{fmtNumber(c.count)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}

const METRIC_COLORS: Record<string, string> = {
  AUC: '#6366f1',
  Gini: '#10b981',
  KS: '#f59e0b',
  PSI: '#ef4444',
  Brier: '#8b5cf6',
};

export default function Backtesting() {
  const ct = useChartTheme();
  const [backtests, setBacktests] = useState<BacktestResult[]>([]);
  const [trend, setTrend] = useState<BacktestTrendPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelType, setModelType] = useState<string>('PD');
  const [selectedBacktest, setSelectedBacktest] = useState<BacktestResult | null>(null);

  const loadData = async () => {
    setError(null);
    try {
      const [results, trendData] = await Promise.all([
        api.listBacktests(modelType),
        api.backtestTrend(modelType),
      ]);
      setBacktests(results);
      setTrend(trendData);
    } catch (e: any) {
      setError(e.message || 'Failed to load backtest data');
    }
    finally { setLoading(false); }
  };

  useEffect(() => { setLoading(true); loadData(); }, [modelType]);

  const handleRun = async () => {
    setRunning(true);
    try {
      const result = await api.runBacktest(modelType);
      await loadData();
      setSelectedBacktest(result);
    } catch (e: any) {
      setError(e?.message || 'Failed to run backtest');
    } finally { setRunning(false); }
  };

  const openDetail = async (row: BacktestResult) => {
    try {
      const detail = await api.getBacktest(row.backtest_id);
      setSelectedBacktest(detail);
    } catch (e: any) {
      setError(e?.message || 'Failed to load backtest details');
    }
  };

  const latest = backtests.length > 0 ? backtests[0] : null;
  const totalRuns = backtests.length;
  const greenRuns = backtests.filter(b => b.overall_traffic_light === 'Green').length;
  const amberRuns = backtests.filter(b => b.overall_traffic_light === 'Amber').length;
  const redRuns = backtests.filter(b => b.overall_traffic_light === 'Red').length;

  const trendChartData = useMemo(() => {
    return trend.map(t => ({
      ...t,
      date: t.backtest_date ? new Date(t.backtest_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '',
    }));
  }, [trend]);

  if (loading) return <PageLoader />;

  if (error && backtests.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="Model Backtesting" subtitle="IFRS 9 model validation with traffic light assessment" />
        <ErrorDisplay title="Failed to load backtests" message={error} technicalDetails={error}
          onRetry={() => { setLoading(true); loadData(); }} onDismiss={() => setError(null)} />
      </div>
    );
  }

  const columns = [
    {
      key: 'overall_traffic_light', label: 'Status',
      format: (v: string) => <TrafficLightBadge light={v} />,
    },
    { key: 'model_type', label: 'Model', format: (v: string) => (
      <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{v}</span>
    )},
    {
      key: 'backtest_date', label: 'Date',
      format: (v: string) => <span className="text-slate-500">{fmtDateTime(v)}</span>,
    },
    { key: 'total_loans', label: 'Loans', align: 'right' as const, format: (v: number) => fmtNumber(v) },
    {
      key: 'pass_count', label: 'Pass / Amber / Fail', align: 'center' as const,
      format: (_: number, row: BacktestResult) => (
        <div className="flex items-center justify-center gap-2">
          <span className="text-emerald-600 font-bold">{row.pass_count}</span>
          <span className="text-slate-300">/</span>
          <span className="text-amber-600 font-bold">{row.amber_count}</span>
          <span className="text-slate-300">/</span>
          <span className="text-red-600 font-bold">{row.fail_count}</span>
        </div>
      ),
    },
    { key: 'observation_window', label: 'Obs. Window' },
    { key: 'outcome_window', label: 'Out. Window' },
    {
      key: '_action', label: '',
      format: (_: any, row: BacktestResult) => (
        <button onClick={(e) => { e.stopPropagation(); openDetail(row); }}
          className="p-1.5 rounded-lg hover:bg-brand/10 transition">
          <Eye size={14} className="text-brand" />
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Model Backtesting" subtitle="IFRS 9 model validation with traffic light assessment">
        <div className="flex items-center gap-3">
          <select value={modelType} onChange={e => setModelType(e.target.value)}
            aria-label="Model type"
            className="text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 focus:ring-1 focus:ring-brand/20 font-semibold">
            {MODEL_TYPES.map(t => <option key={t} value={t}>{t} Model</option>)}
          </select>
          <button onClick={handleRun} disabled={running}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold btn-primary disabled:opacity-40 shadow-sm">
            {running ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
            {running ? 'Running...' : 'Run Backtest'}
          </button>
        </div>
      </PageHeader>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard
          title="Latest Result"
          value={latest?.overall_traffic_light || 'N/A'}
          subtitle={latest ? fmtDateTime(latest.backtest_date) : 'No backtests yet'}
          color={latest?.overall_traffic_light === 'Green' ? 'green' : latest?.overall_traffic_light === 'Amber' ? 'amber' : latest?.overall_traffic_light === 'Red' ? 'red' : 'navy'}
          icon={latest?.overall_traffic_light === 'Green' ? <CheckCircle2 size={20} /> : latest?.overall_traffic_light === 'Amber' ? <AlertTriangle size={20} /> : <Target size={20} />}
        />
        <KpiCard title="Total Runs" value={String(totalRuns)} subtitle={`${modelType} model backtests`} color="blue" icon={<FlaskConical size={20} />} />
        <KpiCard
          title="Pass Rate"
          value={totalRuns > 0 ? fmtPct(greenRuns / totalRuns * 100, 0) : '—'}
          subtitle={`${greenRuns} green / ${amberRuns} amber / ${redRuns} red`}
          color={greenRuns >= totalRuns * 0.7 ? 'green' : 'amber'}
          icon={<Activity size={20} />}
        />
        <KpiCard
          title="Latest Loans"
          value={latest ? fmtNumber(latest.total_loans) : '—'}
          subtitle="Portfolio coverage"
          color="purple"
          icon={<Users size={20} />}
        />
      </div>

      {/* Trend Charts */}
      {trendChartData.length > 1 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Discrimination Metrics Trend" subtitle="AUC, Gini, KS over time" accent="brand" icon={<TrendingUp size={16} />}>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: ct.axisLight }} />
                  <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} domain={[0, 1]} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
                  <ReferenceLine y={0.7} stroke="#10b981" strokeDasharray="5 5" label={{ value: 'AUC Green', fontSize: 9, fill: '#10b981' }} />
                  <ReferenceLine y={0.6} stroke="#f59e0b" strokeDasharray="5 5" label={{ value: 'AUC Amber', fontSize: 9, fill: '#f59e0b' }} />
                  <Line type="monotone" dataKey="AUC" stroke={METRIC_COLORS.AUC} strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Gini" stroke={METRIC_COLORS.Gini} strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="KS" stroke={METRIC_COLORS.KS} strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <Card title="Stability & Calibration Trend" subtitle="PSI and Brier score over time" accent="blue" icon={<BarChart3 size={16} />}>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                  <XAxis dataKey="date" tick={{ fontSize: 10, fill: ct.axisLight }} />
                  <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} domain={[0, 0.5]} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
                  <ReferenceLine y={0.1} stroke="#10b981" strokeDasharray="5 5" label={{ value: 'PSI Green', fontSize: 9, fill: '#10b981' }} />
                  <ReferenceLine y={0.25} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'PSI Red', fontSize: 9, fill: '#ef4444' }} />
                  <Line type="monotone" dataKey="PSI" stroke={METRIC_COLORS.PSI} strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Brier" stroke={METRIC_COLORS.Brier} strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      )}

      {/* Latest Backtest Metrics Quick View */}
      {latest && (
        <Card title="Latest Backtest Metrics" subtitle={`${latest.model_type} model — ${fmtDateTime(latest.backtest_date)}`}
          accent={latest.overall_traffic_light === 'Green' ? 'brand' : latest.overall_traffic_light === 'Amber' ? 'amber' : 'red'}
          icon={<Target size={16} />}
          action={
            <button onClick={() => openDetail(latest)}
              className="flex items-center gap-1 text-xs font-semibold text-brand hover:underline">
              Full Detail <ChevronRight size={14} />
            </button>
          }>
          {latest.metrics && latest.metrics.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {(latest.metrics as BacktestMetric[]).map(m => <MetricCard key={m.metric_id || m.metric_name} metric={m} />)}
            </div>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-300 italic">Click "Full Detail" to load metrics</p>
          )}
        </Card>
      )}

      {/* Results Table */}
      <Card title="Backtest History" subtitle="All backtest runs" icon={<FlaskConical size={16} />}>
        {backtests.length === 0 ? (
          <EmptyState
            icon={<FlaskConical size={48} />}
            title="No backtests run yet"
            description="Run your first backtest to validate model performance."
            action={{ label: 'Run Backtest', onClick: handleRun }}
          />
        ) : (
          <DataTable columns={columns} data={backtests} pageSize={10} onRowClick={openDetail} exportName={`backtests_${modelType}`} />
        )}
      </Card>

      {/* Detail Side Panel */}
      <AnimatePresence>
        {selectedBacktest && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/30 z-40" onClick={() => setSelectedBacktest(null)} />
            <DetailPanel backtest={selectedBacktest} onClose={() => setSelectedBacktest(null)} />
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
