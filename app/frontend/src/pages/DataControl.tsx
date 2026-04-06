import { useEffect, useState } from 'react';
import { ShieldCheck, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import LockedBanner from '../components/LockedBanner';
import NotebookLink from '../components/NotebookLink';
import PageLoader from '../components/PageLoader';
import PageHeader from '../components/PageHeader';
import ApprovalForm from '../components/ApprovalForm';
import { api, type Project } from '../lib/api';
import { fmtCurrency, fmtPct } from '../lib/format';
import { config } from '../lib/config';
import StepDescription from '../components/StepDescription';
import HelpTooltip, { IFRS9_HELP } from '../components/HelpTooltip';
import { usePermissions } from '../hooks/usePermissions';

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject: (comment: string) => Promise<void>;
}

export default function DataControl({ project, onApprove, onReject }: Props) {
  const { canEdit } = usePermissions(project?.project_id);
  const [dq, setDq] = useState<any[]>([]);
  const [recon, setRecon] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!project || project.current_step < 2) return;
    setError(null);
    Promise.all([api.dqResults(), api.glReconciliation()])
      .then(([d, r]) => { setDq(d); setRecon(r); })
      .catch(e => setError(e?.message || 'Failed to load data quality results'))
      .finally(() => setLoading(false));
  }, [project]);

  if (!project || project.current_step < 2) return <LockedBanner />;
  if (loading) return <PageLoader />;
  if (error) return <div className="p-6 text-red-600 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800"><p className="font-semibold">Error loading data</p><p className="text-sm mt-1">{error}</p></div>;

  const passed = dq.filter(d => d.passed).length;
  const total = dq.length;
  const score = total > 0 ? (passed / total * 100) : 0;
  const reconPass = recon.filter(r => r.status === 'PASS').length;
  const critFail = dq.filter(d => !d.passed && d.severity?.toLowerCase() === 'critical').length;
  const stepSt = project.step_status.data_control || 'pending';

  return (
    <div className="space-y-6">
      {!canEdit && (
        <div className="mb-4 px-4 py-2 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 text-xs text-amber-700 dark:text-amber-300 flex items-center gap-2">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m0 0v2m0-2h2m-2 0H10m9.364-7.364A9 9 0 1112 3a9 9 0 019.364 9.636z" /></svg>
          You have view-only access to this project.
        </div>
      )}
      <PageHeader title="Data Control" subtitle="Review data quality checks and GL reconciliation" status={stepSt} />

      <StepDescription
        description="Validate data quality checks and GL reconciliation. Ensure data integrity before modeling — all critical checks must pass and GL variances must be within tolerance."
        ifrsRef="Per IFRS 7.35I — reconciliation from opening to closing balance of the loss allowance."
        tips={[
          `GL reconciliation tolerance is ±${config.governance.glReconciliationTolerancePct}% — variances beyond this require Finance sign-off`,
          'Critical DQ failures must be zero before approval is permitted',
          `DQ score below ${config.governance.dqScoreThresholdPct}% triggers mandatory Data Governance review`,
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="DQ Score" value={fmtPct(score, 1)} subtitle={`${passed}/${total} passed`} color={score >= 95 ? 'green' : 'red'} icon={<ShieldCheck size={20} />} />
        <KpiCard title="GL Reconciliation" value={`${reconPass}/${recon.length} PASS`} subtitle="Product recon" color={recon.length > 0 && reconPass === recon.length ? 'green' : 'amber'} icon={<CheckCircle2 size={20} />} />
        <KpiCard title="Critical Failures" value={String(critFail)} subtitle="Blocking issues" color={critFail === 0 ? 'green' : 'red'} icon={<AlertCircle size={20} />} />
        <KpiCard title="Step Status" value={stepSt.toUpperCase()} color={stepSt === 'completed' ? 'green' : 'amber'} />
      </div>

      <Card title={<span className="flex items-center gap-1.5">GL Reconciliation <HelpTooltip content={IFRS9_HELP.GL_RECON} size={13} /></span>} subtitle="IFRS 7.35I — Loan tape vs General Ledger">
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
                <span className={`inline-flex items-center gap-1 text-xs font-semibold ${v === 'PASS' ? 'text-emerald-700' : 'text-red-600'}`}>
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
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${v?.toLowerCase() === 'critical' ? 'bg-red-50 text-red-600' : v?.toLowerCase() === 'high' ? 'bg-amber-50 text-amber-600' : 'bg-slate-50 dark:bg-slate-800/50 text-slate-500'}`}>
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
      <NotebookLink notebooks={['02_run_data_processing']} />

      <Card title="Materiality Thresholds" subtitle="Governance-approved tolerance levels for data quality gates">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-300 uppercase">GL Reconciliation Tolerance</p>
            <p className="text-lg font-bold text-slate-700 dark:text-slate-200">± {config.governance.glReconciliationTolerancePct}%</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-300">Variance exceeding threshold requires investigation and sign-off by Finance</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-300 uppercase">Critical DQ Failures</p>
            <p className={`text-lg font-bold ${critFail === 0 ? 'text-emerald-600' : 'text-red-600'}`}>{critFail === 0 ? 'None — Clear' : `${critFail} Blocking`}</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-300">Critical failures must be zero before approval is permitted</p>
          </div>
          <div className="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
            <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-300 uppercase">Minimum DQ Score</p>
            <p className="text-lg font-bold text-slate-700 dark:text-slate-200">≥ {config.governance.dqScoreThresholdPct}%</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-300">Below threshold triggers mandatory review by Data Governance team</p>
          </div>
        </div>
      </Card>

      {stepSt !== 'completed' && (
        <Card>
          {critFail > 0 && (
            <div className="mb-3 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2">
              <AlertCircle size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-amber-700">Critical DQ Failures Detected</p>
                <p className="text-xs text-amber-600">{critFail} critical data quality check(s) failed. Approval requires documented justification in the comments field.</p>
              </div>
            </div>
          )}
          {score < config.governance.dqScoreThresholdPct && critFail === 0 && (
            <div className="mb-3 p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2">
              <AlertCircle size={16} className="text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-amber-700">Below DQ Threshold</p>
                <p className="text-xs text-amber-600">DQ score is {fmtPct(score, 1)} (threshold: {config.governance.dqScoreThresholdPct}%). Approval requires documented justification in the comments field.</p>
              </div>
            </div>
          )}
          <ApprovalForm onApprove={onApprove} onReject={onReject} title="Data Quality & GL Reconciliation Decision" approveLabel="✓ Approve Data Quality" disabled={!canEdit} />
        </Card>
      )}
    </div>
  );
}
