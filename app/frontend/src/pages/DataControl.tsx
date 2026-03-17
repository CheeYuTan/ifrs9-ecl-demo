import { useEffect, useState } from 'react';
import { ShieldCheck, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import LockedBanner from '../components/LockedBanner';
import StatusBadge from '../components/StatusBadge';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtPct } from '../lib/format';
import { config } from '../lib/config';

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}

export default function DataControl({ project, onApprove, onReject }: Props) {
  const [dq, setDq] = useState<any[]>([]);
  const [recon, setRecon] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [acting, setActing] = useState(false);

  useEffect(() => {
    if (!project || project.current_step < 2) return;
    Promise.all([api.dqResults(), api.glReconciliation()])
      .then(([d, r]) => { setDq(d); setRecon(r); })
      .finally(() => setLoading(false));
  }, [project]);

  if (!project || project.current_step < 2) return <LockedBanner />;
  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>;

  const passed = dq.filter(d => d.passed).length;
  const total = dq.length;
  const score = total > 0 ? (passed / total * 100) : 0;
  const reconPass = recon.filter(r => r.status === 'PASS').length;
  const critFail = dq.filter(d => !d.passed && d.severity?.toLowerCase() === 'critical').length;
  const stepSt = project.step_status.data_control || 'pending';

  const handleAction = async (type: 'approve' | 'reject') => {
    if (type === 'reject' && !comment) return;
    setActing(true);
    type === 'approve' ? await onApprove(comment) : await onReject(comment);
    setActing(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-800">Data Control</h2>
          <p className="text-sm text-slate-400 mt-1">Review data quality checks and GL reconciliation</p>
        </div>
        <StatusBadge status={stepSt} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="DQ Score" value={fmtPct(score, 1)} subtitle={`${passed}/${total} passed`} color={score >= 95 ? 'green' : 'red'} icon={<ShieldCheck size={20} />} />
        <KpiCard title="GL Reconciliation" value={`${reconPass}/${recon.length} PASS`} subtitle="Product recon" color={reconPass >= 4 ? 'green' : 'amber'} icon={<CheckCircle2 size={20} />} />
        <KpiCard title="Critical Failures" value={String(critFail)} subtitle="Blocking issues" color={critFail === 0 ? 'green' : 'red'} icon={<AlertCircle size={20} />} />
        <KpiCard title="Step Status" value={stepSt.toUpperCase()} color={stepSt === 'completed' ? 'green' : 'amber'} />
      </div>

      <Card title="GL Reconciliation" subtitle="IFRS 7.35I — Loan tape vs General Ledger">
        <DataTable
          exportName="gl_reconciliation"
          columns={[
            { key: 'product_type', label: 'Product' },
            { key: 'gl_balance', label: `GL Balance (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v, 2) },
            { key: 'loan_tape_balance', label: `Loan Tape (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v, 2) },
            { key: 'variance', label: `Variance (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v, 2) },
            { key: 'variance_pct', label: 'Var %', align: 'right', format: v => fmtPct(v, 2) },
            { key: 'status', label: 'Status', align: 'center',
              format: (v: string) => (
                <span className={`inline-flex items-center gap-1 text-xs font-semibold ${v === 'PASS' ? 'text-emerald-600' : 'text-red-500'}`}>
                  {v === 'PASS' ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {v}
                </span>
              )},
          ]}
          data={recon}
        />
      </Card>

      <Card title="Data Quality Checks" subtitle="Automated validation results">
        <DataTable
          exportName="dq_checks"
          columns={[
            { key: 'check_id', label: 'Check ID' },
            { key: 'category', label: 'Category' },
            { key: 'description', label: 'Description' },
            { key: 'severity', label: 'Severity', align: 'center',
              format: (v: string) => (
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${v?.toLowerCase() === 'critical' ? 'bg-red-50 text-red-600' : v?.toLowerCase() === 'high' ? 'bg-amber-50 text-amber-600' : 'bg-slate-50 text-slate-500'}`}>
                  {v}
                </span>
              )},
            { key: 'failures', label: 'Failures', align: 'right' },
            { key: 'passed', label: 'Status', align: 'center',
              format: (v: boolean) => (
                <span className={`inline-flex items-center gap-1 text-xs font-semibold ${v ? 'text-emerald-600' : 'text-red-500'}`}>
                  {v ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {v ? 'PASS' : 'FAIL'}
                </span>
              )},
          ]}
          data={dq}
          pageSize={20}
        />
      </Card>

      {/* Materiality & Tolerance Thresholds */}
      <Card title="Materiality Thresholds" subtitle="Governance-approved tolerance levels for data quality gates">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">GL Reconciliation Tolerance</p>
            <p className="text-lg font-bold text-slate-700">± 0.50%</p>
            <p className="text-[10px] text-slate-400">Variance exceeding threshold requires investigation and sign-off by Finance</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">Critical DQ Failures</p>
            <p className={`text-lg font-bold ${critFail === 0 ? 'text-emerald-600' : 'text-red-600'}`}>{critFail === 0 ? 'None — Clear' : `${critFail} Blocking`}</p>
            <p className="text-[10px] text-slate-400">Critical failures must be zero before approval is permitted</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
            <p className="text-[10px] font-semibold text-slate-400 uppercase">Minimum DQ Score</p>
            <p className="text-lg font-bold text-slate-700">≥ 90%</p>
            <p className="text-[10px] text-slate-400">Below threshold triggers mandatory review by Data Governance team</p>
          </div>
        </div>
      </Card>

      {stepSt !== 'completed' && (
        <Card>
          <h3 className="text-sm font-bold text-slate-700 mb-3">Data Control Decision</h3>
          {critFail > 0 && (
            <div className="mb-3 p-3 rounded-lg bg-red-50 border border-red-200 flex items-start gap-2">
              <AlertCircle size={16} className="text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-red-700">Approval Blocked</p>
                <p className="text-xs text-red-600">{critFail} critical data quality check(s) failed. Resolve all critical failures before approval is permitted. You may reject with remediation instructions.</p>
              </div>
            </div>
          )}
          {score < 90 && critFail === 0 && (
            <div className="mb-3 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2">
              <AlertCircle size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-amber-700">Below DQ Threshold</p>
                <p className="text-xs text-amber-600">DQ score is {fmtPct(score, 1)} (threshold: 90%). Approval requires documented justification in the comments field.</p>
              </div>
            </div>
          )}
          <textarea value={comment} onChange={e => setComment(e.target.value)} rows={2}
            placeholder={critFail > 0 ? "Rejection comments — describe required remediation actions..." : "Add review comments (required for rejection)..."}
            className="w-full px-3 py-2.5 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition resize-none mb-3" />
          <div className="flex gap-3">
            <button onClick={() => handleAction('approve')} disabled={acting || critFail > 0 || (score < 90 && !comment)}
              className="px-5 py-2.5 bg-emerald-500 text-white text-sm font-semibold rounded-lg hover:bg-emerald-600 disabled:opacity-50 transition shadow-sm"
              title={critFail > 0 ? 'Cannot approve with critical DQ failures' : ''}>
              {acting ? 'Processing...' : '✓ Approve Data'}
            </button>
            <button onClick={() => handleAction('reject')} disabled={acting || !comment}
              className="px-5 py-2.5 bg-white text-red-500 text-sm font-semibold rounded-lg border border-red-200 hover:bg-red-50 disabled:opacity-40 transition">
              ✗ Reject Data
            </button>
          </div>
        </Card>
      )}
    </div>
  );
}
