import { useEffect, useState, useMemo, useCallback } from 'react';
import ErrorDisplay from '../components/ErrorDisplay';
import { Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import { Database, TrendingUp, AlertTriangle, Layers, Server, Clock, FileCheck, GitBranch } from 'lucide-react';
import { useChartTheme } from '../lib/chartTheme';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import DrillDownChart from '../components/DrillDownChart';
import NotebookLink from '../components/NotebookLink';
import LockedBanner from '../components/LockedBanner';
import StatusBadge from '../components/StatusBadge';
import ChartTooltip from '../components/ChartTooltip';
import PageLoader from '../components/PageLoader';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtNumber, fmtPct } from '../lib/format';
import { config } from '../lib/config';
import { STAGE_COLORS_ARRAY } from '../lib/chartUtils';
import StepDescription from '../components/StepDescription';
import HelpTooltip, { IFRS9_HELP } from '../components/HelpTooltip';
import { usePermissions } from '../hooks/usePermissions';

interface Props {
  project: Project | null;
  onComplete: () => Promise<void>;
}

export default function DataProcessing({ project, onComplete }: Props) {
  const { canEdit } = usePermissions(project?.project_id);
  const ct = useChartTheme();
  const [portfolio, setPortfolio] = useState<any[]>([]);
  const [stages, setStages] = useState<any[]>([]);
  const [cohortByProduct, setCohortByProduct] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);
  const [loadedAt, setLoadedAt] = useState<string | null>(null);
  const [adminConfig, setAdminConfig] = useState<any>(null);
  const [selectedStage, setSelectedStage] = useState<number | null>(null);
  const [stageDrillData, setStageDrillData] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/admin/config').then(r => r.ok ? r.json() : null).then(data => { if (data) setAdminConfig(data); }).catch(() => {});
  }, []);

  const loadData = useCallback(async () => {
    if (!project || project.current_step < 1) return;
    setLoading(true);
    setError(null);
    try {
      const [p, s] = await Promise.all([api.portfolioSummary(), api.stageDistribution()]);
      setPortfolio(p); setStages(s);
      setLoadedAt(new Date().toLocaleTimeString());
      setLoading(false);
      const cohortMap: Record<string, any[]> = {};
      const promises = p.map(async (row: any) => {
        try {
          const cohorts = await api.portfolioByCohort(row.product_type);
          if (cohorts && cohorts.length > 0) {
            cohortMap[row.product_type] = cohorts;
          }
        } catch (e) {
          console.warn(`Failed to load cohorts for ${row.product_type}:`, e);
        }
      });
      await Promise.all(promises);
      setCohortByProduct({ ...cohortMap });
    } catch (e: any) {
      setError(e?.message || 'Failed to load portfolio data');
      setLoading(false);
    }
  }, [project]);

  useEffect(() => { loadData(); }, [loadData]);

  const portfolioDrillData = useMemo(() => ({
    totalData: portfolio.map(r => ({ ...r, name: r.product_type })),
    productData: cohortByProduct,
    cohortData: {},
  }), [portfolio, cohortByProduct]);

  const handleComplete = useCallback(async () => {
    setActing(true);
    try { await onComplete(); } finally { setActing(false); }
  }, [onComplete]);

  const handleStageClick = useCallback(async (entry: any) => {
    const stage = entry?.stage;
    if (stage == null) return;
    if (selectedStage === stage) {
      setSelectedStage(null);
      setStageDrillData([]);
      return;
    }
    setSelectedStage(stage);
    try {
      const data = await api.eclByStageProduct(stage);
      setStageDrillData(data || []);
    } catch {
      setStageDrillData([]);
    }
  }, [selectedStage]);

  const renderCustomPieLabel = useCallback(({ cx, cy, midAngle, innerRadius, outerRadius, name, percent }: any) => {
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 1.4;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    return (
      <text x={x} y={y} fill={ct.axis} textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central" fontSize={11} fontWeight={600}>
        {name} ({(percent * 100).toFixed(0)}%)
      </text>
    );
  }, [ct.axis]);

  if (!project || project.current_step < 1) return <LockedBanner />;
  if (loading) return <PageLoader />;
  if (error) return <ErrorDisplay message={error} onRetry={loadData} />;

  const totalLoans = portfolio.reduce((s, r) => s + r.loan_count, 0);
  const totalGca = portfolio.reduce((s, r) => s + r.total_gca, 0);
  const s3 = stages.find(s => s.assessed_stage === 3);
  const s3pct = s3 && totalLoans > 0 ? (s3.loan_count / totalLoans * 100) : 0;
  const stepSt = project.step_status.data_processing || 'pending';

  const pieData = stages.map(s => ({ name: `Stage ${s.assessed_stage}`, value: s.total_gca, stage: s.assessed_stage }));

  return (
    <div className="space-y-5">
      {!canEdit && (
        <div className="mb-4 px-4 py-2 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m9.364-7.364A9 9 0 1112 3a9 9 0 019.364 9.636z" /></svg>
          You have view-only access to this project.
        </div>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-800 dark:text-slate-100">Data Processing</h2>
          <p className="text-sm text-slate-500 mt-1">
            Review portfolio data loaded from the loan tape
            {loadedAt && <span className="ml-2 text-[11px] text-slate-500">Data loaded at {loadedAt}</span>}
          </p>
        </div>
        <StatusBadge status={stepSt} />
      </div>

      <StepDescription
        description="Review your loan portfolio data quality, completeness, and distribution before ECL calculation. Verify total loan counts, GCA, stage distribution, and days past due against source system expectations."
        ifrsRef="Per IFRS 9.B5.5.49-51 — use reasonable and supportable information available without undue cost or effort."
        tips={[
          'Check that total loan count and GCA match the core banking system extract',
          'Verify Stage 3 rate is consistent with known credit-impaired exposures',
          'Review DPD averages by product for anomalies',
        ]}
      />

      <Card accent="blue" icon={<Server size={16} />} title="Data Lineage & Source Traceability" subtitle="Audit trail: source system to model-ready">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { icon: Server, color: 'text-indigo-500', bg: 'bg-indigo-50', label: 'Source System', value: 'Core Banking System (CBS)', detail: 'Core Banking T24 to Unity Catalog' },
            { icon: Clock, color: 'text-blue-500', bg: 'bg-blue-50', label: 'Extraction Date', value: project.reporting_date || '2025-12-31', detail: 'COB cut-off: 23:59 local time' },
            { icon: GitBranch, color: 'text-emerald-500', bg: 'bg-emerald-50', label: 'Pipeline', value: 'Lakeflow DLT to Lakebase', detail: 'Bronze to Silver to Gold to Lakebase' },
            { icon: FileCheck, color: 'text-teal-500', bg: 'bg-teal-50', label: 'Completeness', value: `${fmtNumber(totalLoans)} / ${fmtNumber(totalLoans)} loaded`, detail: '100% coverage' },
          ].map(item => (
            <div key={item.label} className={`flex items-start gap-3 p-3.5 rounded-xl ${item.bg} border border-slate-100/50 dark:border-slate-700/50`}>
              <item.icon size={16} className={`${item.color} mt-0.5 flex-shrink-0`} />
              <div>
                <p className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">{item.label}</p>
                <p className="text-xs font-bold text-slate-700 dark:text-slate-200 mt-0.5">{item.value}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">{item.detail}</p>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 flex items-center justify-between border-t border-slate-100 dark:border-slate-700 pt-3">
          <div className="flex items-center gap-4 text-[11px] text-slate-500">
            <span>UC Catalog: <span className="font-mono font-semibold text-slate-500">{adminConfig?.data_sources?.catalog || 'lakemeter_catalog'}.{adminConfig?.data_sources?.schema || 'expected_credit_loss'}</span></span>
          </div>
          <NotebookLink notebooks={['01_generate_data', '02_run_data_processing']} compact />
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total Loans" value={fmtNumber(totalLoans)} subtitle="Current reporting period" color="blue" icon={<Database size={20} />} />
        <KpiCard title={<span className="flex items-center gap-1">Gross Carrying Amount <HelpTooltip content={IFRS9_HELP.GCA} size={12} /></span>} value={fmtCurrency(totalGca)} subtitle="Current reporting period" color="indigo" icon={<TrendingUp size={20} />} />
        <KpiCard title={<span className="flex items-center gap-1">Stage 3 Rate <HelpTooltip content={IFRS9_HELP.STAGE_3} size={12} /></span>} value={fmtPct(s3pct, 1)} subtitle="Credit-impaired" color="red" icon={<AlertTriangle size={20} />} />
        <KpiCard title="Products" value={String(portfolio.length)} subtitle="Loan programs" color="teal" icon={<Layers size={20} />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-5">
        <Card title="IFRS 9 Stage Distribution" subtitle={selectedStage ? `Stage ${selectedStage} — click again to go back` : 'Click a stage to drill down'} className="lg:col-span-2">
          {selectedStage && stageDrillData.length > 0 ? (
            <div>
              <button onClick={() => { setSelectedStage(null); setStageDrillData([]); }}
                className="text-xs text-brand hover:underline mb-2 flex items-center gap-1">
                ← Back to all stages
              </button>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={stageDrillData} layout="vertical" margin={{ left: 10, right: 20, top: 5, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke={ct.grid} />
                  <XAxis type="number" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v) => fmtCurrency(v)} />
                  <YAxis type="category" dataKey="product_type" tick={{ fontSize: 10, fill: ct.axis }} width={100} />
                  <Tooltip content={<ChartTooltip formatValue={fmtCurrency} />} />
                  <Bar dataKey="total_ecl" name="ECL" fill={STAGE_COLORS_ARRAY[(selectedStage || 1) - 1]} radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={60} outerRadius={95} paddingAngle={4}
                  label={renderCustomPieLabel} labelLine={{ stroke: '#CBD5E1', strokeWidth: 1 }}
                  onClick={handleStageClick} style={{ cursor: 'pointer' }}>
                  {pieData.map((_, i) => <Cell key={i} fill={STAGE_COLORS_ARRAY[i]} />)}
                </Pie>
                <Tooltip content={<ChartTooltip formatValue={fmtCurrency} />} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Days Past Due Drill-Down" subtitle="Click a product → drill by risk band, age group, etc." className="lg:col-span-3">
          <DrillDownChart
            data={{
              totalData: portfolio.map(r => ({ ...r, name: r.product_type })),
              productData: cohortByProduct,
              cohortData: {},
            }}
            dataKey="avg_dpd"
            nameKey="product_type"
            title="Avg Days Past Due"
            formatValue={(v: number) => fmtNumber(v, 1)}
            fetchByDimension={(product, dim) => api.portfolioByCohort(product, dim)}
          />
        </Card>
      </div>

      <Card title="Portfolio by Product" subtitle="Click a product bar to drill down by dimension">
        <DrillDownChart
          data={portfolioDrillData}
          dataKey="total_gca"
          nameKey="product_type"
          title="Gross Carrying Amount by Product"
          formatValue={fmtCurrency}
          fetchByDimension={(product, dim) => api.portfolioByCohort(product, dim)}
        />
        <div className="mt-4 border-t border-slate-100 dark:border-slate-700 pt-4">
        <DataTable
          exportName="portfolio_by_product"
          columns={[
            { key: 'product_type', label: 'Product' },
            { key: 'loan_count', label: 'Loans', align: 'right', format: v => fmtNumber(v) },
            { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
            { key: 'avg_pd_pct', label: 'Avg PD %', align: 'right', format: (v: any) => fmtPct(Number(v) || 0) },
            { key: 'avg_eir_pct', label: 'Avg EIR %', align: 'right', format: v => fmtPct(v) },
            { key: 'avg_dpd', label: 'Avg DPD', align: 'right', format: v => fmtNumber(v, 1) },
            { key: 'stage_1_count', label: <span className="inline-flex items-center gap-1">Stage 1 <HelpTooltip content={IFRS9_HELP.STAGE_1} size={11} position="bottom" /></span>, align: 'right', format: v => fmtNumber(v) },
            { key: 'stage_2_count', label: <span className="inline-flex items-center gap-1">Stage 2 <HelpTooltip content={IFRS9_HELP.STAGE_2} size={11} position="bottom" /></span>, align: 'right', format: v => fmtNumber(v) },
            { key: 'stage_3_count', label: <span className="inline-flex items-center gap-1">Stage 3 <HelpTooltip content={IFRS9_HELP.STAGE_3} size={11} position="bottom" /></span>, align: 'right', format: v => fmtNumber(v) },
          ]}
          data={portfolio}
        />
        </div>
      </Card>

      <Card title="PD Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
        <DrillDownChart
          data={{
            totalData: portfolio.map(r => ({ ...r, name: r.product_type, avg_pd_pct: r.avg_pd_pct ?? 0 })),
            productData: cohortByProduct,
            cohortData: {},
          }}
          dataKey="avg_pd_pct"
          nameKey="product_type"
          title="Avg PD %"
          formatValue={(v: number) => `${Number(v).toFixed(2)}%`}
          fetchByDimension={(product, dim) => api.portfolioByCohort(product, dim)}
        />
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Loan Count Drill-Down" subtitle="Click a product → drill by dimension">
          <DrillDownChart
            data={portfolioDrillData}
            dataKey="loan_count"
            nameKey="product_type"
            title="Loan Count"
            formatValue={fmtNumber}
            fetchByDimension={(product, dim) => api.portfolioByCohort(product, dim)}
          />
        </Card>
        <Card title="GCA Drill-Down" subtitle="Click a product → drill by dimension">
          <DrillDownChart
            data={portfolioDrillData}
            dataKey="total_gca"
            nameKey="product_type"
            title="Gross Carrying Amount"
            formatValue={fmtCurrency}
            fetchByDimension={(product, dim) => api.portfolioByCohort(product, dim)}
          />
        </Card>
      </div>

      {stepSt !== 'completed' && (
        <Card accent="brand">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200">Ready to proceed?</h3>
              <p className="text-xs text-slate-500 mt-1">Review the portfolio data above. If correct, mark complete to proceed to Data Control.</p>
            </div>
            <button onClick={handleComplete} disabled={acting || !canEdit}
              className={`px-6 py-3 gradient-brand text-white text-sm font-bold rounded-2xl hover:opacity-80 disabled:opacity-50 transition shadow-lg glow-brand ${!canEdit ? 'opacity-50 cursor-not-allowed' : ''}`}>
              {acting ? 'Processing...' : 'Mark Complete'}
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
