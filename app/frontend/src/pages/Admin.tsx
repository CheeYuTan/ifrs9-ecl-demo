import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database, Settings, Cpu, Briefcase, Shield, Palette, Info, Save, Undo2,
  BarChart3,
} from 'lucide-react';
import { useToast } from '../components/Toast';
import { fetchJson } from './admin/types';
import type { AdminConfig } from './admin/types';
import AdminDataMappings from './admin/AdminDataMappings';
import AdminModelConfig from './admin/AdminModelConfig';
import AdminJobsConfig from './admin/AdminJobsConfig';
import AdminAppSettings from './admin/AdminAppSettings';
import AdminThemeConfig from './admin/AdminThemeConfig';
import AdminSystemConfig from './admin/AdminSystemConfig';
import AdminAnalytics from './admin/AdminAnalytics';

// ── Tab definition ──────────────────────────────────────────────────────────

const TABS = [
  { key: 'data', label: 'Data Mapping', icon: Database, desc: 'Map source tables' },
  { key: 'model', label: 'Model Config', icon: Cpu, desc: 'Models & parameters' },
  { key: 'jobs', label: 'Jobs & Pipelines', icon: Briefcase, desc: 'Workspace & jobs' },
  { key: 'app', label: 'App Settings', icon: Settings, desc: 'Organization & UI' },
  { key: 'theme', label: 'Theme', icon: Palette, desc: 'Colors & dark mode' },
  { key: 'system', label: 'System', icon: Shield, desc: 'Import / export' },
  { key: 'analytics', label: 'Analytics', icon: BarChart3, desc: 'Platform usage' },
] as const;

type TabKey = typeof TABS[number]['key'];

// ── Main Admin Page ─────────────────────────────────────────────────────────

export default function Admin() {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState<TabKey>('data');
  const [config, setConfig] = useState<AdminConfig | null>(null);
  const [savedConfig, setSavedConfig] = useState<AdminConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  const loadConfig = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchJson<AdminConfig>('/api/admin/config');
      setConfig(data); setSavedConfig(JSON.parse(JSON.stringify(data))); setDirty(false);
    } catch (e: any) { toast(`Failed to load config: ${e.message}`, 'error'); }
    finally { setLoading(false); }
  }, [toast]);

  useEffect(() => { loadConfig(); }, [loadConfig]);

  useEffect(() => {
    if (!dirty) return;
    const handler = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ''; };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [dirty]);

  const handleChange = (updated: AdminConfig) => { setConfig(updated); setDirty(true); };

  const handleDiscard = () => {
    if (!savedConfig || !window.confirm('Discard all unsaved changes?')) return;
    setConfig(JSON.parse(JSON.stringify(savedConfig))); setDirty(false); toast('Changes discarded', 'info');
  };

  const handleSave = async () => {
    if (!config) return;
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!config.app_settings.organization_name?.trim()) errors.push('Organization name is required');
    const totalWeight = config.app_settings.scenarios.reduce((s, sc) => s + (sc.weight || 0), 0);
    if (Math.abs(totalWeight - 1.0) > 0.01) errors.push(`Scenario weights sum to ${(totalWeight * 100).toFixed(1)}%`);
    for (const [product, vals] of Object.entries(config.model.lgd_assumptions)) {
      if (vals.lgd < 0 || vals.lgd > 1) errors.push(`LGD for "${product}" out of range`);
      if (vals.cure_rate < 0 || vals.cure_rate > 1) errors.push(`Cure rate for "${product}" out of range`);
    }
    if (!config.jobs.workspace_url?.trim()) warnings.push('Workspace URL is empty');
    if (Object.values(config.model.satellite_models).filter(m => m.enabled).length === 0) warnings.push('No satellite models enabled');

    if (errors.length > 0) { toast(`Cannot save: ${errors.join('; ')}`, 'error'); return; }

    setSaving(true);
    try {
      const saved = await fetchJson<AdminConfig>('/api/admin/config', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(config),
      });
      setConfig(saved); setSavedConfig(JSON.parse(JSON.stringify(saved))); setDirty(false);
      toast(warnings.length > 0 ? `Saved with warnings: ${warnings.join('; ')}` : 'Configuration saved', warnings.length > 0 ? 'info' : 'success');
    } catch (e: any) { toast(`Failed to save: ${e.message}`, 'error'); }
    finally { setSaving(false); }
  };

  if (loading || !config) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center mx-auto mb-3 animate-pulse">
            <Settings size={20} className="text-white" />
          </div>
          <p className="text-sm text-slate-400">Loading configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-11 h-11 rounded-2xl gradient-brand flex items-center justify-center shadow-lg">
            <Settings size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-extrabold text-slate-800 dark:text-white">Administration</h2>
            <p className="text-sm text-slate-400 mt-0.5">Configure data sources, models, jobs, and settings</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {dirty && (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-1.5 text-xs font-semibold text-amber-600 bg-amber-50 px-3 py-1.5 rounded-full border border-amber-200">
              <Info size={12} /> Unsaved changes
            </motion.div>
          )}
          {dirty && (
            <button onClick={handleDiscard}
              className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-slate-500 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition">
              <Undo2 size={14} /> Discard
            </button>
          )}
          <button onClick={handleSave} disabled={saving || !dirty}
            className="flex items-center gap-2 px-5 py-2.5 text-xs font-bold gradient-brand text-white rounded-xl hover:opacity-90 transition disabled:opacity-40 shadow-md">
            <Save size={14} /> {saving ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1.5 bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm rounded-2xl border border-gray-200 dark:border-slate-700 shadow-sm p-1.5 overflow-x-auto">
        {TABS.map(t => {
          const Icon = t.icon;
          const isActive = t.key === activeTab;
          return (
            <button key={t.key} onClick={() => setActiveTab(t.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-xl transition-all whitespace-nowrap ${
                isActive ? 'gradient-navy text-white shadow-md' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-slate-700/80 hover:text-slate-700 dark:hover:text-slate-300'
              }`}>
              <Icon size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
          {activeTab === 'data' && <AdminDataMappings config={config} onChange={handleChange} />}
          {activeTab === 'model' && <AdminModelConfig config={config} onChange={handleChange} />}
          {activeTab === 'jobs' && <AdminJobsConfig config={config} onChange={handleChange} />}
          {activeTab === 'app' && <AdminAppSettings config={config} onChange={handleChange} />}
          {activeTab === 'theme' && <AdminThemeConfig />}
          {activeTab === 'system' && <AdminSystemConfig config={config} onReload={loadConfig} />}
          {activeTab === 'analytics' && <AdminAnalytics />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
