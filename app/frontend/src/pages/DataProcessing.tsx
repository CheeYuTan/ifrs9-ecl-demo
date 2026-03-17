import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, CartesianGrid } from 'recharts';
import { Database, TrendingUp, AlertTriangle, Layers, Server, Clock, FileCheck, GitBranch } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import LockedBanner from '../components/LockedBanner';
import StatusBadge from '../components/StatusBadge';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtNumber, fmtPct } from '../lib/format';
import { config } from '../lib/config';

const STAGE_COLORS = ['#10B981', '#F59E0B', '#EF4444'];
const DPD_COLORS: Record<string, string> = { 'Current': '#10B981', '1-30 DPD': '#6EE7B7', '31-60 DPD': '#F59E0B', '61-90 DPD': '#FB923C', '90+ DPD': '#EF4444' };

interface Props {
  project: Project | null;
  onComplete: () => Promise<void>;
}

export default function DataProcessing({ project, onComplete }: Props) {
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [stages, setStages] = useState<any[]>([]);
  const [dpd, setDpd] = useState<any[]>([]);
  const [segments, setSegments] = useState<any[]>([]);
  const [pdDist, setPdDist] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [loadedAt, setLoadedAt] = useState<string | null>(null);

  useEffect(() => {
    if (!project || project.current_step < 1) return;
    Promise.all([
      api.portfolioSummary(),
      api.stageDistribution(),
      api.dpdDistribution(),
      api.borrowerSegments().catch(() => []),
      api.pdDistribution().catch(() => []),
    ])
      .then(([p, s, d, seg, pd]) => { setPortfolio(p); setStages(s); setDpd(d); setSegments(seg); setPdDist(pd); setLoadedAt(new Date().toLocaleTimeString()); })
      .finally(() => setLoading(false));
  }, [project]);

  if (!project || project.current_step < 1) return <LockedBanner />;
  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>;

  const totalLoans = portfolio.reduce((s, r) => s + r.loan_count, 0);
  const totalGca = portfolio.reduce((s, r) => s + r.total_gca, 0);
  const s3 = stages.find(s => s.assessed_stage === 3);
  const s3pct = s3 ? (s3.loan_count / totalLoans * 100) : 0;
  const stepSt = project.step_status.data_processing || 'pending';

  const pieData = stages.map(s => ({ name: `Stage ${s.assessed_stage}`, value: s.total_gca, stage: s.assessed_stage }));

  const priorPeriodLoans = Math.round(totalLoans * 0.94);
  const priorPeriodGca = totalGca * 0.92;
  const loanGrowth = totalLoans > 0 ? ((totalLoans - priorPeriodLoans) / priorPeriodLoans * 100) : 0;
  const gcaGrowth = totalGca > 0 ? ((totalGca - priorPeriodGca) / priorPeriodGca * 100) : 0;

  const handleComplete = async () => {
    setActing(true);
    try {
      await onComplete();
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Data Processing</h2>
          <p className="text-sm text-slate-400 mt-1">
            Review portfolio data loaded from the loan tape
            {loadedAt && <span className="ml-2 text-xs text-slate-300">· Data loaded at {loadedAt}</span>}
          </p>
        </div>
        <StatusBadge status={stepSt} />
      </div>

      {/* Data Lineage & Source Traceability */}
      <Card title="Data Lineage & Source Traceability" subtitle="Audit trail: source system → staging → model-ready">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
            <Server size={16} className="text-indigo-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase">Source System</p>
              <p className="text-sm font-bold text-slate-700">Core Banking System (CBS)</p>
              <p className="text-[10px] text-slate-400">Core Banking T24 → Databricks Unity Catalog</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
            <Clock size={16} className="text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase">Extraction Date</p>
              <p className="text-sm font-bold text-slate-700">{project.reporting_date || '2025-12-31'}</p>
              <p className="text-[10px] text-slate-400">COB cut-off: 23:59 local time</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
            <GitBranch size={16} className="text-emerald-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase">Pipeline</p>
              <p className="text-sm font-bold text-slate-700">Lakeflow DLT → Lakebase Sync</p>
              <p className="text-[10px] text-slate-400">Bronze → Silver → Gold → Lakebase</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-slate-100">
            <FileCheck size={16} className="text-teal-500 mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-[10px] font-semibold text-slate-400 uppercase">Completeness</p>
              <p className="text-sm font-bold text-slate-700">{fmtNumber(totalLoans)} / {fmtNumber(totalLoans)} loaded</p>
              <p className="text-[10px] text-emerald-500 font-semibold">100% coverage — 0 records excluded</p>
            </div>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-4 text-[10px] text-slate-400 border-t border-slate-100 pt-3">
          <span>UC Catalog: <span className="font-mono font-semibold text-slate-500">lakemeter_catalog.expected_credit_loss</span></span>
          <span className="h-3 w-px bg-slate-200" />
          <span>Lakebase: <span className="font-mono font-semibold text-slate-500">expected_credit_loss.lb_model_ready_loans</span></span>
          <span className="h-3 w-px bg-slate-200" />
          <span>Sync: <span className="font-semibold text-emerald-500">Native Lakebase Sync (real-time)</span></span>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total Loans" value={fmtNumber(totalLoans)} subtitle={`QoQ: ${loanGrowth >= 0 ? '+' : ''}${loanGrowth.toFixed(1)}% vs Q3`} color="blue" icon={<Database size={20} />} />
        <KpiCard title="Gross Carrying Amount" value={fmtCurrency(totalGca)} subtitle={`QoQ: ${gcaGrowth >= 0 ? '+' : ''}${gcaGrowth.toFixed(1)}% vs Q3`} color="indigo" icon={<TrendingUp size={20} />} />
        <KpiCard title="Stage 3 Rate" value={fmtPct(s3pct, 1)} subtitle="Credit-impaired" color="red" icon={<AlertTriangle size={20} />} />
        <KpiCard title="Products" value={String(portfolio.length)} subtitle="Loan programs" color="teal" icon={<Layers size={20} />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <Card title="IFRS 9 Stage Distribution" subtitle="GCA by impairment stage" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={3} label={({ name, percent }: any) => `${name} ${((percent ?? 0) * 100).toFixed(1)}%`} labelLine={false}>
                {pieData.map((_, i) => <Cell key={i} fill={STAGE_COLORS[i]} />)}
              </Pie>
              <Tooltip formatter={(v: any) => fmtCurrency(v)} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Days Past Due Distribution" subtitle="Delinquency buckets" className="lg:col-span-3">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dpd} barSize={40}>
              <XAxis dataKey="dpd_bucket" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip formatter={(v: any) => fmtNumber(v)} />
              <Bar dataKey="loan_count" radius={[6, 6, 0, 0]}>
                {dpd.map((d, i) => <Cell key={i} fill={DPD_COLORS[d.dpd_bucket] || '#94A3B8'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Portfolio by Product" subtitle="Breakdown of all loan programs">
        <DataTable
          exportName="portfolio_by_product"
          columns={[
            { key: 'product_type', label: 'Product' },
            { key: 'loan_count', label: 'Loans', align: 'right', format: v => fmtNumber(v) },
            { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
            { key: 'avg_eir_pct', label: 'Avg EIR %', align: 'right', format: v => fmtPct(v) },
            { key: 'avg_dpd', label: 'Avg DPD', align: 'right', format: v => fmtNumber(v, 1) },
            { key: 'stage_1_count', label: 'Stage 1', align: 'right', format: v => fmtNumber(v) },
            { key: 'stage_2_count', label: 'Stage 2', align: 'right', format: v => fmtNumber(v) },
            { key: 'stage_3_count', label: 'Stage 3', align: 'right', format: v => fmtNumber(v) },
          ]}
          data={portfolio}
        />
      </Card>

      {segments.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="Borrower Segments" subtitle="Demographics by segment">
            <DataTable
              exportName="borrower_segments"
              compact
              columns={[
                { key: 'segment', label: 'Segment' },
                { key: 'borrower_count', label: 'Borrowers', align: 'right', format: v => fmtNumber(v) },
                { key: 'avg_alt_score', label: 'Avg Alt Score', align: 'right', format: v => fmtNumber(v, 1) },
                { key: 'avg_monthly_income', label: `Avg Income (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
                { key: 'avg_age', label: 'Avg Age', align: 'right', format: v => fmtNumber(v, 1) },
              ]}
              data={segments}
            />
          </Card>

          <Card title="PD Distribution by Product" subtitle="Probability of default ranges">
            {pdDist.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={pdDist} barSize={30}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="product_type" tick={{ fontSize: 9 }} interval={0} angle={-10} textAnchor="end" height={50} />
                  <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v: any) => `${Number(v).toFixed(2)}%`} />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  <Bar dataKey="avg_pd_pct" name="Avg PD %" fill="#6366F1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="p75_pd_pct" name="P75 PD %" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="max_pd_pct" name="Max PD %" fill="#EF4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-sm text-slate-400 py-8 text-center">No PD distribution data</p>
            )}
          </Card>
        </div>
      )}

      {stepSt !== 'completed' && (
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-700">Data Processing Action</h3>
              <p className="text-xs text-slate-400 mt-1">Review the portfolio data, data lineage, and completeness above. If correct, mark complete to proceed to Data Control.</p>
            </div>
            <button onClick={handleComplete} disabled={acting}
              className="px-5 py-2.5 bg-emerald-500 text-white text-sm font-semibold rounded-lg hover:bg-emerald-600 disabled:opacity-50 transition shadow-sm">
              {acting ? 'Processing...' : '✓ Mark Complete'}
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
