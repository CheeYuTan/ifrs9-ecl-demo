import { useState, useEffect, useRef } from 'react';
import {
  Plug, Layers, Info, Download, Upload,
  RotateCcw, Wand2,
} from 'lucide-react';
import Card from '../../components/Card';
import { useToast } from '../../components/Toast';
import { fetchJson } from './types';
import type { AdminConfig } from './types';

function Badge({ variant, children }: { variant: 'green' | 'red'; children: React.ReactNode }) {
  const cls = variant === 'green'
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : 'bg-red-50 text-red-700 border-red-200';
  return <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${cls}`}>{children}</span>;
}

export interface AdminSystemConfigProps {
  config: AdminConfig;
  onReload: () => void;
}

export default function AdminSystemConfig({ config, onReload }: AdminSystemConfigProps) {
  const { toast } = useToast();
  const [resetting, setResetting] = useState(false);
  const [connStatus, setConnStatus] = useState<any>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleReset = async () => {
    if (!window.confirm('Reset ALL configuration to factory defaults?')) return;
    setResetting(true);
    try { await fetchJson('/api/admin/seed-defaults', { method: 'POST' }); toast('Configuration reset', 'success'); onReload(); }
    catch (e: any) { toast(`Reset failed: ${e.message}`, 'error'); }
    finally { setResetting(false); }
  };

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `ecl-config-${new Date().toISOString().slice(0, 10)}.json`; a.click();
    URL.revokeObjectURL(url);
    toast('Configuration exported', 'success');
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (ev) => {
      try {
        const imported = JSON.parse(ev.target?.result as string);
        const missing = ['data_sources', 'model', 'jobs', 'app_settings'].filter(s => !(s in imported));
        if (missing.length > 0) { toast(`Invalid: missing ${missing.join(', ')}`, 'error'); return; }
        if (!window.confirm('Import this configuration?')) return;
        await fetchJson('/api/admin/config', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(imported) });
        toast('Configuration imported', 'success'); onReload();
      } catch (err: any) { toast(`Import failed: ${err.message}`, 'error'); }
    };
    reader.readAsText(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  useEffect(() => {
    fetchJson<any>('/api/admin/test-connection', { method: 'POST' }).then(setConnStatus).catch(() => setConnStatus({ connected: false, error: 'Request failed' }));
  }, []);

  return (
    <div className="space-y-4">
      <Card accent="brand" icon={<Plug size={16} />} title="Connection Status" subtitle="Current system connectivity">
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${connStatus?.connected ? 'bg-emerald-500 shadow-lg shadow-emerald-500/30' : connStatus ? 'bg-red-500' : 'bg-slate-300 animate-pulse'}`} />
            <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">Lakebase PostgreSQL</span>
            {connStatus?.connected && <Badge variant="green">Connected</Badge>}
            {connStatus && !connStatus.connected && <Badge variant="red">Disconnected</Badge>}
          </div>
          {connStatus?.connected && (
            <div className="ml-6 text-xs text-slate-400 space-y-0.5">
              <p>Schema: <span className="font-mono text-slate-600">{connStatus.schema}</span></p>
              <p>Prefix: <span className="font-mono text-slate-600">{connStatus.prefix}</span></p>
            </div>
          )}
        </div>
      </Card>

      <Card icon={<Layers size={16} />} title="Configuration Management">
        <div className="flex flex-wrap gap-3">
          <button onClick={handleExport} className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition text-slate-700 dark:text-slate-200 shadow-sm">
            <Download size={14} /> Export Config
          </button>
          <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition text-slate-700 dark:text-slate-200 shadow-sm">
            <Upload size={14} /> Import Config
          </button>
          <input ref={fileInputRef} type="file" accept=".json" onChange={handleImport} className="hidden" aria-label="Import configuration file" />
          <div className="flex-1" />
          <button onClick={async () => {
            try {
              await fetch('/api/setup/reset', { method: 'POST' });
              toast('Setup wizard will show on next page load', 'info');
              setTimeout(() => window.location.reload(), 1000);
            } catch (e: any) { toast(`Failed: ${e.message}`, 'error'); }
          }}
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold bg-amber-50 border border-amber-200 rounded-xl hover:bg-amber-100 transition text-amber-700">
            <Wand2 size={14} /> Re-run Setup Wizard
          </button>
          <button onClick={handleReset} disabled={resetting}
            className="flex items-center gap-2 px-4 py-2.5 text-xs font-semibold bg-red-50 border border-red-200 rounded-xl hover:bg-red-100 transition text-red-700 disabled:opacity-50">
            <RotateCcw size={14} /> {resetting ? 'Resetting...' : 'Reset to Defaults'}
          </button>
        </div>
      </Card>

      <Card icon={<Info size={16} />} title="About">
        <div className="space-y-2 text-xs text-slate-500">
          {[
            ['Application', config.app_settings.app_title],
            ['Framework', config.app_settings.framework],
            ['Model Version', config.app_settings.model_version],
            ['Stack', 'FastAPI + React + Databricks Lakebase'],
          ].map(([label, val]) => (
            <div key={label} className="flex justify-between">
              <span>{label}</span>
              <span className="font-semibold text-slate-700 dark:text-slate-200">{val}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
