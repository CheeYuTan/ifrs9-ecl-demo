import { useEffect, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box, Trophy, Clock, CheckCircle2, XCircle, Send, Shield, Archive,
  Plus, GitCompare, X, Filter, Eye, Star,
  User, FileText, Activity,
} from 'lucide-react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, Tooltip,
} from 'recharts';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import KpiCard from '../components/KpiCard';
import PageHeader from '../components/PageHeader';
import PageLoader from '../components/PageLoader';
import EmptyState from '../components/EmptyState';
import ErrorDisplay from '../components/ErrorDisplay';
import ConfirmDialog from '../components/ConfirmDialog';
import { useChartTheme } from '../lib/chartTheme';
import { api, type ModelRegistryEntry, type ModelAuditEntry } from '../lib/api';
import { getCurrentUser } from '../lib/userContext';
import { fmtPct, fmtDateTime, fmtNumber } from '../lib/format';

const MODEL_TYPES = ['PD', 'LGD', 'EAD', 'Staging'] as const;

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: any }> = {
  draft:          { label: 'Draft',          color: 'text-slate-600 dark:text-slate-400',   bg: 'bg-slate-50 border-slate-200',    icon: FileText },
  pending_review: { label: 'Pending Review', color: 'text-amber-700',  bg: 'bg-amber-50 border-amber-200',    icon: Clock },
  approved:       { label: 'Approved',       color: 'text-blue-700',   bg: 'bg-blue-50 border-blue-200',      icon: CheckCircle2 },
  active:         { label: 'Active',         color: 'text-emerald-700',bg: 'bg-emerald-50 border-emerald-200', icon: Activity },
  retired:        { label: 'Retired',        color: 'text-red-700',    bg: 'bg-red-50 border-red-200',         icon: Archive },
};

function ModelStatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border ${cfg.bg} ${cfg.color}`}>
      <Icon size={12} /> {cfg.label}
    </span>
  );
}

function ChampionBadge() {
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-700 border border-amber-200">
      <Trophy size={10} /> Champion
    </span>
  );
}

interface RegisterFormProps {
  onSubmit: (data: Partial<ModelRegistryEntry>) => Promise<void>;
  onCancel: () => void;
}

function RegisterForm({ onSubmit, onCancel }: RegisterFormProps) {
  const [form, setForm] = useState({
    model_name: '', model_type: 'PD', algorithm: '', version: 1,
    description: '', product_type: '', created_by: 'Model Developer',
    auc: '', gini: '', ks: '', accuracy: '', rmse: '', r_squared: '',
    notes: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const metrics: Record<string, number> = {};
      if (form.auc) metrics.auc = parseFloat(form.auc);
      if (form.gini) metrics.gini = parseFloat(form.gini);
      if (form.ks) metrics.ks = parseFloat(form.ks);
      if (form.accuracy) metrics.accuracy = parseFloat(form.accuracy);
      if (form.rmse) metrics.rmse = parseFloat(form.rmse);
      if (form.r_squared) metrics.r_squared = parseFloat(form.r_squared);

      await onSubmit({
        model_name: form.model_name,
        model_type: form.model_type,
        algorithm: form.algorithm,
        version: form.version,
        description: form.description,
        product_type: form.product_type,
        created_by: form.created_by,
        performance_metrics: metrics,
        notes: form.notes,
      });
    } finally {
      setSubmitting(false);
    }
  };

  const field = (label: string, key: keyof typeof form, type = 'text', placeholder = '') => {
    const inputId = `model-reg-${key}`;
    return (
      <div>
        <label htmlFor={inputId} className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">{label}</label>
        <input id={inputId} type={type} value={form[key]} onChange={e => setForm(f => ({ ...f, [key]: type === 'number' ? e.target.value : e.target.value }))}
          placeholder={placeholder} className="form-input text-xs" />
      </div>
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {field('Model Name', 'model_name', 'text', 'e.g. PD Logistic v2.1')}
        <div>
          <label htmlFor="model-reg-model_type" className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Model Type</label>
          <select id="model-reg-model_type" value={form.model_type} onChange={e => setForm(f => ({ ...f, model_type: e.target.value }))} className="form-input text-xs">
            {MODEL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
        {field('Algorithm', 'algorithm', 'text', 'e.g. Logistic Regression')}
        {field('Version', 'version', 'number')}
        {field('Product Type', 'product_type', 'text', 'e.g. Personal Loans')}
        {field('Created By', 'created_by', 'text', 'Your name')}
      </div>
      <div>
        <label htmlFor="model-reg-description" className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Description</label>
        <textarea id="model-reg-description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          rows={2} placeholder="Model description..." className="form-input text-xs" />
      </div>
      <div>
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Performance Metrics</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {field('AUC', 'auc', 'number', '0.85')}
          {field('Gini', 'gini', 'number', '0.70')}
          {field('KS Statistic', 'ks', 'number', '0.45')}
          {field('Accuracy', 'accuracy', 'number', '0.92')}
          {field('RMSE', 'rmse', 'number', '0.05')}
          {field('R-Squared', 'r_squared', 'number', '0.88')}
        </div>
      </div>
      <div>
        <label htmlFor="model-reg-notes" className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1.5">Notes</label>
        <textarea id="model-reg-notes" value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))}
          rows={2} placeholder="Additional notes..." className="form-input text-xs" />
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button type="button" onClick={onCancel} className="btn-secondary text-xs">Cancel</button>
        <button type="submit" disabled={submitting || !form.model_name || !form.algorithm}
          className="btn-primary text-xs disabled:opacity-40">
          {submitting ? 'Registering...' : 'Register Model'}
        </button>
      </div>
    </form>
  );
}

interface DetailPanelProps {
  model: ModelRegistryEntry;
  audit: ModelAuditEntry[];
  onClose: () => void;
  onStatusChange: (status: string, comment: string) => Promise<void>;
  onPromote: () => Promise<void>;
}

function DetailPanel({ model, audit, onClose, onStatusChange, onPromote }: DetailPanelProps) {
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  const doAction = async (status: string) => {
    setActing(true);
    try { await onStatusChange(status, comment); setComment(''); }
    finally { setActing(false); }
  };

  const doPromote = async () => {
    setActing(true);
    try { await onPromote(); }
    finally { setActing(false); }
  };

  const metrics = model.performance_metrics || {};
  const metricEntries = Object.entries(metrics).filter(([, v]) => v != null);

  const transitions: Record<string, { label: string; next: string; icon: any; color: string }[]> = {
    draft:          [{ label: 'Submit for Review', next: 'pending_review', icon: Send, color: 'btn-primary' }],
    pending_review: [
      { label: 'Approve', next: 'approved', icon: CheckCircle2, color: 'bg-emerald-600 text-white hover:bg-emerald-700' },
      { label: 'Reject', next: 'draft', icon: XCircle, color: 'bg-red-600 text-white hover:bg-red-700' },
    ],
    approved:       [{ label: 'Promote to Active', next: 'active', icon: Activity, color: 'btn-primary' }],
    active:         [{ label: 'Retire', next: 'retired', icon: Archive, color: 'bg-red-600 text-white hover:bg-red-700' }],
    retired:        [],
  };

  const actions = transitions[model.status] || [];

  return (
    <motion.div initial={{ opacity: 0, x: 40 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 40 }}
      className="fixed inset-y-0 right-0 w-full max-w-lg bg-white dark:bg-slate-800 shadow-2xl z-50 overflow-y-auto border-l border-slate-200 dark:border-slate-700">
      <div className="sticky top-0 bg-white dark:bg-slate-800 z-10 px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center">
            <Box size={18} className="text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800 dark:text-white">{model.model_name}</h3>
            <p className="text-[10px] text-slate-400">v{model.version} &middot; {model.model_type} &middot; {model.algorithm}</p>
          </div>
        </div>
        <button onClick={onClose} aria-label="Close model details" className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition focus-visible:ring-2 focus-visible:ring-brand"><X size={18} className="text-slate-400" /></button>
      </div>

      <div className="p-6 space-y-6">
        <div className="flex items-center gap-3">
          <ModelStatusBadge status={model.status} />
          {model.is_champion && <ChampionBadge />}
        </div>

        {model.description && (
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Description</p>
            <p className="text-sm text-slate-600 dark:text-slate-300">{model.description}</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-bold text-slate-400 uppercase">Product</p>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{model.product_type || '—'}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-bold text-slate-400 uppercase">Created By</p>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{model.created_by}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[10px] font-bold text-slate-400 uppercase">Created</p>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{fmtDateTime(model.created_at)}</p>
          </div>
          {model.approved_by && (
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
              <p className="text-[10px] font-bold text-slate-400 uppercase">Approved By</p>
              <p className="text-sm font-semibold text-slate-700 dark:text-slate-200 mt-0.5">{model.approved_by}</p>
            </div>
          )}
        </div>

        {metricEntries.length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Performance Metrics</p>
            <div className="grid grid-cols-3 gap-2">
              {metricEntries.map(([key, val]) => (
                <div key={key} className="p-3 rounded-xl bg-gradient-to-br from-blue-50 to-white dark:from-blue-950/40 dark:to-slate-800/60 border border-blue-100/50 dark:border-blue-900/30 text-center">
                  <p className="text-[10px] font-bold text-blue-400 uppercase">{key.replace(/_/g, ' ')}</p>
                  <p className="text-lg font-extrabold text-slate-800 dark:text-white mt-0.5">
                    {typeof val === 'number' ? (val < 1 && val > 0 ? fmtPct(val * 100, 1) : fmtNumber(val, 4)) : String(val)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {Object.keys(model.parameters || {}).length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Parameters</p>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 border border-slate-100 dark:border-slate-700">
              <pre className="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap">{JSON.stringify(model.parameters, null, 2)}</pre>
            </div>
          </div>
        )}

        {Object.keys(model.training_data_info || {}).length > 0 && (
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Training Data</p>
            <div className="bg-slate-50 dark:bg-slate-800 rounded-xl p-3 border border-slate-100 dark:border-slate-700">
              <pre className="text-xs text-slate-600 dark:text-slate-300 whitespace-pre-wrap">{JSON.stringify(model.training_data_info, null, 2)}</pre>
            </div>
          </div>
        )}

        {(actions.length > 0 || (model.status === 'approved' || model.status === 'active') && !model.is_champion) && (
          <div className="border-t border-slate-100 dark:border-slate-700 pt-5">
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Actions</p>
            <label htmlFor="model-action-comment" className="sr-only">Action comment</label>
            <textarea id="model-action-comment" value={comment} onChange={e => setComment(e.target.value)}
              placeholder="Add a comment (optional)..." rows={2}
              className="form-input text-xs mb-3 w-full" />
            <div className="flex flex-wrap gap-2">
              {actions.map(a => {
                const Icon = a.icon;
                return (
                  <button key={a.next} onClick={() => doAction(a.next)} disabled={acting}
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition shadow-sm ${a.color} disabled:opacity-40`}>
                    <Icon size={14} /> {a.label}
                  </button>
                );
              })}
              {(model.status === 'approved' || model.status === 'active') && !model.is_champion && (
                <button onClick={doPromote} disabled={acting}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-500 to-yellow-500 text-white hover:opacity-90 transition shadow-sm disabled:opacity-40">
                  <Trophy size={14} /> Set as Champion
                </button>
              )}
            </div>
          </div>
        )}

        <div className="border-t border-slate-100 dark:border-slate-700 pt-5">
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Audit Trail</p>
          {audit.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No audit entries yet</p>
          ) : (
            <div className="space-y-3">
              {audit.map(a => (
                <div key={a.audit_id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-700 flex items-center justify-center flex-shrink-0">
                      <User size={12} className="text-slate-400" />
                    </div>
                    <div className="w-px flex-1 bg-slate-100 dark:bg-slate-700 mt-1" />
                  </div>
                  <div className="pb-3 min-w-0">
                    <p className="text-xs font-semibold text-slate-700 dark:text-slate-200">
                      {a.action.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </p>
                    <p className="text-[10px] text-slate-400 mt-0.5">
                      {a.performed_by} &middot; {fmtDateTime(a.performed_at)}
                    </p>
                    {a.old_status && a.new_status && (
                      <p className="text-[10px] text-slate-500 mt-0.5">
                        {a.old_status} &rarr; {a.new_status}
                      </p>
                    )}
                    {a.comment && <p className="text-xs text-slate-500 mt-1 italic">{a.comment}</p>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

interface ComparisonViewProps {
  models: ModelRegistryEntry[];
  onClose: () => void;
}

function ComparisonView({ models, onClose }: ComparisonViewProps) {
  const ct = useChartTheme();
  const allMetricKeys = useMemo(() => {
    const keys = new Set<string>();
    models.forEach(m => Object.keys(m.performance_metrics || {}).forEach(k => keys.add(k)));
    return Array.from(keys);
  }, [models]);

  const radarData = useMemo(() => {
    return allMetricKeys.map(key => {
      const entry: Record<string, any> = { metric: key.replace(/_/g, ' ').toUpperCase() };
      models.forEach((m, i) => {
        const val = m.performance_metrics?.[key];
        entry[`model_${i}`] = typeof val === 'number' ? val : 0;
      });
      return entry;
    });
  }, [models, allMetricKeys]);

  const COLORS = ['#6366f1', '#10b981', '#f59e0b'];

  return (
    <Card title="Model Comparison" subtitle={`Comparing ${models.length} models`} accent="purple"
      icon={<GitCompare size={16} />}
      action={<button onClick={onClose} className="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 transition"><X size={16} className="text-slate-400" /></button>}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Metrics Comparison</p>
          <div className="overflow-x-auto rounded-xl border border-slate-100 dark:border-slate-700">
            <table className="w-full text-xs">
              <thead>
                <tr className="bg-slate-50 dark:bg-slate-800/60">
                  <th className="px-3 py-2 text-left text-[10px] font-bold text-slate-400 uppercase">Metric</th>
                  {models.map((m, i) => (
                    <th key={m.model_id} className="px-3 py-2 text-right text-[10px] font-bold uppercase" style={{ color: COLORS[i] }}>
                      {m.model_name} v{m.version}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {allMetricKeys.map(key => {
                  const vals = models.map(m => m.performance_metrics?.[key]);
                  const numVals = vals.filter(v => typeof v === 'number') as number[];
                  const bestVal = key === 'rmse' ? Math.min(...numVals) : Math.max(...numVals);
                  return (
                    <tr key={key} className="border-t border-slate-100 dark:border-slate-700">
                      <td className="px-3 py-2 font-semibold text-slate-600 dark:text-slate-300">{key.replace(/_/g, ' ').toUpperCase()}</td>
                      {vals.map((v, i) => {
                        const isBest = typeof v === 'number' && v === bestVal && numVals.length > 1;
                        return (
                          <td key={i} className={`px-3 py-2 text-right font-mono ${isBest ? 'font-bold text-emerald-600' : 'text-slate-600 dark:text-slate-300'}`}>
                            {typeof v === 'number' ? fmtNumber(v, 4) : '—'}
                            {isBest && <Star size={10} className="inline ml-1 text-emerald-500" />}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {radarData.length >= 3 && (
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Radar Comparison</p>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke={ct.grid} />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 10, fill: ct.axisLight }} />
                  <PolarRadiusAxis tick={{ fontSize: 9, fill: ct.axisLight }} />
                  {models.map((m, i) => (
                    <Radar key={m.model_id} name={`${m.model_name} v${m.version}`}
                      dataKey={`model_${i}`} stroke={COLORS[i]} fill={COLORS[i]} fillOpacity={0.15} strokeWidth={2} />
                  ))}
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-3">
        {models.map((m, i) => (
          <div key={m.model_id} className="p-3 rounded-xl border border-slate-100 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/40">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i] }} />
              <span className="text-xs font-bold text-slate-700 dark:text-slate-200">{m.model_name} v{m.version}</span>
            </div>
            <div className="space-y-1 text-[10px] text-slate-500">
              <p>Type: <span className="font-semibold text-slate-600 dark:text-slate-300">{m.model_type}</span></p>
              <p>Algorithm: <span className="font-semibold text-slate-600 dark:text-slate-300">{m.algorithm}</span></p>
              <p>Status: <ModelStatusBadge status={m.status} /></p>
              {m.is_champion && <ChampionBadge />}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default function ModelRegistry() {
  const [models, setModels] = useState<ModelRegistryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<ModelRegistryEntry | null>(null);
  const [audit, setAudit] = useState<ModelAuditEntry[]>([]);
  const [showRegister, setShowRegister] = useState(false);
  const [compareIds, setCompareIds] = useState<Set<string>>(new Set());
  const [comparing, setComparing] = useState(false);
  const [comparisonModels, setComparisonModels] = useState<ModelRegistryEntry[] | null>(null);
  const [retireConfirm, setRetireConfirm] = useState<{ model: ModelRegistryEntry; comment: string } | null>(null);
  const [retireLoading, setRetireLoading] = useState(false);

  const loadModels = async () => {
    setError(null);
    try {
      const data = await api.listModels(filterType || undefined, filterStatus || undefined);
      setModels(data);
    } catch (e: any) {
      setError(e.message || 'Failed to load models');
    }
    finally { setLoading(false); }
  };

  useEffect(() => { loadModels(); }, [filterType, filterStatus]);

  const openDetail = async (model: ModelRegistryEntry) => {
    setSelectedModel(model);
    try { setAudit(await api.getModelAudit(model.model_id)); }
    catch { setAudit([]); }
  };

  const handleStatusChange = async (status: string, comment: string) => {
    if (!selectedModel) return;
    if (status === 'retired') {
      setRetireConfirm({ model: selectedModel, comment });
      return;
    }
    try {
      const updated = await api.updateModelStatus(selectedModel.model_id, status, getCurrentUser(), comment);
      setSelectedModel(updated);
      setAudit(await api.getModelAudit(updated.model_id));
      await loadModels();
    } catch (e: any) {
      setError(e?.message || 'Failed to update model status');
    }
  };

  const confirmRetire = async () => {
    if (!retireConfirm) return;
    setRetireLoading(true);
    try {
      const updated = await api.updateModelStatus(retireConfirm.model.model_id, 'retired', getCurrentUser(), retireConfirm.comment);
      setSelectedModel(updated);
      setAudit(await api.getModelAudit(updated.model_id));
      await loadModels();
    } finally {
      setRetireLoading(false);
      setRetireConfirm(null);
    }
  };

  const handlePromote = async () => {
    if (!selectedModel) return;
    try {
      const updated = await api.promoteChampion(selectedModel.model_id, getCurrentUser());
      setSelectedModel(updated);
      setAudit(await api.getModelAudit(updated.model_id));
      await loadModels();
    } catch (e: any) {
      setError(e?.message || 'Failed to promote model');
    }
  };

  const handleRegister = async (data: Partial<ModelRegistryEntry>) => {
    await api.registerModel(data);
    setShowRegister(false);
    await loadModels();
  };

  const toggleCompare = (id: string) => {
    setCompareIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else if (next.size < 3) next.add(id);
      return next;
    });
  };

  const runComparison = async () => {
    if (compareIds.size < 2) return;
    setComparing(true);
    try {
      const result = await api.compareModels(Array.from(compareIds));
      setComparisonModels(result);
    } finally { setComparing(false); }
  };

  if (loading) return <PageLoader />;

  if (error && models.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="Model Registry" subtitle="IFRS 9 model governance, versioning, and lifecycle management" />
        <ErrorDisplay
          title="Failed to load model registry"
          message={error}
          technicalDetails={error}
          onRetry={() => { setLoading(true); loadModels(); }}
          onDismiss={() => setError(null)}
        />
      </div>
    );
  }

  const totalModels = models.length;
  const activeModels = models.filter(m => m.status === 'active').length;
  const champions = models.filter(m => m.is_champion).length;
  const pendingReview = models.filter(m => m.status === 'pending_review').length;

  const columns = [
    {
      key: '_compare', label: '',
      format: (_: any, row: ModelRegistryEntry) => (
        <input type="checkbox" checked={compareIds.has(row.model_id)}
          onChange={() => toggleCompare(row.model_id)}
          onClick={(e) => e.stopPropagation()}
          className="w-3.5 h-3.5 rounded border-slate-300 text-brand focus:ring-brand/20 cursor-pointer" />
      ),
    },
    { key: 'model_name', label: 'Model Name', format: (v: string, row: ModelRegistryEntry) => (
      <div className="flex items-center gap-2">
        <span className="font-semibold text-slate-700 dark:text-slate-200">{v}</span>
        {row.is_champion && <ChampionBadge />}
      </div>
    )},
    { key: 'model_type', label: 'Type', format: (v: string) => (
      <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{v}</span>
    )},
    { key: 'version', label: 'Version', align: 'center' as const, format: (v: number) => `v${v}` },
    { key: 'algorithm', label: 'Algorithm' },
    { key: 'status', label: 'Status', format: (v: string) => <ModelStatusBadge status={v} /> },
    { key: 'performance_metrics', label: 'AUC', align: 'right' as const, format: (v: Record<string, any>) => {
      const auc = v?.auc;
      return auc != null ? <span className="font-mono font-semibold">{fmtNumber(auc, 4)}</span> : '—';
    }},
    { key: '_gini', label: 'Gini', align: 'right' as const, format: (_: any, row: ModelRegistryEntry) => {
      const gini = row.performance_metrics?.gini as number | null | undefined;
      return gini != null ? <span className="font-mono font-semibold">{fmtNumber(gini, 4)}</span> : '—';
    }},
    { key: 'created_at', label: 'Created', format: (v: string) => (
      <span className="text-slate-400">{fmtDateTime(v)}</span>
    )},
    { key: '_action', label: '', format: (_: any, row: ModelRegistryEntry) => (
      <button onClick={(e) => { e.stopPropagation(); openDetail(row); }}
        className="p-1.5 rounded-lg hover:bg-brand/10 transition">
        <Eye size={14} className="text-brand" />
      </button>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="Model Registry" subtitle="IFRS 9 model governance, versioning, and lifecycle management">
        <button onClick={() => setShowRegister(!showRegister)}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition shadow-sm ${
            showRegister ? 'btn-secondary' : 'btn-primary'
          }`}>
          {showRegister ? <X size={14} /> : <Plus size={14} />}
          {showRegister ? 'Cancel' : 'Register Model'}
        </button>
      </PageHeader>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Total Models" value={String(totalModels)} subtitle="Registered versions" color="blue" icon={<Box size={20} />} />
        <KpiCard title="Active Models" value={String(activeModels)} subtitle="In production" color="green" icon={<Activity size={20} />} />
        <KpiCard title="Champions" value={String(champions)} subtitle="Best per type" color="amber" icon={<Trophy size={20} />} />
        <KpiCard title="Pending Review" value={String(pendingReview)} subtitle="Awaiting approval" color={pendingReview > 0 ? 'amber' : 'navy'} icon={<Clock size={20} />} />
      </div>

      <AnimatePresence>
        {showRegister && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}>
            <Card title="Register New Model" subtitle="Add a new model version to the registry" accent="brand" icon={<Plus size={16} />}>
              <RegisterForm onSubmit={handleRegister} onCancel={() => setShowRegister(false)} />
            </Card>
          </motion.div>
        )}
      </AnimatePresence>

      {comparisonModels && (
        <ComparisonView models={comparisonModels} onClose={() => { setComparisonModels(null); setCompareIds(new Set()); }} />
      )}

      <Card title="Model Inventory" subtitle="All registered model versions"
        icon={<Shield size={16} />}
        action={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Filter size={13} className="text-slate-400" />
              <label className="sr-only" htmlFor="model-filter-type">Filter by model type</label>
              <select id="model-filter-type" value={filterType} onChange={e => setFilterType(e.target.value)}
                onClick={e => e.stopPropagation()}
                className="text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 focus:ring-1 focus:ring-brand/20">
                <option value="">All Types</option>
                {MODEL_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <label className="sr-only" htmlFor="model-filter-status">Filter by status</label>
              <select id="model-filter-status" value={filterStatus} onChange={e => setFilterStatus(e.target.value)}
                onClick={e => e.stopPropagation()}
                className="text-xs border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 focus:ring-1 focus:ring-brand/20">
                <option value="">All Statuses</option>
                {Object.entries(STATUS_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
              </select>
            </div>
            {compareIds.size >= 2 && (
              <button onClick={runComparison} disabled={comparing}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-purple-600 text-white hover:bg-purple-700 transition shadow-sm disabled:opacity-40">
                <GitCompare size={13} /> Compare ({compareIds.size})
              </button>
            )}
          </div>
        }>
        {models.length === 0 ? (
          <EmptyState
            icon={<Box size={48} />}
            title="No models registered yet"
            description="Register your first PD, LGD, or EAD model to get started."
            action={{ label: 'Register Model', onClick: () => setShowRegister(true) }}
          />
        ) : (
          <DataTable columns={columns} data={models} pageSize={12} onRowClick={openDetail} exportName="model_registry" />
        )}
      </Card>

      <AnimatePresence>
        {selectedModel && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/30 z-40" onClick={() => setSelectedModel(null)}
              onKeyDown={e => { if (e.key === 'Escape') setSelectedModel(null); }}
              role="presentation" />
            <DetailPanel model={selectedModel} audit={audit} onClose={() => setSelectedModel(null)}
              onStatusChange={handleStatusChange} onPromote={handlePromote} />
          </>
        )}
      </AnimatePresence>

      <ConfirmDialog
        open={!!retireConfirm}
        title="Retire Model"
        description={`Are you sure you want to retire "${retireConfirm?.model.model_name}"? Retired models cannot be used in production and this action should only be taken when a replacement model is active.`}
        confirmLabel="Retire Model"
        variant="danger"
        icon={<Archive size={16} className="text-red-500" />}
        onConfirm={confirmRetire}
        onCancel={() => setRetireConfirm(null)}
        loading={retireLoading}
      />
    </div>
  );
}
