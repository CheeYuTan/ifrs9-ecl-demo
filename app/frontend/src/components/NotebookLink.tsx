import { useEffect, useState } from 'react';
import { Play, ExternalLink } from 'lucide-react';
import { api } from '../lib/api';

/* Notebook-key → display info and which backend job_key it belongs to */
const NOTEBOOK_META: Record<string, { label: string; description: string; jobKey: string }> = {
  '01_generate_data': {
    label: 'Generate Demo Data',
    description: 'Synthetic data generation for demo (not for production)',
    jobKey: 'demo_data',
  },
  '02_run_data_processing': {
    label: 'Full Pipeline',
    description: 'Process mapped data → Models → ECL → Sync',
    jobKey: 'full_pipeline',
  },
  '03a_satellite_model': {
    label: 'Satellite Model Pipeline',
    description: '8 regression models per product × cohort',
    jobKey: 'satellite_ecl_sync',
  },
  '03b_run_ecl_calculation': {
    label: 'ECL Calculation Pipeline',
    description: 'Monte Carlo ECL with satellite model coefficients + sync',
    jobKey: 'satellite_ecl_sync',
  },
  '04_sync_to_lakebase': {
    label: 'Sync to Lakebase',
    description: 'UC Delta → Lakebase PostgreSQL sync',
    jobKey: 'satellite_ecl_sync',
  },
};

interface Props {
  notebooks: string[];
  compact?: boolean;
}

export default function NotebookLink({ notebooks, compact }: Props) {
  const [jobIds, setJobIds] = useState<Record<string, number>>({});
  const [wsHost, setWsHost] = useState('');
  const [wsId, setWsId] = useState('');

  useEffect(() => {
    api.jobsConfig().then((cfg: any) => {
      const ids: Record<string, number> = {};
      if (cfg.job_ids) {
        for (const [k, v] of Object.entries(cfg.job_ids)) {
          ids[k] = Number(v);
        }
      }
      if (cfg.jobs) {
        for (const [k, v] of Object.entries(cfg.jobs as Record<string, any>)) {
          if (v?.job_id && !ids[k]) ids[k] = Number(v.job_id);
        }
      }
      setJobIds(ids);
      // Extract workspace URL info if available
      const host = cfg.workspace_url || cfg.workspace_host || '';
      const id = cfg.workspace_id || '';
      if (host) setWsHost(host.replace(/\/+$/, ''));
      if (id) setWsId(id);
    }).catch(() => {});
  }, []);

  const buildUrl = (jobId: number): string | null => {
    if (wsHost && wsId) return `${wsHost}/?o=${wsId}#job/${jobId}`;
    if (wsHost) return `${wsHost}/#job/${jobId}`;
    return null;
  };

  const seen = new Set<string>();
  const items = notebooks
    .map(k => {
      const meta = NOTEBOOK_META[k];
      if (!meta) return null;
      const jobId = jobIds[meta.jobKey];
      return { ...meta, jobId, notebookKey: k };
    })
    .filter(Boolean)
    .filter(item => {
      // De-duplicate by jobKey (same job shouldn't show twice)
      if (seen.has(item!.jobKey)) return false;
      seen.add(item!.jobKey);
      return true;
    }) as Array<{ label: string; description: string; jobKey: string; jobId: number | undefined; notebookKey: string }>;

  if (!items.length) return null;

  if (compact) {
    return (
      <div className="flex items-center gap-3 flex-wrap">
        <Play size={12} className="text-slate-400 flex-shrink-0" />
        {items.map((item) => {
          const url = item.jobId ? buildUrl(item.jobId) : null;
          return url ? (
            <a
              key={item.jobKey}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[10px] font-semibold text-brand hover:underline"
            >
              {item.label} <ExternalLink size={9} />
            </a>
          ) : (
            <span key={item.jobKey} className="text-[10px] font-semibold text-slate-500">{item.label} (not provisioned)</span>
          );
        })}
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg bg-indigo-50/50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800">
      <Play size={16} className="text-indigo-500 mt-0.5 flex-shrink-0" />
      <div className="flex-1 min-w-0">
        <p className="text-[10px] font-semibold text-slate-500 uppercase mb-1.5">Databricks Jobs</p>
        <div className="space-y-1">
          {items.map((item) => {
            const url = item.jobId ? buildUrl(item.jobId) : null;
            return url ? (
              <a
                key={item.jobKey}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between group"
              >
                <div>
                  <span className="text-xs font-semibold text-indigo-700 group-hover:underline">{item.label}</span>
                  <span className="text-[10px] text-slate-500 ml-2">{item.description}</span>
                </div>
                <ExternalLink size={11} className="text-indigo-400 flex-shrink-0 opacity-0 group-hover:opacity-100 transition" />
              </a>
            ) : (
              <div key={item.jobKey} className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-semibold text-slate-500">{item.label}</span>
                  <span className="text-[10px] text-slate-500 ml-2">Not provisioned — go to Admin → Jobs to set up</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
