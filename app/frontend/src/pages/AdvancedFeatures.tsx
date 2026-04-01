import { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, Cell,
} from 'recharts';
import { useChartTheme } from '../lib/chartTheme';
import {
  HeartPulse, CreditCard, Shield, Play, Loader2, TrendingUp,
  Clock, Layers, BarChart3, ArrowRightLeft, Percent, Building,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import Card from '../components/Card';
import KpiCard from '../components/KpiCard';
import DataTable from '../components/DataTable';
import PageLoader from '../components/PageLoader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import { api } from '../lib/api';
import { fmtNumber, fmtPct, fmtCurrency, fmtDateTime, formatProductName } from '../lib/format';

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#06B6D4', '#EC4899'];

type TabKey = 'cure_rates' | 'ccf' | 'collateral';

export default function AdvancedFeatures() {
  const [activeTab, setActiveTab] = useState<TabKey>('cure_rates');

  const tabs: { key: TabKey; label: string; icon: typeof HeartPulse }[] = [
    { key: 'cure_rates', label: 'Cure Rates', icon: HeartPulse },
    { key: 'ccf', label: 'CCF Analysis', icon: CreditCard },
    { key: 'collateral', label: 'Collateral Haircuts', icon: Shield },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800 dark:text-white">Advanced ECL Features</h2>
          <p className="text-sm text-slate-400 mt-1">Cure rate modeling, credit conversion factors & collateral haircut analysis</p>
        </div>
      </div>

      <div className="flex gap-1 bg-slate-100 dark:bg-slate-800 rounded-xl p-1">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm'
                  : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              <Icon size={14} />
              {tab.label}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
          {activeTab === 'cure_rates' && <CureRatesTab />}
          {activeTab === 'ccf' && <CCFTab />}
          {activeTab === 'collateral' && <CollateralTab />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}


function CureRatesTab() {
  const ct = useChartTheme();
  const [data, setData] = useState<any>(null);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [computing, setComputing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadAnalyses(); }, []);

  const loadAnalyses = async () => {
    setLoading(true);
    try {
      const list = await api.listCureAnalyses();
      setAnalyses(list);
      if (list.length > 0) {
        const detail = await api.getCureAnalysis(list[0].analysis_id);
        setData(detail);
      }
    } catch { setAnalyses([]); }
    finally { setLoading(false); }
  };

  const handleCompute = async () => {
    setComputing(true);
    setError(null);
    try {
      const result = await api.computeCureRates();
      setData(result);
      await loadAnalyses();
    } catch (e: any) {
      setError(e.message || 'Computation failed');
    } finally {
      setComputing(false);
    }
  };

  if (loading) return <PageLoader />;

  const cureByDpd = data?.cure_by_dpd || [];
  const cureByProduct = data?.cure_by_product || [];
  const cureTrend = data?.cure_trend || [];
  const timeToCure = data?.time_to_cure || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">
          {analyses.length > 0 ? `${analyses.length} analysis run(s)` : 'No analyses yet'}
        </div>
        <button onClick={handleCompute} disabled={computing} className="btn-primary text-xs flex items-center gap-2">
          {computing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {computing ? 'Computing...' : 'Compute Cure Rates'}
        </button>
      </div>

      {error && (
        <ErrorDisplay title="Cure rate computation failed" message={error} technicalDetails={error}
          onRetry={handleCompute} onDismiss={() => setError(null)} />
      )}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <KpiCard title="Overall Cure Rate" value={fmtPct((data.overall_cure_rate || 0) * 100, 1)}
              subtitle="Stage 2/3 → Stage 1" icon={<HeartPulse size={20} />} color="green" />
            <KpiCard title="Total Observations" value={fmtNumber(data.total_observations || 0)}
              subtitle="Across all products" icon={<Layers size={20} />} color="blue" />
            <KpiCard title="Products Analyzed" value={fmtNumber(cureByProduct.length)}
              icon={<BarChart3 size={20} />} color="purple" />
            <KpiCard title="Latest Analysis" value={data.created_at ? fmtDateTime(data.created_at).split(',')[0] : '—'}
              icon={<Clock size={20} />} color="amber" />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <Card title="Cure Rate by DPD Bucket" subtitle="Probability of returning to Stage 1" icon={<BarChart3 size={16} />} accent="brand">
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={cureByDpd}>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="dpd_bucket" tick={{ fontSize: 10, fill: ct.axisLight }} />
                    <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => fmtPct(v * 100, 0)} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Bar dataKey="cure_rate" name="Cure Rate" radius={[6, 6, 0, 0]}>
                      {cureByDpd.map((_: any, i: number) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="Cure Rate Trend" subtitle="Monthly cure rate over 12 months" icon={<TrendingUp size={16} />} accent="blue">
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={cureTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="month" tick={{ fontSize: 10, fill: ct.axisLight }} />
                    <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => fmtPct(v * 100, 0)} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Line dataKey="cure_rate" name="Cure Rate" stroke="#3B82F6" strokeWidth={2.5} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <Card title="Cure Rate by Product" icon={<Layers size={16} />}>
              <DataTable
                columns={[
                  { key: 'product_type', label: 'Product', format: (v: string) => formatProductName(v) },
                  { key: 'cure_rate', label: 'Cure Rate', align: 'right' as const, format: (v: number) => fmtPct(v * 100, 2) },
                  { key: 'sample_size', label: 'Sample Size', align: 'right' as const, format: (v: number) => fmtNumber(v) },
                ]}
                data={cureByProduct}
                compact
                exportName="cure_rates_by_product"
              />
            </Card>

            <Card title="Time-to-Cure Distribution" subtitle="Probability of cure within N months" icon={<Clock size={16} />}>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={timeToCure}>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="months" tick={{ fontSize: 10, fill: ct.axisLight }} label={{ value: 'Months', position: 'bottom', offset: -5 }} />
                    <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => fmtPct(v * 100, 0)} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} labelFormatter={l => `${l} months`}
                      contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Bar dataKey="probability" name="Probability" fill="#10B981" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>
        </>
      )}

      {!data && !computing && (
        <Card>
          <EmptyState
            icon={<HeartPulse size={48} />}
            title="No analyses computed"
            description="Run cure rate, CCF, or collateral analysis."
            action={{ label: 'Compute Cure Rates', onClick: handleCompute }}
          />
        </Card>
      )}
    </div>
  );
}


