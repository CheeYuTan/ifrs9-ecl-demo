import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import { useChartTheme } from '../../lib/chartTheme';
import { Shield, Zap, AlertTriangle, Activity, Dice5, Play, Loader2, Info } from 'lucide-react';
import KpiCard from '../../components/KpiCard';
import Card from '../../components/Card';
import DataTable from '../../components/DataTable';
import DrillDownChart from '../../components/DrillDownChart';
import { api } from '../../lib/api';
import { fmtCurrency, fmtPct, fmtNumber } from '../../lib/format';
import { config } from '../../lib/config';
import { buildDrillDownData } from '../../lib/chartUtils';
import { safeFmt } from './types';
import type { StressedDatum, WaterfallDatum } from './types';

interface Props {
  pdShock: number;
  lgdShock: number;
  eadShock: number;
  setPdShock: (v: number) => void;
  setLgdShock: (v: number) => void;
  setEadShock: (v: number) => void;
  sensMode: 'quick' | 'full';
  setSensMode: (v: 'quick' | 'full') => void;
  baseEcl: number;
  baseGca: number;
  totalStressedEcl: number;
  totalDelta: number;
  deltaPct: number;
  stressedData: StressedDatum[];
  sensitivityWaterfall: WaterfallDatum[];
  eclCohortByProduct: Record<string, any[]>;
  /* full sim */
  simDefaults: any;
  fullSimLoading: boolean;
  fullSimResult: any;
  fullSimEcl: number | null;
  fullSimError: string | null;
  runStressedSimulation: () => void;
}

export default function SensitivityTab({
  pdShock, lgdShock, eadShock, setPdShock, setLgdShock, setEadShock,
  sensMode, setSensMode,
  baseEcl, baseGca, totalStressedEcl, totalDelta, deltaPct,
  stressedData, sensitivityWaterfall, eclCohortByProduct,
  simDefaults, fullSimLoading, fullSimResult, fullSimEcl, fullSimError,
  runStressedSimulation,
}: Props) {
  const ct = useChartTheme();

  return (
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
                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer brand-range" />
              <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                <span>-50%</span><span>0%</span><span>+50%</span><span>+100%</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          <button onClick={() => { setPdShock(0); setLgdShock(0); setEadShock(0); }}
            className="px-3 py-1.5 text-xs font-semibold text-slate-500 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Reset</button>
          <button onClick={() => { setPdShock(20); setLgdShock(10); setEadShock(5); }}
            className="px-3 py-1.5 text-xs font-semibold text-amber-600 bg-amber-50 rounded-lg hover:bg-amber-100 transition">Adverse</button>
          <button onClick={() => { setPdShock(50); setLgdShock(25); setEadShock(15); }}
            className="px-3 py-1.5 text-xs font-semibold text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition">Severe</button>
          <button onClick={() => { setPdShock(100); setLgdShock(50); setEadShock(30); }}
            className="px-3 py-1.5 text-xs font-semibold text-red-700 bg-red-100 rounded-lg hover:bg-red-200 transition">Extreme</button>
        </div>
      </Card>

      {/* Mode toggle */}
      <div className="flex items-center gap-3 bg-white dark:bg-slate-800/80 rounded-xl shadow-sm p-3">
        <div className="flex bg-slate-100 dark:bg-slate-800 rounded-lg p-0.5">
          <button onClick={() => setSensMode('quick')}
            className={`px-4 py-2 text-xs font-semibold rounded-md transition-all ${sensMode === 'quick' ? 'bg-white dark:bg-slate-700 text-navy dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}>
            <Activity size={12} className="inline mr-1.5 -mt-0.5" />Quick Estimate
          </button>
          <button onClick={() => setSensMode('full')}
            className={`px-4 py-2 text-xs font-semibold rounded-md transition-all ${sensMode === 'full' ? 'bg-white dark:bg-slate-700 text-navy dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'}`}>
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
                <BarChart data={sensitivityWaterfall} barSize={45} margin={{ bottom: 20 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: ct.axisLight }} interval={0} angle={-10} textAnchor="end" height={50} tickMargin={12} />
                  <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={(v: any) => fmtCurrency(Math.abs(Number(v) || 0))} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
                  <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                    {sensitivityWaterfall.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Base vs Stressed ECL" subtitle="Click a product → drill by risk band, age group, etc.">
              <DrillDownChart
                data={buildDrillDownData(stressedData, eclCohortByProduct)}
                dataKey="stressed_ecl"
                nameKey="product_type"
                title="Stressed ECL by Product → Cohort"
                formatValue={(v) => fmtCurrency(v)}
                fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
              />
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
                      <tr className="border-b border-slate-200 dark:border-slate-700">
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
                        <tr key={p.label} className="border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800">
                          <td className="py-2 px-3 text-xs font-medium text-slate-700 dark:text-slate-200">{p.label}</td>
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

              {(fullSimResult.loss_allowance_by_stage || fullSimResult.stage_summary || []).length > 0 && (
                <Card title="Stressed Simulation — ECL by Stage" subtitle="Monte Carlo results with shocked PD/LGD bounds (EAD multiplier applied)">
                  <DataTable
                    columns={[
                      { key: 'assessed_stage', label: 'Stage', format: (v: any) => `Stage ${v}` },
                      { key: 'loan_count', label: 'Loans', align: 'right' as const, format: (v: any) => fmtNumber(Number(v) || 0) },
                      { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency(Number(v) || 0) },
                      { key: 'total_ecl', label: `Simulated ECL (${config.currencySymbol})`, align: 'right' as const, format: (v: any) => fmtCurrency((Number(v) || 0) * (1 + (fullSimResult.eadShock || 0) / 100)) },
                      { key: 'coverage_pct', label: 'Coverage %', align: 'right' as const, format: (v: any) => fmtPct(Number(v) || 0) },
                    ]}
                    data={fullSimResult.loss_allowance_by_stage || fullSimResult.stage_summary}
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
                  <div className="bg-slate-50 dark:bg-slate-800/60 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
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
                      <div className="flex justify-between"><span className="text-indigo-600">Delta %</span><span className="font-mono font-semibold text-indigo-800">{baseEcl > 0 ? ((fullSimEcl - baseEcl) / baseEcl * 100 >= 0 ? '+' : '') + ((fullSimEcl - baseEcl) / baseEcl * 100).toFixed(1) + '%' : '\u2014'}</span></div>
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
            <div className="bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 rounded-xl p-8 text-center">
              <Dice5 size={32} className="mx-auto text-slate-300 mb-3" />
              <p className="text-sm text-slate-500 font-medium">Configure shocks above and click "Run Stressed Simulation"</p>
              <p className="text-xs text-slate-400 mt-1">The engine will re-run the full Monte Carlo with stressed PD/LGD bounds</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
