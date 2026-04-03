import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, CartesianGrid,
} from 'recharts';
import { useChartTheme } from '../../lib/chartTheme';
import Card from '../../components/Card';
import DataTable from '../../components/DataTable';
import { fmtCurrency, fmtNumber } from '../../lib/format';
import { config } from '../../lib/config';

interface Props {
  vintageData: any[];
}

export default function VintageTab({ vintageData }: Props) {
  const ct = useChartTheme();

  return (
    <div className="space-y-6">
      <Card title="Vintage Delinquency Curves" subtitle="DPD rates by origination cohort">
        {vintageData.length > 0 ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={vintageData}>
              <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
              <XAxis dataKey="vintage_cohort" tick={{ fontSize: 11, fill: ct.axisLight }} tickMargin={12} />
              <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v: any) => `${Number(v).toFixed(2)}%`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
              <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
              <Line type="monotone" dataKey="delinquency_rate" name="Any DPD" stroke="#F59E0B" strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="dpd30_rate" name="30+ DPD" stroke="#EF4444" strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="dpd60_rate" name="60+ DPD" stroke="#DC2626" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="dpd90_rate" name="90+ DPD" stroke="#F87171" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-slate-400 py-8 text-center">No vintage data available</p>
        )}
      </Card>

      <Card title="Vintage PD Trend" subtitle="Average PD by origination cohort">
        {vintageData.length > 0 ? (
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={vintageData} barSize={35} margin={{ bottom: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
              <XAxis dataKey="vintage_cohort" tick={{ fontSize: 11, fill: ct.axisLight }} tickMargin={12} />
              <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} tickFormatter={v => `${v}%`} />
              <Tooltip formatter={(v: any) => `${Number(v).toFixed(2)}%`} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
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
  );
}