function CCFTab() {
  const ct = useChartTheme();
  const [data, setData] = useState<any>(null);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [computing, setComputing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadAnalyses(); }, []);

  const loadAnalyses = async () => {
    setLoading(true);
    try {
      const list = await api.listCCFAnalyses();
      setAnalyses(list);
      if (list.length > 0) {
        const detail = await api.getCCFAnalysis(list[0].analysis_id);
        setData(detail);
      }
    } catch { setAnalyses([]); }
    finally { setLoading(false); }
  };

  const handleCompute = async () => {
    setComputing(true);
    setError(null);
    try {
      const result = await api.computeCCF();
      setData(result);
      await loadAnalyses();
    } catch (e: any) {
      setError(e.message || 'Computation failed');
    } finally {
      setComputing(false);
    }
  };

  if (loading) return <PageLoader />;

  const ccfByStage = data?.ccf_by_stage || [];
  const ccfByUtil = data?.ccf_by_utilization || [];
  const ccfSummary = data?.ccf_by_product_summary || [];

  const stageChartData = (() => {
    const products = [...new Set(ccfByStage.map((r: any) => r.product_type))];
    return products.map((prod: any) => {
      const row: any = { product_type: formatProductName(prod) };
      ccfByStage.filter((r: any) => r.product_type === prod).forEach((r: any) => {
        row[`stage_${r.stage}`] = r.ccf;
      });
      return row;
    });
  })();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">
          {analyses.length > 0 ? `${analyses.length} analysis run(s)` : 'No analyses yet'}
        </div>
        <button onClick={handleCompute} disabled={computing} className="btn-primary text-xs flex items-center gap-2">
          {computing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {computing ? 'Computing...' : 'Compute CCF'}
        </button>
      </div>

      {error && (
        <ErrorDisplay title="CCF computation failed" message={error} technicalDetails={error}
          onRetry={handleCompute} onDismiss={() => setError(null)} />
      )}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <KpiCard title="Avg CCF" value={fmtPct((data.overall_avg_ccf || 0) * 100, 1)}
              subtitle="Across all products/stages" icon={<Percent size={20} />} color="blue" />
            <KpiCard title="Total EAD" value={fmtCurrency(data.total_ead || 0)}
              subtitle="Exposure at Default" icon={<CreditCard size={20} />} color="green" />
            <KpiCard title="Products" value={fmtNumber(ccfSummary.length)}
              subtitle={`${ccfSummary.filter((r: any) => r.is_revolving).length} revolving`}
              icon={<ArrowRightLeft size={20} />} color="purple" />
            <KpiCard title="Utilization Bands" value={fmtNumber(ccfByUtil.length)}
              icon={<BarChart3 size={20} />} color="amber" />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <Card title="CCF by Stage & Product" subtitle="Grouped by product type" icon={<BarChart3 size={16} />} accent="brand">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stageChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="product_type" tick={{ fontSize: 9, fill: ct.axisLight }} angle={-20} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => fmtPct(v * 100, 0)} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Legend wrapperStyle={{ fontSize: 11, color: ct.label }} />
                    <Bar dataKey="stage_1" name="Stage 1" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="stage_2" name="Stage 2" fill="#F59E0B" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="stage_3" name="Stage 3" fill="#EF4444" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="CCF by Utilization Band" subtitle="Drawn % vs conversion factor" icon={<TrendingUp size={16} />} accent="blue">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={ccfByUtil}>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="utilization_band" tick={{ fontSize: 10, fill: ct.axisLight }} />
                    <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => fmtPct(v * 100, 0)} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Line dataKey="ccf" name="CCF" stroke="#8B5CF6" strokeWidth={2.5} dot={{ r: 4, fill: '#8B5CF6' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <Card title="EAD Summary by Product" subtitle="Gross carrying amount × CCF = Exposure at Default" icon={<CreditCard size={16} />}>
            <DataTable
              columns={[
                { key: 'product_type', label: 'Product', format: (v: string) => (
                  <span className="inline-flex items-center gap-2">
                    {formatProductName(v)}
                    {ccfSummary.find((r: any) => r.product_type === v)?.is_revolving && (
                      <span className="text-[9px] font-bold bg-purple-100 text-purple-600 px-1.5 py-0.5 rounded-full">REVOLVING</span>
                    )}
                  </span>
                )},
                { key: 'avg_ccf', label: 'Avg CCF', align: 'right' as const, format: (v: number) => fmtPct(v * 100, 2) },
                { key: 'total_gca', label: 'Total GCA', align: 'right' as const, format: (v: number) => fmtCurrency(v) },
                { key: 'total_ead', label: 'Total EAD', align: 'right' as const, format: (v: number) => fmtCurrency(v) },
              ]}
              data={ccfSummary}
              compact
              exportName="ccf_summary"
            />
          </Card>
        </>
      )}

      {!data && !computing && (
        <Card>
          <EmptyState
            icon={<CreditCard size={48} />}
            title="No CCF analysis yet"
            description="Compute credit conversion factors for revolving facilities."
            action={{ label: 'Compute CCF', onClick: handleCompute }}
          />
        </Card>
      )}
    </div>
  );
}


