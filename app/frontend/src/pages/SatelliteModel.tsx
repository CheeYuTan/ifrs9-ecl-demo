import { useEffect, useState, useMemo, useCallback, useRef } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { Cpu, Check, X, History, RotateCcw, Clock, Play, Loader2, ExternalLink, AlertTriangle } from 'lucide-react';
import { useChartTheme } from '../lib/chartTheme';
import Card from '../components/Card';
import JobRunLink from '../components/JobRunLink';
import LockedBanner from '../components/LockedBanner';
import PageLoader from '../components/PageLoader';
import { useToast } from '../components/Toast';
import { api, type Project } from '../lib/api';
import { formatProductName } from '../lib/format';
import StepDescription from '../components/StepDescription';

const DEFAULT_MODEL_COLORS: Record<string, string> = {
  linear_regression: '#3B82F6',
  logistic_regression: '#10B981',
  polynomial_deg2: '#F59E0B',
  ridge_regression: '#8B5CF6',
  random_forest: '#EF4444',
  elastic_net: '#06B6D4',
  gradient_boosting: '#EC4899',
  xgboost: '#F97316',
};

const DEFAULT_MODEL_LABELS: Record<string, string> = {
  linear_regression: 'Linear Regression',
  logistic_regression: 'Logistic Regression',
  polynomial_deg2: 'Polynomial (deg 2)',
  ridge_regression: 'Ridge Regression',
  random_forest: 'Random Forest',
  elastic_net: 'Elastic Net',
  gradient_boosting: 'Gradient Boosting',
  xgboost: 'XGBoost',
};

const PALETTE = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#EC4899', '#F97316', '#14B8A6', '#A855F7', '#F43F5E', '#84CC16'];

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}

