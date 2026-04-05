import { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { FolderPlus, Calendar, FileText, Briefcase, User, Clock, CheckCircle2, ArrowRight } from 'lucide-react';
import Card from '../components/Card';
import type { Project, AuditEntry } from '../lib/api';
import { api } from '../lib/api';
import { fmtDateTime } from '../lib/format';
import { config } from '../lib/config';

interface Props {
  project: Project | null;
  onCreate: (data: { project_id: string; project_name: string; project_type: string; description: string; reporting_date: string }) => Promise<void>;
  onSelectProject?: (id: string) => void;
}

const PID_REGEX = /^[a-zA-Z0-9-]+$/;

interface FieldErrors {
  pid?: string;
  name?: string;
  rdate?: string;
}

export default function CreateProject({ project, onCreate, onSelectProject }: Props) {
  const [pid, setPid] = useState(project?.project_id || '');
  const [name, setName] = useState(project?.project_name || '');
  const [ptype, setPtype] = useState(project?.project_type || 'ifrs9');
  const [rdate, setRdate] = useState(project?.reporting_date || config.defaultReportingDate);
  const [desc, setDesc] = useState(project?.description || '');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [allProjects, setAllProjects] = useState<Project[]>([]);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.listProjects().then(setAllProjects).catch(() => {});
  }, []);

  const fieldErrors = useMemo((): FieldErrors => {
    const errors: FieldErrors = {};
    if (!pid.trim()) {
      errors.pid = 'Project ID is required';
    } else if (!PID_REGEX.test(pid)) {
      errors.pid = 'Only alphanumeric characters and hyphens allowed';
    } else if (pid.length > 50) {
      errors.pid = 'Maximum 50 characters';
    }

    if (!name.trim()) {
      errors.name = 'Project name is required';
    } else if (name.length > 200) {
      errors.name = 'Maximum 200 characters';
    }

    if (!rdate) {
      errors.rdate = 'Reporting date is required';
    } else {
      const d = new Date(rdate);
      if (isNaN(d.getTime())) {
        errors.rdate = 'Must be a valid date';
      } else {
        const oneYearFromNow = new Date();
        oneYearFromNow.setFullYear(oneYearFromNow.getFullYear() + 1);
        if (d > oneYearFromNow) {
          errors.rdate = 'Cannot be more than 1 year in the future';
        }
      }
    }
    return errors;
  }, [pid, name, rdate]);

  const isFormValid = Object.keys(fieldErrors).length === 0;

  const markTouched = (field: string) => setTouched(prev => ({ ...prev, [field]: true }));

  const handleSubmit = async () => {
    setTouched({ pid: true, name: true, rdate: true });
    if (!isFormValid) return;
    setLoading(true);
    try {
      await onCreate({ project_id: pid, project_name: name, project_type: ptype, description: desc, reporting_date: rdate });
      setMsg('Project created successfully!');
      api.listProjects().then(setAllProjects).catch(() => {});
    } catch (e: any) {
      setMsg(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-extrabold text-slate-800 dark:text-slate-100">Create ECL Project</h2>
        <p className="text-sm text-slate-400 mt-1">Define the {config.framework} ECL run parameters for {config.bankName}</p>
      </div>

      {allProjects.length > 0 && !project && (
        <Card accent="blue" icon={<FolderPlus size={16} />} title="Existing Projects" subtitle={`${allProjects.length} project(s) found`}>
          <div className="space-y-2">
            {allProjects.map(p => (
              <div key={p.project_id} onClick={() => onSelectProject?.(p.project_id)} role="button" tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && onSelectProject?.(p.project_id)}
                className="flex items-center gap-3 p-3 rounded-xl border border-slate-100 dark:border-slate-700 hover:border-brand/30 hover:bg-brand/3 transition group cursor-pointer">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${p.signed_off_by ? 'bg-emerald-50 text-emerald-600' : 'bg-blue-50 text-blue-600'}`}>
                  {p.signed_off_by ? <CheckCircle2 size={14} /> : <Clock size={14} />}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">{p.project_name || p.project_id}</p>
                  <p className="text-[11px] text-slate-400">
                    {p.project_id} &middot; {p.reporting_date} &middot; Step {(p.current_step ?? 0) + 1}/8
                    {p.signed_off_by && <span className="text-emerald-500 ml-1">Signed by {p.signed_off_by}</span>}
                  </p>
                </div>
                <ArrowRight size={14} className="text-slate-300 group-hover:text-brand transition" />
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card accent="brand">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label htmlFor="create-project-id" className="form-label">Project ID</label>
            <div className="relative">
              <FolderPlus size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" aria-hidden="true" />
              <input id="create-project-id" value={pid}
                onChange={e => setPid(e.target.value)}
                onBlur={() => markTouched('pid')}
                placeholder="Q4-2025-IFRS9"
                maxLength={50}
                className={`form-input pl-11 ${touched.pid && fieldErrors.pid ? 'border-red-300 focus:ring-red-200' : ''}`} />
            </div>
            {touched.pid && fieldErrors.pid && (
              <p className="text-xs text-red-500 mt-1">{fieldErrors.pid}</p>
            )}
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{pid.length}/50 characters</p>
          </div>
          <div>
            <label htmlFor="create-project-name" className="form-label">Project Name</label>
            <div className="relative">
              <Briefcase size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" aria-hidden="true" />
              <input id="create-project-name" value={name}
                onChange={e => setName(e.target.value)}
                onBlur={() => markTouched('name')}
                placeholder="Q4 2025 IFRS 9 ECL"
                maxLength={200}
                className={`form-input pl-11 ${touched.name && fieldErrors.name ? 'border-red-300 focus:ring-red-200' : ''}`} />
            </div>
            {touched.name && fieldErrors.name && (
              <p className="text-xs text-red-500 mt-1">{fieldErrors.name}</p>
            )}
            <p className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">{name.length}/200 characters</p>
          </div>
          <div>
            <label htmlFor="create-project-framework" className="form-label">Accounting Framework</label>
            <select id="create-project-framework" value={ptype} onChange={e => setPtype(e.target.value)} className="form-input">
              <option value="ifrs9">IFRS 9 — Expected Credit Loss (ECL)</option>
              <option value="cecl">CECL — Current Expected Credit Loss (US GAAP ASC 326)</option>
              <option value="stress">Regulatory Stress Test</option>
            </select>
          </div>
          <div>
            <label htmlFor="create-project-date" className="form-label">Reporting Date</label>
            <div className="relative">
              <Calendar size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-500 pointer-events-none" aria-hidden="true" />
              <input id="create-project-date" type="date" value={rdate}
                onChange={e => setRdate(e.target.value)}
                onBlur={() => markTouched('rdate')}
                className={`form-input pl-11 ${touched.rdate && fieldErrors.rdate ? 'border-red-300 focus:ring-red-200' : ''}`} />
            </div>
            {touched.rdate && fieldErrors.rdate && (
              <p className="text-xs text-red-500 mt-1">{fieldErrors.rdate}</p>
            )}
          </div>
          <div className="md:col-span-2">
            <label htmlFor="create-project-desc" className="form-label">Description</label>
            <div className="relative">
              <FileText size={16} className="absolute left-3.5 top-3.5 text-slate-400 dark:text-slate-500 pointer-events-none" aria-hidden="true" />
              <textarea id="create-project-desc" value={desc} onChange={e => setDesc(e.target.value)} rows={3}
                placeholder="Describe the ECL run scope, portfolios, and scenarios..."
                className="form-input pl-11 resize-none" />
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              { label: 'Accounting Standard', value: config.regulatoryFramework },
              { label: 'Local Regulator', value: config.localRegulator },
              { label: 'Model Version', value: `ECL Engine ${config.modelVersion}` },
            ].map(item => (
              <div key={item.label} className="p-3 rounded-xl bg-gradient-to-br from-brand/5 to-brand-dark/5 border border-brand/10">
                <p className="text-[10px] font-bold text-brand/60 uppercase">{item.label}</p>
                <p className="text-xs font-bold text-brand-dark mt-0.5">{item.value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 mt-5 pt-4 border-t border-slate-100 dark:border-slate-700">
          <button onClick={handleSubmit} disabled={loading || !isFormValid} className="btn-primary shadow-md disabled:opacity-40">
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
        <Card icon={<Clock size={16} />} title="Audit Trail" subtitle="Project activity log">
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {[...project.audit_log].reverse().map((a: AuditEntry, i: number) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <div className="w-8 h-8 rounded-xl surface flex items-center justify-center flex-shrink-0 mt-0.5">
                  <User size={14} className="text-slate-400" />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-slate-700 dark:text-slate-200">{a.action}</p>
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
