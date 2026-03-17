import { useState } from 'react';
import { motion } from 'framer-motion';
import { FolderPlus, Calendar, FileText, Briefcase, User } from 'lucide-react';
import Card from '../components/Card';
import type { Project, AuditEntry } from '../lib/api';
import { fmtDateTime } from '../lib/format';
import { config } from '../lib/config';

interface Props {
  project: Project | null;
  onCreate: (data: { project_id: string; project_name: string; project_type: string; description: string; reporting_date: string }) => Promise<void>;
}

export default function CreateProject({ project, onCreate }: Props) {
  const [pid, setPid] = useState(project?.project_id || '');
  const [name, setName] = useState(project?.project_name || '');
  const [ptype, setPtype] = useState(project?.project_type || 'ifrs9');
  const [rdate, setRdate] = useState(project?.reporting_date || config.defaultReportingDate);
  const [desc, setDesc] = useState(project?.description || '');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const handleSubmit = async () => {
    if (!pid || !name) { setMsg('Project ID and Name are required'); return; }
    setLoading(true);
    try {
      await onCreate({ project_id: pid, project_name: name, project_type: ptype, description: desc, reporting_date: rdate });
      setMsg('Project created successfully!');
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-slate-800">Create ECL Project</h2>
        <p className="text-sm text-slate-400 mt-1">Define the {config.framework} ECL run parameters for {config.bankName}</p>
      </div>

      <Card>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Project ID</label>
            <div className="relative">
              <FolderPlus size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300" />
              <input value={pid} onChange={e => setPid(e.target.value)} placeholder="Q4-2025-IFRS9"
                className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Project Name</label>
            <div className="relative">
              <Briefcase size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300" />
              <input value={name} onChange={e => setName(e.target.value)} placeholder="Q4 2025 IFRS 9 ECL"
                className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Accounting Framework</label>
            <select value={ptype} onChange={e => setPtype(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition bg-white">
              <option value="ifrs9">IFRS 9 — Expected Credit Loss (ECL)</option>
              <option value="cecl">CECL — Current Expected Credit Loss (US GAAP ASC 326)</option>
              <option value="stress">Regulatory Stress Test</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Reporting Date</label>
            <div className="relative">
              <Calendar size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300" />
              <input type="date" value={rdate} onChange={e => setRdate(e.target.value)}
                className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition" />
            </div>
          </div>
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5">Description</label>
            <div className="relative">
              <FileText size={16} className="absolute left-3 top-3 text-slate-300" />
              <textarea value={desc} onChange={e => setDesc(e.target.value)} rows={3}
                placeholder="Describe the ECL run scope, portfolios, and scenarios..."
                className="w-full pl-10 pr-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none" />
            </div>
          </div>
        </div>

        {/* Regulatory Context */}
        <div className="mt-4 pt-4 border-t border-slate-100">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <p className="text-[10px] font-semibold text-blue-400 uppercase">Accounting Standard</p>
              <p className="text-xs font-bold text-blue-700">{config.regulatoryFramework}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <p className="text-[10px] font-semibold text-blue-400 uppercase">Local Regulator</p>
              <p className="text-xs font-bold text-blue-700">{config.localRegulator}</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <p className="text-[10px] font-semibold text-blue-400 uppercase">Model Version</p>
              <p className="text-xs font-bold text-blue-700">ECL Engine {config.modelVersion} — Validated {config.lastValidation}</p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-5 pt-4 border-t border-slate-100">
          <button onClick={handleSubmit} disabled={loading}
            className="px-6 py-2.5 bg-brand text-white text-sm font-semibold rounded-lg hover:bg-brand-dark disabled:opacity-50 transition shadow-sm">
            {loading ? 'Creating...' : project ? 'Update Project' : 'Create Project'}
          </button>
          {msg && (
            <motion.span initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
              className={`text-sm font-medium ${msg.startsWith('Error') ? 'text-red-500' : 'text-emerald-500'}`}>
              {msg}
            </motion.span>
          )}
        </div>
      </Card>

      {project && project.audit_log?.length > 0 && (
        <Card title="Audit Trail" subtitle="Project activity log">
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {[...project.audit_log].reverse().map((a: AuditEntry, i: number) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User size={14} className="text-slate-400" />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-slate-700">{a.action}</p>
                  <p className="text-xs text-slate-400">{a.user} &middot; {fmtDateTime(a.ts)}</p>
                  {a.detail && <p className="text-xs text-slate-500 mt-0.5">{a.detail}</p>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