export default function SatelliteModel({ project, onApprove, onReject }: Props) {
  const ct = useChartTheme();
  const [comparison, setComparison] = useState<any[]>([]);
  const [selected, setSelected] = useState<any[]>([]);
  const [, setCohorts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);
  const [activeProduct, setActiveProduct] = useState<string | null>(null);
  const [activeCohort, setActiveCohort] = useState<string | null>(null);

  const [runs, setRuns] = useState<any[]>([]);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [showRunHistory, setShowRunHistory] = useState(false);
  const [modelConfig, setModelConfig] = useState<Record<string, any>>({});
  const [jobError, setJobError] = useState<string | null>(null);
  const { toast } = useToast();

  const MODEL_LABELS = useMemo<Record<string, string>>(() => {
    if (Object.keys(modelConfig).length > 0) {
      return Object.fromEntries(
        Object.entries(modelConfig).map(([k, v]: [string, any]) => [k, v.label || k])
      );
    }
    return DEFAULT_MODEL_LABELS;
  }, [modelConfig]);

  const MODEL_COLORS = useMemo<Record<string, string>>(() => {
    const keys = Object.keys(MODEL_LABELS);
    if (Object.keys(modelConfig).length > 0) {
      return Object.fromEntries(keys.map((k, i) => [k, PALETTE[i % PALETTE.length]]));
    }
    return DEFAULT_MODEL_COLORS;
  }, [MODEL_LABELS, modelConfig]);

  const [enabledModels, setEnabledModels] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(Object.keys(DEFAULT_MODEL_LABELS).map(k => [k, true]))
  );
  const [jobRunning, setJobRunning] = useState(false);
  const [currentJobRun, setCurrentJobRun] = useState<any>(null);
  const [jobRuns, setJobRuns] = useState<any[]>([]);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isLocked = !project || (project.current_step ?? 0) < 3;
  const isCompleted = project?.step_status?.satellite_model === 'completed';

  const loadData = useCallback((runId?: string) => {
    setLoading(true);
    Promise.all([
      api.satelliteModelComparison(runId),
      api.satelliteModelSelected(runId),
      api.cohortSummary(),
    ]).then(([comp, sel, coh]) => {
      setComparison(comp);
      setSelected(sel);
      setCohorts(coh);
      if (sel.length > 0) {
        setActiveProduct(sel[0].product_type);
      }
      setActiveCohort(null);
      if (runId) setActiveRunId(runId);
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (isLocked) return;
    loadData();
    api.modelRuns('satellite_model').then(setRuns).catch(() => {});
    fetch('/api/admin/config')
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        const models = data?.model?.satellite_models;
        if (models && typeof models === 'object') setModelConfig(models);
      })
      .catch(() => {});
  }, [isLocked, loadData]);

  useEffect(() => {
    setEnabledModels(prev => {
      const keys = Object.keys(MODEL_LABELS);
      const next: Record<string, boolean> = {};
      for (const k of keys) next[k] = prev[k] ?? true;
      return next;
    });
  }, [MODEL_LABELS]);

  const restoreRun = useCallback((runId: string) => {
    setActiveRunId(runId);
    loadData(runId);
    setShowRunHistory(false);
  }, [loadData]);

  const loadLatest = useCallback(() => {
    setActiveRunId(null);
    loadData();
    setShowRunHistory(false);
  }, [loadData]);

  const toggleModel = useCallback((key: string) => {
    setEnabledModels(prev => ({ ...prev, [key]: !prev[key] }));
  }, []);

  const selectAllModels = useCallback(() => {
    setEnabledModels(Object.fromEntries(Object.keys(MODEL_LABELS).map(k => [k, true])));
  }, [MODEL_LABELS]);

  const triggerJob = useCallback(async () => {
    const selectedModels = Object.entries(enabledModels).filter(([, v]) => v).map(([k]) => k);
    if (selectedModels.length === 0) {
      toast('Select at least one model to run', 'error');
      return;
    }
    setJobRunning(true);
    setJobError(null);
    toast(`Triggering pipeline with ${selectedModels.length} models...`, 'info');
    try {
      const result = await api.triggerJob('satellite_ecl_sync', selectedModels);
      setCurrentJobRun(result);
      toast(`Job triggered successfully (run_id: ${result.run_id})`, 'success');
      pollRef.current = setInterval(async () => {
        try {
          const status = await api.jobRunStatus(result.run_id);
          setCurrentJobRun(status);
          if (status.lifecycle_state === 'TERMINATED' || status.lifecycle_state === 'INTERNAL_ERROR' || status.lifecycle_state === 'SKIPPED') {
            if (pollRef.current) clearInterval(pollRef.current);
            pollRef.current = null;
            setJobRunning(false);
            if (status.result_state === 'SUCCESS') {
              toast('Pipeline completed successfully! Refreshing data...', 'success');
              setTimeout(() => loadData(), 2000);
            } else {
              const msg = status.state_message || status.result_state || 'Unknown error';
              toast(`Pipeline failed: ${msg}`, 'error');
              setJobError(msg);
            }
            api.jobRuns('satellite_ecl_sync', 10).then(setJobRuns).catch(() => {});
          }
        } catch { /* polling error, will retry */ }
      }, 5000);
    } catch (e: any) {
      const msg = e?.message || 'Failed to trigger job. Check Admin > Jobs config.';
      toast(msg, 'error');
      setJobError(msg);
      setJobRunning(false);
    }
  }, [enabledModels, loadData, toast]);

  useEffect(() => {
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, []);

  useEffect(() => {
    if (!isLocked) {
      api.jobRuns('satellite_ecl_sync', 10).then(setJobRuns).catch(() => {});
    }
  }, [isLocked]);

  const products = useMemo(() => {
    const set = new Set(selected.map(r => r.product_type));
    return Array.from(set).sort();
  }, [selected]);

  const productCohorts = useMemo(() => {
    if (!activeProduct) return [];
    return selected.filter(r => r.product_type === activeProduct);
  }, [selected, activeProduct]);

  const cohortModels = useMemo(() => {
    if (!activeProduct || !activeCohort) return [];
    return comparison.filter(r => r.product_type === activeProduct && r.cohort_id === activeCohort);
  }, [comparison, activeProduct, activeCohort]);

  const selectedModel = useMemo(() => {
    if (!activeProduct || !activeCohort) return null;
    return selected.find(r => r.product_type === activeProduct && r.cohort_id === activeCohort);
  }, [selected, activeProduct, activeCohort]);

  const modelWinSummary = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const row of selected) {
      counts[row.model_type] = (counts[row.model_type] || 0) + 1;
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([model, count]) => ({ model, count }));
  }, [selected]);

  const productModelChart = useMemo(() => {
    if (!activeProduct) return [];
    const productSel = selected.filter(r => r.product_type === activeProduct);
    const counts: Record<string, number> = {};
    for (const row of productSel) {
      counts[row.model_type] = (counts[row.model_type] || 0) + 1;
    }
    return Object.entries(counts).map(([model, count]) => ({
      name: MODEL_LABELS[model] || model,
      count,
      fill: MODEL_COLORS[model] || '#94A3B8',
    }));
  }, [selected, activeProduct]);

  if (isLocked) return <LockedBanner requiredStep={3} />;

  if (loading) return <PageLoader />;

  return (
    <div className="space-y-5">
      <StepDescription
        description="Select and calibrate macroeconomic satellite models that link forward-looking economic scenarios to credit risk parameters (PD, LGD). Up to 8 model types are evaluated per product-cohort with automatic hyperparameter tuning, per IFRS 9.5.5.17(b) forward-looking information requirements."
        ifrsRef="Per IFRS 9.5.5.17 — measure ECL reflecting an unbiased, probability-weighted amount from a range of possible outcomes."
        tips={[
          'Best model is auto-selected by lowest AIC (parametric) or CV-RMSE (tree-based)',
          'Review R², RMSE, and coefficient signs for economic plausibility',
          'Run the pipeline to refresh models with latest data',
        ]}
      />

      {/* Header */}
      <Card>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-800 dark:text-slate-100 flex items-center gap-2">
              <Cpu size={20} className="text-brand" /> Satellite Model Selection
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Up to 8 models with automatic hyperparameter tuning (GridSearchCV). Best model auto-selected by lowest AIC (parametric) or CV-RMSE (tree-based).
            </p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <span className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg font-semibold text-slate-600 dark:text-slate-300">
              {selected.length} product-cohort models
            </span>
            <span className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg font-semibold text-slate-600 dark:text-slate-300">
              {comparison.length} total evaluations
            </span>
            <button
              onClick={() => setShowRunHistory(!showRunHistory)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-semibold transition ${
                showRunHistory ? 'bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              <History size={14} /> Run History
            </button>
          </div>
        </div>
      </Card>

      {activeRunId && (
        <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-amber-50 border border-amber-200">
          <div className="flex items-center gap-2.5">
            <RotateCcw size={16} className="text-amber-600" />
            <span className="text-sm font-semibold text-amber-800">
              Viewing historical run: <span className="font-mono">{activeRunId.slice(0, 19)}</span>
            </span>
          </div>
          <button onClick={loadLatest}
            className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 hover:text-amber-800 px-3 py-1.5 rounded-lg hover:bg-amber-100 transition">
            <X size={14} /> Back to Latest
          </button>
        </div>
      )}

      {showRunHistory && (
        <Card title="Run History" subtitle="Browse and restore previous satellite model runs">
          {runs.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {runs.map((run: any) => {
                const models = Array.isArray(run.models_used) ? run.models_used : [];
                const summary = typeof run.best_model_summary === 'object' ? run.best_model_summary : {};
                const isActive = activeRunId === run.run_id;
                return (
                  <div key={run.run_id}
                    className={`flex items-center justify-between p-3 rounded-lg border transition ${
                      isActive ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-700' : 'bg-slate-50 dark:bg-slate-800 border-slate-100 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700'
                    }`}>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <Clock size={12} className="text-slate-400" />
                        <span className="text-xs font-mono font-semibold text-slate-700 dark:text-slate-200">
                          {run.run_timestamp ? new Date(run.run_timestamp).toLocaleString() : run.run_id.slice(0, 19)}
                        </span>
                        {isActive && <span className="text-[10px] px-1.5 py-0.5 bg-indigo-200 text-indigo-700 rounded-full font-bold">VIEWING</span>}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-400">
                        <span>{models.length} models</span>
                        <span>{run.total_cohorts} cohorts</span>
                        {Object.entries(summary).slice(0, 3).map(([k, v]) => (
                          <span key={k}>{k}: {String(v)}</span>
                        ))}
                        {run.notes && <span className="italic">{run.notes}</span>}
                      </div>
                    </div>
                    {!isActive && (
                      <button onClick={() => restoreRun(run.run_id)}
                        className="flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-3 py-1.5 rounded-lg hover:bg-indigo-50 transition">
                        <RotateCcw size={12} /> Restore
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-slate-400 py-4 text-center">No previous runs found. Runs are saved automatically when the satellite model pipeline executes.</p>
          )}
        </Card>
      )}

      {/* Run Pipeline */}
      <Card title="Run Satellite Model Pipeline" subtitle="Select models, trigger a Databricks Job, and monitor progress — all observability is native in Databricks">
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2 mt-2">
          {Object.entries(MODEL_LABELS).map(([key, label]) => (
            <button
              key={key}
              onClick={() => toggleModel(key)}
              disabled={jobRunning}
              className={`rounded-lg border p-2 text-center transition text-[11px] font-semibold ${
                enabledModels[key]
                  ? 'bg-white dark:bg-slate-800 border-brand text-brand shadow-sm ring-1 ring-brand/20'
                  : 'bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-700 text-slate-400'
              } ${jobRunning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-md'}`}
            >
              <div className="w-2.5 h-2.5 rounded-full mx-auto mb-1" style={{ background: enabledModels[key] ? (MODEL_COLORS[key] || '#94A3B8') : '#CBD5E1' }} />
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={triggerJob}
            disabled={jobRunning || Object.values(enabledModels).filter(Boolean).length === 0}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand text-white text-xs font-bold rounded-lg hover:bg-brand-dark transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {jobRunning ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            {jobRunning ? 'Running...' : `Run ${Object.values(enabledModels).filter(Boolean).length} Models`}
          </button>
          <button onClick={selectAllModels} disabled={jobRunning} className="text-xs text-brand hover:underline disabled:opacity-50">
            Select All
          </button>
          <span className="text-[10px] text-slate-400 ml-auto">
            Pipeline: Satellite Model → ECL Calculation → Sync to Lakebase
          </span>
        </div>
        {jobError && (
          <div className="mt-3 flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
            <AlertTriangle size={14} className="text-red-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-semibold text-red-700">Job trigger failed</p>
              <p className="text-xs text-red-600 mt-0.5">{jobError}</p>
              <p className="text-[10px] text-red-400 mt-1">Check Admin &gt; Jobs &amp; Pipelines to verify the job ID and workspace URL are configured correctly.</p>
            </div>
          </div>
        )}
        {currentJobRun && (
          <div className="mt-3">
            <JobRunLink run={currentJobRun} label="Satellite Model + ECL Pipeline" />
          </div>
        )}
      </Card>

      {/* Recent Job Runs */}
      {jobRuns.length > 0 && (
        <Card title="Recent Pipeline Runs" subtitle="Click to view full run details in Databricks">
          <div className="space-y-1.5 max-h-48 overflow-y-auto mt-1">
            {jobRuns.map((run: any) => (
              <a
                key={run.run_id}
                href={run.run_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-700/80 transition group"
              >
                <div className="flex items-center gap-2 text-xs">
                  <span className={`w-2 h-2 rounded-full ${
                    run.result_state === 'SUCCESS' ? 'bg-emerald-500' :
                    run.result_state === 'FAILED' ? 'bg-red-500' :
                    run.lifecycle_state === 'RUNNING' ? 'bg-blue-500 animate-pulse' : 'bg-slate-300'
                  }`} />
                  <span className="font-semibold text-slate-700 dark:text-slate-200">
                    {run.result_state || run.lifecycle_state}
                  </span>
                  <span className="text-slate-400">
                    {run.start_time ? new Date(run.start_time).toLocaleString() : '—'}
                  </span>
                  {run.run_duration_ms > 0 && (
                    <span className="text-slate-400">({Math.round(run.run_duration_ms / 1000)}s)</span>
                  )}
                </div>
                <ExternalLink size={12} className="text-slate-300 group-hover:text-brand transition" />
              </a>
            ))}
          </div>
        </Card>
      )}

      {/* Model Win Summary */}
      <Card title="Model Selection Summary" subtitle="Which model type was selected most often across all product-cohort combinations">
        <div className="grid grid-cols-4 md:grid-cols-8 gap-3 mt-2">
          {modelWinSummary.map(({ model, count }) => (
            <div key={model} className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 text-center">
              <div className="w-3 h-3 rounded-full mx-auto mb-1.5" style={{ background: MODEL_COLORS[model] || '#94A3B8' }} />
              <div className="text-lg font-bold text-slate-800 dark:text-slate-100">{count}</div>
              <div className="text-[10px] text-slate-400 font-semibold">{MODEL_LABELS[model] || model}</div>
            </div>
          ))}
        </div>
      </Card>

      {/* Product Selector */}
      <Card title="Product Selection">
        <div className="flex gap-2 flex-wrap">
          {products.map(p => (
            <button
              key={p}
              onClick={() => { setActiveProduct(p); setActiveCohort(null); }}
              className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
                activeProduct === p
                  ? 'bg-navy text-white shadow-sm'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-600'
              }`}
            >
              {formatProductName(p)}
              <span className="ml-1.5 opacity-60">
                ({selected.filter(r => r.product_type === p).length} cohorts)
              </span>
            </button>
          ))}
        </div>
      </Card>

      {activeProduct && (
        <>
          {/* Model distribution chart for selected product */}
          <Card title={`Model Distribution — ${formatProductName(activeProduct)}`} subtitle="Number of cohorts won by each model type">
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={productModelChart} layout="vertical" margin={{ left: 120, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ct.grid} />
                  <XAxis type="number" tick={{ fontSize: 11, fill: ct.axisLight }} tickMargin={12} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: ct.axisLight }} width={110} tickMargin={8} />
                  <Tooltip contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {productModelChart.map((entry, i) => (
                      <Cell key={i} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Cohort Table */}
          <Card title={`Cohort Models — ${formatProductName(activeProduct)}`} subtitle="Click a cohort to see full model comparison">
            <div className="overflow-x-auto mt-2">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-left text-slate-400 font-semibold">
                    <th className="py-2 px-3">Cohort</th>
                    <th className="py-2 px-3">Best Model</th>
                    <th className="py-2 px-3 text-right">R²</th>
                    <th className="py-2 px-3 text-right">RMSE</th>
                    <th className="py-2 px-3 text-right">AIC</th>
                    <th className="py-2 px-3">Selection Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {productCohorts.map(row => (
                    <tr
                      key={row.cohort_id}
                      onClick={() => setActiveCohort(row.cohort_id)}
                      className={`border-b border-slate-100 cursor-pointer transition hover:bg-slate-50 ${
                        activeCohort === row.cohort_id ? 'bg-brand-light' : ''
                      }`}
                    >
                      <td className="py-2 px-3 font-mono text-[11px]">{row.cohort_id}</td>
                      <td className="py-2 px-3">
                        <span className="inline-flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ background: MODEL_COLORS[row.model_type] || '#94A3B8' }} />
                          {MODEL_LABELS[row.model_type] || row.model_type}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-right font-mono">{row.r_squared?.toFixed(4)}</td>
                      <td className="py-2 px-3 text-right font-mono">{row.rmse?.toFixed(6)}</td>
                      <td className="py-2 px-3 text-right font-mono">{row.aic?.toFixed(2) ?? '—'}</td>
                      <td className="py-2 px-3 text-slate-400">{row.selection_reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Detailed Model Comparison for selected cohort */}
          {activeCohort && (
            <Card
              title={`Model Comparison — ${activeCohort}`}
              subtitle={`${cohortModels.length} models evaluated for ${formatProductName(activeProduct)} / ${activeCohort}`}
            >
              <div className="overflow-x-auto mt-2">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-left text-slate-400 font-semibold">
                      <th className="py-2 px-3">Model</th>
                      <th className="py-2 px-3 text-right">R²</th>
                      <th className="py-2 px-3 text-right">RMSE</th>
                      <th className="py-2 px-3 text-right">AIC</th>
                      <th className="py-2 px-3 text-right">BIC</th>
                      <th className="py-2 px-3 text-right">CV-RMSE</th>
                      <th className="py-2 px-3 text-center">Selected</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cohortModels.map(row => {
                      const isBest = selectedModel?.model_type === row.model_type;
                      return (
                        <tr key={row.model_type} className={`border-b border-slate-100 ${isBest ? 'bg-emerald-50 font-semibold' : ''}`}>
                          <td className="py-2 px-3">
                            <span className="inline-flex items-center gap-1.5">
                              <span className="w-2 h-2 rounded-full" style={{ background: MODEL_COLORS[row.model_type] || '#94A3B8' }} />
                              {MODEL_LABELS[row.model_type] || row.model_type}
                            </span>
                          </td>
                          <td className="py-2 px-3 text-right font-mono">{row.r_squared?.toFixed(4)}</td>
                          <td className="py-2 px-3 text-right font-mono">{row.rmse?.toFixed(6)}</td>
                          <td className="py-2 px-3 text-right font-mono">{row.aic?.toFixed(2) ?? '—'}</td>
                          <td className="py-2 px-3 text-right font-mono">{row.bic?.toFixed(2) ?? '—'}</td>
                          <td className="py-2 px-3 text-right font-mono">{row.cv_rmse?.toFixed(6) ?? '—'}</td>
                          <td className="py-2 px-3 text-center">
                            {isBest && <Check size={14} className="text-emerald-600 mx-auto" />}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Formula & Coefficients */}
              {selectedModel && (
                <div className="mt-4 p-4 bg-slate-50 dark:bg-slate-900/50 rounded-lg border border-slate-200 dark:border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-xs font-bold text-slate-600 dark:text-slate-300">Selected Model Formula</h4>
                    <span className="text-[10px] font-semibold text-slate-400 px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded">
                      {MODEL_LABELS[selectedModel.model_type] || selectedModel.model_type}
                    </span>
                  </div>
                  <code className="text-xs font-mono text-slate-700 dark:text-slate-200 block whitespace-pre-wrap break-all">
                    {selectedModel.formula}
                  </code>
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <div>
                      <h5 className="text-[10px] font-bold text-slate-400 mb-1">COEFFICIENTS</h5>
                      {(() => {
                        try {
                          const coeffs = JSON.parse(selectedModel.coefficients_json);
                          return (
                            <div className="space-y-1">
                              {Object.entries(coeffs).map(([k, v]) => (
                                <div key={k} className="flex justify-between text-[11px]">
                                  <span className="text-slate-500">{k}</span>
                                  <span className="font-mono font-semibold text-slate-700 dark:text-slate-200">{typeof v === 'number' ? v.toFixed(6) : String(v)}</span>
                                </div>
                              ))}
                            </div>
                          );
                        } catch { return <span className="text-xs text-slate-400">—</span>; }
                      })()}
                    </div>
                    <div>
                      <h5 className="text-[10px] font-bold text-slate-400 mb-1">FIT METRICS</h5>
                      <div className="space-y-1 text-[11px]">
                        <div className="flex justify-between"><span className="text-slate-500">R²</span><span className="font-mono font-semibold">{selectedModel.r_squared?.toFixed(4)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">RMSE</span><span className="font-mono font-semibold">{selectedModel.rmse?.toFixed(6)}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">AIC</span><span className="font-mono font-semibold">{selectedModel.aic?.toFixed(2) ?? '—'}</span></div>
                        <div className="flex justify-between"><span className="text-slate-500">Observations</span><span className="font-mono font-semibold">{selectedModel.n_observations}</span></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          )}
        </>
      )}

      {/* Approve / Reject */}
      {!isCompleted && (
        <Card>
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-2">Approve Satellite Model Selection</h3>
              <p className="text-xs text-slate-400 mb-3">
                Review the auto-selected models per product-cohort. Once approved, these models will be used in the Monte Carlo ECL calculation.
              </p>
              <textarea
                value={comment}
                onChange={e => setComment(e.target.value)}
                placeholder="Optional: Add review comments..."
                className="w-full border border-slate-200 dark:border-slate-700 rounded-lg px-3 py-2 text-xs resize-none h-16 focus:ring-2 focus:ring-brand focus:border-brand outline-none"
              />
            </div>
            <div className="flex flex-col gap-2 pt-6">
              <button
                onClick={async () => { setActing(true); try { await onApprove(comment); } catch { /* handled by parent */ } finally { setActing(false); } }}
                disabled={acting}
                className="px-5 py-2.5 bg-brand text-white text-xs font-bold rounded-lg hover:bg-brand-dark transition disabled:opacity-50"
              >
                <Check size={14} className="inline mr-1" /> Approve
              </button>
              <button
                onClick={async () => { setActing(true); try { await onReject(comment || 'Rejected'); } catch { /* handled by parent */ } finally { setActing(false); } }}
                disabled={acting || !comment}
                className="px-5 py-2.5 bg-red-500 text-white text-xs font-bold rounded-lg hover:bg-red-600 transition disabled:opacity-50"
              >
                <X size={14} className="inline mr-1" /> Reject
              </button>
            </div>
          </div>
        </Card>
      )}

      {isCompleted && (
        <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 font-semibold">
          <Check size={14} /> Satellite model selection approved. Proceed to Monte Carlo execution.
        </div>
      )}
    </div>
  );
}
