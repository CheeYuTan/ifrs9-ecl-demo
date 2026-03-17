import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { Layers, DollarSign, TrendingUp, Percent, Plus, Trash2, AlertTriangle, Clock } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import LockedBanner from '../components/LockedBanner';
import StatusBadge from '../components/StatusBadge';
import { api, type Project, type Overlay } from '../lib/api';
import { fmtCurrency, fmtPct } from '../lib/format';
import { config } from '../lib/config';

const OVERLAY_CAP_PCT = 15;

const DEFAULT_OVERLAYS: Overlay[] = [
  { id: 'OVL-001', product: 'Emergency Microloan', type: 'PD Uplift', amount: 320000, reason: 'Gig economy platform consolidation — increased default risk for informal workers', ifrs9: 'IFRS 9.5.5.17(c)', approved_by: 'J. Smith, Head of Credit Risk', expiry: '2026-03-31', classification: 'temporary' },
  { id: 'OVL-002', product: 'Career Transition', type: 'PD Uplift', amount: 180000, reason: 'Sector-specific layoffs in technology sector not captured by macro scenarios', ifrs9: 'IFRS 9.5.5.17(c)', approved_by: 'D. Kim, CRO', expiry: '2026-06-30', classification: 'temporary' },
  { id: 'OVL-003', product: 'Credit Builder', type: 'LGD Reduction', amount: -15000, reason: 'Financial literacy programme graduates show 12% higher recovery rates', ifrs9: 'IFRS 9.5.5.17(a)', approved_by: 'A. Reyes, Model Validation', expiry: '', classification: 'permanent' },
];

interface Props {
  project: Project | null;
  onSubmit: (overlays: Overlay[], comment: string) => Promise<void>;
}

