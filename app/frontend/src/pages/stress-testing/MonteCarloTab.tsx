import Card from '../../components/Card';
import DataTable from '../../components/DataTable';
import DrillDownChart from '../../components/DrillDownChart';
import ThreeLevelDrillDown from '../../components/ThreeLevelDrillDown';
import ScenarioProductBarChart from '../../components/ScenarioProductBarChart';
import { api } from '../../lib/api';
import { fmtCurrency, fmtNumber } from '../../lib/format';
import { buildDrillDownData } from '../../lib/chartUtils';
import type { McChartDatum } from './types';

interface Props {
  mcChartData: McChartDatum[];
  SCENARIO_COLORS: Record<string, string>;
  SCENARIO_LABELS: Record<string, string>;
  scenarioByProduct: any[];
  eclProduct: any[];
  eclCohortByProduct: Record<string, any[]>;
  nScenarios: number;
}

export default function MonteCarloTab({
  mcChartData, SCENARIO_COLORS, SCENARIO_LABELS,
  scenarioByProduct, eclProduct, eclCohortByProduct, nScenarios,
}: Props) {
  return (
    <div className="space-y-6">
      <Card title="Forward-Looking Credit Loss Distribution" subtitle="Monte Carlo simulation: Mean ECL by scenario → Product → Cohort drill-down">
        {mcChartData.length > 0 ? (
          <ThreeLevelDrillDown
            level0Data={mcChartData.map(d => ({ ...d, name: d.scenario, mean_ecl: d.mean }))}
            level0Key="scenarioKey"
            level0Label="Scenario"
            dataKey="mean_ecl"
            title="MC Mean ECL"
            formatValue={(v) => fmtCurrency(v)}
            level0Colors={SCENARIO_COLORS}
            fetchProductData={async (scenario) => {
              const data = await api.eclByScenarioProductDetail(String(scenario));
              return data.map((r: any) => ({ ...r, mean_ecl: Number(r.total_ecl) || 0, name: r.product_type }));
            }}
            fetchCohortData={async (product, dim) => {
              const data = await api.eclByCohort(product, dim || 'risk_band');
              return data.map((r: any) => ({ ...r, mean_ecl: Number(r.total_ecl) || 0 }));
            }}
            height={380}
          />
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
                        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">{d.scenario}</span>
                        <span className="text-[11px] px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-300 font-mono">{(d.weight * 100).toFixed(0)}%</span>
                      </div>
                      <span className="text-xs font-mono text-slate-500 dark:text-slate-400">{fmtCurrency(d.mean)}</span>
                    </div>
                    <div className="relative h-5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                      <div className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                        style={{ width: `${barWidth}%`, backgroundColor: color, opacity: 0.7 }} />
                      <div className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                        style={{ width: `${maxEcl > 0 ? d.mean / maxEcl * 100 : 0}%`, backgroundColor: color }} />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500 dark:text-slate-300 mt-0.5">
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
                  <tr className="border-b border-slate-200 dark:border-slate-700">
                    <th className="text-left py-2 px-2 text-xs font-semibold text-slate-600 dark:text-slate-200">Plausible Scenario</th>
                    <th className="text-right py-2 px-2 text-xs font-semibold text-slate-600 dark:text-slate-200">Stressed PD ×</th>
                    <th className="text-right py-2 px-2 text-xs font-semibold text-slate-600 dark:text-slate-200">PD σ</th>
                    <th className="text-right py-2 px-2 text-xs font-semibold text-slate-600 dark:text-slate-200">Stressed LGD ×</th>
                    <th className="text-right py-2 px-2 text-xs font-semibold text-slate-600 dark:text-slate-200">LGD σ</th>
                    <th className="text-right py-2 px-2 text-xs font-semibold text-slate-600 dark:text-slate-200">MC Sims</th>
                  </tr>
                </thead>
                <tbody>
                  {mcChartData.map(d => (
                    <tr key={d.scenarioKey} className="border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800">
                      <td className="py-2 px-2">
                        <div className="flex items-center gap-1.5">
                          <div className="w-2 h-2 rounded-full" style={{ backgroundColor: SCENARIO_COLORS[d.scenarioKey] || '#6B7280' }} />
                          <span className="text-xs font-medium text-slate-700 dark:text-slate-200">{d.scenario}</span>
                        </div>
                      </td>
                      <td className={`py-2 px-2 text-right text-xs font-mono ${d.pd_mult > 1.1 ? 'text-red-600' : d.pd_mult < 0.95 ? 'text-emerald-600' : 'text-slate-600 dark:text-slate-300'}`}>
                        {d.pd_mult.toFixed(3)}
                      </td>
                      <td className="py-2 px-2 text-right text-xs font-mono text-slate-500 dark:text-slate-400">{(d.pd_vol * 100).toFixed(1)}%</td>
                      <td className={`py-2 px-2 text-right text-xs font-mono ${d.lgd_mult > 1.05 ? 'text-red-600' : 'text-slate-600 dark:text-slate-300'}`}>
                        {d.lgd_mult.toFixed(3)}
                      </td>
                      <td className="py-2 px-2 text-right text-xs font-mono text-slate-500 dark:text-slate-400">{(d.lgd_vol * 100).toFixed(1)}%</td>
                      <td className="py-2 px-2 text-right text-xs font-mono text-slate-500 dark:text-slate-400">{fmtNumber(d.n_sims)}</td>
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
        <ScenarioProductBarChart
          data={scenarioByProduct}
          scenarioColors={SCENARIO_COLORS}
          scenarioLabels={SCENARIO_LABELS}
          height={350}
        />
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

      {eclProduct.length > 0 && (
        <Card title="ECL Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
          <DrillDownChart
            data={buildDrillDownData(eclProduct, eclCohortByProduct)}
            dataKey="total_ecl"
            nameKey="product_type"
            title="ECL by Product → Cohort"
            formatValue={(v) => fmtCurrency(v)}
            fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
          />
        </Card>
      )}

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
  );
}
