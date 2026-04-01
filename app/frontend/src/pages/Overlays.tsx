import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { Layers, DollarSign, TrendingUp, Percent, Plus, Trash2, AlertTriangle, Clock } from 'lucide-react';
import { useChartTheme } from '../lib/chartTheme';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DrillDownChart from '../components/DrillDownChart';
import LockedBanner from '../components/LockedBanner';
import NotebookLink from '../components/NotebookLink';
import PageLoader from '../components/PageLoader';
import PageHeader from '../components/PageHeader';
import { api, type Project, type Overlay } from '../lib/api';
import { fmtCurrency, fmtPct } from '../lib/format';
import { config } from '../lib/config';
import { buildDrillDownData } from '../lib/chartUtils';
import StepDescription from '../components/StepDescription';
import HelpTooltip, { IFRS9_HELP } from '../components/HelpTooltip';

const OVERLAY_CAP_PCT = 15;

const DEFAULT_OVERLAYS: Overlay[] = [
  { id: 'OVL-001', product: 'Credit Card', type: 'PD Uplift', amount: 320000, reason: 'Rising consumer debt levels and increased utilization rates in unsecured revolving credit', ifrs9: 'IFRS 9.5.5.17(c)', approved_by: 'J. Smith, Head of Credit Risk', expiry: '2026-03-31', classification: 'temporary' },
  { id: 'OVL-002', product: 'Commercial Loan', type: 'PD Uplift', amount: 180000, reason: 'Sector-specific downturn in commercial real estate not captured by macro scenarios', ifrs9: 'IFRS 9.5.5.17(c)', approved_by: 'D. Kim, CRO', expiry: '2026-06-30', classification: 'temporary' },
  { id: 'OVL-003', product: 'Residential Mortgage', type: 'LGD Reduction', amount: -15000, reason: 'Government housing support programme reduces loss severity on collateralized exposures', ifrs9: 'IFRS 9.5.5.17(a)', approved_by: 'A. Reyes, Model Validation', expiry: '', classification: 'permanent' },
];

interface Props {
  project: Project | null;
  onSubmit: (overlays: Overlay[], comment: string) => Promise<void>;
}

