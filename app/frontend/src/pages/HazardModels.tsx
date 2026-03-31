import { useEffect, useState, useMemo } from 'react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
  BarChart, Bar, Cell,
} from 'recharts';
import { useChartTheme } from '../lib/chartTheme';
import { Activity, Play, Loader2, TrendingDown, Shield, BarChart3, Layers, Clock, Target } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../components/Card';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import PageLoader from '../components/PageLoader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import { api } from '../lib/api';
import { fmtNumber, fmtPct, fmtDateTime, formatProductName } from '../lib/format';

const MODEL_TYPE_LABELS: Record<string, string> = {
  cox_ph: 'Cox PH',
  discrete_time: 'Discrete-Time',
  kaplan_meier: 'Kaplan-Meier',
};

const MODEL_TYPE_COLORS: Record<string, string> = {
  cox_ph: '#3B82F6',
  discrete_time: '#10B981',
  kaplan_meier: '#F59E0B',
};

const SEGMENT_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#EC4899', '#F97316'];

type TabKey = 'overview' | 'survival' | 'hazard' | 'pd_term' | 'coefficients' | 'compare';

export default function HazardModels() {
  const [models, setModels] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [termStructure, setTermStructure] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [estimating, setEstimating] = useState(false);
  const [estimateType, setEstimateType] = useState<string>('cox_ph');
  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [compareData, setCompareData] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  useEffect(() => {
    if (selectedModel?.model_id) {
      api.hazardTermStructure(selectedModel.model_id).then(setTermStructure).catch(() => {});
    }
  }, [selectedModel?.model_id]);

  const loadModels = async () => {
    setLoading(true);
    try {
      const list = await api.hazardListModels();
      setModels(list);
      if (list.length > 0 && !selectedModel) {
        const detail = await api.hazardGetModel(list[0].model_id);
        setSelectedModel(detail);
      }
    } catch {
      setModels([]);
    } finally {
      setLoading(false);
    }
  };

  const handleEstimate = async () => {
    setEstimating(true);
    setError(null);
    try {
      const result = await api.hazardEstimate(estimateType);
      setSelectedModel(result);
      await loadModels();
      setActiveTab('survival');
    } catch (e: any) {
      setError(e.message || 'Estimation failed');
    } finally {
      setEstimating(false);
    }
  };

  const handleSelectModel = async (row: any) => {
    try {
      const detail = await api.hazardGetModel(row.model_id);
      setSelectedModel(detail);
    } catch { /* */ }
  };

  const handleCompare = async () => {
    if (compareIds.length < 2) return;
    try {
      const result = await api.hazardCompare(compareIds);
      setCompareData(result);
      setActiveTab('compare');
    } catch { /* */ }
  };

  const toggleCompare = (modelId: string) => {
    setCompareIds(prev =>
      prev.includes(modelId) ? prev.filter(id => id !== modelId) : [...prev, modelId].slice(-4)
    );
  };

  const bestConcordance = useMemo(() => {
    if (!models.length) return null;
    return models.reduce((best, m) => (m.concordance_index || 0) > (best.concordance_index || 0) ? m : best, models[0]);
  }, [models]);

  const latestDate = useMemo(() => {
    if (!models.length) return null;
    return models.reduce((latest, m) => {
      const d = m.created_at || m.estimation_date;
      return d > (latest || '') ? d : latest;
    }, '');
  }, [models]);

  const curves = selectedModel?.curves || [];
  const coefficients = selectedModel?.coefficients?.covariates || [];

  const tabs: { key: TabKey; label: string; icon: typeof Activity }[] = [
    { key: 'overview', label: 'Overview', icon: BarChart3 },
    { key: 'survival', label: 'Survival Curves', icon: TrendingDown },
    { key: 'hazard', label: 'Hazard Rates', icon: Activity },
    { key: 'pd_term', label: 'PD Term Structure', icon: Target },
    { key: 'coefficients', label: 'Coefficients', icon: Layers },
    { key: 'compare', label: 'Compare', icon: Shield },
  ];

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">Hazard Models</h2>
          <p className="text-sm text-slate-500 mt-1">Survival analysis for PD term structure — 12-month and lifetime PD estimation per IFRS 9.5.5.9</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={estimateType}
            onChange={e => setEstimateType(e.target.value)}
            aria-label="Hazard model type"
            className="form-input text-xs py-2 px-3 rounded-xl"
          >
            <option value="cox_ph">Cox Proportional Hazards</option>
            <option value="discrete_time">Discrete-Time Logistic</option>
            <option value="kaplan_meier">Kaplan-Meier</option>
          </select>
          <button
            onClick={handleEstimate}
            disabled={estimating}
            className="btn-primary text-xs flex items-center gap-2"
          >
            {estimating ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {estimating ? 'Estimating...' : 'Estimate Model'}
          </button>
        </div>
      </div>

      {error && (
        <ErrorDisplay title="Estimation failed" message={error} technicalDetails={error}
          onRetry={handleEstimate} onDismiss={() => setError(null)} />
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <KpiCard
          title="Total Models"
          value={fmtNumber(models.length)}
          subtitle={`${new Set(models.map(m => m.model_type)).size} model types`}
          icon={<Layers size={20} />}
          color="blue"
        />
        <KpiCard
          title="Best Concordance"
          value={bestConcordance ? fmtPct((bestConcordance.concordance_index || 0) * 100, 1) : '—'}
          subtitle={bestConcordance ? MODEL_TYPE_LABELS[bestConcordance.model_type] || bestConcordance.model_type : ''}
          icon={<Target size={20} />}
          color="green"
        />
        <KpiCard
          title="Latest Estimation"
          value={latestDate ? fmtDateTime(latestDate).split(',')[0] : '—'}
          icon={<Clock size={20} />}
          color="amber"
        />
        <KpiCard
          title="Active Model"
          value={selectedModel ? (MODEL_TYPE_LABELS[selectedModel.model_type] || selectedModel.model_type) : '—'}
          subtitle={selectedModel ? `C-index: ${fmtPct((selectedModel.concordance_index || 0) * 100, 1)}` : ''}
          icon={<Activity size={20} />}
          color="purple"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-xl p-1">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
          {activeTab === 'overview' && <OverviewTab models={models} selectedModel={selectedModel} onSelect={handleSelectModel} compareIds={compareIds} onToggleCompare={toggleCompare} onCompare={handleCompare} />}
          {activeTab === 'survival' && <SurvivalTab curves={curves} modelType={selectedModel?.model_type} />}
          {activeTab === 'hazard' && <HazardRateTab curves={curves} modelType={selectedModel?.model_type} />}
          {activeTab === 'pd_term' && <PDTermTab termStructure={termStructure} modelType={selectedModel?.model_type} />}
          {activeTab === 'coefficients' && <CoefficientTab coefficients={coefficients} modelType={selectedModel?.model_type} />}
          {activeTab === 'compare' && <CompareTab compareData={compareData} models={models} compareIds={compareIds} onToggleCompare={toggleCompare} onCompare={handleCompare} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}


function OverviewTab({ models, selectedModel, onSelect, compareIds, onToggleCompare, onCompare }: {
  models: any[]; selectedModel: any; onSelect: (row: any) => void;
  compareIds: string[]; onToggleCompare: (id: string) => void; onCompare: () => void;
}) {
  const ct = useChartTheme();
  const columns = [
    { key: 'model_type', label: 'Type', format: (v: string) => (
      <span className="inline-flex items-center gap-1.5">
        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: MODEL_TYPE_COLORS[v] || '#94a3b8' }} />
        {MODEL_TYPE_LABELS[v] || v}
      </span>
    )},
    { key: 'concordance_index', label: 'C-Index', align: 'right' as const, format: (v: number) => fmtPct((v || 0) * 100, 2) },
    { key: 'log_likelihood', label: 'Log-Lik', align: 'right' as const, format: (v: number) => v != null ? fmtNumber(v, 1) : '—' },
    { key: 'aic', label: 'AIC', align: 'right' as const, format: (v: number) => v ? fmtNumber(v, 1) : '—' },
    { key: 'bic', label: 'BIC', align: 'right' as const, format: (v: number) => v ? fmtNumber(v, 1) : '—' },
    { key: 'product_type', label: 'Product', format: (v: string) => v ? formatProductName(v) : 'All' },
    { key: 'n_observations', label: 'N Obs', align: 'right' as const, format: (v: number) => fmtNumber(v) },
    { key: 'n_events', label: 'Events', align: 'right' as const, format: (v: number) => fmtNumber(v) },
    { key: 'created_at', label: 'Estimated', format: (v: string) => fmtDateTime(v) },
    { key: 'model_id', label: 'Compare', align: 'center' as const, format: (v: string) => (
      <input
        type="checkbox"
        checked={compareIds.includes(v)}
        onChange={() => onToggleCompare(v)}
        onClick={e => e.stopPropagation()}
        className="w-4 h-4 rounded border-slate-300 text-brand focus:ring-brand/30"
      />
    )},
  ];

  return (
    <div className="space-y-6">
      {compareIds.length >= 2 && (
        <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3">
          <span className="text-sm text-blue-700 font-medium">{compareIds.length} models selected</span>
          <button onClick={onCompare} className="btn-primary text-xs">Compare Models</button>
        </motion.div>
      )}

      <Card title="Estimated Models" subtitle="All hazard models with fit statistics" icon={<Layers size={16} />}>
        {models.length > 0 ? (
          <DataTable columns={columns} data={models} onRowClick={onSelect} selectedRow={selectedModel} compact exportName="hazard_models" />
        ) : (
          <EmptyState
            icon={<Activity size={48} />}
            title="No hazard models estimated"
            description="Estimate a Cox PH or Kaplan-Meier model."
          />
        )}
      </Card>

      {selectedModel && (
        <div className="grid grid-cols-2 gap-6">
          <Card title="Model Summary" icon={<BarChart3 size={16} />}>
            <div className="space-y-3 text-sm">
              <Row label="Model ID" value={selectedModel.model_id} />
              <Row label="Type" value={MODEL_TYPE_LABELS[selectedModel.model_type] || selectedModel.model_type} />
              <Row label="Concordance Index" value={fmtPct((selectedModel.concordance_index || 0) * 100, 2)} />
              <Row label="Log-Likelihood" value={fmtNumber(selectedModel.log_likelihood, 2)} />
              <Row label="AIC" value={selectedModel.aic ? fmtNumber(selectedModel.aic, 2) : 'N/A'} />
              <Row label="BIC" value={selectedModel.bic ? fmtNumber(selectedModel.bic, 2) : 'N/A'} />
              <Row label="Observations" value={fmtNumber(selectedModel.n_observations)} />
              <Row label="Default Events" value={fmtNumber(selectedModel.n_events)} />
            </div>
          </Card>

          {selectedModel.curves?.length > 0 && (
            <Card title="Survival Preview" subtitle="S(t) — all segments" icon={<TrendingDown size={16} />}>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="t" type="number" domain={[0, 60]} label={{ value: 'Month', position: 'bottom', offset: -5 }} tick={{ fontSize: 10, fill: ct.axisLight }} />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: any) => fmtPct(v * 100, 0)} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} labelFormatter={l => `Month ${l}`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    {selectedModel.curves.slice(0, 5).map((curve: any, idx: number) => {
                      const data = curve.time_points.map((t: number, i: number) => ({ t, s: curve.survival_probs[i] }));
                      return (
                        <Line key={curve.segment || idx} data={data} dataKey="s" name={curve.segment === 'all' ? 'Overall' : formatProductName(curve.segment)}
                          stroke={SEGMENT_COLORS[idx % SEGMENT_COLORS.length]} strokeWidth={curve.segment === 'all' ? 2.5 : 1.5} dot={false} />
                      );
                    })}
                    <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}


function SurvivalTab({ curves, modelType }: { curves: any[]; modelType?: string }) {
  const ct = useChartTheme();
  if (!curves.length) return <HazardEmptyState message="Estimate a model to view survival curves" />;

  const chartData = curves[0]?.time_points?.map((t: number, i: number) => {
    const point: any = { month: t };
    curves.forEach((c: any) => {
      point[c.segment || 'all'] = c.survival_probs[i];
    });
    return point;
  }) || [];

  return (
    <Card title="Survival Curves S(t)" subtitle={`${MODEL_TYPE_LABELS[modelType || ''] || modelType} — Probability of surviving beyond time t`} icon={<TrendingDown size={16} />} accent="blue">
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
            <XAxis dataKey="month" tick={{ fontSize: 10, fill: ct.axisLight }} label={{ value: 'Month', position: 'bottom', offset: -5 }} />
            <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: any) => fmtPct(v * 100, 0)} label={{ value: 'S(t)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 3)} labelFormatter={l => `Month ${l}`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
            {curves.map((c: any, idx: number) => (
              <Line key={c.segment} dataKey={c.segment || 'all'} name={c.segment === 'all' ? 'Overall' : formatProductName(c.segment)}
                stroke={SEGMENT_COLORS[idx % SEGMENT_COLORS.length]} strokeWidth={c.segment === 'all' ? 3 : 1.5} dot={false}
                strokeDasharray={c.segment === 'all' ? undefined : '4 2'} />
            ))}
            <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-4 text-xs">
        {curves.filter(c => c.segment === 'all').map((c: any) => {
          const s12 = c.survival_probs[11] || 0;
          const s24 = c.survival_probs[23] || 0;
          const s60 = c.survival_probs[c.survival_probs.length - 1] || 0;
          return (
            <div key="stats" className="col-span-3 grid grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-xl p-3 text-center">
                <p className="text-slate-400 font-semibold">12-Month PD</p>
                <p className="text-lg font-bold text-blue-700">{fmtPct((1 - s12) * 100, 2)}</p>
              </div>
              <div className="bg-amber-50 rounded-xl p-3 text-center">
                <p className="text-slate-400 font-semibold">24-Month PD</p>
                <p className="text-lg font-bold text-amber-700">{fmtPct((1 - s24) * 100, 2)}</p>
              </div>
              <div className="bg-red-50 rounded-xl p-3 text-center">
                <p className="text-slate-400 font-semibold">Lifetime PD (60m)</p>
                <p className="text-lg font-bold text-red-700">{fmtPct((1 - s60) * 100, 2)}</p>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}


function HazardRateTab({ curves, modelType }: { curves: any[]; modelType?: string }) {
  const ct = useChartTheme();
  if (!curves.length) return <HazardEmptyState message="Estimate a model to view hazard rates" />;

  const allCurve = curves.find((c: any) => c.segment === 'all') || curves[0];
  const barData = allCurve.time_points.map((t: number, i: number) => ({
    month: t,
    hazard: allCurve.hazard_rates[i],
  }));

  const lineData = curves[0]?.time_points?.map((t: number, i: number) => {
    const point: any = { month: t };
    curves.forEach((c: any) => {
      point[c.segment || 'all'] = c.hazard_rates[i];
    });
    return point;
  }) || [];

  return (
    <div className="space-y-6">
      <Card title="Hazard Rate h(t)" subtitle={`${MODEL_TYPE_LABELS[modelType || ''] || modelType} — Instantaneous default probability at time t`} icon={<Activity size={16} />} accent="purple">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: ct.axisLight }} label={{ value: 'Month', position: 'bottom', offset: -5 }} />
              <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: any) => fmtPct(v * 100, 2)} label={{ value: 'h(t)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 4)} labelFormatter={l => `Month ${l}`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
              <Bar dataKey="hazard" name="Hazard Rate" radius={[2, 2, 0, 0]}>
                {barData.map((_: any, i: number) => (
                  <Cell key={i} fill={`rgba(139, 92, 246, ${0.3 + 0.7 * ((Number(barData[i].hazard) || 0) / Math.max(...barData.map((d: any) => d.hazard), 0.001))})`} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {curves.length > 1 && (
        <Card title="Hazard Rates by Segment" icon={<Layers size={16} />}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={lineData}>
                <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: ct.axisLight }} />
                <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: any) => fmtPct(v * 100, 2)} />
                <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 4)} labelFormatter={l => `Month ${l}`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                {curves.map((c: any, idx: number) => (
                  <Line key={c.segment} dataKey={c.segment || 'all'} name={c.segment === 'all' ? 'Overall' : formatProductName(c.segment)}
                    stroke={SEGMENT_COLORS[idx % SEGMENT_COLORS.length]} strokeWidth={c.segment === 'all' ? 2.5 : 1.5} dot={false} />
                ))}
                <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}


function PDTermTab({ termStructure, modelType }: { termStructure: any; modelType?: string }) {
  const ct = useChartTheme();
  if (!termStructure) return <HazardEmptyState message="Select a model to view PD term structure" />;

  const chartData = termStructure.time_points.map((t: number, i: number) => ({
    month: t,
    marginal: termStructure.marginal_pd[i],
    cumulative: termStructure.cumulative_pd[i],
    forward: termStructure.forward_pd[i],
  }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <KpiCard title="12-Month PD (Stage 1)" value={fmtPct(termStructure.pd_12_month * 100, 3)} subtitle="1 - S(12)" icon={<Shield size={20} />} color="blue" />
        <KpiCard title="Lifetime PD (Stage 2)" value={fmtPct(termStructure.pd_lifetime * 100, 3)} subtitle={`1 - S(${termStructure.time_points.length})`} icon={<TrendingDown size={20} />} color="red" />
      </div>

      <Card title="PD Term Structure" subtitle={`${MODEL_TYPE_LABELS[modelType || ''] || modelType} — Marginal, cumulative, and forward PD`} icon={<Target size={16} />} accent="brand">
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
              <XAxis dataKey="month" tick={{ fontSize: 10, fill: ct.axisLight }} label={{ value: 'Month', position: 'bottom', offset: -5 }} />
              <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: any) => fmtPct(v * 100, 1)} />
              <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 4)} labelFormatter={l => `Month ${l}`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
              <Line dataKey="cumulative" name="Cumulative PD" stroke="#EF4444" strokeWidth={2.5} dot={false} />
              <Line dataKey="marginal" name="Marginal PD" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
              <Line dataKey="forward" name="12m Forward PD" stroke="#10B981" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
              <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card title="PD by Time Bucket" icon={<BarChart3 size={16} />}>
        <div className="grid grid-cols-5 gap-3">
          {[
            { label: '0-12m', idx: 11 },
            { label: '12-24m', idx: 23 },
            { label: '24-36m', idx: 35 },
            { label: '36-48m', idx: 47 },
            { label: '48-60m', idx: 59 },
          ].map(bucket => {
            const cpd = termStructure.cumulative_pd[Math.min(bucket.idx, termStructure.cumulative_pd.length - 1)] || 0;
            const prevCpd = bucket.idx > 11 ? (termStructure.cumulative_pd[bucket.idx - 12] || 0) : 0;
            const periodPd = cpd - prevCpd;
            return (
              <div key={bucket.label} className="bg-slate-50 dark:bg-slate-800/60 rounded-xl p-3 text-center">
                <p className="text-[10px] text-slate-400 font-semibold uppercase">{bucket.label}</p>
                <p className="text-sm font-bold text-slate-700 dark:text-slate-200 mt-1">{fmtPct(periodPd * 100, 2)}</p>
                <p className="text-[10px] text-slate-400">Cum: {fmtPct(cpd * 100, 2)}</p>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}


function CoefficientTab({ coefficients, modelType }: { coefficients: any[]; modelType?: string }) {
  const ct = useChartTheme();
  if (!coefficients.length) {
    return (
      <Card title="Model Coefficients" icon={<Layers size={16} />}>
        <div className="text-center py-12 text-slate-400">
          <Layers size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-semibold">
            {modelType === 'kaplan_meier'
              ? 'Kaplan-Meier is non-parametric — no coefficients to display'
              : 'No coefficients available'}
          </p>
        </div>
      </Card>
    );
  }

  const columns = [
    { key: 'name', label: 'Covariate', format: (v: string) => formatProductName(v.replace(/_/g, ' ')) },
    { key: 'coefficient', label: 'Coefficient (β)', align: 'right' as const, format: (v: number) => v?.toFixed(5) || '—' },
    { key: 'hazard_ratio', label: 'Hazard Ratio', align: 'right' as const, format: (v: number) => v?.toFixed(4) || '—' },
    { key: 'std_error', label: 'Std Error', align: 'right' as const, format: (v: number) => v?.toFixed(5) || '—' },
    { key: 'z_score', label: 'z-Score', align: 'right' as const, format: (v: number) => v?.toFixed(3) || '—' },
    { key: 'p_value', label: 'p-Value', align: 'right' as const, format: (v: number) => {
      if (v == null) return '—';
      const sig = v < 0.001 ? '***' : v < 0.01 ? '**' : v < 0.05 ? '*' : '';
      return <span className={v < 0.05 ? 'text-emerald-600 font-semibold' : 'text-slate-500'}>{v.toFixed(4)}{sig}</span>;
    }},
    { key: 'ci_lower', label: '95% CI Lower', align: 'right' as const, format: (v: number) => v?.toFixed(5) || '—' },
    { key: 'ci_upper', label: '95% CI Upper', align: 'right' as const, format: (v: number) => v?.toFixed(5) || '—' },
  ];

  const hrData = coefficients.filter(c => c.hazard_ratio != null).map(c => ({
    name: formatProductName(c.name.replace(/_/g, ' ')),
    hr: c.hazard_ratio,
    ci_low: Math.exp(c.ci_lower || 0),
    ci_high: Math.exp(c.ci_upper || 0),
  }));

  return (
    <div className="space-y-6">
      <Card title="Cox PH Coefficients" subtitle="Covariate effects on hazard rate — exp(β) = hazard ratio" icon={<Layers size={16} />} accent="purple">
        <DataTable columns={columns} data={coefficients} compact exportName="hazard_coefficients" />
      </Card>

      {hrData.length > 0 && (
        <Card title="Hazard Ratios" subtitle="exp(β) — values > 1 increase default risk" icon={<BarChart3 size={16} />}>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hrData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                <XAxis type="number" tick={{ fontSize: 10, fill: ct.axisLight }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fill: ct.axisLight }} width={140} />
                <Tooltip contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                <Bar dataKey="hr" name="Hazard Ratio" radius={[0, 4, 4, 0]}>
                  {hrData.map((d, i) => (
                    <Cell key={i} fill={d.hr > 1 ? '#EF4444' : '#10B981'} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-[10px] text-slate-400 mt-2 text-center">
            *** p &lt; 0.001 &nbsp; ** p &lt; 0.01 &nbsp; * p &lt; 0.05
          </p>
        </Card>
      )}
    </div>
  );
}


function CompareTab({ compareData, compareIds, onCompare }: {
  compareData: any; models?: any[]; compareIds: string[]; onToggleCompare?: (id: string) => void; onCompare: () => void;
}) {
  const ct = useChartTheme();
  if (!compareData || !compareData.models?.length) {
    return (
      <Card title="Model Comparison" icon={<Shield size={16} />}>
        <div className="text-center py-12 text-slate-400">
          <Shield size={40} className="mx-auto mb-3 opacity-30" />
          <p className="font-semibold">Select 2-4 models from the Overview tab to compare</p>
          <p className="text-xs mt-1">{compareIds.length} model(s) selected</p>
          {compareIds.length >= 2 && (
            <button onClick={onCompare} className="btn-primary text-xs mt-4">Compare Now</button>
          )}
        </div>
      </Card>
    );
  }

  const metricColumns = [
    { key: 'model_type', label: 'Type', format: (v: string) => MODEL_TYPE_LABELS[v] || v },
    { key: 'concordance_index', label: 'C-Index', align: 'right' as const, format: (v: number) => fmtPct((v || 0) * 100, 2) },
    { key: 'log_likelihood', label: 'Log-Lik', align: 'right' as const, format: (v: number) => fmtNumber(v, 1) },
    { key: 'aic', label: 'AIC', align: 'right' as const, format: (v: number) => v ? fmtNumber(v, 1) : 'N/A' },
    { key: 'bic', label: 'BIC', align: 'right' as const, format: (v: number) => v ? fmtNumber(v, 1) : 'N/A' },
    { key: 'n_observations', label: 'N', align: 'right' as const, format: (v: number) => fmtNumber(v) },
    { key: 'n_events', label: 'Events', align: 'right' as const, format: (v: number) => fmtNumber(v) },
  ];

  const curveChartData = compareData.curves?.[0]?.time_points?.map((t: number, i: number) => {
    const point: any = { month: t };
    compareData.curves.forEach((c: any) => {
      const label = `${MODEL_TYPE_LABELS[c.model_type] || c.model_type}`;
      point[label] = c.survival_probs[i];
    });
    return point;
  }) || [];

  const curveKeys = compareData.curves?.map((c: any) => MODEL_TYPE_LABELS[c.model_type] || c.model_type) || [];

  return (
    <div className="space-y-6">
      <Card title="Model Comparison" subtitle="Side-by-side fit statistics" icon={<Shield size={16} />} accent="brand">
        <DataTable columns={metricColumns} data={compareData.models} compact />
      </Card>

      {curveChartData.length > 0 && (
        <Card title="Survival Curve Overlay" subtitle="Comparing S(t) across models" icon={<TrendingDown size={16} />}>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={curveChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                <XAxis dataKey="month" tick={{ fontSize: 10, fill: ct.axisLight }} label={{ value: 'Month', position: 'bottom', offset: -5 }} />
                <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: any) => fmtPct(v * 100, 0)} />
                <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 3)} labelFormatter={l => `Month ${l}`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                {curveKeys.map((key: string, idx: number) => (
                  <Line key={key} dataKey={key} name={key} stroke={SEGMENT_COLORS[idx % SEGMENT_COLORS.length]} strokeWidth={2.5} dot={false} />
                ))}
                <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      )}
    </div>
  );
}


function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between items-center py-1.5 border-b border-slate-100 dark:border-slate-700 last:border-0">
      <span className="text-slate-400 text-xs font-medium">{label}</span>
      <span className="text-slate-700 dark:text-slate-200 text-xs font-semibold font-mono">{value}</span>
    </div>
  );
}

function HazardEmptyState({ message }: { message: string }) {
  return (
    <Card>
      <div className="text-center py-16 text-slate-400">
        <Activity size={48} className="mx-auto mb-4 opacity-20" />
        <p className="font-semibold">{message}</p>
      </div>
    </Card>
  );
}
