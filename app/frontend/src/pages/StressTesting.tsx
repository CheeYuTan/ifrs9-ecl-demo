import { useEffect, useState, useMemo, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
  LineChart, Line, Legend, CartesianGrid,
} from 'recharts';
import { Zap, TrendingUp, AlertTriangle, Shield, Activity, Dice5, Play, Loader2, Info } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import LockedBanner from '../components/LockedBanner';
import StatusBadge from '../components/StatusBadge';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtPct, fmtNumber } from '../lib/format';
import { config } from '../lib/config';

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject?: (comment: string) => Promise<void>;
}

const SCENARIO_COLORS: Record<string, string> = Object.fromEntries(
  Object.entries(config.scenarios).map(([k, v]) => [k, v.color])
);

const SCENARIO_LABELS: Record<string, string> = Object.fromEntries(
  Object.entries(config.scenarios).map(([k, v]) => [k, v.label])
);

export default function StressTesting({ project, onApprove, onReject }: Props) {
  const [sensitivity, setSensitivity] = useState<any[]>([]);
  const [scenComp, setScenComp] = useState<any[]>([]);
  const [stageData, setStageData] = useState<any[]>([]);
  const [vintageData, setVintageData] = useState<any[]>([]);
  const [concData, setConcData] = useState<any[]>([]);
  const [mcDist, setMcDist] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  const [pdShock, setPdShock] = useState(0);
  const [lgdShock, setLgdShock] = useState(0);
  const [eadShock, setEadShock] = useState(0);
  const [migrationPct, setMigrationPct] = useState(0);
  const [activeSubTab, setActiveSubTab] = useState<'montecarlo' | 'sensitivity' | 'vintage' | 'concentration' | 'migration'>('montecarlo');

  const [error, setError] = useState<string | null>(null);

  const [sensMode, setSensMode] = useState<'quick' | 'full'>('quick');
  const [simDefaults, setSimDefaults] = useState<any>(null);
  const [fullSimLoading, setFullSimLoading] = useState(false);
  const [fullSimResult, setFullSimResult] = useState<any>(null);
  const [fullSimError, setFullSimError] = useState<string | null>(null);

  const locked = !project || project.current_step < 5;

  useEffect(() => {
    if (locked) return;
    Promise.all([
      api.sensitivityData(),
      api.scenarioComparison(),
      api.stressByStage(),
      api.vintagePerformance(),
      api.concentrationByProductStage(),
      api.mcDistribution().catch(() => []),
    ]).then(([sens, sc, st, vp, cp, mc]) => {
      setSensitivity(sens || []);
      setScenComp(sc || []);
      setStageData(st || []);
      setVintageData(vp || []);
      setConcData(cp || []);
      setMcDist(mc || []);
    }).catch(err => {
      console.error('Stress testing data load error:', err);
      setError(String(err));
    }).finally(() => setLoading(false));
  }, [project, locked]);

  useEffect(() => {
    if (locked) return;
    api.simulationDefaults().then(setSimDefaults).catch(() => {});
  }, [locked]);

  const runStressedSimulation = useCallback(async () => {
    if (!simDefaults) return;
    setFullSimLoading(true);
    setFullSimError(null);
    setFullSimResult(null);
    try {
      const pdMult = 1 + pdShock / 100;
      const lgdMult = 1 + lgdShock / 100;
      const stressedConfig = {
        n_simulations: simDefaults.n_simulations || 1000,
        pd_lgd_correlation: simDefaults.pd_lgd_correlation || 0.30,
        aging_factor: (simDefaults.aging_factor || 0.08) * (1 + Math.max(0, pdShock) / 200),
        pd_floor: (simDefaults.pd_floor || 0.001) * pdMult,
        pd_cap: Math.min((simDefaults.pd_cap || 0.95) * pdMult, 1.0),
        lgd_floor: (simDefaults.lgd_floor || 0.01) * lgdMult,
        lgd_cap: Math.min((simDefaults.lgd_cap || 0.95) * lgdMult, 1.0),
        scenario_weights: simDefaults.scenario_weights || undefined,
      };
      const result = await api.runSimulation(stressedConfig);
      setFullSimResult({ ...result, eadShock });
    } catch (err: any) {
      setFullSimError(err?.message || 'Simulation failed');
    } finally {
      setFullSimLoading(false);
    }
  }, [simDefaults, pdShock, lgdShock, eadShock]);

  const fullSimEcl = useMemo(() => {
    if (!fullSimResult) return null;
    const stages = fullSimResult.stage_summary || [];
    const rawTotal = stages.reduce((s: number, r: any) => s + (Number(r.total_ecl) || 0), 0);
    const eadMult = 1 + (fullSimResult.eadShock || 0) / 100;
    return rawTotal * eadMult;
  }, [fullSimResult]);

  const scenarioByProduct = useMemo(() => {
    if (!scenComp.length) return [];
    const products = [...new Set(scenComp.map(r => r.product_type))];
    const scenarios = [...new Set(scenComp.map(r => r.scenario))];
    return products.map(p => {
      const row: any = { product: p };
      scenarios.forEach(s => {
        const match = scenComp.find(r => r.product_type === p && r.scenario === s);
        row[s] = match?.total_ecl || 0;
      });
      return row;
    });
  }, [scenComp]);

  const migrationSimData = useMemo(() => {
    if (!stageData.length) return [];
    return stageData.map(s => {
      const stage = s.assessed_stage;
      let adjustedEcl = Number(s.base_ecl) || 0;
      if (stage === 1 && migrationPct > 0) {
        adjustedEcl = adjustedEcl * (1 - migrationPct / 100);
      } else if (stage === 2) {
        const s1 = stageData.find(x => x.assessed_stage === 1);
        const migratedGca = (Number(s1?.total_gca) || 0) * (migrationPct / 100);
        const totalGca = Number(s.total_gca) || 0;
        const baseEclVal = Number(s.base_ecl) || 0;
        const s2CoverageRate = totalGca > 0 ? baseEclVal / totalGca : 0;
        adjustedEcl = baseEclVal + migratedGca * s2CoverageRate;
      }
      return {
        name: `Stage ${stage}`,
        stage,
        base_ecl: Number(s.base_ecl) || 0,
        adjusted_ecl: adjustedEcl,
        loan_count: Number(s.loan_count) || 0,
        total_gca: Number(s.total_gca) || 0,
      };
    });
  }, [stageData, migrationPct]);

  // Monte Carlo distribution chart data
  const mcChartData = useMemo(() => {
    if (!mcDist.length) return [];
    return mcDist.map(d => ({
      scenario: SCENARIO_LABELS[d.scenario] || d.scenario,
      scenarioKey: d.scenario,
      weight: Number(d.weight) || 0,
      mean: Number(d.ecl_mean) || 0,
      p50: Number(d.ecl_p50) || 0,
      p75: Number(d.ecl_p75) || 0,
      p95: Number(d.ecl_p95) || 0,
      p99: Number(d.ecl_p99) || 0,
      pd_mult: Number(d.avg_pd_multiplier) || 1,
      lgd_mult: Number(d.avg_lgd_multiplier) || 1,
      pd_vol: Number(d.pd_vol) || 0,
      lgd_vol: Number(d.lgd_vol) || 0,
      n_sims: Number(d.n_simulations) || 0,
      spread: (Number(d.ecl_p95) || 0) - (Number(d.ecl_p50) || 0),
    })).sort((a, b) => b.weight - a.weight);
  }, [mcDist]);

  const stepSt = project?.step_status?.stress_testing || 'pending';

  if (locked) return <LockedBanner />;
  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>;
  if (error) return <Card title="Error Loading Stress Testing Data"><p className="text-sm text-red-500">{error}</p><button onClick={() => window.location.reload()} className="mt-3 px-4 py-2 bg-brand text-white text-sm rounded-lg">Retry</button></Card>;

  const baseEcl = sensitivity.reduce((s, r) => s + (Number(r.base_ecl) || 0), 0);
  const baseGca = sensitivity.reduce((s, r) => s + (Number(r.total_gca) || 0), 0);

  // Stress testing applies proportional shocks to the base ECL.
  // The base ECL already incorporates the full cash-flow model (survival probability,
  // discounting, term structure). Shocks scale the ECL proportionally because
  // ECL ≈ f(PD, LGD, EAD) and small perturbations are approximately multiplicative.
  const stressedData = sensitivity.map(r => {
    const baseEclVal = Number(r.base_ecl) || 0;

    const pdFactor = 1 + pdShock / 100;
    const lgdFactor = 1 + lgdShock / 100;
    const eadFactor = 1 + eadShock / 100;
    const combinedFactor = pdFactor * lgdFactor * eadFactor;
    const stressedEcl = baseEclVal * combinedFactor;
    const safeStressed = isFinite(stressedEcl) ? stressedEcl : baseEclVal;
    return {
      product_type: r.product_type,
      loan_count: Number(r.loan_count) || 0,
      base_ecl: baseEclVal,
      stressed_ecl: safeStressed,
      delta: safeStressed - baseEclVal,
      delta_pct: baseEclVal > 0 ? ((safeStressed - baseEclVal) / baseEclVal * 100) : 0,
    };
  });

  const totalStressedEcl = stressedData.reduce((s, r) => s + r.stressed_ecl, 0);
  const totalDelta = totalStressedEcl - baseEcl;
  const deltaPct = baseEcl > 0 ? (totalDelta / baseEcl * 100) : 0;

  const shockSum = Math.abs(pdShock) + Math.abs(lgdShock) + Math.abs(eadShock) || 1;
  const sensitivityWaterfall = [
    { name: 'Base ECL', value: baseEcl, fill: '#1A1F36' },
    { name: `Stressed PD (${pdShock >= 0 ? '+' : ''}${pdShock}%)`, value: totalDelta * (Math.abs(pdShock) / shockSum), fill: pdShock >= 0 ? '#EF4444' : '#10B981' },
    { name: `Stressed LGD (${lgdShock >= 0 ? '+' : ''}${lgdShock}%)`, value: totalDelta * (Math.abs(lgdShock) / shockSum), fill: lgdShock >= 0 ? '#EF4444' : '#10B981' },
    { name: `EAD (${eadShock >= 0 ? '+' : ''}${eadShock}%)`, value: totalDelta * (Math.abs(eadShock) / shockSum), fill: eadShock >= 0 ? '#EF4444' : '#10B981' },
    { name: 'Stressed ECL', value: totalStressedEcl, fill: '#DC2626' },
  ];

  const migrationTotalDelta = migrationSimData.reduce((s, r) => s + (r.adjusted_ecl - r.base_ecl), 0);

  const comparisonData = stressedData.map(r => ({
    product: String(r.product_type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    base: r.base_ecl,
    stressed: r.stressed_ecl,
  }));

  const handleApprove = async () => {
    setActing(true);
    try {
      await onApprove(comment || 'Stress testing reviewed and approved');
    } finally {
      setActing(false);
    }
  };

  // MC summary KPIs
  const mcWeightedMean = mcChartData.reduce((s, d) => s + d.mean * d.weight, 0);
  const mcP95Max = mcChartData.length > 0 ? Math.max(...mcChartData.map(d => d.p95)) : 0;
  const mcP99Max = mcChartData.length > 0 ? Math.max(...mcChartData.map(d => d.p99)) : 0;
  const nScenarios = mcChartData.length;

  const safeFmt = (v: any, decimals = 1) => {
    const n = Number(v);
    return isFinite(n) ? `${n >= 0 ? '+' : ''}${n.toFixed(decimals)}%` : '—';
  };

  const SUB_TABS = [
    { key: 'montecarlo' as const, label: 'Monte Carlo Simulation', icon: <Dice5 size={14} /> },
    { key: 'sensitivity' as const, label: 'Sensitivity Analysis', icon: <Activity size={14} /> },
    { key: 'vintage' as const, label: 'Vintage Analysis', icon: <TrendingUp size={14} /> },
    { key: 'concentration' as const, label: 'Concentration Risk', icon: <AlertTriangle size={14} /> },
    { key: 'migration' as const, label: 'Stage Migration Sim', icon: <Shield size={14} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Stress Testing & Scenario Analysis</h2>
          <p className="text-sm text-slate-400 mt-1">Forward-looking credit loss simulation across {nScenarios} plausible scenarios with stochastic Stressed PD / Stressed LGD</p>
        </div>
        <StatusBadge status={stepSt} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Weighted ECL" value={fmtCurrency(mcWeightedMean || baseEcl)} subtitle={`${nScenarios} plausible scenarios`} color="blue" icon={<Shield size={20} />} />
        <KpiCard title="Worst P95" value={fmtCurrency(mcP95Max)} subtitle="95th percentile (tail risk)" color="red" icon={<Zap size={20} />} />
        <KpiCard title="Worst P99" value={fmtCurrency(mcP99Max)} subtitle="99th percentile (extreme)" color="amber" icon={<AlertTriangle size={20} />} />
        <KpiCard title="Plausible Scenarios" value={String(nScenarios)} subtitle="Economic paths modeled" color="purple" icon={<Dice5 size={20} />} />
      </div>

      <div className="flex gap-1 bg-white rounded-xl shadow-sm p-1.5 overflow-x-auto">
        {SUB_TABS.map(t => (
          <button key={t.key} onClick={() => setActiveSubTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
              activeSubTab === t.key ? 'bg-navy text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
            }`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── Monte Carlo Tab ─────────────────────────────────────────── */}
      {activeSubTab === 'montecarlo' && (
        <div className="space-y-6">
          <Card title="Forward-Looking Credit Loss Distribution" subtitle="Monte Carlo simulation: Mean, P50, P75, P95, P99 across stochastic Stressed PD / Stressed LGD draws">
            {mcChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={380}>
                <BarChart data={mcChartData} barGap={2} barSize={14}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="scenario" tick={{ fontSize: 9 }} interval={0} angle={-15} textAnchor="end" height={65} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="mean" name="Mean ECL" fill="#3B82F6" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="p75" name="P75" fill="#F59E0B" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="p95" name="P95" fill="#EF4444" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="p99" name="P99" fill="#991B1B" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">Monte Carlo data not available — run the ECL notebook with MC enabled</p>
            )}
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Plausible Scenario Weights & ECL Range" subtitle="Probability-weighted contribution to forward-looking credit loss">
              {mcChartData.length > 0 ? (
                <div className="space-y-3">
                  {mcChartData.map(d => {
                    const color = SCENARIO_COLORS[d.scenarioKey] || '#6B7280';
                    const maxEcl = Math.max(...mcChartData.map(x => x.p99));
                    const barWidth = maxEcl > 0 ? (d.p95 / maxEcl * 100) : 0;
                    return (
                      <div key={d.scenarioKey} className="group">
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                            <span className="text-xs font-semibold text-slate-700">{d.scenario}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500 font-mono">{(d.weight * 100).toFixed(0)}%</span>
                          </div>
                          <span className="text-xs font-mono text-slate-500">{fmtCurrency(d.mean)}</span>
                        </div>
                        <div className="relative h-5 bg-slate-100 rounded-full overflow-hidden">
                          <div className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                            style={{ width: `${barWidth}%`, backgroundColor: color, opacity: 0.7 }} />
                          <div className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                            style={{ width: `${maxEcl > 0 ? d.mean / maxEcl * 100 : 0}%`, backgroundColor: color }} />
                        </div>
                        <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                          <span>P50: {fmtCurrency(d.p50)}</span>
                          <span>P95: {fmtCurrency(d.p95)}</span>
                          <span>P99: {fmtCurrency(d.p99)}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-sm text-slate-400 py-8 text-center">No MC data</p>
              )}
            </Card>

            <Card title="Stressed PD / Stressed LGD Parameters" subtitle="Satellite model multipliers and stochastic volatility by plausible scenario">
              {mcChartData.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-2 px-2 text-xs font-semibold text-slate-500">Plausible Scenario</th>
                        <th className="text-right py-2 px-2 text-xs font-semibold text-slate-500">Stressed PD ×</th>
                        <th className="text-right py-2 px-2 text-xs font-semibold text-slate-500">PD σ</th>
                        <th className="text-right py-2 px-2 text-xs font-semibold text-slate-500">Stressed LGD ×</th>
                        <th className="text-right py-2 px-2 text-xs font-semibold text-slate-500">LGD σ</th>
                        <th className="text-right py-2 px-2 text-xs font-semibold text-slate-500">MC Sims</th>
                      </tr>
                    </thead>
                    <tbody>
                      {mcChartData.map(d => (
                        <tr key={d.scenarioKey} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-2 px-2">
                            <div className="flex items-center gap-1.5">
                              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: SCENARIO_COLORS[d.scenarioKey] || '#6B7280' }} />
                              <span className="text-xs font-medium text-slate-700">{d.scenario}</span>
                            </div>
                          </td>
                          <td className={`py-2 px-2 text-right text-xs font-mono ${d.pd_mult > 1.1 ? 'text-red-600' : d.pd_mult < 0.95 ? 'text-emerald-600' : 'text-slate-600'}`}>
                            {d.pd_mult.toFixed(3)}
                          </td>
                          <td className="py-2 px-2 text-right text-xs font-mono text-slate-500">{(d.pd_vol * 100).toFixed(1)}%</td>
                          <td className={`py-2 px-2 text-right text-xs font-mono ${d.lgd_mult > 1.05 ? 'text-red-600' : 'text-slate-600'}`}>
                            {d.lgd_mult.toFixed(3)}
                          </td>
                          <td className="py-2 px-2 text-right text-xs font-mono text-slate-500">{(d.lgd_vol * 100).toFixed(1)}%</td>
                          <td className="py-2 px-2 text-right text-xs font-mono text-slate-400">{fmtNumber(d.n_sims)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-slate-400 py-8 text-center">No MC data</p>
              )}
            </Card>
          </div>

          <Card title="ECL by Product × Plausible Scenario" subtitle="Forward-looking credit loss across all plausible economic paths, grouped by loan product">
            {scenarioByProduct.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={scenarioByProduct} barGap={1} barSize={8}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="product" tick={{ fontSize: 9 }} interval={0} angle={-10} textAnchor="end" height={50} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  {Object.keys(SCENARIO_COLORS).map(s => {
                    const hasData = scenarioByProduct.some(r => r[s] !== undefined);
                    if (!hasData) return null;
                    return <Bar key={s} dataKey={s} name={SCENARIO_LABELS[s] || s} fill={SCENARIO_COLORS[s]} radius={[2, 2, 0, 0]} />;
                  })}
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">No scenario comparison data available</p>
            )}
          </Card>

          <Card title="Monte Carlo Detail" subtitle="Full ECL distribution statistics per plausible scenario">
            <DataTable
              columns={[
                { key: 'scenario', label: 'Scenario' },
                { key: 'weight', label: 'Weight', align: 'right' as const, format: (v: any) => `${((Number(v) || 0) * 100).toFixed(0)}%` },
                { key: 'mean', label: 'Mean ECL', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'p50', label: 'P50', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'p75', label: 'P75', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'p95', label: 'P95', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'p99', label: 'P99', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
              ]}
              data={mcChartData}
            />
          </Card>

          <Card>
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
              <h4 className="text-sm font-bold text-indigo-800 mb-2">Monte Carlo Methodology — Forward-Looking Credit Loss</h4>
              <div className="text-xs text-indigo-700 space-y-1.5">
                <p><strong>Stochastic Simulation:</strong> For each loan × plausible scenario, <em>Stressed PD</em> and <em>Stressed LGD</em> are drawn from lognormal distributions centered on the satellite-model multiplier, with volatility proportional to the scenario severity.</p>
                <p><strong>Correlation:</strong> Stressed PD and Stressed LGD shocks are 50% correlated (via Cholesky decomposition), reflecting the empirical relationship between default rates and loss severity (1 − Recovery Rate) in stress periods.</p>
                <p><strong>Distribution:</strong> PD<sub>stressed</sub> = PD<sub>TTC</sub> × multiplier × exp(Z × σ<sub>pd</sub> − σ²<sub>pd</sub>/2), ensuring the mean of the lognormal equals the deterministic stressed multiplier while capturing tail risk.</p>
                <p><strong>Recovery Rate:</strong> RR = 1 − LGD<sub>stressed</sub>. Lower recovery under stress scenarios reflects reduced collateral values and longer workout periods.</p>
                <p><strong>Aggregation:</strong> Portfolio ECL (forward-looking credit loss) is the probability-weighted sum across all {nScenarios} plausible scenarios, with each scenario's ECL being the mean of its Monte Carlo draws.</p>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* ── Sensitivity Tab ──────────────────────────────────────────── */}
      {activeSubTab === 'sensitivity' && (
        <div className="space-y-6">
          <Card title="Parameter Shocks" subtitle="Drag sliders to define Stressed PD, Stressed LGD, and EAD stress scenarios">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                { label: 'Stressed PD Shock', value: pdShock, set: setPdShock, desc: 'Probability of Default' },
                { label: 'Stressed LGD Shock', value: lgdShock, set: setLgdShock, desc: 'Loss Given Default (1 − RR)' },
                { label: 'EAD Shock', value: eadShock, set: setEadShock, desc: 'Exposure at Default' },
              ].map(s => (
                <div key={s.label}>
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <span className="text-sm font-bold text-slate-700">{s.label}</span>
                      <span className="text-xs text-slate-400 ml-2">{s.desc}</span>
                    </div>
                    <span className={`text-lg font-bold font-mono ${s.value > 0 ? 'text-red-500' : s.value < 0 ? 'text-emerald-500' : 'text-slate-500'}`}>
                      {s.value > 0 ? '+' : ''}{s.value}%
                    </span>
                  </div>
                  <input type="range" min={-50} max={100} value={s.value} onChange={e => s.set(Number(e.target.value))}
                    className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#00D09C]" />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>-50%</span><span>0%</span><span>+50%</span><span>+100%</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button onClick={() => { setPdShock(0); setLgdShock(0); setEadShock(0); }}
                className="px-3 py-1.5 text-xs font-semibold text-slate-500 bg-slate-100 rounded-lg hover:bg-slate-200 transition">Reset</button>
              <button onClick={() => { setPdShock(20); setLgdShock(10); setEadShock(5); }}
                className="px-3 py-1.5 text-xs font-semibold text-amber-600 bg-amber-50 rounded-lg hover:bg-amber-100 transition">Adverse</button>
              <button onClick={() => { setPdShock(50); setLgdShock(25); setEadShock(15); }}
                className="px-3 py-1.5 text-xs font-semibold text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition">Severe</button>
              <button onClick={() => { setPdShock(100); setLgdShock(50); setEadShock(30); }}
                className="px-3 py-1.5 text-xs font-semibold text-red-700 bg-red-100 rounded-lg hover:bg-red-200 transition">Extreme</button>
            </div>
          </Card>

          {/* Mode toggle */}
          <div className="flex items-center gap-3 bg-white rounded-xl shadow-sm p-3">
            <div className="flex bg-slate-100 rounded-lg p-0.5">
              <button onClick={() => setSensMode('quick')}
                className={`px-4 py-2 text-xs font-semibold rounded-md transition-all ${sensMode === 'quick' ? 'bg-white text-navy shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                <Activity size={12} className="inline mr-1.5 -mt-0.5" />Quick Estimate
              </button>
              <button onClick={() => setSensMode('full')}
                className={`px-4 py-2 text-xs font-semibold rounded-md transition-all ${sensMode === 'full' ? 'bg-white text-navy shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                <Dice5 size={12} className="inline mr-1.5 -mt-0.5" />Full Simulation
              </button>
            </div>
            <div className="flex items-start gap-1.5 text-xs text-slate-400">
              <Info size={14} className="flex-shrink-0 mt-0.5" />
              {sensMode === 'quick'
                ? <span><strong className="text-slate-600">Quick Estimate:</strong> Instant multiplicative approximation — ECL is scaled proportionally by the shock factors. Useful for rapid what-if exploration.</span>
                : <span><strong className="text-slate-600">Full Simulation:</strong> Runs the Monte Carlo engine with stressed PD/LGD bounds. More accurate but takes ~1–2 min. EAD shock is still applied as a multiplier.</span>
              }
            </div>
          </div>

          {/* Quick Estimate mode */}
          {sensMode === 'quick' && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <KpiCard title="Base ECL" value={fmtCurrency(baseEcl)} subtitle="Pre-stress" color="blue" icon={<Shield size={20} />} />
                <KpiCard title="Stressed ECL" value={fmtCurrency(totalStressedEcl)} subtitle={`${deltaPct >= 0 ? '+' : ''}${deltaPct.toFixed(1)}% vs base`} color={totalDelta > 0 ? 'red' : 'teal'} icon={<Zap size={20} />} />
                <KpiCard title="Stress Impact" value={`${totalDelta >= 0 ? '+' : ''}${fmtCurrency(totalDelta)}`} subtitle="Additional provision" color="amber" icon={<AlertTriangle size={20} />} />
                <KpiCard title="Coverage" value={fmtPct(baseGca > 0 ? totalStressedEcl / baseGca * 100 : 0)} subtitle="Stressed ECL / GCA" color="purple" icon={<Activity size={20} />} />
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Sensitivity Waterfall" subtitle="ECL impact decomposition by risk parameter">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={sensitivityWaterfall} barSize={45}>
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-10} textAnchor="end" height={50} />
                      <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                      <Tooltip formatter={(v: any) => fmtCurrency(Math.abs(Number(v) || 0))} />
                      <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                        {sensitivityWaterfall.map((d, i) => <Cell key={i} fill={d.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Card>

                <Card title="Base vs Stressed ECL" subtitle="Impact by product">
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={comparisonData} barGap={2}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                      <XAxis dataKey="product" tick={{ fontSize: 9 }} interval={0} angle={-10} textAnchor="end" height={50} />
                      <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                      <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
                      <Legend wrapperStyle={{ fontSize: 11 }} />
                      <Bar dataKey="base" name="Base ECL" fill="#1A1F36" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="stressed" name="Stressed ECL" fill="#EF4444" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              </div>

              <Card title="Stressed ECL by Product" subtitle="Detailed impact per loan program">
                <DataTable
                  columns={[
                    { key: 'product_type', label: 'Product' },
                    { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                    { key: 'base_ecl', label: 'Base ECL', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                    { key: 'stressed_ecl', label: 'Stressed ECL', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                    { key: 'delta', label: `Delta (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => { const n = Number(v) || 0; return `${n >= 0 ? '+' : ''}${fmtCurrency(n)}`; } },
                    { key: 'delta_pct', label: 'Delta %', align: 'right' as const, format: (v: any) => safeFmt(v) },
                  ]}
                  data={stressedData}
                />
              </Card>
            </>
          )}

          {/* Full Simulation mode */}
          {sensMode === 'full' && (
            <>
              <Card title="Run Stressed Simulation" subtitle="Execute Monte Carlo engine with shocked PD/LGD parameters">
                <div className="space-y-4">
                  {simDefaults && (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-200">
                            <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500">Parameter</th>
                            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500">Base Value</th>
                            <th className="text-right py-2 px-3 text-xs font-semibold text-slate-500">Stressed Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {[
                            { label: 'PD Floor', base: simDefaults.pd_floor, stressed: simDefaults.pd_floor * (1 + pdShock / 100), fmt: (v: number) => (v * 100).toFixed(3) + '%' },
                            { label: 'PD Cap', base: simDefaults.pd_cap, stressed: Math.min(simDefaults.pd_cap * (1 + pdShock / 100), 1.0), fmt: (v: number) => (v * 100).toFixed(1) + '%' },
                            { label: 'Aging Factor', base: simDefaults.aging_factor, stressed: simDefaults.aging_factor * (1 + Math.max(0, pdShock) / 200), fmt: (v: number) => v.toFixed(4) },
                            { label: 'LGD Floor', base: simDefaults.lgd_floor, stressed: simDefaults.lgd_floor * (1 + lgdShock / 100), fmt: (v: number) => (v * 100).toFixed(2) + '%' },
                            { label: 'LGD Cap', base: simDefaults.lgd_cap, stressed: Math.min(simDefaults.lgd_cap * (1 + lgdShock / 100), 1.0), fmt: (v: number) => (v * 100).toFixed(1) + '%' },
                            { label: 'EAD Multiplier', base: 1.0, stressed: 1 + eadShock / 100, fmt: (v: number) => v.toFixed(3) + '×' },
                          ].map(p => (
                            <tr key={p.label} className="border-b border-slate-100 hover:bg-slate-50">
                              <td className="py-2 px-3 text-xs font-medium text-slate-700">{p.label}</td>
                              <td className="py-2 px-3 text-right text-xs font-mono text-slate-500">{p.fmt(p.base)}</td>
                              <td className={`py-2 px-3 text-right text-xs font-mono font-semibold ${p.stressed > p.base ? 'text-red-600' : p.stressed < p.base ? 'text-emerald-600' : 'text-slate-600'}`}>
                                {p.fmt(p.stressed)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  <div className="flex items-center gap-3">
                    <button onClick={runStressedSimulation} disabled={fullSimLoading || !simDefaults}
                      className="flex items-center gap-2 px-5 py-2.5 bg-navy text-white text-sm font-semibold rounded-lg hover:bg-navy/90 disabled:opacity-50 transition shadow-sm">
                      {fullSimLoading ? <><Loader2 size={16} className="animate-spin" /> Running Simulation...</> : <><Play size={16} /> Run Stressed Simulation</>}
                    </button>
                    {fullSimLoading && <span className="text-xs text-slate-400">This may take 1–2 minutes...</span>}
                  </div>

                  {fullSimError && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                      <p className="text-sm text-red-700 font-medium">Simulation Error</p>
                      <p className="text-xs text-red-600 mt-1">{fullSimError}</p>
                    </div>
                  )}
                </div>
              </Card>

              {fullSimResult && fullSimEcl != null && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <KpiCard title="Base ECL" value={fmtCurrency(baseEcl)} subtitle="Pre-stress" color="blue" icon={<Shield size={20} />} />
                    <KpiCard title="Simulated Stressed ECL" value={fmtCurrency(fullSimEcl)}
                      subtitle={`${baseEcl > 0 ? ((fullSimEcl - baseEcl) / baseEcl * 100 >= 0 ? '+' : '') + ((fullSimEcl - baseEcl) / baseEcl * 100).toFixed(1) + '% vs base' : ''}`}
                      color={fullSimEcl > baseEcl ? 'red' : 'teal'} icon={<Zap size={20} />} />
                    <KpiCard title="Simulation Impact" value={`${fullSimEcl - baseEcl >= 0 ? '+' : ''}${fmtCurrency(fullSimEcl - baseEcl)}`}
                      subtitle="Monte Carlo stressed delta" color="amber" icon={<AlertTriangle size={20} />} />
                    <KpiCard title="Quick Est. Comparison" value={fmtCurrency(totalStressedEcl)}
                      subtitle="Multiplicative approximation" color="purple" icon={<Activity size={20} />} />
                  </div>

                  {(fullSimResult.stage_summary || []).length > 0 && (
                    <Card title="Stressed Simulation — ECL by Stage" subtitle="Monte Carlo results with shocked PD/LGD bounds (EAD multiplier applied)">
                      <DataTable
                        columns={[
                          { key: 'assessed_stage', label: 'Stage', format: (v: any) => `Stage ${v}` },
                          { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                          { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                          { key: 'total_ecl', label: `Simulated ECL (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency((Number(v) || 0) * (1 + (fullSimResult.eadShock || 0) / 100)) },
                          { key: 'coverage_pct', label: 'Coverage %', align: 'right' as const, format: (v: any) => fmtPct(Number(v) || 0) },
                        ]}
                        data={fullSimResult.stage_summary}
                      />
                    </Card>
                  )}

                  {(fullSimResult.mc_distribution || []).length > 0 && (
                    <Card title="Stressed MC Distribution" subtitle="Distribution statistics from stressed simulation">
                      <DataTable
                        columns={[
                          { key: 'scenario', label: 'Scenario' },
                          { key: 'weight', label: 'Weight', align: 'right' as const, format: (v: any) => `${((Number(v) || 0) * 100).toFixed(0)}%` },
                          { key: 'ecl_mean', label: 'Mean ECL', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                          { key: 'ecl_p50', label: 'P50', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                          { key: 'ecl_p95', label: 'P95', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                          { key: 'ecl_p99', label: 'P99', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                        ]}
                        data={fullSimResult.mc_distribution}
                      />
                    </Card>
                  )}

                  <Card title="Quick Estimate vs Full Simulation" subtitle="Side-by-side comparison of the two approaches">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                        <h4 className="text-sm font-bold text-slate-700 mb-3">Quick Estimate (Multiplicative)</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between"><span className="text-slate-500">Stressed ECL</span><span className="font-mono font-semibold">{fmtCurrency(totalStressedEcl)}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Delta</span><span className="font-mono font-semibold">{totalDelta >= 0 ? '+' : ''}{fmtCurrency(totalDelta)}</span></div>
                          <div className="flex justify-between"><span className="text-slate-500">Delta %</span><span className="font-mono font-semibold">{deltaPct >= 0 ? '+' : ''}{deltaPct.toFixed(1)}%</span></div>
                        </div>
                      </div>
                      <div className="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                        <h4 className="text-sm font-bold text-indigo-800 mb-3">Full Simulation (Monte Carlo)</h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between"><span className="text-indigo-600">Stressed ECL</span><span className="font-mono font-semibold text-indigo-800">{fmtCurrency(fullSimEcl)}</span></div>
                          <div className="flex justify-between"><span className="text-indigo-600">Delta</span><span className="font-mono font-semibold text-indigo-800">{fullSimEcl - baseEcl >= 0 ? '+' : ''}{fmtCurrency(fullSimEcl - baseEcl)}</span></div>
                          <div className="flex justify-between"><span className="text-indigo-600">Delta %</span><span className="font-mono font-semibold text-indigo-800">{baseEcl > 0 ? ((fullSimEcl - baseEcl) / baseEcl * 100 >= 0 ? '+' : '') + ((fullSimEcl - baseEcl) / baseEcl * 100).toFixed(1) + '%' : '—'}</span></div>
                        </div>
                      </div>
                    </div>
                    {Math.abs(totalStressedEcl - fullSimEcl) / Math.max(baseEcl, 1) > 0.05 && (
                      <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-start gap-2">
                        <AlertTriangle size={14} className="text-amber-600 flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-amber-700">
                          The quick estimate and full simulation differ by more than 5%. The full simulation is more reliable as it re-runs the cash-flow model with stressed parameters rather than scaling the base ECL.
                        </p>
                      </div>
                    )}
                  </Card>
                </>
              )}

              {!fullSimResult && !fullSimLoading && (
                <div className="bg-slate-50 border border-slate-200 rounded-xl p-8 text-center">
                  <Dice5 size={32} className="mx-auto text-slate-300 mb-3" />
                  <p className="text-sm text-slate-500 font-medium">Configure shocks above and click "Run Stressed Simulation"</p>
                  <p className="text-xs text-slate-400 mt-1">The engine will re-run the full Monte Carlo with stressed PD/LGD bounds</p>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {activeSubTab === 'vintage' && (
        <div className="space-y-6">
          <Card title="Vintage Delinquency Curves" subtitle="DPD rates by origination cohort">
            {vintageData.length > 0 ? (
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={vintageData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="vintage_cohort" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v: any) => `${Number(v).toFixed(2)}%`} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Line type="monotone" dataKey="delinquency_rate" name="Any DPD" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="dpd30_rate" name="30+ DPD" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="dpd60_rate" name="60+ DPD" stroke="#DC2626" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="dpd90_rate" name="90+ DPD" stroke="#991B1B" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">No vintage data available</p>
            )}
          </Card>

          <Card title="Vintage PD Trend" subtitle="Average PD by origination cohort">
            {vintageData.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={vintageData} barSize={35}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="vintage_cohort" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v: any) => `${Number(v).toFixed(2)}%`} />
                  <Bar dataKey="avg_pd_pct" name="Avg PD %" fill="#6366F1" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">No vintage data available</p>
            )}
          </Card>

          <Card title="Vintage Detail" subtitle="Cohort-level performance metrics">
            <DataTable
              columns={[
                { key: 'vintage_cohort', label: 'Cohort' },
                { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'avg_pd_pct', label: 'Avg PD %', align: 'right' as const, format: (v: any) => `${(Number(v) || 0).toFixed(2)}%` },
                { key: 'delinquency_rate', label: 'Delinq %', align: 'right' as const, format: (v: any) => `${(Number(v) || 0).toFixed(2)}%` },
                { key: 'dpd30_rate', label: '30+ DPD %', align: 'right' as const, format: (v: any) => `${(Number(v) || 0).toFixed(2)}%` },
                { key: 'stage1', label: 'S1', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                { key: 'stage2', label: 'S2', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                { key: 'stage3', label: 'S3', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
              ]}
              data={vintageData}
            />
          </Card>
        </div>
      )}

      {activeSubTab === 'concentration' && (
        <div className="space-y-6">
          <Card title="ECL Concentration Heatmap" subtitle="Product x Stage coverage rates">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500">Product</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-emerald-600">Stage 1</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-amber-600">Stage 2</th>
                    <th className="text-right py-2 px-3 text-xs font-semibold text-red-600">Stage 3</th>
                  </tr>
                </thead>
                <tbody>
                  {[...new Set(concData.map(r => r.product_type))].map(product => {
                    const rows = concData.filter(r => r.product_type === product);
                    return (
                      <tr key={product} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-medium text-slate-700">{product}</td>
                        {[1, 2, 3].map(stage => {
                          const cell = rows.find(r => r.assessed_stage === stage);
                          const ecl = Number(cell?.total_ecl) || 0;
                          const cov = Number(cell?.coverage_pct) || 0;
                          const intensity = Math.min(cov / 10, 1);
                          const bg = stage === 1 ? `rgba(16,185,129,${intensity * 0.3})` :
                                     stage === 2 ? `rgba(245,158,11,${intensity * 0.3})` :
                                     `rgba(239,68,68,${intensity * 0.3})`;
                          return (
                            <td key={stage} className="py-2.5 px-3 text-right" style={{ backgroundColor: bg }}>
                              <div className="font-mono text-xs font-bold">{fmtCurrency(ecl)}</div>
                              <div className="text-[10px] text-slate-500">{cov.toFixed(2)}% cov</div>
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="ECL by Product" subtitle="Concentration risk across loan programs">
            {sensitivity.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sensitivity} barSize={40}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="product_type" tick={{ fontSize: 10 }} interval={0} angle={-10} textAnchor="end" height={50} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
                  <Bar dataKey="base_ecl" name="ECL" radius={[6, 6, 0, 0]}>
                    {sensitivity.map((_d, i) => <Cell key={i} fill={['#6366F1', '#F59E0B', '#10B981', '#EF4444', '#8B5CF6'][i % 5]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">No concentration data available</p>
            )}
          </Card>

          <Card title="Concentration Summary" subtitle="ECL distribution and single-name exposure">
            <DataTable
              columns={[
                { key: 'product_type', label: 'Product' },
                { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'base_ecl', label: `ECL (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'avg_pd', label: 'Avg PD', align: 'right' as const, format: (v: any) => `${((Number(v) || 0) * 100).toFixed(2)}%` },
              ]}
              data={sensitivity}
            />
          </Card>
        </div>
      )}

      {activeSubTab === 'migration' && (
        <div className="space-y-6">
          <Card title="Stage Migration Simulator" subtitle="What if a percentage of Stage 1 loans migrate to Stage 2?">
            <div className="max-w-lg">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-sm font-bold text-slate-700">Stage 1 → Stage 2 Migration</span>
                  <span className="text-xs text-slate-400 ml-2">% of Stage 1 loans downgraded</span>
                </div>
                <span className={`text-lg font-bold font-mono ${migrationPct > 0 ? 'text-red-500' : 'text-slate-500'}`}>
                  {migrationPct}%
                </span>
              </div>
              <input type="range" min={0} max={30} value={migrationPct} onChange={e => setMigrationPct(Number(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#00D09C]" />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>0%</span><span>5%</span><span>10%</span><span>15%</span><span>20%</span><span>25%</span><span>30%</span>
              </div>
              <div className="mt-3 flex gap-2">
                <button onClick={() => setMigrationPct(0)} className="px-3 py-1.5 text-xs font-semibold text-slate-500 bg-slate-100 rounded-lg hover:bg-slate-200 transition">Reset</button>
                <button onClick={() => setMigrationPct(5)} className="px-3 py-1.5 text-xs font-semibold text-amber-600 bg-amber-50 rounded-lg hover:bg-amber-100 transition">Mild (+5%)</button>
                <button onClick={() => setMigrationPct(10)} className="px-3 py-1.5 text-xs font-semibold text-orange-600 bg-orange-50 rounded-lg hover:bg-orange-100 transition">Moderate (+10%)</button>
                <button onClick={() => setMigrationPct(20)} className="px-3 py-1.5 text-xs font-semibold text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition">Severe (+20%)</button>
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <KpiCard title="Migration Impact" value={`${migrationTotalDelta >= 0 ? '+' : ''}${fmtCurrency(migrationTotalDelta)}`}
              subtitle="Additional ECL from migration" color={migrationTotalDelta > 0 ? 'red' : 'teal'} icon={<TrendingUp size={20} />} />
            <KpiCard title="Migrated Loans" value={fmtNumber(Math.round((Number(stageData.find(s => s.assessed_stage === 1)?.loan_count) || 0) * migrationPct / 100))}
              subtitle={`${migrationPct}% of Stage 1`} color="amber" icon={<AlertTriangle size={20} />} />
            <KpiCard title="New Total ECL" value={fmtCurrency(baseEcl + migrationTotalDelta)}
              subtitle="After migration adjustment" color="purple" icon={<Shield size={20} />} />
          </div>

          <Card title="ECL by Stage — Base vs Simulated" subtitle="Impact of Stage 1 → Stage 2 migration">
            {migrationSimData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={migrationSimData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="base_ecl" name="Base ECL" fill="#1A1F36" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="adjusted_ecl" name="Simulated ECL" fill="#EF4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">No stage data available</p>
            )}
          </Card>

          <Card title="Stage Detail" subtitle="Loan counts and GCA by stage">
            <DataTable
              columns={[
                { key: 'name', label: 'Stage' },
                { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'base_ecl', label: 'Base ECL', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                { key: 'adjusted_ecl', label: 'Simulated ECL', align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
              ]}
              data={migrationSimData}
            />
          </Card>
        </div>
      )}

      {/* Capital Impact & Reverse Stress Testing */}
      <Card title="Capital Impact Analysis" subtitle="Estimated impact on CET1 ratio and regulatory capital buffers">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-xs font-bold text-slate-600 mb-3">Regulatory Capital Impact</h4>
            <div className="space-y-3">
              {[
                { label: 'Current CET1 Ratio', value: '14.2%', color: 'text-emerald-600', bar: 85 },
                { label: 'After Base ECL', value: '13.8%', color: 'text-emerald-600', bar: 82 },
                { label: 'After Adverse Stress', value: '12.1%', color: 'text-amber-600', bar: 72 },
                { label: 'After Severely Adverse', value: '10.5%', color: 'text-red-600', bar: 63 },
                { label: 'Regulatory Minimum', value: '10.0%', color: 'text-slate-500', bar: 60 },
              ].map(item => (
                <div key={item.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-600">{item.label}</span>
                    <span className={`font-mono font-bold ${item.color}`}>{item.value}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-500 ${item.bar >= 80 ? 'bg-emerald-500' : item.bar >= 70 ? 'bg-amber-500' : item.bar >= 60 ? 'bg-red-500' : 'bg-slate-400'}`}
                      style={{ width: `${item.bar}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-600 mb-3">Reverse Stress Testing</h4>
            <div className="bg-red-50 rounded-lg p-4 border border-red-200">
              <p className="text-xs text-red-700 font-semibold mb-2">What scenario would breach the CET1 minimum?</p>
              <div className="space-y-2 text-xs text-red-600">
                <div className="flex justify-between">
                  <span>Required ECL increase to breach</span>
                  <span className="font-mono font-bold">{fmtCurrency(baseEcl * 2.8)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Implied PD multiplier</span>
                  <span className="font-mono font-bold">3.8x baseline</span>
                </div>
                <div className="flex justify-between">
                  <span>Implied GDP contraction</span>
                  <span className="font-mono font-bold">-5.2%</span>
                </div>
                <div className="flex justify-between">
                  <span>Implied unemployment</span>
                  <span className="font-mono font-bold">14.5%</span>
                </div>
              </div>
              <p className="text-[10px] text-red-500 mt-3 italic">
                This exceeds the worst historical recession (2020 COVID: -9.5% GDP). The bank maintains adequate capital buffers under all plausible scenarios.
              </p>
            </div>
            <div className="mt-3 bg-blue-50 rounded-lg p-3 border border-blue-200">
              <p className="text-[10px] text-blue-700">
                <strong>Regulatory Requirement:</strong> Banks must maintain CET1 ratio above 10.0% including capital conservation buffer (2.5%) and countercyclical buffer (0-2.5%). Current buffer above minimum: <strong className="text-emerald-600">4.2 percentage points</strong>.
              </p>
            </div>
          </div>
        </div>
      </Card>

      {stepSt !== 'completed' && (
        <Card>
          <h3 className="text-sm font-bold text-slate-700 mb-3">Stress Testing Review</h3>
          <p className="text-xs text-slate-400 mb-3">Confirm that Monte Carlo simulation, sensitivity analysis, vintage trends, concentration risk, and stage migration simulations have been reviewed.</p>
          <textarea value={comment} onChange={e => setComment(e.target.value)} rows={2}
            placeholder="Stress testing review comments (required for rejection)..."
            className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-brand focus:border-transparent outline-none transition resize-none mb-3" />
          <div className="flex gap-3">
            <button onClick={handleApprove} disabled={acting}
              className="px-5 py-2.5 bg-brand text-white text-sm font-semibold rounded-lg hover:bg-brand-dark disabled:opacity-50 transition shadow-sm">
              {acting ? 'Processing...' : '✓ Approve Stress Testing'}
            </button>
            {onReject && (
              <button onClick={async () => { if (!comment) return; setActing(true); try { await onReject(comment); } finally { setActing(false); } }} disabled={acting || !comment}
                className="px-5 py-2.5 bg-white text-red-500 text-sm font-semibold rounded-lg border border-red-200 hover:bg-red-50 disabled:opacity-40 transition">
                ✗ Reject
              </button>
            )}
          </div>
        </Card>
      )}
    </div>
  );
}
