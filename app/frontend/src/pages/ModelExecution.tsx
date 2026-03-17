import { useEffect, useState, useCallback } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, Legend } from 'recharts';
import { DollarSign, Percent, Activity, BarChart3, Info, ChevronDown, ChevronUp, FlaskConical, X } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import LockedBanner from '../components/LockedBanner';
import StatusBadge from '../components/StatusBadge';
import SimulationPanel from '../components/SimulationPanel';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtNumber, fmtPct } from '../lib/format';
import { config, type ScenarioConfig } from '../lib/config';

const STAGE_COLORS: Record<number, string> = { 1: '#10B981', 2: '#F59E0B', 3: '#EF4444' };

function formatProductName(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}
const SCEN_COLORS: Record<string, string> = {
  ...Object.fromEntries(Object.entries(config.scenarios).map(([k, v]) => [k, v.color])),
  base: '#10B981',
};

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}

function CollapsibleSection({ title, icon, children, defaultOpen = false }: { title: string; icon: React.ReactNode; children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-5 py-3.5 bg-slate-50 hover:bg-slate-100 transition">
        <div className="flex items-center gap-2.5">
          <span className="text-slate-400">{icon}</span>
          <span className="text-sm font-bold text-slate-700">{title}</span>
        </div>
        {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </button>
      {open && <div className="px-5 py-4 bg-white">{children}</div>}
    </div>
  );
}

export default function ModelExecution({ project, onApprove, onReject }: Props) {
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [scenario, setScenario] = useState<any[]>([]);
  const [lossStage, setLossStage] = useState<any[]>([]);
  const [scenByProduct, setScenByProduct] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  const [simResults, setSimResults] = useState<any>(null);
  const [usingSimulation, setUsingSimulation] = useState(false);
  const [preComputed, setPreComputed] = useState<{ eclProduct: any[]; scenario: any[]; lossStage: any[]; scenByProduct: any[] } | null>(null);
  const [products, setProducts] = useState<any[]>([]);

  useEffect(() => {
    api.simulationDefaults()
      .then((data: any) => { if (data.products) setProducts(data.products); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!project || project.current_step < 3) return;
    Promise.all([api.eclByProduct(), api.scenarioSummary(), api.lossAllowanceByStage(), api.eclByScenarioProduct()])
      .then(([ep, sc, ls, sp]) => {
        setEclProduct(ep); setScenario(sc); setLossStage(ls); setScenByProduct(sp);
        setPreComputed({ eclProduct: ep, scenario: sc, lossStage: ls, scenByProduct: sp });
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

  if (!project || project.current_step < 3) return <LockedBanner />;
  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>;

  const totalEcl = eclProduct.reduce((s, r) => s + (Number(r.total_ecl) || 0), 0);
  const totalGca = eclProduct.reduce((s, r) => s + (Number(r.total_gca) || 0), 0);
  const coverage = totalGca > 0 ? (totalEcl / totalGca * 100) : 0;
  const stepSt = project.step_status.model_execution || 'pending';
  const mcSt = project.step_status.model_control || 'pending';
  const combinedSt = mcSt === 'completed' ? 'completed' : stepSt;

  const stageBarData = lossStage.map(s => ({ name: `Stage ${s.assessed_stage}`, ecl: Number(s.total_ecl) || 0, stage: s.assessed_stage }));
  const scenBarData = scenario.map(s => ({ name: s.scenario, ecl: Number(s.total_ecl) || 0, weighted: Number(s.weighted) || 0 }));

  const scenProductChart = (() => {
    const products = [...new Set(scenByProduct.map(r => r.product_type))];
    const scenarios = [...new Set(scenByProduct.map(r => r.scenario))];
    return products.map(p => {
      const row: any = { product: String(p).replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) };
      scenarios.forEach(s => {
        const match = scenByProduct.find(r => r.product_type === p && r.scenario === s);
        row[s] = Number(match?.total_ecl) || 0;
      });
      return row;
    });
  })();

  const handleAction = async (type: 'approve' | 'reject') => {
    if (type === 'reject' && !comment) return;
    setActing(true);
    try {
      type === 'approve' ? await onApprove(comment) : await onReject(comment);
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Model Execution & Control</h2>
          <p className="text-sm text-slate-400 mt-1">Forward-looking credit loss engine — Stressed PD, Stressed LGD, EAD across plausible scenarios</p>
        </div>
        <StatusBadge status={combinedSt} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total ECL" value={fmtCurrency(totalEcl)} subtitle="Probability-weighted" color="red" icon={<DollarSign size={20} />} />
        <KpiCard title="Coverage" value={fmtPct(coverage)} subtitle="ECL / GCA" color="indigo" icon={<Percent size={20} />} />
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
                  <tr className="bg-slate-100">
                    <th className="py-2 px-3 text-left font-semibold text-slate-600">Product</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600">Pre-computed ECL</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600">Simulation ECL</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600">Delta</th>
                    <th className="py-2 px-3 text-right font-semibold text-slate-600">Delta %</th>
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
                      <tr key={simRow.product_type} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-medium text-slate-700">{formatProductName(simRow.product_type)}</td>
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
                      <tr className="bg-slate-50 font-bold">
                        <td className="py-2.5 px-3 text-slate-800">Total</td>
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
              <h4 className="text-xs font-bold text-slate-600 mb-3">Visual Comparison</h4>
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
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="product" tick={{ fontSize: 9 }} interval={0} angle={-10} textAnchor="end" height={55} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="Pre-computed" fill="#94A3B8" radius={[3, 3, 0, 0]} />
                  <Bar dataKey="Simulation" fill="#6366F1" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>
      )}

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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {scenario.map(s => {
                  const key = String(s.scenario);
                  const cfg = (config.scenarios[key] || { color: '#6B7280', label: key }) as ScenarioConfig;
                  return (
                    <div key={key} className="rounded-lg p-2.5 border" style={{ borderColor: cfg.color + '30', backgroundColor: cfg.color + '08' }}>
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: cfg.color }} />
                        <span className="text-[10px] font-bold" style={{ color: cfg.color }}>{cfg.label || key}</span>
                      </div>
                      <div className="text-xs font-mono font-bold text-slate-700 mt-1">{((Number(s.weight) || 0) * 100).toFixed(0)}%</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">ECL: {fmtCurrency(Number(s.total_ecl) || 0)}</div>
                      <div className="text-[10px] text-slate-400">Weighted: {fmtCurrency(Number(s.weighted_contribution || s.weighted) || 0)}</div>
                      {'gdp' in cfg && (
                        <div className="mt-1.5 pt-1.5 border-t" style={{ borderColor: cfg.color + '20' }}>
                          <div className="grid grid-cols-3 gap-x-1.5 text-[9px] text-slate-500">
                            <span>GDP <span className="font-mono font-bold text-slate-600">{cfg.gdp > 0 ? '+' : ''}{cfg.gdp}%</span></span>
                            <span>Unemp <span className="font-mono font-bold text-slate-600">{cfg.unemployment}%</span></span>
                            <span>CPI <span className="font-mono font-bold text-slate-600">{cfg.inflation}%</span></span>
                          </div>
                          <p className="text-[9px] text-slate-400 italic mt-1 leading-tight">{cfg.narrative}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              <p className="text-[10px] text-slate-400 italic mt-2">
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
              <div className="bg-slate-50 rounded-lg p-4">
                <h4 className="text-xs font-bold text-slate-700 mb-2">Satellite Model Formula (Logistic Regression)</h4>
                <div className="bg-white rounded-lg p-3 border border-slate-200 font-mono text-[11px] text-slate-700 leading-relaxed space-y-1">
                  <div>logit(PD) = β<sub>0</sub> + β<sub>1</sub>×Unemployment + β<sub>2</sub>×GDP + β<sub>3</sub>×Inflation</div>
                  <div>PD<sub>stressed</sub> = sigmoid(logit) = 1 / (1 + e<sup>−logit</sup>)</div>
                  <div className="text-slate-400 mt-1">Multiplier = PD<sub>scenario</sub> / PD<sub>baseline</sub></div>
                </div>
                <p className="text-[10px] text-slate-400 mt-2">
                  logit(p) = ln(p/(1−p)) maps probabilities to unbounded log-odds. sigmoid maps back to [0,1].
                  Coefficients β<sub>0</sub>–β<sub>3</sub> are product-specific, estimated via logistic regression on 20 quarters of observed default rates (v4.0).
                  LGD uses the same logistic structure with separate γ coefficients. Non-linearity means severe stress produces disproportionately higher losses.
                </p>
              </div>
              <div className="overflow-x-auto mt-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Base LGD</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Recovery Rate</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">PD-LGD ρ</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Prepay Rate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.length > 0 ? products.map(p => (
                      <tr key={p.product_type} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-medium text-slate-700">{formatProductName(p.product_type)}</td>
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
              <div className="bg-slate-50 rounded-lg p-4">
                <h4 className="text-xs font-bold text-slate-700 mb-2">Core ECL Formula (per quarter)</h4>
                <div className="bg-white rounded-lg p-3 border border-slate-200 font-mono text-xs text-slate-700 leading-relaxed">
                  ECL<sub>q</sub> = Survival<sub>q</sub> × PD<sub>stressed,q</sub> × LGD<sub>stressed</sub> × EAD<sub>q</sub> × DF<sub>q</sub>
                </div>
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-500">
                  <div><span className="font-mono font-bold text-slate-700">PD<sub>stressed,q</sub></span> = 1 − (1 − PD<sub>stressed</sub>)<sup>0.25</sup> — quarterly marginal stressed default probability</div>
                  <div><span className="font-mono font-bold text-slate-700">Survival<sub>q</sub></span> = ∏(1 − PD<sub>stressed,i</sub>) for i &lt; q — probability of surviving to quarter q</div>
                  <div><span className="font-mono font-bold text-slate-700">EAD<sub>q</sub></span> = GCA × (1 − q×3 / remaining_months) — amortizing exposure at default</div>
                  <div><span className="font-mono font-bold text-slate-700">DF<sub>q</sub></span> = 1 / (1 + EIR/4)<sup>q</sup> — quarterly discount factor at effective interest rate</div>
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
                    <tr className="bg-slate-100">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Base LGD</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Recovery Rate</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">PD-LGD ρ</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Prepay Rate</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Collateralized</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {products.length > 0 ? products.map(p => {
                      const isCollateralized = p.product_type === 'credit_builder';
                      return (
                        <tr key={p.product_type} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-medium text-slate-700">{formatProductName(p.product_type)}</td>
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
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                {[
                  { metric: 'Gini Coefficient', value: '0.72', status: 'green', threshold: '> 0.60' },
                  { metric: 'KS Statistic', value: '0.48', status: 'green', threshold: '> 0.40' },
                  { metric: 'AUC-ROC', value: '0.86', status: 'green', threshold: '> 0.75' },
                  { metric: 'Hosmer-Lemeshow', value: '0.34', status: 'green', threshold: 'p > 0.05' },
                  { metric: 'Traffic Light', value: 'GREEN', status: 'green', threshold: 'Binomial test' },
                ].map(m => (
                  <div key={m.metric} className="rounded-lg p-2.5 bg-slate-50 border border-slate-100">
                    <p className="text-[10px] font-semibold text-slate-400 uppercase">{m.metric}</p>
                    <p className={`text-lg font-bold font-mono ${m.status === 'green' ? 'text-emerald-600' : m.status === 'amber' ? 'text-amber-600' : 'text-red-600'}`}>{m.value}</p>
                    <p className="text-[9px] text-slate-400">Threshold: {m.threshold}</p>
                  </div>
                ))}
              </div>
              <div className="overflow-x-auto mt-3">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-100">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Predicted DR</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Actual DR</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Ratio (P/A)</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Traffic Light</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {[
                      { product: 'Credit Builder', predicted: 3.2, actual: 2.8, ratio: 1.14 },
                      { product: 'Emergency Microloan', predicted: 8.5, actual: 9.1, ratio: 0.93 },
                      { product: 'Career Transition', predicted: 5.1, actual: 4.7, ratio: 1.09 },
                      { product: 'BNPL Professional', predicted: 6.8, actual: 7.2, ratio: 0.94 },
                      { product: 'Payroll Advance', predicted: 4.2, actual: 3.9, ratio: 1.08 },
                    ].map(row => {
                      const tl = row.ratio >= 0.8 && row.ratio <= 1.2 ? 'GREEN' : row.ratio >= 0.7 && row.ratio <= 1.3 ? 'AMBER' : 'RED';
                      const color = tl === 'GREEN' ? 'text-emerald-600 bg-emerald-50' : tl === 'AMBER' ? 'text-amber-600 bg-amber-50' : 'text-red-600 bg-red-50';
                      return (
                        <tr key={row.product} className="hover:bg-slate-50">
                          <td className="py-2 px-3 font-medium text-slate-700">{row.product}</td>
                          <td className="py-2 px-3 text-center font-mono">{row.predicted}%</td>
                          <td className="py-2 px-3 text-center font-mono">{row.actual}%</td>
                          <td className="py-2 px-3 text-center font-mono">{row.ratio.toFixed(2)}x</td>
                          <td className="py-2 px-3 text-center"><span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${color}`}>{tl}</span></td>
                        </tr>
                      );
                    })}
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
                    <tr className="bg-slate-100">
                      <th className="py-2 px-3 text-left font-semibold text-slate-600">Product</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">PD Relative Threshold</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">PD Absolute Threshold</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">DPD Backstop</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Cure Period (Months)</th>
                      <th className="py-2 px-3 text-center font-semibold text-slate-600">Last Calibrated</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {[
                      { product: 'Credit Builder', relative: '2.0x', absolute: '3%', dpd: '30 DPD', cure: 3, calibrated: 'Oct 2025' },
                      { product: 'Emergency Microloan', relative: '2.5x', absolute: '5%', dpd: '30 DPD', cure: 2, calibrated: 'Oct 2025' },
                      { product: 'Career Transition', relative: '2.0x', absolute: '4%', dpd: '30 DPD', cure: 3, calibrated: 'Oct 2025' },
                      { product: 'BNPL Professional', relative: '2.5x', absolute: '4%', dpd: '30 DPD', cure: 2, calibrated: 'Oct 2025' },
                      { product: 'Payroll Advance', relative: '3.0x', absolute: '6%', dpd: '15 DPD', cure: 1, calibrated: 'Oct 2025' },
                    ].map(row => (
                      <tr key={row.product} className="hover:bg-slate-50">
                        <td className="py-2 px-3 font-medium text-slate-700">{row.product}</td>
                        <td className="py-2 px-3 text-center font-mono">{row.relative}</td>
                        <td className="py-2 px-3 text-center font-mono">{row.absolute}</td>
                        <td className="py-2 px-3 text-center font-mono">{row.dpd}</td>
                        <td className="py-2 px-3 text-center font-mono">{row.cure}</td>
                        <td className="py-2 px-3 text-center text-slate-400">{row.calibrated}</td>
                      </tr>
                    ))}
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
              <div className="bg-slate-50 rounded-lg p-4">
                <div className="bg-white rounded-lg p-3 border border-slate-200 font-mono text-xs text-slate-700 text-center">
                  ECL<sub>final</sub> = Σ (Scenario Weight<sub>i</sub> × ECL<sub>i</sub>) across {scenario.length} scenarios
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-2">
                {scenario.map(s => {
                  const color = SCEN_COLORS[s.scenario] || '#94A3B8';
                  return (
                    <div key={s.scenario} className="rounded-lg p-2.5 border" style={{ borderColor: color + '40', backgroundColor: color + '08' }}>
                      <div className="text-[9px] font-bold uppercase tracking-wider truncate" style={{ color }}>{s.scenario.replace(/_/g, ' ')}</div>
                      <div className="text-sm font-bold text-slate-800 mt-0.5">{fmtCurrency(Number(s.total_ecl) || 0)}</div>
                      <div className="text-[10px] text-slate-400">× {((Number(s.weight) || 0) * 100).toFixed(0)}% = {fmtCurrency(Number(s.weighted) || 0)}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </CollapsibleSection>

        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="ECL by Stage" subtitle="IFRS 9 three-stage model">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={stageBarData} barSize={50}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
              <Bar dataKey="ecl" radius={[6, 6, 0, 0]}>
                {stageBarData.map((d, i) => <Cell key={i} fill={STAGE_COLORS[d.stage] || '#94A3B8'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="ECL by Scenario" subtitle="Macro-economic scenarios">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={scenBarData} barSize={50}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
              <Bar dataKey="ecl" radius={[6, 6, 0, 0]}>
                {scenBarData.map((d, i) => <Cell key={i} fill={SCEN_COLORS[d.name] || '#94A3B8'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {scenProductChart.length > 0 && (
        <Card title="ECL by Scenario × Product" subtitle="Breakdown showing how each product responds to macro stress">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={scenProductChart} barGap={2}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="product" tick={{ fontSize: 9 }} interval={0} angle={-10} textAnchor="end" height={55} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
              <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              {Object.entries(SCEN_COLORS).map(([key, color]) => {
                const hasData = scenProductChart.some((r: any) => r[key] !== undefined);
                if (!hasData) return null;
                return <Bar key={key} dataKey={key} name={key.replace(/_/g, ' ')} fill={color} radius={[2, 2, 0, 0]} />;
              })}
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}

      <Card title="Loss Allowance by Stage" subtitle="IFRS 7.35H Disclosure">
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
          <h3 className="text-sm font-bold text-slate-700 mb-2">Model Execution & Control Decision</h3>
          <div className="mb-3 grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
              <p className="text-xs font-bold text-blue-700">Model Execution (Step 1)</p>
              <p className="text-[10px] text-blue-600 mt-1">Confirm ECL engine has run successfully: all {scenario.length} scenarios computed, coverage ratios within expected range (1-8%), and Monte Carlo convergence achieved.</p>
              <p className="text-[10px] text-blue-500 mt-1">Approver: <span className="font-semibold">ECL Engine / Model Developer</span></p>
            </div>
            <div className="p-3 rounded-lg bg-indigo-50 border border-indigo-200">
              <p className="text-xs font-bold text-indigo-700">Model Control (Step 2)</p>
              <p className="text-[10px] text-indigo-600 mt-1">Independent validation: backtesting passes (all products GREEN), SICR thresholds calibrated, satellite model coefficients reviewed, scenario weights approved by ESC.</p>
              <p className="text-[10px] text-indigo-500 mt-1">Approver: <span className="font-semibold">Independent Model Validator</span></p>
            </div>
          </div>
          <textarea value={comment} onChange={e => setComment(e.target.value)} rows={2}
            placeholder="Model validation review comments..."
            className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none mb-3" />
          <div className="flex gap-3">
            <button onClick={() => handleAction('approve')} disabled={acting}
              className="px-5 py-2.5 bg-emerald-500 text-white text-sm font-semibold rounded-lg hover:bg-emerald-600 disabled:opacity-50 transition shadow-sm">
              {acting ? 'Processing...' : '✓ Approve Model Results'}
            </button>
            <button onClick={() => handleAction('reject')} disabled={acting || !comment}
              className="px-5 py-2.5 bg-white text-red-500 text-sm font-semibold rounded-lg border border-red-200 hover:bg-red-50 disabled:opacity-40 transition">
              ✗ Reject
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
