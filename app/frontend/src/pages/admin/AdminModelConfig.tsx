import { useState } from 'react';
import {
  Cpu, Lock, Target, TrendingUp,
  ToggleLeft, ToggleRight, Plus, Trash2,
  Loader2, Sparkles, HelpCircle,
} from 'lucide-react';
import Card from '../../components/Card';
import { useToast } from '../../components/Toast';
import { fetchJson, inputCls, labelCls, PARAM_LABELS, SICR_LABELS } from './types';
import type { AdminConfig, LgdAssumption } from './types';

function Tooltip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex ml-1 cursor-help">
      <HelpCircle size={11} className="text-slate-300 group-hover:text-slate-500 dark:group-hover:text-slate-400 transition" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 text-[10px] leading-tight bg-slate-800 text-white rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition pointer-events-none w-52 z-50 text-center">
        {text}
      </span>
    </span>
  );
}

export interface AdminModelConfigProps {
  config: AdminConfig;
  onChange: (c: AdminConfig) => void;
}

export default function AdminModelConfig({ config, onChange }: AdminModelConfigProps) {
  const { toast } = useToast();
  const [newProductKey, setNewProductKey] = useState('');
  const [showSicr, setShowSicr] = useState(false);
  const [discoveredProducts, setDiscoveredProducts] = useState<any[]>([]);
  const [discovering, setDiscovering] = useState(false);
  const models = config.model.satellite_models;
  const params = config.model.default_parameters;
  const sicr = config.model.sicr_thresholds;
  const lgd = config.model.lgd_assumptions;

  const toggleModel = (key: string) => {
    const updated = { ...config };
    updated.model = { ...updated.model, satellite_models: { ...models, [key]: { ...models[key], enabled: !models[key].enabled } } };
    onChange(updated);
  };

  const updateParam = (key: string, val: number) => {
    const updated = { ...config };
    updated.model = { ...updated.model, default_parameters: { ...params, [key]: val } };
    onChange(updated);
  };

  const updateSicr = (key: string, val: number) => {
    const updated = { ...config };
    updated.model = { ...updated.model, sicr_thresholds: { ...sicr, [key]: val } };
    onChange(updated);
  };

  const updateLgd = (product: string, field: 'lgd' | 'cure_rate', val: number) => {
    const updated = { ...config };
    updated.model = { ...updated.model, lgd_assumptions: { ...lgd, [product]: { ...lgd[product], [field]: val } } };
    onChange(updated);
  };

  const addLgdProduct = () => {
    if (!newProductKey.trim()) return;
    const key = newProductKey.trim().toLowerCase().replace(/\s+/g, '_');
    if (lgd[key]) { toast(`Product "${key}" already exists`, 'error'); return; }
    const updated = { ...config };
    updated.model = { ...updated.model, lgd_assumptions: { ...lgd, [key]: { lgd: 0.40, cure_rate: 0.20 } } };
    onChange(updated);
    setNewProductKey('');
  };

  const removeLgdProduct = (product: string) => {
    if (!window.confirm(`Remove LGD assumptions for "${product}"?`)) return;
    const updated = { ...config };
    const newLgd = { ...lgd };
    delete newLgd[product];
    updated.model = { ...updated.model, lgd_assumptions: newLgd };
    onChange(updated);
  };

  const handleDiscoverProducts = async () => {
    setDiscovering(true);
    try {
      const products = await fetchJson<any[]>('/api/admin/discover-products');
      setDiscoveredProducts(products);
      if (products.length === 0) { toast('No products found in data', 'info'); return; }
      const autoLgd = await fetchJson<Record<string, LgdAssumption>>('/api/admin/auto-setup-lgd', { method: 'POST' });
      const updated = { ...config };
      updated.model = { ...updated.model, lgd_assumptions: { ...autoLgd } };
      onChange(updated);
      toast(`Discovered ${products.length} products from data`, 'success');
    } catch (e: any) { toast(`Discovery failed: ${e.message}`, 'error'); }
    finally { setDiscovering(false); }
  };

  const enabledCount = Object.values(models).filter(m => m.enabled).length;

  return (
    <div className="space-y-4">
      <Card accent="blue" icon={<Target size={16} />} title="Satellite Models" subtitle={`${enabledCount}/${Object.keys(models).length} models enabled`}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Object.entries(models).map(([key, m]) => (
            <button key={key} onClick={() => toggleModel(key)}
              className={`flex items-center gap-3 p-3 rounded-xl border-2 transition-all ${m.enabled ? 'border-brand/30 bg-brand/5 shadow-sm' : 'border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-800/50 opacity-60'}`}>
              {m.enabled ? <ToggleRight size={20} className="text-brand" /> : <ToggleLeft size={20} className="text-slate-400" />}
              <span className={`text-xs font-semibold ${m.enabled ? 'text-brand-dark' : 'text-slate-500 dark:text-slate-400'}`}>{m.label}</span>
            </button>
          ))}
        </div>
      </Card>

      <Card accent="purple" icon={<Cpu size={16} />} title="Simulation Parameters" subtitle="Monte Carlo engine defaults">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(params).map(([key, val]) => {
            const meta = PARAM_LABELS[key];
            return (
              <div key={key}>
                <label className={labelCls}>{meta?.label || key.replace(/_/g, ' ')}{meta?.help && <Tooltip text={meta.help} />}</label>
                <input type="number" step={key === 'n_simulations' ? 100 : 0.01} value={val}
                  onChange={e => updateParam(key, parseFloat(e.target.value) || 0)} className={inputCls} />
              </div>
            );
          })}
        </div>
      </Card>

      <Card icon={<Lock size={16} />} title="SICR Thresholds" subtitle="IFRS 9 stage transition triggers"
        action={
          <button onClick={() => setShowSicr(!showSicr)} className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition">
            {showSicr ? 'Hide' : 'Show'} <span className={`ml-1 transition-transform inline-block ${showSicr ? 'rotate-180' : ''}`}>▾</span>
          </button>
        }
      >
        {!showSicr ? (
          <div className="flex items-center gap-2 p-3 bg-slate-50 dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700">
            <span className="text-xs text-slate-500 dark:text-slate-400">Using IFRS 9 standard defaults (DPD 30/90/90, PD relative 2x, PD absolute 0.5%). These rarely need changing.</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {Object.entries(sicr).map(([key, val]) => {
              const meta = SICR_LABELS[key];
              return (
                <div key={key}>
                  <label className={labelCls}>{meta?.label || key.replace(/_/g, ' ')}{meta?.help && <Tooltip text={meta.help} />}</label>
                  <input type="number" step={key.includes('threshold') && !key.includes('dpd') ? 0.001 : 1} value={val}
                    onChange={e => updateSicr(key, parseFloat(e.target.value) || 0)} className={inputCls} />
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <Card accent="brand" icon={<TrendingUp size={16} />} title="LGD Assumptions" subtitle="Loss Given Default per product type"
        action={
          <button onClick={handleDiscoverProducts} disabled={discovering}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold gradient-brand text-white rounded-xl hover:opacity-90 transition disabled:opacity-50 shadow-sm">
            {discovering ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
            {discovering ? 'Discovering...' : 'Auto-Discover from Data'}
          </button>
        }
      >
        {discoveredProducts.length > 0 && (
          <div className="mb-4 p-3 bg-brand/5 rounded-xl border border-brand/10">
            <p className="text-xs text-brand-dark font-semibold mb-1">Discovered {discoveredProducts.length} products from loan data:</p>
            <div className="flex flex-wrap gap-2">
              {discoveredProducts.map(p => (
                <span key={p.product_type} className="text-[10px] font-mono bg-white dark:bg-slate-800 rounded-lg px-2 py-1 border border-brand/15 text-slate-600 dark:text-slate-300">
                  {p.product_type} <span className="text-slate-400">({p.loan_count.toLocaleString()} loans)</span>
                </span>
              ))}
            </div>
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 dark:border-slate-700">
                <th className="text-left py-2 px-3 text-[10px] font-bold text-slate-400 uppercase">Product Type</th>
                <th className="text-left py-2 px-3 text-[10px] font-bold text-slate-400 uppercase">LGD <Tooltip text="Loss Given Default (0-1)" /></th>
                <th className="text-left py-2 px-3 text-[10px] font-bold text-slate-400 uppercase">Cure Rate <Tooltip text="Probability of cure (0-1)" /></th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(lgd).map(([product, vals]) => (
                <tr key={product} className="border-b border-slate-50 dark:border-slate-800 hover:bg-brand/3 transition">
                  <td className="py-2 px-3 font-mono text-xs font-semibold text-slate-700 dark:text-slate-200">{product}</td>
                  <td className="py-2 px-3">
                    <input type="number" step={0.01} min={0} max={1} value={vals.lgd}
                      onChange={e => updateLgd(product, 'lgd', parseFloat(e.target.value) || 0)}
                      className="w-24 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none" />
                  </td>
                  <td className="py-2 px-3">
                    <input type="number" step={0.01} min={0} max={1} value={vals.cure_rate}
                      onChange={e => updateLgd(product, 'cure_rate', parseFloat(e.target.value) || 0)}
                      className="w-24 px-2 py-1 rounded-lg border border-slate-200 dark:border-slate-700 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none" />
                  </td>
                  <td className="py-2 px-3">
                    <button onClick={() => removeLgdProduct(product)} aria-label={`Remove ${product}`} className="text-slate-300 hover:text-red-500 transition focus-visible:ring-2 focus-visible:ring-brand rounded"><Trash2 size={14} /></button>
                  </td>
                </tr>
              ))}
              <tr className="border-t border-slate-200 dark:border-slate-700 bg-slate-50/30 dark:bg-slate-800/30">
                <td className="py-2 px-3">
                  <input value={newProductKey} onChange={e => setNewProductKey(e.target.value)} onKeyDown={e => e.key === 'Enter' && addLgdProduct()}
                    placeholder="e.g. corporate_loan" className="w-full px-2 py-1 rounded-lg border border-dashed border-slate-300 dark:border-slate-600 text-xs font-mono focus:ring-2 focus:ring-brand/30 outline-none placeholder:text-slate-300 bg-white dark:bg-slate-800" />
                </td>
                <td className="py-2 px-3 text-xs text-slate-400 font-mono">0.40</td>
                <td className="py-2 px-3 text-xs text-slate-400 font-mono">0.20</td>
                <td className="py-2 px-3">
                  <button onClick={addLgdProduct} disabled={!newProductKey.trim()} className="text-brand hover:text-brand-dark disabled:text-slate-300 transition"><Plus size={14} /></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
