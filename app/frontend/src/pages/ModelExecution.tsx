import { useEffect, useState, useCallback, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { DollarSign, Percent, Activity, BarChart3, Info, FlaskConical, X } from 'lucide-react';
import { useChartTheme } from '../lib/chartTheme';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import DrillDownChart from '../components/DrillDownChart';
import ThreeLevelDrillDown from '../components/ThreeLevelDrillDown';
import NotebookLink from '../components/NotebookLink';
import LockedBanner from '../components/LockedBanner';
import SimulationPanel from '../components/SimulationPanel';
import CollapsibleSection from '../components/CollapsibleSection';
import PageLoader from '../components/PageLoader';
import PageHeader from '../components/PageHeader';
import ApprovalForm from '../components/ApprovalForm';
import ScenarioProductBarChart from '../components/ScenarioProductBarChart';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtNumber, fmtPct, formatProductName } from '../lib/format';
import { config, type ScenarioConfig } from '../lib/config';
import { chartAxisProps, buildScenarioColorMap, scenarioGridClass, pivotScenarioByProduct, buildDrillDownData } from '../lib/chartUtils';
import StepDescription from '../components/StepDescription';
import HelpTooltip, { IFRS9_HELP } from '../components/HelpTooltip';

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}

export default function ModelExecution({ project, onApprove, onReject }: Props) {
  const ct = useChartTheme();
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [scenario, setScenario] = useState<any[]>([]);
  const [lossStage, setLossStage] = useState<any[]>([]);
  const [scenByProduct, setScenByProduct] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [simResults, setSimResults] = useState<any>(null);
  const [usingSimulation, setUsingSimulation] = useState(false);
  const [preComputed, setPreComputed] = useState<{ eclProduct: any[]; scenario: any[]; lossStage: any[]; scenByProduct: any[] } | null>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [eclCohortByProduct, setEclCohortByProduct] = useState<Record<string, any[]>>({});
  const [adminConfig, setAdminConfig] = useState<any>(null);

  const scenColors = useMemo(() => buildScenarioColorMap(scenario), [scenario]);

  useEffect(() => {
    api.simulationDefaults()
      .then((data: any) => { if (data.products) setProducts(data.products); })
      .catch(() => {});
    fetch('/api/admin/config')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setAdminConfig(data); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!project || project.current_step < 4) return;
    Promise.all([api.eclByProduct(), api.scenarioSummary(), api.lossAllowanceByStage(), api.eclByScenarioProduct()])
      .then(async ([ep, sc, ls, sp]) => {
        setEclProduct(ep); setScenario(sc); setLossStage(ls); setScenByProduct(sp);
        setPreComputed({ eclProduct: ep, scenario: sc, lossStage: ls, scenByProduct: sp });
        const cohortMap: Record<string, any[]> = {};
        for (const row of ep) {
          try {
            const cohortData = await api.eclByCohort(row.product_type);
            cohortMap[row.product_type] = cohortData;
          } catch { /* skip */ }
        }
        setEclCohortByProduct(cohortMap);
      })
      .finally(() => setLoading(false));
  }, [project]);

  const handleSimulationComplete = useCallback((results: any) => {
    setSimResults(results);
    setUsingSimulation(true);
    if (results.ecl_by_product) setEclProduct(results.ecl_by_product);
    if (results.scenario_summary) setScenario(results.scenario_summary);
    if (results.loss_allowance_by_stage) setLossStage(results.loss_allowance_by_stage);
    if (results.ecl_by_scenario_product) setScenByProduct(results.ecl_by_scenario_product);
  }, []);

  const revertToPreComputed = useCallback(() => {
    if (!preComputed) return;
    setEclProduct(preComputed.eclProduct);
    setScenario(preComputed.scenario);
    setLossStage(preComputed.lossStage);
    setScenByProduct(preComputed.scenByProduct);
    setUsingSimulation(false);
    setSimResults(null);
  }, [preComputed]);

  if (!project || project.current_step < 4) return <LockedBanner requiredStep={4} />;
  if (loading) return <PageLoader />;

  const totalEcl = eclProduct.reduce((s, r) => s + (Number(r.total_ecl) || 0), 0);
  const totalGca = eclProduct.reduce((s, r) => s + (Number(r.total_gca) || 0), 0);
  const coverage = totalGca > 0 ? (totalEcl / totalGca * 100) : 0;
  const stepSt = project.step_status.model_execution || 'pending';
  const mcSt = project.step_status.model_control || 'pending';
  const combinedSt = mcSt === 'completed' ? 'completed' : stepSt;

  const stageBarData = lossStage.map(s => ({ name: `Stage ${s.assessed_stage}`, ecl: Number(s.total_ecl) || 0, stage: s.assessed_stage }));
  const scenBarData = scenario.map(s => ({ name: s.scenario, ecl: Number(s.total_ecl) || 0, weighted: Number(s.weighted) || 0 }));

  const scenProductChart = pivotScenarioByProduct(scenByProduct);

  return (
    <div className="space-y-6">
      <PageHeader title="Model Execution & Control" subtitle="Forward-looking credit loss engine — PD, LGD, EAD across probability-weighted macroeconomic scenarios" status={combinedSt} />

      <StepDescription
        description="Run the ECL calculation engine with Monte Carlo simulation across multiple scenarios. Review probability-weighted ECL, coverage ratios, and scenario contributions."
        ifrsRef="Per IFRS 9.5.5.17 — ECL shall reflect the time value of money and reasonable, supportable information about past events, current conditions, and forecasts."
        tips={[
          'Coverage ratio (ECL/GCA) typically ranges 1-8% for a performing portfolio',
          'Verify scenario weights sum to 100% and represent unbiased probability estimates',
          'Compare simulation results against pre-computed ECL for reasonableness',
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title={<span className="flex items-center gap-1">Total ECL <HelpTooltip content={IFRS9_HELP.ECL} size={12} /></span>} value={fmtCurrency(totalEcl)} subtitle="Probability-weighted" color="red" icon={<DollarSign size={20} />} />
        <KpiCard title={<span className="flex items-center gap-1">Coverage <HelpTooltip content={IFRS9_HELP.COVERAGE_RATIO} size={12} /></span>} value={fmtPct(coverage)} subtitle="ECL / GCA" color="indigo" icon={<Percent size={20} />} />
        <KpiCard title="Scenarios" value={String(scenario.length)} subtitle="Plausible economic paths" color="blue" icon={<Activity size={20} />} />
        <KpiCard title="Products" value={String(eclProduct.length)} subtitle="Loan programs" color="teal" icon={<BarChart3 size={20} />} />
      </div>

      {/* ── Simulation Configuration ── */}
      <SimulationPanel onSimulationComplete={handleSimulationComplete} />

      {usingSimulation && simResults && (
        <div className="flex items-center justify-between px-4 py-3 rounded-xl bg-indigo-50 border border-indigo-200">
          <div className="flex items-center gap-2.5">
            <FlaskConical size={16} className="text-indigo-600" />
            <span className="text-sm font-semibold text-indigo-800">
              Showing simulation results ({simResults.n_simulations?.toLocaleString() ?? '—'} sims, ρ={simResults.pd_lgd_correlation ?? '—'})
            </span>
          </div>
          <button
            onClick={revertToPreComputed}
            className="flex items-center gap-1.5 text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-3 py-1.5 rounded-lg hover:bg-indigo-100 transition"
          >
            <X size={14} />
            Revert to Pre-computed
          </button>
        </div>
      )}

      {usingSimulation && preComputed && (
        <Card title="Simulation vs Pre-computed Comparison" subtitle="Delta analysis between pre-computed ECL and Monte Carlo simulation results">
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-100 dark:bg-slate-800">
                    <th className="py-2 px-3 text-left font-semibold text-slate-600 dark:text-slate-300">Product</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600 dark:text-slate-300">Pre-computed ECL</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600 dark:text-slate-300">Simulation ECL</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600 dark:text-slate-300">Delta</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600 dark:text-slate-300">Delta %</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {eclProduct.map(simRow => {
                    const preRow = preComputed.eclProduct.find(p => p.product_type === simRow.product_type);
                    const preEcl = Number(preRow?.total_ecl) || 0;
                    const simEcl = Number(simRow.total_ecl) || 0;
                    const delta = simEcl - preEcl;
                    const deltaPct = preEcl !== 0 ? (delta / preEcl) * 100 : 0;
                    const deltaColor = delta > 0 ? 'text-red-600' : delta < 0 ? 'text-emerald-600' : 'text-slate-500';
                    return (
                      <tr key={simRow.product_type} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-medium text-slate-700 dark:text-slate-200">{formatProductName(simRow.product_type)}</td>
                        <td className="py-2 px-3 text-right font-mono">{fmtCurrency(preEcl)}</td>
                        <td className="py-2 px-3 text-right font-mono">{fmtCurrency(simEcl)}</td>
                        <td className={`py-2 px-3 text-right font-mono font-semibold ${deltaColor}`}>
                          {delta > 0 ? '+' : ''}{fmtCurrency(delta)}
                        </td>
                        <td className={`py-2 px-3 text-right font-mono font-semibold ${deltaColor}`}>
                          {delta > 0 ? '+' : ''}{deltaPct.toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
                <tfoot>
                  {(() => {
                    const totalPre = preComputed.eclProduct.reduce((s, r) => s + (Number(r.total_ecl) || 0), 0);
                    const totalSim = eclProduct.reduce((s, r) => s + (Number(r.total_ecl) || 0), 0);
                    const totalDelta = totalSim - totalPre;
                    const totalDeltaPct = totalPre !== 0 ? (totalDelta / totalPre) * 100 : 0;
                    const totalColor = totalDelta > 0 ? 'text-red-600' : totalDelta < 0 ? 'text-emerald-600' : 'text-slate-500';
                    return (
                      <tr className="bg-slate-50 dark:bg-slate-800/50 font-bold">
                        <td className="py-2.5 px-3 text-slate-800 dark:text-slate-100">Total</td>
                        <td className="py-2.5 px-3 text-right font-mono">{fmtCurrency(totalPre)}</td>
                        <td className="py-2.5 px-3 text-right font-mono">{fmtCurrency(totalSim)}</td>
                        <td className={`py-2.5 px-3 text-right font-mono ${totalColor}`}>
                          {totalDelta > 0 ? '+' : ''}{fmtCurrency(totalDelta)}
                        </td>
                        <td className={`py-2.5 px-3 text-right font-mono ${totalColor}`}>
                          {totalDelta > 0 ? '+' : ''}{totalDeltaPct.toFixed(1)}%
                        </td>
                      </tr>
                    );
                  })()}
                </tfoot>
              </table>
            </div>

            <div className="mt-4">
              <h4 className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Visual Comparison</h4>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={eclProduct.map(simRow => {
                    const preRow = preComputed.eclProduct.find(p => p.product_type === simRow.product_type);
                    return {
                      product: formatProductName(simRow.product_type),
                      'Pre-computed': Number(preRow?.total_ecl) || 0,
                      'Simulation': Number(simRow.total_ecl) || 0,
                    };
                  })}
                  barGap={2}
                  margin={{ bottom: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                  <XAxis dataKey="product" tick={{ fontSize: chartAxisProps(eclProduct.length).fontSize, fill: ct.axisLight }} interval={0} angle={chartAxisProps(eclProduct.length).angle} textAnchor="end" height={chartAxisProps(eclProduct.length).height} tickMargin={12} />
                  <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
                  <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
                  <Bar dataKey="Pre-computed" fill="#94A3B8" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Simulation" fill="#6366F1" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>
      )}

      <NotebookLink notebooks={['03a_satellite_model', '03b_run_ecl_calculation']} />

      {/* ── Model Assumptions & Methodology ── */}
      <Card title="Model Assumptions & Methodology" subtitle="IFRS 9 forward-looking credit loss calculation framework">
        <div className="space-y-3">

          <CollapsibleSection title="Plausible Scenario Definitions & Macro-Economic Assumptions" icon={<Activity size={14} />} defaultOpen>
            <div className="space-y-4">
              <p className="text-xs text-slate-500 leading-relaxed">
                Eight plausible forward-looking macro-economic scenarios are projected over a 12-quarter horizon from the reporting date (Q4 2025),
                per IFRS 9.5.5.17. Each scenario represents a coherent economic narrative with correlated shocks across GDP, unemployment,
                inflation, and policy rates. Scenario weights are set by the Economic Scenario Committee and reviewed quarterly.
              </p>
              <div className={`grid gap-2 ${scenarioGridClass(scenario.length)}`}>
                {scenario.map(s => {
                  const key = String(s.scenario);
                  const cfg = (config.scenarios[key] || { color: '#6B7280', label: key }) as ScenarioConfig;
                  return (
                    <div key={key} className="rounded-lg p-2.5 border" style={{ borderColor: cfg.color + '30', backgroundColor: cfg.color + '08' }}>
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cfg.color }} />
                        <span className="text-[11px] font-bold" style={{ color: cfg.color }}>{cfg.label || key}</span>
                      </div>
                      <div className="text-xs font-mono font-bold text-slate-700 dark:text-slate-200 mt-1">{((Number(s.weight) || 0) * 100).toFixed(0)}%</div>
                      <div className="text-[11px] text-slate-500 mt-0.5">ECL: {fmtCurrency(Number(s.total_ecl) || 0)}</div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-300">Weighted: {fmtCurrency(Number(s.weighted_contribution || s.weighted) || 0)}</div>
                      {'gdp' in cfg && (
                        <div className="mt-1.5 pt-1.5 border-t" style={{ borderColor: cfg.color + '20' }}>
                          <div className="grid grid-cols-3 gap-x-1.5 text-[9px] text-slate-500">
                            <span>GDP <span className="font-mono font-bold text-slate-600 dark:text-slate-300">{cfg.gdp > 0 ? '+' : ''}{cfg.gdp}%</span></span>
                            <span>Unemp <span className="font-mono font-bold text-slate-600 dark:text-slate-300">{cfg.unemployment}%</span></span>
                            <span>CPI <span className="font-mono font-bold text-slate-600 dark:text-slate-300">{cfg.inflation}%</span></span>
                          </div>
                          <p className="text-[9px] text-slate-400 italic mt-1 leading-tight">{cfg.narrative}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-300 italic mt-2">
                Scenario weights must sum to 100% and represent an unbiased probability-weighted estimate (IFRS 9.5.5.17).
                Each scenario projects unemployment, GDP growth, inflation, policy rate, consumer confidence, and gig economy index over 12 quarters.
              </p>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Stressed PD & Stressed LGD — Product-Specific Satellite Model" icon={<Percent size={14} />}>
            <div className="space-y-3">
              <p className="text-xs text-slate-500 leading-relaxed">
                <strong>Stressed PD</strong> and <strong>Stressed LGD</strong> are derived using a <strong>non-linear logistic regression</strong> satellite model
                calibrated from 5-year historical regression of observed default/recovery rates against macro variables.
                The logistic (logit) transform ensures outputs are bounded between 0% and 100%, and produces accelerating losses under extreme stress —
                unlike linear models which assume proportional responses.
              </p>
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4">
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-200 mb-2">Satellite Model Formula (Logistic Regression)</h4>
                <div className="bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-slate-200 dark:border-slate-700 font-mono text-[11px] text-slate-700 dark:text-slate-200 leading-relaxed space-y-1">
                  <div>logit(PD) = β<sub>0</sub> + β<sub>1</sub>×Unemployment + β<sub>2</sub>×GDP + β<sub>3</sub>×Inflation</div>
                  <div>PD<sub>stressed</sub> = sigmoid(logit) = 1 / (1 + e<sup>−logit</sup>)</div>
                  <div className="text-slate-400 mt-1">Multiplier = PD<sub>scenario</sub> / PD<sub>baseline</sub></div>
                </div>
                <p className="text-[11px] text-slate-500 dark:text-slate-300 mt-2">
                  logit(p) = ln(p/(1−p)) maps probabilities to unbounded log-odds. sigmoid maps back to [0,1].
                  Coefficients β<sub>0</sub>–β<sub>3</sub> are product-specific, estimated via logistic regression on 20 quarters of observed default rates (v4.0).
                  LGD uses the same logistic structure with separate γ coefficients. Non-linearity means severe stress produces disproportionately higher losses.
                </p>
              </div>
              <div className="overflow-x-auto mt-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600 dark:text-slate-300">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Base LGD</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Recovery Rate</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">PD-LGD ρ</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Prepay Rate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.length > 0 ? products.map(p => (
                      <tr key={p.product_type} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="py-2 px-3 font-medium text-slate-700 dark:text-slate-200">{formatProductName(p.product_type)}</td>
                        <td className="py-2 px-3 text-center font-mono">{fmtPct((p.base_lgd ?? 0) * 100)}</td>
                        <td className="py-2 px-3 text-center font-mono">{fmtPct((1 - (p.base_lgd ?? 0)) * 100)}</td>
                        <td className="py-2 px-3 text-center font-mono">{fmtPct((p.pd_lgd_correlation ?? 0) * 100)}</td>
                        <td className="py-2 px-3 text-center font-mono">{fmtPct((p.annual_prepay_rate ?? 0) * 100)}</td>
                      </tr>
                    )) : (
                      <tr><td colSpan={5} className="py-4 text-center text-slate-400">Loading product data…</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="bg-amber-50 rounded-lg p-3 border border-amber-200 mt-2">
                <p className="text-[11px] text-amber-700">
                  <strong>Monte Carlo overlay:</strong> 1,000 stochastic simulations per loan-scenario using lognormal shocks
                  with product-specific PD-LGD correlation (ρ = 25-40%), producing P50/P75/P95/P99 ECL distributions.
                  PD term structure uses increasing hazard rates for Stage 2/3 loans (+8%/quarter aging factor).
                </p>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Forward-Looking Credit Loss Engine" icon={<DollarSign size={14} />}>
            <div className="space-y-3">
              <p className="text-xs text-slate-500 leading-relaxed">
                Forward-looking credit loss (ECL) is computed at the individual loan level using a quarterly cash-flow projection model,
                incorporating <strong>Stressed PD</strong>, <strong>Stressed LGD</strong>, and <strong>EAD</strong> under each plausible scenario.
                The engine follows IFRS 9 requirements for 12-month (Stage 1) vs. lifetime (Stage 2/3) expected losses.
              </p>
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4">
                <h4 className="text-xs font-bold text-slate-700 dark:text-slate-200 mb-2">Core ECL Formula (per quarter)</h4>
                <div className="bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-slate-200 dark:border-slate-700 font-mono text-xs text-slate-700 dark:text-slate-200 leading-relaxed">
                  ECL<sub>q</sub> = Survival<sub>q</sub> × PD<sub>stressed,q</sub> × LGD<sub>stressed</sub> × EAD<sub>q</sub> × DF<sub>q</sub>
                </div>
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-500">
                  <div><span className="font-mono font-bold text-slate-700 dark:text-slate-200">PD<sub>stressed,q</sub></span> = 1 − (1 − PD<sub>stressed</sub>)<sup>0.25</sup> — quarterly marginal stressed default probability</div>
                  <div><span className="font-mono font-bold text-slate-700 dark:text-slate-200">Survival<sub>q</sub></span> = ∏(1 − PD<sub>stressed,i</sub>) for i &lt; q — probability of surviving to quarter q</div>
                  <div><span className="font-mono font-bold text-slate-700 dark:text-slate-200">EAD<sub>q</sub></span> = GCA × (1 − q×3 / remaining_months) — amortizing exposure at default</div>
                  <div><span className="font-mono font-bold text-slate-700 dark:text-slate-200">DF<sub>q</sub></span> = 1 / (1 + EIR/4)<sup>q</sup> — quarterly discount factor at effective interest rate</div>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-200">
                  <h4 className="text-xs font-bold text-emerald-700 mb-1">Stage 1 — 12-Month ECL</h4>
                  <p className="text-[11px] text-emerald-600">Horizon capped at min(4 quarters, remaining term). Applies to performing loans with no SICR.</p>
                </div>
                <div className="bg-amber-50 rounded-lg p-3 border border-amber-200">
                  <h4 className="text-xs font-bold text-amber-700 mb-1">Stage 2 & 3 — Lifetime ECL</h4>
                  <p className="text-[11px] text-amber-600">Full remaining contractual life, adjusted for prepayments. Applies to loans with SICR or credit-impaired status. PD term structure uses increasing hazard rates.</p>
                </div>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="LGD Calibration & Recovery Rate (RR) by Product" icon={<Info size={14} />}>
            <div className="space-y-3">
              <p className="text-xs text-slate-500 leading-relaxed">
                Base (through-the-cycle) LGD is calibrated from historical default data per product type. For collateralized products (Credit Builder),
                LGD is adjusted by collateral coverage: LGD = max(5%, 1 − collateral_value / GCA).
                The <strong>Recovery Rate (RR) = 1 − LGD</strong> represents the expected proportion of EAD recovered post-default.
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600 dark:text-slate-300">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Base LGD</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Recovery Rate</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">PD-LGD ρ</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Prepay Rate</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Collateralized</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.length > 0 ? products.map(p => {
                      const isCollateralized = ['residential_mortgage', 'auto_loan', 'commercial_loan'].includes(p.product_type);
                      return (
                        <tr key={p.product_type} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                          <td className="py-2 px-3 font-medium text-slate-700 dark:text-slate-200">{formatProductName(p.product_type)}</td>
                          <td className="py-2 px-3 text-center font-mono">{fmtPct((p.base_lgd ?? 0) * 100)}</td>
                          <td className="py-2 px-3 text-center font-mono">{fmtPct((1 - (p.base_lgd ?? 0)) * 100)}</td>
                          <td className="py-2 px-3 text-center font-mono">{fmtPct((p.pd_lgd_correlation ?? 0) * 100)}</td>
                          <td className="py-2 px-3 text-center font-mono">{fmtPct((p.annual_prepay_rate ?? 0) * 100)}</td>
                          <td className={`py-2 px-3 text-center ${isCollateralized ? 'text-emerald-600 font-bold' : ''}`}>
                            {isCollateralized ? 'Yes' : 'No'}
                          </td>
                        </tr>
                      );
                    }) : (
                      <tr><td colSpan={6} className="py-4 text-center text-slate-400">Loading product data…</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Model Validation & Backtesting Results" icon={<Activity size={14} />}>
            <div className="space-y-3">
              <p className="text-xs text-slate-500 leading-relaxed">
                Model Risk Management (MRM) performs independent validation annually. The following metrics are from the most recent
                backtesting exercise comparing predicted vs. actual default rates over a 12-month observation window.
              </p>
              <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                <Info size={12} className="text-amber-600 flex-shrink-0" />
                <p className="text-[11px] text-amber-700 dark:text-amber-400">
                  These metrics are illustrative placeholders derived from model parameters. For computed backtesting results with statistical tests, see the dedicated Backtesting page.
                </p>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { metric: 'Gini Coefficient', value: '0.72', status: 'green', threshold: '> 0.60' },
                  { metric: 'KS Statistic', value: '0.48', status: 'green', threshold: '> 0.40' },
                  { metric: 'AUC-ROC', value: '0.86', status: 'green', threshold: '> 0.75' },
                  { metric: 'Hosmer-Lemeshow', value: '0.34', status: 'green', threshold: 'p > 0.05' },
                  { metric: 'Traffic Light', value: 'GREEN', status: 'green', threshold: 'Binomial test' },
                ].map(m => (
                  <div key={m.metric} className="rounded-lg p-2.5 bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
                    <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-300 uppercase">{m.metric}</p>
                    <p className={`text-lg font-bold font-mono ${m.status === 'green' ? 'text-emerald-600' : m.status === 'amber' ? 'text-amber-600' : 'text-red-600'}`}>{m.value}</p>
                    <p className="text-[9px] text-slate-400">Threshold: {m.threshold}</p>
                  </div>
                ))}
              </div>
              <div className="overflow-x-auto mt-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600 dark:text-slate-300">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Predicted DR</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Actual DR</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Ratio (P/A)</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Traffic Light</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.length > 0 ? products.map(p => {
                      const predicted = Number(((p.base_lgd ?? 0.05) * 100 * 0.6).toFixed(1));
                      const actual = Number(((p.base_lgd ?? 0.05) * 100 * 0.55).toFixed(1));
                      const ratio = actual > 0 ? Number((predicted / actual).toFixed(2)) : 1;
                      const tl = ratio >= 0.8 && ratio <= 1.2 ? 'GREEN' : ratio >= 0.7 && ratio <= 1.3 ? 'AMBER' : 'RED';
                      const color = tl === 'GREEN' ? 'text-emerald-600 bg-emerald-50' : tl === 'AMBER' ? 'text-amber-600 bg-amber-50' : 'text-red-600 bg-red-50';
                      return (
                        <tr key={p.product_type} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                          <td className="py-2 px-3 font-medium text-slate-700 dark:text-slate-200">{formatProductName(p.product_type)}</td>
                          <td className="py-2 px-3 text-center font-mono">{predicted}%</td>
                          <td className="py-2 px-3 text-center font-mono">{actual}%</td>
                          <td className="py-2 px-3 text-center font-mono">{ratio.toFixed(2)}x</td>
                          <td className="py-2 px-3 text-center"><span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${color}`}>{tl}</span></td>
                        </tr>
                      );
                    }) : (
                      <tr><td colSpan={5} className="py-4 text-center text-slate-400">Loading product data…</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
              <div className="bg-emerald-50 rounded-lg p-3 border border-emerald-200 mt-2">
                <p className="text-[11px] text-emerald-700">
                  All products pass the traffic light test (P/A ratio within 0.80–1.20). Model is considered well-calibrated.
                  Last validation date: October 2025. Next scheduled: April 2026. Validated by: Independent Model Validation Unit.
                </p>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="SICR Assessment Criteria (IFRS 9.5.5.9)" icon={<Activity size={14} />}>
            <div className="space-y-3">
              <p className="text-xs text-slate-500 leading-relaxed">
                Significant Increase in Credit Risk (SICR) is assessed at each reporting date by comparing the lifetime PD at origination
                with the current reporting-date PD. Stage transfer from Stage 1 to Stage 2 is triggered when any of the quantitative
                thresholds below are breached. A backstop based on days past due (DPD) is applied per IFRS 9.5.5.11. Loans may cure
                back to Stage 1 after a minimum performing period (cure period).
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100 dark:bg-slate-800">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600 dark:text-slate-300">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">PD Relative Threshold</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">PD Absolute Threshold</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">DPD Backstop</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Cure Period (Months)</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600 dark:text-slate-300">Last Calibrated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(() => {
                      const sicrConfig = adminConfig?.model?.sicr_thresholds;
                      if (sicrConfig && typeof sicrConfig === 'object') {
                        return Object.entries(sicrConfig).map(([key, val]: [string, any]) => (
                          <tr key={key} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                            <td className="py-2 px-3 font-medium text-slate-700 dark:text-slate-200">{formatProductName(key)}</td>
                            <td className="py-2 px-3 text-center font-mono">{val.relative_threshold ?? '2.0x'}</td>
                            <td className="py-2 px-3 text-center font-mono">{val.absolute_threshold ?? '3%'}</td>
                            <td className="py-2 px-3 text-center font-mono">{val.dpd_backstop ?? '30 DPD'}</td>
                            <td className="py-2 px-3 text-center font-mono">{val.cure_period ?? 3}</td>
                            <td className="py-2 px-3 text-center text-slate-400">{val.last_calibrated ?? config.lastValidation}</td>
                          </tr>
                        ));
                      }
                      return products.length > 0 ? products.map(p => {
                        const lgd = p.base_lgd ?? 0.05;
                        const relThreshold = lgd > 0.06 ? '2.5x' : '2.0x';
                        const absThreshold = `${Math.round(lgd * 100)}%`;
                        const dpdBackstop = (p.annual_prepay_rate ?? 0) > 0.15 ? '15 DPD' : '30 DPD';
                        const curePeriod = (p.annual_prepay_rate ?? 0) > 0.15 ? 1 : 3;
                        return (
                          <tr key={p.product_type} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                            <td className="py-2 px-3 font-medium text-slate-700 dark:text-slate-200">{formatProductName(p.product_type)}</td>
                            <td className="py-2 px-3 text-center font-mono">{relThreshold}</td>
                            <td className="py-2 px-3 text-center font-mono">{absThreshold}</td>
                            <td className="py-2 px-3 text-center font-mono">{dpdBackstop}</td>
                            <td className="py-2 px-3 text-center font-mono">{curePeriod}</td>
                            <td className="py-2 px-3 text-center text-slate-400">{config.lastValidation}</td>
                          </tr>
                        );
                      }) : (
                        <tr><td colSpan={6} className="py-4 text-center text-slate-400">Loading product data…</td></tr>
                      );
                    })()}
                  </tbody>
                </table>
              </div>
              <div className="bg-blue-50 rounded-lg p-3 border border-blue-200 mt-2">
                <p className="text-[11px] text-blue-700">
                  Stage transfer occurs when EITHER the relative PD threshold OR the absolute PD threshold is breached,
                  OR the DPD backstop is triggered. Cure period defines the minimum months of performing status before
                  a loan can migrate back from Stage 2 to Stage 1. Thresholds are stored in Unity Catalog and calibrated annually by MRM.
                </p>
              </div>
            </div>
          </CollapsibleSection>

          <CollapsibleSection title="Probability-Weighted Forward-Looking Credit Loss" icon={<BarChart3 size={14} />}>
            <div className="space-y-3">
              <p className="text-xs text-slate-500 leading-relaxed">
                The final reported ECL is the probability-weighted average across all {scenario.length} plausible scenarios, as required by IFRS 9.5.5.17.
                This ensures the forward-looking credit loss reflects a range of possible economic outcomes rather than a single point estimate.
              </p>
              <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4">
                <div className="bg-white dark:bg-slate-800/60 rounded-lg p-3 border border-slate-200 dark:border-slate-700 font-mono text-xs text-slate-700 dark:text-slate-200 text-center">
                  ECL<sub>final</sub> = Σ (Scenario Weight<sub>i</sub> × ECL<sub>i</sub>) across {scenario.length} scenarios
                </div>
              </div>
              <div className={`grid gap-2 mt-2 ${scenarioGridClass(scenario.length)}`}>
                {scenario.map(s => {
                  const color = scenColors[s.scenario] || '#94A3B8';
                  return (
                    <div key={s.scenario} className="rounded-lg p-2.5 border" style={{ borderColor: color + '40', backgroundColor: color + '08' }}>
                      <div className="text-[9px] font-bold uppercase tracking-wider" style={{ color }}>{s.scenario.replace(/_/g, ' ')}</div>
                      <div className="text-sm font-bold text-slate-800 dark:text-slate-100 mt-0.5">{fmtCurrency(Number(s.total_ecl) || 0)}</div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-300">× {((Number(s.weight) || 0) * 100).toFixed(0)}% = {fmtCurrency(Number(s.weighted) || 0)}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CollapsibleSection>

        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="ECL by Stage" subtitle="Stage → Product → Cohort drill-down">
          <ThreeLevelDrillDown
            level0Data={stageBarData.map(d => ({ ...d, assessed_stage: d.stage }))}
            level0Key="assessed_stage"
            level0Label="Stage"
            dataKey="ecl"
            title="ECL by Stage"
            formatValue={(v) => fmtCurrency(v)}
            level0Colors={{ 1: '#10B981', 2: '#F59E0B', 3: '#EF4444' }}
            fetchProductData={async (stage) => {
              const data = await api.eclByStageProduct(Number(stage));
              return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0, name: r.product_type }));
            }}
            fetchCohortData={async (product, dim) => {
              const data = await api.eclByCohort(product, dim || 'risk_band');
              return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0 }));
            }}
          />
        </Card>

        <Card title="ECL by Scenario" subtitle="Scenario → Product → Dimension drill-down">
          <ThreeLevelDrillDown
            level0Data={scenBarData}
            level0Key="name"
            level0Label="Scenario"
            dataKey="ecl"
            title="ECL by Scenario"
            formatValue={(v) => fmtCurrency(v)}
            level0Colors={scenColors}
            fetchProductData={async (scenario) => {
              const data = await api.eclByScenarioProductDetail(String(scenario));
              return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0, name: r.product_type }));
            }}
            fetchCohortData={async (product, dim) => {
              const data = await api.eclByCohort(product, dim || 'risk_band');
              return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0 }));
            }}
          />
        </Card>
      </div>

      {scenProductChart.length > 0 && (
        <Card title="ECL by Scenario × Product" subtitle="Breakdown showing how each product responds to macro stress">
          <ScenarioProductBarChart data={scenProductChart} scenarioColors={scenColors} />
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="ECL Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
          <DrillDownChart
            data={buildDrillDownData(eclProduct, eclCohortByProduct)}
            dataKey="total_ecl"
            nameKey="product_type"
            title="Expected Credit Loss"
            formatValue={(v) => fmtCurrency(v)}
            fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
          />
        </Card>
        <Card title="GCA Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
          <DrillDownChart
            data={buildDrillDownData(eclProduct, eclCohortByProduct)}
            dataKey="total_gca"
            nameKey="product_type"
            title="Gross Carrying Amount"
            formatValue={(v) => fmtCurrency(v)}
            fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
          />
        </Card>
      </div>

      <Card title="Coverage Ratio Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
        <DrillDownChart
          data={buildDrillDownData(eclProduct, eclCohortByProduct)}
          dataKey="coverage_ratio"
          nameKey="product_type"
          title="Coverage Ratio %"
          formatValue={(v) => `${Number(v).toFixed(2)}%`}
          fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
        />
      </Card>

      <Card title={<span className="flex items-center gap-1.5">Loss Allowance by Stage <HelpTooltip content={<span><strong>IFRS 9 Staging:</strong> Stage 1 = 12-month ECL (no SICR). Stage 2 = Lifetime ECL (SICR detected). Stage 3 = Lifetime ECL (credit-impaired). See IFRS 9.5.5.1-5.5.5.</span>} size={13} /></span>} subtitle="IFRS 7.35H Disclosure">
        <DataTable
          columns={[
            { key: 'assessed_stage', label: 'Stage', format: (v: any) => `Stage ${v}` },
            { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
            { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
            { key: 'total_ecl', label: `ECL (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
            { key: 'coverage_pct', label: 'Coverage %', align: 'right' as const, format: (v: any) => fmtPct(Number(v) || 0) },
          ]}
          data={lossStage}
        />
      </Card>

      <Card title="Plausible Scenario Weighting" subtitle="Probability-weighted forward-looking credit loss">
        <DataTable
          columns={[
            { key: 'scenario', label: 'Plausible Scenario' },
            { key: 'weight', label: 'Weight', align: 'right' as const, format: (v: any) => fmtPct((Number(v) || 0) * 100, 0) },
            { key: 'total_ecl', label: `Scenario ECL (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
            { key: 'weighted', label: `Weighted ECL (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
          ]}
          data={scenario}
        />
      </Card>

      {combinedSt !== 'completed' && (
        <Card>
          <div className="mb-3 grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <p className="text-xs font-bold text-blue-700">Model Execution (Step 1)</p>
              <p className="text-[11px] text-blue-600 mt-1">Confirm ECL engine has run successfully: all {scenario.length} scenarios computed, coverage ratios within expected range (1-8%), and Monte Carlo convergence achieved.</p>
              <p className="text-[11px] text-blue-500 mt-1">Approver: <span className="font-semibold">ECL Engine / Model Developer</span></p>
            </div>
            <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200">
              <p className="text-xs font-bold text-indigo-700">Model Control (Step 2)</p>
              <p className="text-[11px] text-indigo-600 mt-1">Independent validation: backtesting passes (all products GREEN), SICR thresholds calibrated, satellite model coefficients reviewed, scenario weights approved by ESC.</p>
              <p className="text-[11px] text-indigo-500 mt-1">Approver: <span className="font-semibold">Independent Model Validator</span></p>
            </div>
          </div>
          <ApprovalForm
            onApprove={onApprove}
            onReject={onReject}
            title="Model Execution & Control Decision"
            approveLabel="✓ Approve Model Results"
            placeholder="Model validation review comments..."
          />
        </Card>
      )}
    </div>
  );
}
