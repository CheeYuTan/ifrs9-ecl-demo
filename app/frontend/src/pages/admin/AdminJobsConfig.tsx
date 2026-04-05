import { useState } from 'react';
import {
  Cpu, Briefcase, Globe, Plug,
  ToggleLeft, ToggleRight,
  Loader2, Zap, CheckCircle2, XCircle,
  ArrowRight, Layers,
} from 'lucide-react';
import Card from '../../components/Card';
import { useToast } from '../../components/Toast';
import { fetchJson, inputCls, labelCls } from './types';
import type { AdminConfig } from './types';

export interface AdminJobsConfigProps {
  config: AdminConfig;
  onChange: (c: AdminConfig) => void;
}

export default function AdminJobsConfig({ config, onChange }: AdminJobsConfigProps) {
  const { toast } = useToast();
  const [testing, setTesting] = useState(false);
  const [connStatus, setConnStatus] = useState<any>(null);
  const [detecting, setDetecting] = useState(false);
  const jobs = config.jobs;

  const update = (field: string, value: any) => {
    onChange({ ...config, jobs: { ...jobs, [field]: value } });
  };

  const updateJobId = (key: string, val: string) => {
    onChange({ ...config, jobs: { ...jobs, job_ids: { ...jobs.job_ids, [key]: parseInt(val) || 0 } } });
  };

  const handleAutoDetect = async () => {
    setDetecting(true);
    try {
      const result = await fetchJson<any>('/api/admin/auto-detect-workspace');
      if (result.detected) {
        const updated = { ...config, jobs: { ...jobs, workspace_url: result.workspace_url, workspace_id: result.workspace_id || jobs.workspace_id } };
        onChange(updated);
        toast('Workspace auto-detected from environment', 'success');
      } else {
        toast('Could not auto-detect workspace. Set manually.', 'info');
      }
    } catch (e: any) { toast(`Auto-detect failed: ${e.message}`, 'error'); }
    finally { setDetecting(false); }
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const result = await fetchJson<any>('/api/admin/test-connection', { method: 'POST' });
      setConnStatus(result);
      if (result.connected) toast('Lakebase connection successful', 'success');
      else toast(`Connection failed: ${result.error}`, 'error');
    } catch (e: any) { toast(`Connection test failed: ${e.message}`, 'error'); }
    finally { setTesting(false); }
  };

  return (
    <div className="space-y-4">
      <Card accent="blue" icon={<Globe size={16} />} title="Databricks Workspace" subtitle="Auto-detected from app environment"
        action={
          <button onClick={handleAutoDetect} disabled={detecting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-gradient-to-r from-blue to-indigo text-white rounded-xl hover:opacity-80 transition disabled:opacity-50 shadow-sm">
            {detecting ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
            {detecting ? 'Detecting...' : 'Auto-Detect'}
          </button>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={labelCls}>Workspace URL</label>
            <input value={jobs.workspace_url} onChange={e => update('workspace_url', e.target.value)} placeholder="https://..." className={inputCls} />
          </div>
          <div>
            <label className={labelCls}>Workspace ID</label>
            <input value={jobs.workspace_id} onChange={e => update('workspace_id', e.target.value)} className={inputCls} />
          </div>
        </div>
        {jobs.workspace_url && (
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-300">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span>Connected to <span className="font-mono text-slate-600 dark:text-slate-300">{jobs.workspace_url.replace('https://', '')}</span></span>
          </div>
        )}
      </Card>

      <Card icon={<Briefcase size={16} />} title="Job IDs" subtitle="Databricks Job IDs for each pipeline">
        <div className="space-y-3">
          {Object.entries(jobs.job_ids).map(([key, id]) => (
            <div key={key} className="grid grid-cols-12 gap-3 items-center">
              <div className="col-span-4">
                <span className="text-sm font-semibold text-slate-700 dark:text-slate-200">{key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</span>
              </div>
              <div className="col-span-6">
                <input value={id} onChange={e => updateJobId(key, e.target.value)} className={`${inputCls} font-mono`} />
              </div>
              <div className="col-span-2">
                {jobs.workspace_url && (
                  <a href={`${jobs.workspace_url}/?o=${jobs.workspace_id}#job/${id}`} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-brand hover:text-brand-dark font-semibold flex items-center gap-1">View <ArrowRight size={10} /></a>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card icon={<Layers size={16} />} title="Default Job Parameters" subtitle="Passed to notebook jobs">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(jobs.default_job_params).map(([key, val]) => (
            <div key={key}>
              <label className={labelCls}>{key.replace(/_/g, ' ')}</label>
              <input value={val} onChange={e => onChange({ ...config, jobs: { ...jobs, default_job_params: { ...jobs.default_job_params, [key]: e.target.value } } })} className={inputCls} />
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card icon={<Cpu size={16} />} title="Compute">
          <button onClick={() => update('compute', { ...jobs.compute, use_serverless: !jobs.compute.use_serverless })}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border-2 transition ${jobs.compute.use_serverless ? 'border-brand/30 bg-brand/5' : 'border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800'}`}>
            {jobs.compute.use_serverless ? <ToggleRight size={20} className="text-brand" /> : <ToggleLeft size={20} className="text-slate-400" />}
            <span className="text-sm font-semibold">Serverless Compute</span>
          </button>
        </Card>

        <Card icon={<Plug size={16} />} title="Connection Test">
          <div className="flex items-center gap-3">
            <button onClick={testConnection} disabled={testing}
              className="flex items-center gap-2 px-4 py-2 text-xs font-semibold gradient-brand text-white rounded-xl hover:opacity-80 transition disabled:opacity-50 shadow-sm">
              <Plug size={14} /> {testing ? 'Testing...' : 'Test Connection'}
            </button>
            {connStatus && (
              <div className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-semibold ${connStatus.connected ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}`}>
                {connStatus.connected ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                {connStatus.connected ? 'Connected' : 'Failed'}
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
