import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  Legend, CartesianGrid,
} from 'recharts';
import { useChartTheme } from '../../lib/chartTheme';
import { TrendingUp, AlertTriangle, Shield } from 'lucide-react';
import KpiCard from '../../components/KpiCard';
import Card from '../../components/Card';
import DataTable from '../../components/DataTable';
import ThreeLevelDrillDown from '../../components/ThreeLevelDrillDown';
import { api } from '../../lib/api';
import { fmtCurrency, fmtNumber } from '../../lib/format';
import { config } from '../../lib/config';
import type { MigrationDatum } from './types';

interface Props {
  migrationPct: number;
  setMigrationPct: (v: number) => void;
  migrationSimData: MigrationDatum[];
  migrationTotalDelta: number;
  baseEcl: number;
  stageData: any[];
}

export default function MigrationTab({
  migrationPct, setMigrationPct, migrationSimData,
  migrationTotalDelta, baseEcl, stageData,
}: Props) {
  const ct = useChartTheme();

  return (
    <div className="space-y-6">
      <Card title="Stage Migration Simulator" subtitle="What if a percentage of Stage 1 loans migrate to Stage 2?">
        <div className="max-w-lg">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">Stage 1 → Stage 2 Migration</span>
              <span className="text-xs text-slate-500 dark:text-slate-300 ml-2">% of Stage 1 loans downgraded</span>
            </div>
            <span className={`text-lg font-bold font-mono ${migrationPct > 0 ? 'text-red-500' : 'text-slate-500 dark:text-slate-400'}`}>
              {migrationPct}%
            </span>
          </div>
          <input type="range" min={0} max={30} value={migrationPct} onChange={e => setMigrationPct(Number(e.target.value))}
            className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer brand-range" />
          <div className="flex justify-between text-[11px] text-slate-500 dark:text-slate-300 mt-1">
            <span>0%</span><span>5%</span><span>10%</span><span>15%</span><span>20%</span><span>25%</span><span>30%</span>
          </div>
          <div className="mt-3 flex gap-2">
            <button onClick={() => setMigrationPct(0)} className="px-3 py-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition">Reset</button>
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
            <BarChart data={migrationSimData} barGap={4} margin={{ bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: ct.axisLight }} tickMargin={12} />
              <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
              <Tooltip formatter={(v: any) => fmtCurrency(Number(v) || 0)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
              <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
              <Bar dataKey="base_ecl" name="Base ECL" fill="#6366F1" radius={[4, 4, 0, 0]} />
              <Bar dataKey="adjusted_ecl" name="Simulated ECL" fill="#EF4444" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-slate-400 py-8 text-center">No stage data available</p>
        )}
      </Card>

      <Card title="Base ECL Stage Drill-Down" subtitle="Stage → Product → Cohort drill-down">
        <ThreeLevelDrillDown
          level0Data={migrationSimData.map(d => ({ ...d, assessed_stage: d.stage }))}
          level0Key="assessed_stage"
          level0Label="Stage"
          dataKey="base_ecl"
          title="Base ECL by Stage"
          formatValue={(v) => fmtCurrency(v)}
          level0Colors={{ 1: '#10B981', 2: '#F59E0B', 3: '#EF4444' }}
          fetchProductData={async (stage) => {
            const data = await api.eclByStageProduct(Number(stage));
            return data.map((r: any) => ({ ...r, base_ecl: Number(r.total_ecl) || 0, name: r.product_type }));
          }}
          fetchCohortData={async (product, dim) => {
            const data = await api.eclByCohort(product, dim || 'risk_band');
            return data.map((r: any) => ({ ...r, base_ecl: Number(r.total_ecl) || 0 }));
          }}
        />
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
  );
}
