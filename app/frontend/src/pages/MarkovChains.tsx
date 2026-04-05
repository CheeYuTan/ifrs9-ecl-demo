import { useEffect, useState, useMemo, useCallback } from 'react';
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { useChartTheme } from '../lib/chartTheme';
import { motion, AnimatePresence } from 'framer-motion';
import {
  GitBranch, Play, Loader2, Table2, TrendingUp, BarChart3,
  Layers, RefreshCw, ChevronRight, Info, ArrowRightLeft,
} from 'lucide-react';
import Card from '../components/Card';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import { api } from '../lib/api';
import { fmtPct, fmtNumber, fmtDate } from '../lib/format';

const STAGE_COLORS = ['#10b981', '#f59e0b', '#ef4444', '#6b7280'];
const STAGE_LABELS = ['Stage 1', 'Stage 2', 'Stage 3', 'Default'];

const HEATMAP_COLORS = [
  'bg-emerald-50 text-emerald-700',
  'bg-emerald-100 text-emerald-800',
  'bg-yellow-100 text-yellow-800',
  'bg-orange-100 text-orange-800',
  'bg-red-100 text-red-800',
  'bg-red-200 text-red-900',
  'bg-red-300 text-red-900',
];

function getHeatmapClass(value: number, isDiagonal: boolean, isDefault: boolean): string {
  if (isDefault && isDiagonal) return 'bg-slate-200 dark:bg-slate-600 text-slate-700 dark:text-slate-200 font-bold';
  if (isDiagonal) return 'bg-blue-100 text-blue-800 font-bold';
  if (value < 0.01) return HEATMAP_COLORS[0];
  if (value < 0.03) return HEATMAP_COLORS[1];
  if (value < 0.08) return HEATMAP_COLORS[2];
  if (value < 0.15) return HEATMAP_COLORS[3];
  if (value < 0.30) return HEATMAP_COLORS[4];
  if (value < 0.50) return HEATMAP_COLORS[5];
  return HEATMAP_COLORS[6];
}