function CollateralTab() {
  const ct = useChartTheme();
  const [data, setData] = useState<any>(null);
  const [computing, setComputing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const list = await api.listCollateralAnalyses();
      if (list.length > 0) {
        const result = await api.getCollateralAnalysis(list[0].analysis_id);
        setData(result);
      }
    } catch { /* no data yet */ }
    finally { setLoading(false); }
  };

  const handleCompute = async () => {
    setComputing(true);
    setError(null);
    try {
      const result = await api.computeCollateral();
      setData(result);
    } catch (e: any) {
      setError(e.message || 'Computation failed');
    } finally {
      setComputing(false);
    }
  };

  if (loading) return <PageLoader />;

  const haircuts = data?.haircut_results || [];
  const waterfall = data?.lgd_waterfall || [];
  const summary = data?.summary || {};

  const haircutChart = [...haircuts]
    .filter((r: any) => r.collateral_type !== 'unsecured')
    .sort((a: any, b: any) => b.haircut_pct - a.haircut_pct);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-500">Collateral valuation & LGD impact analysis per IFRS 9.B5.5.55</div>
        <button onClick={handleCompute} disabled={computing} className="btn-primary text-xs flex items-center gap-2">
          {computing ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {computing ? 'Computing...' : 'Compute Haircuts'}
        </button>
      </div>

      {error && (
        <ErrorDisplay title="Collateral computation failed" message={error} technicalDetails={error}
          onRetry={handleCompute} onDismiss={() => setError(null)} />
      )}

      {data && (
        <>
          <div className="grid grid-cols-4 gap-4">
            <KpiCard title="Avg Haircut" value={fmtPct((summary.avg_haircut || 0) * 100, 1)}
              subtitle="Across secured types" icon={<Shield size={20} />} color="red" />
            <KpiCard title="Avg Recovery Rate" value={fmtPct((summary.avg_recovery_rate || 0) * 100, 1)}
              subtitle="Post-default recovery" icon={<TrendingUp size={20} />} color="green" />
            <KpiCard title="Avg Time to Recovery" value={`${summary.avg_time_to_recovery || 0} mo`}
              subtitle="Months to realize collateral" icon={<Clock size={20} />} color="amber" />
            <KpiCard title="Net LGD" value={fmtPct(summary.net_lgd_pct || 0, 1)}
              subtitle={`${summary.secured_pct || 0}% secured`} icon={<Building size={20} />} color="purple" />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <Card title="Haircut by Collateral Type" subtitle="Collateral haircut (forced sale discount) %" icon={<Shield size={16} />} accent="red">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={haircutChart} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis type="number" tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => fmtPct(v * 100, 0)} />
                    <YAxis dataKey="label" type="category" tick={{ fontSize: 10, fill: ct.axisLight }} width={150} />
                    <Tooltip formatter={(v: any) => fmtPct(Number(v) * 100, 2)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Bar dataKey="haircut_pct" name="Haircut %" radius={[0, 6, 6, 0]}>
                      {haircutChart.map((_: any, i: number) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>

            <Card title="LGD Impact Waterfall" subtitle="From gross exposure to net loss" icon={<BarChart3 size={16} />} accent="purple">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={waterfall}>
                    <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                    <XAxis dataKey="step" tick={{ fontSize: 9, fill: ct.axisLight }} angle={-15} textAnchor="end" height={60} />
                    <YAxis tick={{ fontSize: 10, fill: ct.axisLight }} tickFormatter={(v: number) => `${(v / 1e6).toFixed(0)}M`} />
                    <Tooltip formatter={(v: any) => fmtCurrency(Number(v))} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, fontSize: 12 }} />
                    <Bar dataKey="cumulative" name="Cumulative" radius={[4, 4, 0, 0]}>
                      {waterfall.map((_: any, i: number) => (
                        <Cell key={i} fill={i === 0 ? '#3B82F6' : i === waterfall.length - 1 ? '#EF4444' : '#F59E0B'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </div>

          <Card title="Recovery Rate & Time-to-Recovery" subtitle="By collateral type" icon={<Clock size={16} />}>
            <DataTable
              columns={[
                { key: 'label', label: 'Collateral Type' },
                { key: 'haircut_pct', label: 'Haircut %', align: 'right' as const, format: (v: number) => fmtPct(v * 100, 2) },
                { key: 'recovery_rate', label: 'Recovery Rate', align: 'right' as const, format: (v: number) => fmtPct(v * 100, 2) },
                { key: 'time_to_recovery_months', label: 'Time to Recovery', align: 'right' as const, format: (v: number) => `${v.toFixed(1)} mo` },
                { key: 'forced_sale_discount', label: 'Forced Sale Discount', align: 'right' as const, format: (v: number) => fmtPct(v * 100, 2) },
                { key: 'lgd_secured', label: 'LGD (Secured)', align: 'right' as const, format: (v: number) => v != null ? fmtPct(v * 100, 2) : '—' },
                { key: 'sample_size', label: 'Sample', align: 'right' as const, format: (v: number) => fmtNumber(v) },
              ]}
              data={haircuts}
              compact
              exportName="collateral_haircuts"
            />
          </Card>
        </>
      )}

      {!data && !computing && (
        <Card>
          <EmptyState
            icon={<Shield size={48} />}
            title="No collateral analysis yet"
            description="Compute collateral haircuts and LGD impact analysis."
            action={{ label: 'Compute Haircuts', onClick: handleCompute }}
          />
        </Card>
      )}
    </div>
  );
}