export default function Overlays({ project, onSubmit }: Props) {
  const ct = useChartTheme();
  const [overlays, setOverlays] = useState<Overlay[]>([]);
  const [modelEcl, setModelEcl] = useState(0);
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [eclCohortByProduct, setEclCohortByProduct] = useState<Record<string, any[]>>({});
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  useEffect(() => {
    if (!project || project.current_step < 6) return;
    api.eclByProduct().then(async (ep) => {
      setEclProduct(ep);
      setModelEcl(ep.reduce((s: number, r: any) => s + (Number(r.total_ecl) || 0), 0));
      const saved = project.overlays?.length ? project.overlays : DEFAULT_OVERLAYS;
      setOverlays(saved);
      const cohortMap: Record<string, any[]> = {};
      for (const row of ep) {
        try { cohortMap[row.product_type] = await api.eclByCohort(row.product_type); } catch { /* skip */ }
      }
      setEclCohortByProduct(cohortMap);
    }).finally(() => setLoading(false));
  }, [project]);

  if (!project || project.current_step < 6) return <LockedBanner requiredStep={6} />;
  if (loading) return <PageLoader />;

  const net = overlays.reduce((s, o) => s + o.amount, 0);
  const adjusted = modelEcl + net;
  const stepSt = project.step_status.overlays || 'pending';

  const waterfallData = [
    { name: 'Model ECL', value: modelEcl, fill: '#0F2B46' },
    ...overlays.map(o => ({ name: o.reason.slice(0, 18), value: o.amount, fill: o.amount > 0 ? '#EF4444' : '#10B981' })),
    { name: 'Adjusted ECL', value: adjusted, fill: '#1B6B93' },
  ];

  const updateAmount = (id: string, amount: number) => {
    setOverlays(prev => prev.map(o => o.id === id ? { ...o, amount } : o));
  };

  const updateField = (id: string, field: keyof Overlay, value: string | number) => {
    setOverlays(prev => prev.map(o => o.id === id ? { ...o, [field]: value } : o));
  };

  const addOverlay = () => {
    const maxNum = overlays.reduce((max, o) => {
      const m = o.id.match(/OVL-(\d+)/);
      return m ? Math.max(max, parseInt(m[1], 10)) : max;
    }, 0);
    const newId = `OVL-${String(maxNum + 1).padStart(3, '0')}`;
    setOverlays(prev => [...prev, { id: newId, product: '', type: 'PD Uplift', amount: 0, reason: '', ifrs9: 'B5.5.17' }]);
  };

  const removeOverlay = (id: string) => {
    setOverlays(prev => prev.filter(o => o.id !== id));
  };

  const overlayValidationErrors = overlays.reduce<string[]>((errs, o) => {
    if (!o.product) errs.push(`${o.id}: Product is required`);
    if (!o.reason) errs.push(`${o.id}: Reason/justification is required`);
    if (o.amount === 0 || o.amount === undefined) errs.push(`${o.id}: Amount must be non-zero`);
    return errs;
  }, []);
  const overlaysValid = overlays.length > 0 && overlayValidationErrors.length === 0;

  const handleSubmit = async () => {
    if (!overlaysValid) return;
    setActing(true);
    try {
      await onSubmit(overlays, comment);
    } catch {
      // Error is handled by parent via toast
    } finally {
      setActing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Management Overlays" subtitle="Post-model adjustments per IFRS 9.B5.5.17" status={stepSt} />

      <StepDescription
        description="Apply management overlays — post-model adjustments for risks not fully captured by the statistical model. Each overlay must be individually justified, approved, and time-bound."
        ifrsRef="Per IFRS 9.B5.5.17 — management adjustments are permitted when model outputs do not fully capture all relevant risk factors."
        tips={[
          'Net overlay impact must not exceed 15% of model ECL without Board Risk Committee escalation',
          'Temporary overlays expire within 2 quarters; permanent overlays trigger model redevelopment review',
          'Each overlay requires maker-checker approval (Risk Analyst → CRO)',
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Active Overlays" value={String(overlays.length)} subtitle="Adjustments" color="purple" icon={<Layers size={20} />} />
        <KpiCard title="Net Impact" value={`${net >= 0 ? '+' : ''}${fmtCurrency(net)}`} subtitle="On model ECL" color="amber" icon={<TrendingUp size={20} />} />
        <KpiCard title={<span className="flex items-center gap-1">Model ECL <HelpTooltip content={IFRS9_HELP.ECL} size={12} /></span>} value={fmtCurrency(modelEcl)} subtitle="Before overlays" color="blue" icon={<DollarSign size={20} />} />
        <KpiCard title="Adjusted ECL" value={fmtCurrency(adjusted)} subtitle="After overlays" color="red" icon={<Percent size={20} />} />
      </div>

      <Card title="ECL Waterfall" subtitle="Model ECL → Adjusted ECL">
        {waterfallData.length > 2 ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={waterfallData} barSize={45} margin={{ bottom: 20 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: ct.axisLight }} interval={0} angle={-15} textAnchor="end" height={60} tickMargin={12} />
              <YAxis tick={{ fontSize: 11, fill: ct.axisLight }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
              <Tooltip formatter={(v: any) => fmtCurrency(v)} contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
              <ReferenceLine y={0} stroke={ct.reference} />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {waterfallData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="py-12 text-center text-sm text-slate-500">
            Add overlays below to see the ECL waterfall impact
          </div>
        )}
      </Card>

      {eclProduct.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
        </div>
      )}

      <NotebookLink notebooks={['03b_run_ecl_calculation']} />

      {/* Overlay Governance Framework */}
      <Card title="Overlay Governance Framework" subtitle="IFRS 9.B5.5.17 — Overlays must be reasonable, supportable, and time-bound">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Overlay Cap</p>
            <p className="text-lg font-bold text-slate-700 dark:text-slate-200">≤ {OVERLAY_CAP_PCT}% of Model ECL</p>
            <p className={`text-[10px] font-semibold ${Math.abs(net) / Math.max(modelEcl, 1) * 100 > OVERLAY_CAP_PCT ? 'text-red-500' : 'text-emerald-500'}`}>
              Current: {fmtPct(Math.abs(net) / Math.max(modelEcl, 1) * 100, 1)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Approval Required</p>
            <p className="text-sm font-bold text-slate-700 dark:text-slate-200">Each overlay individually</p>
            <p className="text-[10px] text-slate-400">Maker-checker: Risk Analyst → CRO</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Expiry Policy</p>
            <p className="text-sm font-bold text-slate-700 dark:text-slate-200">Temporary: max 2 quarters</p>
            <p className="text-[10px] text-slate-400">Permanent overlays trigger model redevelopment review</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-semibold text-slate-500 uppercase">Classification</p>
            <p className="text-sm font-bold text-slate-700 dark:text-slate-200">{overlays.filter(o => (o as any).classification === 'temporary').length} Temporary / {overlays.filter(o => (o as any).classification !== 'temporary').length} Permanent</p>
            <p className="text-[10px] text-slate-400">Permanent overlays reviewed quarterly by MRM</p>
          </div>
        </div>
        {Math.abs(net) / Math.max(modelEcl, 1) * 100 > OVERLAY_CAP_PCT && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
            <AlertTriangle size={14} className="text-red-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-red-700">
              Net overlay impact ({fmtPct(Math.abs(net) / Math.max(modelEcl, 1) * 100, 1)}) exceeds the {OVERLAY_CAP_PCT}% governance cap. This requires escalation to the Board Risk Committee with documented justification.
            </p>
          </div>
        )}
      </Card>

      <Card title="Overlay Register" subtitle="Add, edit, or remove overlays — changes reflect in real-time">
        <div className="space-y-4">
          {overlays.map(o => (
            <div key={o.id} className="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{o.id}</span>
                  <label className="sr-only" htmlFor={`overlay-type-${o.id}`}>Overlay type</label>
                  <select id={`overlay-type-${o.id}`} value={o.type} onChange={e => updateField(o.id, 'type', e.target.value)}
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border-0 ${o.type.includes('Uplift') ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>
                    <option value="PD Uplift">PD Uplift</option>
                    <option value="LGD Uplift">LGD Uplift</option>
                    <option value="PD Reduction">PD Reduction</option>
                    <option value="LGD Reduction">LGD Reduction</option>
                    <option value="EAD Adjustment">EAD Adjustment</option>
                  </select>
                  <label className="sr-only" htmlFor={`overlay-class-${o.id}`}>Overlay classification</label>
                  <select id={`overlay-class-${o.id}`} value={(o as any).classification || 'temporary'} onChange={e => updateField(o.id, 'classification' as any, e.target.value)}
                    className="text-xs font-semibold px-2 py-0.5 rounded-full border-0 bg-blue-50 text-blue-700">
                    <option value="temporary">Temporary</option>
                    <option value="permanent">Permanent</option>
                  </select>
                </div>
                {stepSt !== 'completed' && (
                  <button onClick={() => removeOverlay(o.id)} className="text-slate-400 hover:text-red-500 transition p-1 focus-visible:ring-2 focus-visible:ring-brand rounded" aria-label={`Remove overlay ${o.id}`} title="Remove overlay">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Product</label>
                  <input value={o.product} onChange={e => updateField(o.id, 'product', e.target.value)}
                    placeholder="e.g. Emergency Microloan"
                    className="form-input" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Reason / Justification</label>
                  <input value={o.reason} onChange={e => updateField(o.id, 'reason', e.target.value)}
                    placeholder="e.g. Gig Economy Platform Disruption"
                    className="form-input" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Amount</label>
                  <input type="number" value={o.amount} onChange={e => updateAmount(o.id, Number(e.target.value))} step={10000}
                    className="form-input font-mono text-right" />
                </div>
              </div>
              <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">IFRS 9 Reference</label>
                  <input value={o.ifrs9} onChange={e => updateField(o.id, 'ifrs9', e.target.value)}
                    placeholder="e.g. B5.5.17(p)"
                    className="form-input text-xs font-mono py-1.5" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Approved By</label>
                  <input value={(o as any).approved_by || ''} onChange={e => updateField(o.id, 'approved_by' as any, e.target.value)}
                    placeholder="e.g. Maria Santos, CRO"
                    className="form-input text-xs py-1.5" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-500 uppercase mb-1 flex items-center gap-1">
                    <Clock size={10} /> Expiry Date
                  </label>
                  <input type="date" value={(o as any).expiry || ''} onChange={e => updateField(o.id, 'expiry' as any, e.target.value)}
                    className="form-input text-xs font-mono py-1.5" />
                </div>
              </div>
            </div>
          ))}
          {stepSt !== 'completed' && (
            <button onClick={addOverlay}
              className="w-full py-3 border-2 border-dashed border-slate-200 dark:border-slate-700 rounded-lg text-sm font-semibold text-slate-500 hover:border-brand hover:text-brand transition flex items-center justify-center gap-2">
              <Plus size={16} /> Add Overlay
            </button>
          )}
        </div>
      </Card>

      {stepSt !== 'completed' && (
        <Card>
          <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-3" id="overlay-submit-heading">Submit Overlays</h3>
          <label htmlFor="overlay-justification" className="sr-only">Justification for overlay package</label>
          <textarea id="overlay-justification" value={comment} onChange={e => setComment(e.target.value)} rows={2}
            placeholder="Justification for overlay package..."
            aria-describedby="overlay-submit-heading"
            className="form-input resize-none mb-3" />
          {overlayValidationErrors.length > 0 && (
            <div className="mb-3 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700">
              <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 mb-1">Please fix before submitting:</p>
              {overlayValidationErrors.map((err, i) => (
                <p key={i} className="text-[10px] text-amber-600 dark:text-amber-500">• {err}</p>
              ))}
            </div>
          )}
          <button onClick={handleSubmit} disabled={acting || !overlaysValid}
            className="btn-primary shadow-sm"
            title={!overlaysValid ? 'Fix validation errors above' : ''}>
            {acting ? 'Submitting...' : '✓ Submit Overlays'}
          </button>
        </Card>
      )}
    </div>
  );
}
