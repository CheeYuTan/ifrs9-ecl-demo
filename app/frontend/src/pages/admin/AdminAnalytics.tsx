import { useState, useEffect } from 'react';
import {
  BarChart3, Users, FolderKanban, Activity, Clock, AlertTriangle,
  Brain, RefreshCw,
} from 'lucide-react';
import { fetchJson } from './types';

interface AnalyticsSummary {
  total_requests_7d: number;
  unique_users_7d: number;
  avg_latency_ms: number;
  error_count_7d: number;
  requests_today: number;
  total_projects: number;
  active_projects: number;
  active_models: number;
}

function MetricCard({ icon: Icon, label, value, sub, color }: {
  icon: typeof BarChart3; label: string; value: string | number; sub?: string;
  color: string;
}) {
  return (
    <div className="bg-white dark:bg-slate-800/80 border border-gray-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
          <Icon size={16} className="text-white" />
        </div>
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-2xl font-extrabold text-slate-800 dark:text-white">{value}</p>
      {sub && <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function AdminAnalytics() {
  const [data, setData] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const d = await fetchJson<AnalyticsSummary>('/api/admin/analytics/summary');
      setData(d);
    } catch (e: any) {
      setError(e.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-center">
          <div className="w-10 h-10 rounded-xl bg-indigo-500 flex items-center justify-center mx-auto mb-3 animate-pulse">
            <BarChart3 size={20} className="text-white" />
          </div>
          <p className="text-sm text-slate-400">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <AlertTriangle size={32} className="mx-auto mb-3 text-amber-500" />
        <p className="text-sm text-slate-500 dark:text-slate-400">{error}</p>
        <button onClick={load}
          className="mt-4 px-4 py-2 text-xs font-semibold bg-indigo-500 text-white rounded-xl hover:bg-indigo-600 transition">
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const errorRate = data.total_requests_7d > 0
    ? ((data.error_count_7d / data.total_requests_7d) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-800 dark:text-white">Platform Analytics</h3>
          <p className="text-xs text-slate-400 mt-0.5">Last 7 days overview</p>
        </div>
        <button onClick={load}
          className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700 transition">
          <RefreshCw size={13} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={Users} label="Unique Users" value={data.unique_users_7d}
          sub="Last 7 days" color="bg-blue-500" />
        <MetricCard icon={Activity} label="API Requests" value={data.total_requests_7d.toLocaleString()}
          sub={`${data.requests_today.toLocaleString()} today`} color="bg-emerald-500" />
        <MetricCard icon={FolderKanban} label="Projects" value={data.total_projects}
          sub={`${data.active_projects} active`} color="bg-violet-500" />
        <MetricCard icon={Brain} label="Active Models" value={data.active_models}
          sub="In model registry" color="bg-amber-500" />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard icon={Clock} label="Avg Latency" value={`${Number(data.avg_latency_ms).toFixed(0)}ms`}
          sub="p50 response time" color="bg-cyan-500" />
        <MetricCard icon={AlertTriangle} label="Error Rate"
          value={`${errorRate}%`}
          sub={`${data.error_count_7d} errors / ${data.total_requests_7d} requests`}
          color={Number(errorRate) > 5 ? 'bg-red-500' : 'bg-slate-500'} />
        <MetricCard icon={BarChart3} label="Requests Today"
          value={data.requests_today.toLocaleString()}
          sub="Since midnight" color="bg-indigo-500" />
      </div>

      <div className="bg-white dark:bg-slate-800/80 border border-gray-200 dark:border-slate-700 rounded-2xl p-5 shadow-sm">
        <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200 mb-2">Lakeview Dashboard</h4>
        <p className="text-xs text-slate-400 dark:text-slate-500 leading-relaxed">
          For detailed analytics with charts and time-series, provision the Databricks Lakeview dashboard.
          Run <code className="bg-slate-100 dark:bg-slate-700 px-1.5 py-0.5 rounded text-xs">python -m dashboards.provision_dashboard</code> from
          the app directory. The dashboard includes 7 pages: User Activity, Project Analytics, Model Performance,
          Job Execution, API Usage, Cost Allocation, and System Health.
        </p>
      </div>
    </div>
  );
}