function TransitionHeatmap({ matrixData, title }: { matrixData: any; title?: string }) {
  if (!matrixData?.matrix || !matrixData?.states) return null;
  const { matrix, states } = matrixData;

  return (
    <div>
      {title && <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">{title}</p>}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr>
              <th className="py-2 px-3 text-left text-[11px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-200 bg-slate-50 dark:bg-slate-700/50 rounded-tl-xl">
                From ↓ / To →
              </th>
              {states.map((s: string) => (
                <th key={s} className="py-2 px-3 text-center text-[11px] font-bold uppercase tracking-wider text-slate-600 dark:text-slate-200 bg-slate-50 dark:bg-slate-700/50 last:rounded-tr-xl">
                  {s}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row: number[], i: number) => (
              <tr key={i} className="border-b border-slate-100 dark:border-slate-700 last:border-0">
                <td className="py-2.5 px-3 text-xs font-bold text-slate-600 dark:text-slate-300 bg-slate-50/50 dark:bg-slate-800/40">
                  {states[i]}
                </td>
                {row.map((val: number, j: number) => {
                  const isDiag = i === j;
                  const isDefault = i === states.length - 1;
                  return (
                    <td key={j} className="py-1.5 px-1.5 text-center">
                      <div className={`rounded-lg py-2 px-2 text-xs font-semibold transition-all ${getHeatmapClass(val, isDiag, isDefault)}`}>
                        {(val * 100).toFixed(2)}%
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="mt-3 flex items-center gap-4 text-[11px] text-slate-500 dark:text-slate-300">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-100 inline-block" /> Diagonal (stay)</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-emerald-100 inline-block" /> Low risk</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-200 inline-block" /> High risk</span>
      </div>
    </div>
  );
}

function ChartTooltipContent({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm rounded-xl shadow-xl border border-slate-100 dark:border-slate-700 px-4 py-3 text-xs">
      <p className="font-bold text-slate-600 dark:text-slate-300 mb-1.5">Month {label}</p>
      {payload.map((p: any) => (
        <div key={p.dataKey} className="flex items-center gap-2 py-0.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: p.color }} />
          <span className="text-slate-500 dark:text-slate-400">{p.name}:</span>
          <span className="font-bold text-slate-700 dark:text-slate-200">{fmtPct(p.value)}</span>
        </div>
      ))}
    </div>
  );
}

type SubTab = 'matrix' | 'forecast' | 'lifetime-pd' | 'compare';

export default function MarkovChains() {
  const ct = useChartTheme();
  const [matrices, setMatrices] = useState<any[]>([]);
  const [selectedMatrix, setSelectedMatrix] = useState<any>(null);
  const [forecastData, setForecastData] = useState<any>(null);
  const [lifetimePd, setLifetimePd] = useState<any>(null);
  const [compareData, setCompareData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [estimating, setEstimating] = useState(false);
  const [forecasting, setForecasting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<SubTab>('matrix');
  const [productFilter, setProductFilter] = useState('');
  const [products, setProducts] = useState<string[]>([]);
  const [horizonMonths, setHorizonMonths] = useState(60);
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set());

  const loadMatrices = useCallback(async () => {
    try {
      const mats = await api.markovListMatrices(productFilter || undefined);
      setMatrices(mats || []);
    } catch (e) {
      console.error('Failed to load matrices:', e);
    }
  }, [productFilter]);

  useEffect(() => {
    setError(null);
    Promise.all([
      api.markovListMatrices(),
      api.portfolioSummary(),
    ]).then(([mats, portfolio]) => {
      setMatrices(mats || []);
      const prods = (portfolio || []).map((p: any) => p.product_type).filter(Boolean);
      setProducts(prods);
    }).catch((e) => {
      setError(e.message || 'Failed to load Markov chain data');
    }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (productFilter) loadMatrices();
  }, [productFilter, loadMatrices]);

  const handleEstimate = async (pt?: string) => {
    setEstimating(true);
    try {
      const result = await api.markovEstimate(pt || undefined);
      setSelectedMatrix(result);
      await loadMatrices();
      setActiveTab('matrix');
    } catch (e) {
      console.error('Estimation failed:', e);
    } finally {
      setEstimating(false);
    }
  };

  const handleSelectMatrix = async (mat: any) => {
    try {
      const full = await api.markovGetMatrix(mat.matrix_id);
      setSelectedMatrix(full);
      setForecastData(null);
      setLifetimePd(null);
    } catch (e) {
      console.error('Failed to load matrix:', e);
    }
  };

  const handleForecast = async () => {
    if (!selectedMatrix) return;
    setForecasting(true);
    try {
      const stageData = await api.stageDistribution();
      const totalLoans = (stageData || []).reduce((s: number, r: any) => s + (r.loan_count || 0), 0);
      const initial = [0, 0, 0, 0];
      for (const r of (stageData || [])) {
        const stage = r.assessed_stage;
        if (stage >= 1 && stage <= 3) {
          initial[stage - 1] = totalLoans > 0 ? r.loan_count / totalLoans : 0;
        }
      }
      const result = await api.markovForecast(selectedMatrix.matrix_id, initial, horizonMonths);
      setForecastData(result);
      setActiveTab('forecast');
    } catch (e) {
      console.error('Forecast failed:', e);
    } finally {
      setForecasting(false);
    }
  };

  const handleLifetimePd = async () => {
    if (!selectedMatrix) return;
    try {
      const result = await api.markovLifetimePd(selectedMatrix.matrix_id, horizonMonths);
      setLifetimePd(result);
      setActiveTab('lifetime-pd');
    } catch (e) {
      console.error('Lifetime PD failed:', e);
    }
  };

  const handleCompare = async () => {
    if (compareIds.size < 2) return;
    try {
      const results = await api.markovCompare(Array.from(compareIds));
      setCompareData(results);
      setActiveTab('compare');
    } catch (e) {
      console.error('Compare failed:', e);
    }
  };

  const toggleCompare = (id: string) => {
    setCompareIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const kpis = useMemo(() => {
    if (!selectedMatrix?.matrix_data?.matrix) return null;
    const m = selectedMatrix.matrix_data.matrix;
    const sicrProb = m[0]?.[1] || 0;
    const cureProb = m[1]?.[0] || 0;
    const defaultProb = m[2]?.[3] || 0;
    const s1Retention = m[0]?.[0] || 0;
    return { sicrProb, cureProb, defaultProb, s1Retention };
  }, [selectedMatrix]);

  const tabs: { key: SubTab; label: string; icon: any }[] = [
    { key: 'matrix', label: 'Transition Matrix', icon: Table2 },
    { key: 'forecast', label: 'Stage Forecast', icon: TrendingUp },
    { key: 'lifetime-pd', label: 'Lifetime PD', icon: BarChart3 },
    { key: 'compare', label: 'Compare', icon: ArrowRightLeft },
  ];

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center animate-pulse">
          <GitBranch size={20} className="text-white" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Markov Chain Transition Models"
        subtitle="State transition matrices for IFRS 9 stage migration and lifetime PD estimation"
      />

      {error && (
        <ErrorDisplay title="Failed to load data" message={error} technicalDetails={error}
          onRetry={() => {
            setLoading(true); setError(null);
            Promise.all([api.markovListMatrices(), api.portfolioSummary()])
              .then(([mats, portfolio]) => {
                setMatrices(mats || []);
                const prods = (portfolio || []).map((p: any) => p.product_type).filter(Boolean);
                setProducts(prods);
              })
              .catch(e => setError(e.message || 'Failed to load'))
              .finally(() => setLoading(false));
          }}
          onDismiss={() => setError(null)} />
      )}

      {/* KPI Cards */}
      {kpis && (
        <div className="grid grid-cols-4 gap-4">
          <KpiCard title="SICR Probability" value={fmtPct(kpis.sicrProb * 100)}
            subtitle="Stage 1 → Stage 2" icon={<TrendingUp size={18} />} color="amber" />
          <KpiCard title="Cure Rate" value={fmtPct(kpis.cureProb * 100)}
            subtitle="Stage 2 → Stage 1" icon={<RefreshCw size={18} />} color="green" />
          <KpiCard title="Default Probability" value={fmtPct(kpis.defaultProb * 100)}
            subtitle="Stage 3 → Default" icon={<BarChart3 size={18} />} color="red" />
          <KpiCard title="Stage 1 Retention" value={fmtPct(kpis.s1Retention * 100)}
            subtitle="Staying in Stage 1" icon={<Layers size={18} />} color="blue" />
        </div>
      )}

      {/* Estimation Controls */}
      <Card title="Estimate Transition Matrix" subtitle="Build from portfolio stage migration data"
        icon={<GitBranch size={16} />} accent="brand">
        <div className="flex items-center gap-4 flex-wrap">
          <button onClick={() => handleEstimate()} disabled={estimating}
            className="btn-primary text-sm flex items-center gap-2">
            {estimating ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
            Estimate All Products
          </button>
          {products.map(p => (
            <button key={p} onClick={() => handleEstimate(p)} disabled={estimating}
              className="btn-secondary text-xs flex items-center gap-2">
              <Play size={12} /> {p.replace(/_/g, ' ')}
            </button>
          ))}
          <div className="ml-auto flex items-center gap-2">
            <label className="text-xs text-slate-500 dark:text-slate-300 font-medium">Horizon:</label>
            <select value={horizonMonths} onChange={e => setHorizonMonths(Number(e.target.value))}
              className="form-input text-xs w-24">
              <option value={12}>12 months</option>
              <option value={24}>24 months</option>
              <option value={36}>36 months</option>
              <option value={60}>60 months</option>
              <option value={120}>120 months</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Sub-tabs */}
      <div className="flex items-center gap-1 bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-2xl p-1.5 border border-slate-100 dark:border-slate-700 shadow-sm">
        {tabs.map(t => {
          const Icon = t.icon;
          const isActive = activeTab === t.key;
          return (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                isActive ? 'gradient-brand text-white shadow-md' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 hover:text-slate-700 dark:hover:text-slate-300'
              }`}>
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        {/* Matrix Tab */}
        {activeTab === 'matrix' && (
          <motion.div key="matrix" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="space-y-6">
            {selectedMatrix?.matrix_data && (
              <Card title={selectedMatrix.model_name || 'Transition Matrix'}
                subtitle={`${selectedMatrix.product_type || 'All Products'} · ${fmtNumber(selectedMatrix.n_observations)} observations`}
                icon={<Table2 size={16} />} accent="blue"
                action={
                  <div className="flex gap-2">
                    <button onClick={handleForecast} disabled={forecasting}
                      className="btn-secondary text-xs flex items-center gap-1.5">
                      {forecasting ? <Loader2 size={12} className="animate-spin" /> : <TrendingUp size={12} />}
                      Forecast
                    </button>
                    <button onClick={handleLifetimePd} className="btn-secondary text-xs flex items-center gap-1.5">
                      <BarChart3 size={12} /> Lifetime PD
                    </button>
                  </div>
                }>
                <TransitionHeatmap matrixData={selectedMatrix.matrix_data} />
                <div className="mt-4 p-3 rounded-xl bg-blue-50/50 border border-blue-100">
                  <div className="flex items-start gap-2">
                    <Info size={14} className="text-blue-500 mt-0.5 flex-shrink-0" />
                    <div className="text-xs text-blue-700 space-y-1">
                      <p><strong>SICR indicator:</strong> Stage 1→2 probability of {fmtPct((selectedMatrix.matrix_data.matrix[0]?.[1] || 0) * 100)} signals significant increase in credit risk.</p>
                      <p><strong>Absorbing state:</strong> Default is an absorbing state — once entered, the loan cannot recover (row sums to 100% on diagonal).</p>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            {!selectedMatrix && matrices.length === 0 && (
              <Card>
                <EmptyState
                  icon={<GitBranch size={48} />}
                  title="No transition matrices estimated"
                  description="Estimate a matrix from your portfolio data."
                  action={{ label: 'Estimate All Products', onClick: () => handleEstimate() }}
                />
              </Card>
            )}
          </motion.div>
        )}

        {/* Forecast Tab */}
        {activeTab === 'forecast' && (
          <motion.div key="forecast" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {forecastData?.forecast_data?.points ? (
              <Card title="Stage Distribution Forecast"
                subtitle={`Projected over ${forecastData.horizon_months} months`}
                icon={<TrendingUp size={16} />} accent="purple">
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={forecastData.forecast_data.points}>
                      <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                      <XAxis dataKey="month" tick={{ fontSize: 11, fill: ct.axisLight }} label={{ value: 'Months', position: 'insideBottom', offset: -5, fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} label={{ value: '% of Portfolio', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                      <Tooltip content={<ChartTooltipContent />} />
                      <Legend wrapperStyle={{ fontSize: 12, color: ct.label }} />
                      {STAGE_LABELS.map((label, i) => (
                        <Area key={label} type="monotone" dataKey={label} stackId="1"
                          fill={STAGE_COLORS[i]} stroke={STAGE_COLORS[i]}
                          fillOpacity={0.7} name={label} />
                      ))}
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 p-3 rounded-xl bg-purple-50/50 border border-purple-100">
                  <div className="flex items-start gap-2">
                    <Info size={14} className="text-purple-500 mt-0.5 flex-shrink-0" />
                    <p className="text-xs text-purple-700">
                      This forecast uses matrix exponentiation (P^n) to project the portfolio's stage distribution forward.
                      The initial distribution is derived from the current portfolio composition.
                    </p>
                  </div>
                </div>
              </Card>
            ) : (
              <Card accent="amber">
                <div className="text-center py-8">
                  <TrendingUp size={40} className="mx-auto text-slate-300 mb-3" />
                  <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">No forecast generated yet</p>
                  <p className="text-xs text-slate-400 mt-1">Select a matrix and click "Forecast" to project stage distributions</p>
                </div>
              </Card>
            )}
          </motion.div>
        )}

        {/* Lifetime PD Tab */}
        {activeTab === 'lifetime-pd' && (
          <motion.div key="lifetime-pd" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            {lifetimePd?.pd_curves ? (
              <Card title="Cumulative Lifetime PD Curves"
                subtitle={`Derived from transition matrix over ${lifetimePd.max_months} months`}
                icon={<BarChart3 size={16} />} accent="red">
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={_buildPdChartData(lifetimePd.pd_curves)}>
                      <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                      <XAxis dataKey="month" tick={{ fontSize: 11, fill: ct.axisLight }} label={{ value: 'Months', position: 'insideBottom', offset: -5, fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} label={{ value: 'Cumulative PD (%)', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                      <Tooltip content={<ChartTooltipContent />} />
                      <Legend wrapperStyle={{ fontSize: 12, color: ct.label }} />
                      {Object.keys(lifetimePd.pd_curves).map((stage, i) => (
                        <Line key={stage} type="monotone" dataKey={stage}
                          stroke={STAGE_COLORS[i]} strokeWidth={2.5}
                          dot={false} name={stage} />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div className="mt-4 grid grid-cols-3 gap-4">
                  {Object.entries(lifetimePd.pd_curves).map(([stage, curve]: [string, any], i) => {
                    const lastPoint = curve[curve.length - 1];
                    const midPoint = curve[Math.floor(curve.length / 2)];
                    return (
                      <div key={stage} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: STAGE_COLORS[i] }} />
                          <span className="text-xs font-bold text-slate-600 dark:text-slate-300">{stage}</span>
                        </div>
                        <div className="space-y-1 text-xs text-slate-500">
                          <div className="flex justify-between">
                            <span>12-month PD:</span>
                            <span className="font-semibold text-slate-700 dark:text-slate-200">{fmtPct(curve[Math.min(12, curve.length - 1)]?.cumulative_pd)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Mid-point PD:</span>
                            <span className="font-semibold text-slate-700 dark:text-slate-200">{fmtPct(midPoint?.cumulative_pd)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Lifetime PD:</span>
                            <span className="font-bold text-slate-800 dark:text-white">{fmtPct(lastPoint?.cumulative_pd)}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </Card>
            ) : (
              <Card accent="amber">
                <div className="text-center py-8">
                  <BarChart3 size={40} className="mx-auto text-slate-300 mb-3" />
                  <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">No lifetime PD computed yet</p>
                  <p className="text-xs text-slate-400 mt-1">Select a matrix and click "Lifetime PD" to compute cumulative default curves</p>
                </div>
              </Card>
            )}
          </motion.div>
        )}

        {/* Compare Tab */}
        {activeTab === 'compare' && (
          <motion.div key="compare" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="space-y-6">
            {compareData.length >= 2 ? (
              <div className="grid grid-cols-2 gap-6">
                {compareData.map((mat, idx) => (
                  <Card key={mat.matrix_id} title={mat.model_name || `Matrix ${idx + 1}`}
                    subtitle={`${mat.product_type || 'All'} · ${fmtNumber(mat.n_observations)} obs`}
                    accent={idx === 0 ? 'blue' : 'purple'}>
                    <TransitionHeatmap matrixData={mat.matrix_data} />
                  </Card>
                ))}
              </div>
            ) : (
              <Card accent="amber">
                <div className="text-center py-8">
                  <ArrowRightLeft size={40} className="mx-auto text-slate-300 mb-3" />
                  <p className="text-sm font-semibold text-slate-600 dark:text-slate-400">Select 2+ matrices to compare</p>
                  <p className="text-xs text-slate-400 mt-1">Use the checkboxes in the matrix list below, then click "Compare Selected"</p>
                </div>
              </Card>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Matrix List */}
      <Card title="Estimated Matrices" subtitle={`${matrices.length} matrices available`}
        icon={<Layers size={16} />}
        action={
          <div className="flex items-center gap-2">
            <select value={productFilter} onChange={e => setProductFilter(e.target.value)}
              className="form-input text-xs w-40">
              <option value="">All Products</option>
              {products.map(p => <option key={p} value={p}>{p.replace(/_/g, ' ')}</option>)}
            </select>
            {compareIds.size >= 2 && (
              <button onClick={handleCompare} className="btn-primary text-xs flex items-center gap-1.5">
                <ArrowRightLeft size={12} /> Compare ({compareIds.size})
              </button>
            )}
          </div>
        }>
        {matrices.length > 0 ? (
          <DataTable
            columns={[
              {
                key: 'select', label: '', align: 'center',
                format: (_: any, row: any) => (
                  <input type="checkbox" checked={compareIds.has(row.matrix_id)}
                    onChange={() => toggleCompare(row.matrix_id)}
                    className="w-3.5 h-3.5 rounded border-slate-300 text-brand focus:ring-brand/30" />
                ),
              },
              { key: 'model_name', label: 'Model Name' },
              { key: 'product_type', label: 'Product', format: (v: any) => v || 'All' },
              { key: 'segment', label: 'Segment', format: (v: any) => v || 'All' },
              { key: 'matrix_type', label: 'Type' },
              { key: 'methodology', label: 'Method' },
              { key: 'n_observations', label: 'Observations', align: 'right', format: (v: any) => fmtNumber(v) },
              { key: 'computed_at', label: 'Computed', format: (v: any) => fmtDate(v) },
              {
                key: 'actions', label: '', align: 'center',
                format: (_: any, row: any) => (
                  <button onClick={(e) => { e.stopPropagation(); handleSelectMatrix(row); }}
                    className="text-brand hover:text-brand/80 transition">
                    <ChevronRight size={16} />
                  </button>
                ),
              },
            ]}
            data={matrices}
            onRowClick={handleSelectMatrix}
            compact
            exportName="markov_matrices"
          />
        ) : (
          <div className="text-center py-6 text-xs text-slate-400">
            No matrices found. Estimate one above to get started.
          </div>
        )}
      </Card>
    </div>
  );
}

function _buildPdChartData(pdCurves: Record<string, any[]>): any[] {
  const stages = Object.keys(pdCurves);
  if (stages.length === 0) return [];
  const maxLen = Math.max(...stages.map(s => pdCurves[s].length));
  const data = [];
  for (let i = 0; i < maxLen; i++) {
    const point: any = { month: i };
    for (const stage of stages) {
      const curve = pdCurves[stage];
      point[stage] = curve[i]?.cumulative_pd ?? null;
    }
    data.push(point);
  }
  return data;
}