export default function Overlays({ project, onSubmit }: Props) {
  const [overlays, setOverlays] = useState<Overlay[]>([]);
  const [modelEcl, setModelEcl] = useState(0);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  useEffect(() => {
    if (!project || project.current_step < 6) return;
    api.eclByProduct().then(ep => {
      setModelEcl(ep.reduce((s: number, r: any) => s + r.total_ecl, 0));
      const saved = project.overlays?.length ? project.overlays : DEFAULT_OVERLAYS;
      setOverlays(saved);
    }).finally(() => setLoading(false));
  }, [project]);

  if (!project || project.current_step < 6) return <LockedBanner />;
  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>;

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
    const newId = `OVL-${String(overlays.length + 1).padStart(3, '0')}`;
    setOverlays(prev => [...prev, { id: newId, product: '', type: 'PD Uplift', amount: 0, reason: '', ifrs9: 'B5.5.17' }]);
  };

  const removeOverlay = (id: string) => {
    setOverlays(prev => prev.filter(o => o.id !== id));
  };

  const handleSubmit = async () => {
    setActing(true);
    await onSubmit(overlays, comment);
    setActing(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Management Overlays</h2>
          <p className="text-sm text-slate-400 mt-1">Post-model adjustments per IFRS 9.B5.5.17</p>
        </div>
        <StatusBadge status={stepSt} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Active Overlays" value={String(overlays.length)} subtitle="Adjustments" color="purple" icon={<Layers size={20} />} />
        <KpiCard title="Net Impact" value={`${net >= 0 ? '+' : ''}${fmtCurrency(net)}`} subtitle="On model ECL" color="amber" icon={<TrendingUp size={20} />} />
        <KpiCard title="Model ECL" value={fmtCurrency(modelEcl)} subtitle="Before overlays" color="blue" icon={<DollarSign size={20} />} />
        <KpiCard title="Adjusted ECL" value={fmtCurrency(adjusted)} subtitle="After overlays" color="red" icon={<Percent size={20} />} />
      </div>

      <Card title="ECL Waterfall" subtitle="Model ECL → Adjusted ECL">
        {waterfallData.length > 2 ? (
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={waterfallData} barSize={45}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11 }} tickFormatter={v => `${config.currencySymbol}${(v / 1e6).toFixed(1)}M`} />
              <Tooltip formatter={(v: any) => fmtCurrency(v)} />
              <ReferenceLine y={0} stroke="#E5E7EB" />
              <Bar dataKey="value" radius={[6, 6, 0, 0]}>
                {waterfallData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="py-12 text-center text-sm text-slate-400">
            Add overlays below to see the ECL waterfall impact
          </div>
        )}
      </Card>

      {/* Overlay Governance Framework */}
      <Card title="Overlay Governance Framework" subtitle="IFRS 9.B5.5.17 — Overlays must be reasonable, supportable, and time-bound">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">Overlay Cap</p>
            <p className="text-lg font-bold text-slate-700">≤ {OVERLAY_CAP_PCT}% of Model ECL</p>
            <p className={`text-[10px] font-semibold ${Math.abs(net) / Math.max(modelEcl, 1) * 100 > OVERLAY_CAP_PCT ? 'text-red-500' : 'text-emerald-500'}`}>
              Current: {fmtPct(Math.abs(net) / Math.max(modelEcl, 1) * 100, 1)}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">Approval Required</p>
            <p className="text-sm font-bold text-slate-700">Each overlay individually</p>
            <p className="text-[10px] text-slate-400">Maker-checker: Risk Analyst → CRO</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">Expiry Policy</p>
            <p className="text-sm font-bold text-slate-700">Temporary: max 2 quarters</p>
            <p className="text-[10px] text-slate-400">Permanent overlays trigger model redevelopment review</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">Classification</p>
            <p className="text-sm font-bold text-slate-700">{overlays.filter(o => (o as any).classification === 'temporary').length} Temporary / {overlays.filter(o => (o as any).classification !== 'temporary').length} Permanent</p>
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
            <div key={o.id} className="p-4 rounded-lg bg-slate-50 border border-slate-100">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{o.id}</span>
                  <select value={o.type} onChange={e => updateField(o.id, 'type', e.target.value)}
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full border-0 ${o.type.includes('Uplift') ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'}`}>
                    <option value="PD Uplift">PD Uplift</option>
                    <option value="LGD Uplift">LGD Uplift</option>
                    <option value="PD Reduction">PD Reduction</option>
                    <option value="LGD Reduction">LGD Reduction</option>
                    <option value="EAD Adjustment">EAD Adjustment</option>
                  </select>
                  <select value={(o as any).classification || 'temporary'} onChange={e => updateField(o.id, 'classification' as any, e.target.value)}
                    className="text-xs font-semibold px-2 py-0.5 rounded-full border-0 bg-blue-50 text-blue-600">
                    <option value="temporary">Temporary</option>
                    <option value="permanent">Permanent</option>
                  </select>
                </div>
                {stepSt !== 'completed' && (
                  <button onClick={() => removeOverlay(o.id)} className="text-slate-300 hover:text-red-500 transition p-1" title="Remove overlay">
                    <Trash2 size={14} />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Product</label>
                  <input value={o.product} onChange={e => updateField(o.id, 'product', e.target.value)}
                    placeholder="e.g. Emergency Microloan"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Reason / Justification</label>
                  <input value={o.reason} onChange={e => updateField(o.id, 'reason', e.target.value)}
                    placeholder="e.g. Gig Economy Platform Disruption"
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Amount</label>
                  <input type="number" value={o.amount} onChange={e => updateAmount(o.id, Number(e.target.value))} step={10000}
                    className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm font-mono text-right focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
                </div>
              </div>
              <div className="mt-2 grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">IFRS 9 Reference</label>
                  <input value={o.ifrs9} onChange={e => updateField(o.id, 'ifrs9', e.target.value)}
                    placeholder="e.g. B5.5.17(p)"
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Approved By</label>
                  <input value={(o as any).approved_by || ''} onChange={e => updateField(o.id, 'approved_by' as any, e.target.value)}
                    placeholder="e.g. Maria Santos, CRO"
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1 flex items-center gap-1">
                    <Clock size={10} /> Expiry Date
                  </label>
                  <input type="date" value={(o as any).expiry || ''} onChange={e => updateField(o.id, 'expiry' as any, e.target.value)}
                    className="w-full px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
                </div>
              </div>
            </div>
          ))}
          {stepSt !== 'completed' && (
            <button onClick={addOverlay}
              className="w-full py-3 border-2 border-dashed border-slate-200 rounded-lg text-sm font-semibold text-slate-400 hover:border-brand hover:text-brand transition flex items-center justify-center gap-2">
              <Plus size={16} /> Add Overlay
            </button>
          )}
        </div>
      </Card>

      {stepSt !== 'completed' && (
        <Card>
          <h3 className="text-sm font-bold text-slate-700 mb-3">Submit Overlays</h3>
          <textarea value={comment} onChange={e => setComment(e.target.value)} rows={2}
            placeholder="Justification for overlay package..."
            className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none mb-3" />
          <button onClick={handleSubmit} disabled={acting}
            className="px-5 py-2.5 bg-emerald-500 text-white text-sm font-semibold rounded-lg hover:bg-emerald-600 disabled:opacity-50 transition shadow-sm">
            {acting ? 'Submitting...' : '✓ Submit Overlays'}
          </button>
        </Card>
      )}
    </div>
  );
}
