import Card from '../../components/Card';
import DataTable from '../../components/DataTable';
import DrillDownChart from '../../components/DrillDownChart';
import ThreeLevelDrillDown from '../../components/ThreeLevelDrillDown';
import { api } from '../../lib/api';
import { fmtCurrency, fmtNumber } from '../../lib/format';
import { config } from '../../lib/config';
import { buildDrillDownData } from '../../lib/chartUtils';

interface Props {
  concData: any[];
  sensitivity: any[];
  eclProduct: any[];
  eclCohortByProduct: Record<string, any[]>;
  stageData: any[];
}

export default function ConcentrationTab({
  concData, sensitivity, eclProduct, eclCohortByProduct, stageData,
}: Props) {
  return (
    <div className="space-y-6">
      <Card title="ECL Concentration Heatmap" subtitle="Product x Stage coverage rates">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700">
                <th className="text-left py-2 px-3 text-xs font-semibold text-slate-500 dark:text-slate-400">Product</th>
                <th className="text-right py-2 px-3 text-xs font-semibold text-emerald-600">Stage 1</th>
                <th className="text-right py-2 px-3 text-xs font-semibold text-amber-600">Stage 2</th>
                <th className="text-right py-2 px-3 text-xs font-semibold text-red-600">Stage 3</th>
              </tr>
            </thead>
            <tbody>
              {[...new Set(concData.map(r => r.product_type))].map(product => {
                const rows = concData.filter(r => r.product_type === product);
                return (
                  <tr key={product} className="border-b border-slate-100 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800">
                    <td className="py-2.5 px-3 font-medium text-slate-700 dark:text-slate-200">{product}</td>
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
                          <div className="text-[10px] text-slate-500 dark:text-slate-400">{cov.toFixed(2)}% cov</div>
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

      {eclProduct.length > 0 && (
        <Card title="GCA Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
          <DrillDownChart
            data={buildDrillDownData(eclProduct, eclCohortByProduct)}
            dataKey="total_gca"
            nameKey="product_type"
            title="GCA by Product → Cohort"
            formatValue={(v) => fmtCurrency(v)}
            fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
          />
        </Card>
      )}

      {stageData.length > 0 && (
        <Card title="ECL by Stage Drill-Down" subtitle="Stage → Product → Cohort">
          <ThreeLevelDrillDown
            level0Data={stageData.map(s => ({ ...s, name: `Stage ${s.assessed_stage}`, ecl: Number(s.base_ecl) || 0 }))}
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
      )}
    </div>
  );
}
