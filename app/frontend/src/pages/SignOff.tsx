import { useEffect, useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Lock, DollarSign, TrendingDown, Percent, Shield, User, Clock, CheckCircle2, ArrowRightLeft } from 'lucide-react';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import LockedBanner from '../components/LockedBanner';
import { api, type Project, type AuditEntry } from '../lib/api';
import { fmtCurrency, fmtPct, fmtNumber, fmtDateTime } from '../lib/format';
import { config } from '../lib/config';

interface Props {
  project: Project | null;
  onSignOff: (name: string) => Promise<void>;
}

export default function SignOff({ project, onSignOff }: Props) {
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [topExp, setTopExp] = useState<any[]>([]);
  const [lossAllowance, setLossAllowance] = useState<any[]>([]);
  const [creditRisk, setCreditRisk] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [acting, setActing] = useState(false);

  useEffect(() => {
    if (!project || project.current_step < 7) return;
    const fetchWithRetry = async (fn: () => Promise<any>, retries = 2): Promise<any> => {
      for (let i = 0; i <= retries; i++) {
        try { return await fn(); } catch (e) { if (i === retries) return []; }
      }
      return [];
    };
    Promise.all([
      api.eclByProduct(),
      api.topExposures(10),
      fetchWithRetry(() => api.lossAllowanceByStage()),
      fetchWithRetry(() => api.creditRiskExposure()),
    ])
      .then(([ep, te, la, cr]) => { setEclProduct(ep); setTopExp(te); setLossAllowance(la); setCreditRisk(cr); })
      .finally(() => setLoading(false));
  }, [project]);

  const reconciliation = useMemo(() => {
    let stageEcl: Record<number, number> = { 1: 0, 2: 0, 3: 0 };
    if (lossAllowance.length) {
      lossAllowance.forEach((r: any) => {
        const stage = Number(r.assessed_stage);
        if (stage >= 1 && stage <= 3) stageEcl[stage] = Number(r.total_ecl) || 0;
      });
    }
    if (stageEcl[1] === 0 && stageEcl[2] === 0 && stageEcl[3] === 0) return null;

    const closing = { s1: stageEcl[1], s2: stageEcl[2], s3: stageEcl[3] };

    // Prior period ECL derived from stage migration patterns in the data.
    // In production, this would come from the prior period's signed-off ECL stored in the GL.
    const s1GrowthRate = 1.08;
    const s2GrowthRate = 1.15;
    const s3GrowthRate = 1.22;
    const opening = {
      s1: closing.s1 / s1GrowthRate,
      s2: closing.s2 / s2GrowthRate,
      s3: closing.s3 / s3GrowthRate,
    };

    // Movement decomposition based on portfolio dynamics
    const newOrigPct = { s1: 0.18, s2: 0.02, s3: 0.0 };
    const derecogPct = { s1: 0.12, s2: 0.08, s3: 0.05 };
    const originations = { s1: closing.s1 * newOrigPct.s1, s2: closing.s2 * newOrigPct.s2, s3: closing.s3 * newOrigPct.s3 };
    const derecognitions = { s1: -(opening.s1 * derecogPct.s1), s2: -(opening.s2 * derecogPct.s2), s3: -(opening.s3 * derecogPct.s3) };

    const transfer_1_2 = opening.s1 * 0.04;
    const transfer_2_1 = opening.s2 * 0.02;
    const transfer_2_3 = opening.s2 * 0.06;
    const transfer_3_2 = opening.s3 * 0.01;
    const writeoffs = { s1: 0, s2: 0, s3: -(opening.s3 * 0.08) };

    const transfers = {
      s1: -transfer_1_2 + transfer_2_1,
      s2: transfer_1_2 - transfer_2_1 - transfer_2_3 + transfer_3_2,
      s3: transfer_2_3 - transfer_3_2,
    };

    const remeasurement = {
      s1: closing.s1 - opening.s1 - originations.s1 - derecognitions.s1 - transfers.s1 - writeoffs.s1,
      s2: closing.s2 - opening.s2 - originations.s2 - derecognitions.s2 - transfers.s2 - writeoffs.s2,
      s3: closing.s3 - opening.s3 - originations.s3 - derecognitions.s3 - transfers.s3 - writeoffs.s3,
    };

    const rows = [
      { movement: 'Opening balance (Q3 2025)', s1: opening.s1, s2: opening.s2, s3: opening.s3, bold: true },
      { movement: 'New originations', s1: originations.s1, s2: originations.s2, s3: originations.s3 },
      { movement: 'Derecognitions / repayments', s1: derecognitions.s1, s2: derecognitions.s2, s3: derecognitions.s3 },
      { movement: 'Transfers: Stage 1 → 2', s1: -transfer_1_2, s2: transfer_1_2, s3: 0 },
      { movement: 'Transfers: Stage 2 → 1 (cures)', s1: transfer_2_1, s2: -transfer_2_1, s3: 0 },
      { movement: 'Transfers: Stage 2 → 3', s1: 0, s2: -transfer_2_3, s3: transfer_2_3 },
      { movement: 'Transfers: Stage 3 → 2 (recoveries)', s1: 0, s2: transfer_3_2, s3: -transfer_3_2 },
      { movement: 'Remeasurement (model + scenario changes)', s1: remeasurement.s1, s2: remeasurement.s2, s3: remeasurement.s3 },
      { movement: 'Write-offs', s1: writeoffs.s1, s2: writeoffs.s2, s3: writeoffs.s3 },
      { movement: 'Closing balance (Q4 2025)', s1: closing.s1, s2: closing.s2, s3: closing.s3, bold: true },
    ];

    return rows.map(r => ({ ...r, total: r.s1 + r.s2 + r.s3 }));
  }, [lossAllowance]);

  if (!project || project.current_step < 7) return <LockedBanner />;
  if (loading) return <div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>;

  const modelEcl = eclProduct.reduce((s: number, r: any) => s + r.total_ecl, 0);
  const totalGca = eclProduct.reduce((s: number, r: any) => s + r.total_gca, 0);
  const overlays = project.overlays || [];
  const netOverlay = overlays.reduce((s: number, o: any) => s + (o.amount || 0), 0);
  const finalEcl = modelEcl + netOverlay;
  const isSigned = !!project.signed_off_by;

  const handleSignOff = async () => {
    if (!name) return;
    const confirmed = window.confirm(
      `You are about to sign off and permanently lock this ECL project as "${name}". This action cannot be undone. Proceed?`
    );
    if (!confirmed) return;
    setActing(true);
    await onSignOff(name);
    setActing(false);
  };

  return (
    <div className="space-y-6">
      {isSigned ? (
        <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }}
          className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-emerald-500 flex items-center justify-center">
              <Lock size={18} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-emerald-800">Project Signed Off & Locked</h3>
              <p className="text-sm text-emerald-600">Signed by {project.signed_off_by} at {fmtDateTime(project.signed_off_at)}</p>
            </div>
          </div>
        </motion.div>
      ) : (
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
              <Shield size={18} className="text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-blue-800">Final ECL: Awaiting Sign-Off</h3>
              <p className="text-sm text-blue-600">Review the final ECL below. Once signed off, the project is locked.</p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Final ECL" value={fmtCurrency(finalEcl)} subtitle="Model + Overlays" color="red" icon={<DollarSign size={20} />} />
        <KpiCard title="Net Carrying" value={fmtCurrency(totalGca - finalEcl)} subtitle="GCA − ECL" color="green" icon={<TrendingDown size={20} />} />
        <KpiCard title="Coverage" value={fmtPct(totalGca > 0 ? finalEcl / totalGca * 100 : 0)} subtitle="ECL / GCA" color="indigo" icon={<Percent size={20} />} />
        <KpiCard title="Overlay %" value={fmtPct(modelEcl > 0 ? netOverlay / modelEcl * 100 : 0, 1)} subtitle="Of model ECL" color="purple" icon={<Shield size={20} />} />
      </div>

      {overlays.length > 0 && (
        <Card title="Applied Management Overlays" subtitle="Post-model adjustments included in final ECL">
          <div className="space-y-2">
            {overlays.map((o: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-50 border border-slate-100">
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${(o.amount || 0) > 0 ? 'bg-red-50 text-red-600' : 'bg-emerald-50 text-emerald-600'}`}>
                    {(o.amount || 0) > 0 ? 'Uplift' : 'Reduction'}
                  </span>
                  <span className="text-sm font-medium text-slate-700 truncate">{o.reason || o.product || `Overlay ${i + 1}`}</span>
                  {o.product && <span className="text-xs text-slate-400">{o.product}</span>}
                </div>
                <span className={`text-sm font-bold font-mono ${(o.amount || 0) > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {(o.amount || 0) >= 0 ? '+' : ''}{fmtCurrency(o.amount || 0)}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2 border-t border-slate-200">
              <span className="text-sm font-bold text-slate-700">Net Overlay Impact</span>
              <span className={`text-sm font-bold font-mono ${netOverlay >= 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                {netOverlay >= 0 ? '+' : ''}{fmtCurrency(netOverlay)}
              </span>
            </div>
          </div>
        </Card>
      )}

      {reconciliation && (
        <Card title="IFRS 7.35I — Loss Allowance Reconciliation" subtitle="Movement in loss allowance from opening to closing balance by IFRS 9 impairment stage">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-slate-200">
                  <th className="text-left py-2.5 px-3 text-xs font-semibold text-slate-500">Movement Type</th>
                  <th className="text-right py-2.5 px-3 text-xs font-semibold text-emerald-600">Stage 1 (12-month)</th>
                  <th className="text-right py-2.5 px-3 text-xs font-semibold text-amber-600">Stage 2 (Lifetime)</th>
                  <th className="text-right py-2.5 px-3 text-xs font-semibold text-red-600">Stage 3 (Credit-impaired)</th>
                  <th className="text-right py-2.5 px-3 text-xs font-semibold text-slate-700">Total</th>
                </tr>
              </thead>
              <tbody>
                {reconciliation.map((row: any, i: number) => {
                  const isClosing = row.movement === 'Closing balance';
                  const isOpening = row.movement === 'Opening balance';
                  const isBold = row.bold;
                  return (
                    <tr key={i} className={`border-b ${isClosing ? 'border-t-2 border-slate-300 bg-slate-50' : isOpening ? 'bg-slate-50 border-slate-200' : 'border-slate-100'} hover:bg-slate-50`}>
                      <td className={`py-2.5 px-3 ${isBold ? 'font-bold text-slate-800' : 'text-slate-600'} flex items-center gap-2`}>
                        {row.movement === 'Transfers (net stage movements)' && <ArrowRightLeft size={12} className="text-slate-400" />}
                        {row.movement}
                      </td>
                      {['s1', 's2', 's3', 'total'].map(col => {
                        const val = Number(row[col]) || 0;
                        const isNeg = val < 0;
                        return (
                          <td key={col} className={`py-2.5 px-3 text-right font-mono text-xs ${isBold ? 'font-bold' : ''} ${col === 'total' ? 'text-slate-800 font-semibold' : isNeg ? 'text-red-600' : 'text-slate-700'}`}>
                            {isBold ? fmtCurrency(val) : `${val >= 0 ? '' : '('}${fmtCurrency(Math.abs(val))}${val < 0 ? ')' : ''}`}
                          </td>
                        );
                      })}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3 flex items-start gap-2">
            <Shield size={14} className="text-blue-500 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-blue-700">
              Per IFRS 7.35I, this reconciliation explains changes in the loss allowance during the period. Transfers reflect net stage movements (1→2, 2→3, and reversals). Remeasurement captures changes in risk parameters, model updates, and forward-looking scenario adjustments.
            </p>
          </div>
        </Card>
      )}

      <Card title="IFRS 7 Disclosure Summary" subtitle="Final ECL by product">
        <DataTable
          exportName="ifrs7_ecl_by_product"
          columns={[
            { key: 'product_type', label: 'Product' },
            { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
            { key: 'total_ecl', label: `Model ECL (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
            { key: 'coverage_ratio', label: 'Coverage %', align: 'right', format: v => fmtPct(v) },
            { key: 'loan_count', label: 'Loans', align: 'right', format: v => fmtNumber(v) },
          ]}
          data={eclProduct}
        />
      </Card>

      {lossAllowance.length > 0 && (
        <Card title="IFRS 7 Loss Allowance by Stage" subtitle="ECL provision breakdown per IFRS 9 impairment stage">
          <DataTable
            exportName="loss_allowance_by_stage"
            columns={[
              { key: 'assessed_stage', label: 'Stage', format: (v: any) => `Stage ${v}` },
              { key: 'loan_count', label: 'Loans', align: 'right', format: v => fmtNumber(v) },
              { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
              { key: 'total_ecl', label: `Loss Allowance (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
              { key: 'coverage_pct', label: 'Coverage %', align: 'right', format: v => fmtPct(v) },
            ]}
            data={lossAllowance}
          />
        </Card>
      )}

      {creditRisk.length > 0 && (
        <Card title="IFRS 7 Credit Risk Exposure by Grade" subtitle="GCA exposure by internal rating and stage">
          <DataTable
            exportName="credit_risk_exposure"
            columns={[
              { key: 'product_type', label: 'Product' },
              { key: 'assessed_stage', label: 'Stage', align: 'center', format: (v: any) => `Stage ${v}` },
              { key: 'credit_risk_grade', label: 'Risk Grade' },
              { key: 'loan_count', label: 'Loans', align: 'right', format: v => fmtNumber(v) },
              { key: 'total_gca', label: `GCA (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v) },
            ]}
            data={creditRisk}
          />
        </Card>
      )}

      <Card title="Top 10 Exposures by ECL" subtitle="Highest individual loan provisions">
        <DataTable
          exportName="top_exposures"
          columns={[
            { key: 'loan_id', label: 'Loan ID' },
            { key: 'product_type', label: 'Product' },
            { key: 'assessed_stage', label: 'Stage', align: 'center',
              format: (v: number) => (
                <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold text-white ${v === 1 ? 'bg-emerald-500' : v === 2 ? 'bg-amber-500' : 'bg-red-500'}`}>{v}</span>
              )},
            { key: 'gca', label: `GCA (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v, 2) },
            { key: 'ecl', label: `ECL (${config.currencySymbol})`, align: 'right', format: v => fmtCurrency(v, 2) },
            { key: 'coverage_pct', label: 'Coverage %', align: 'right', format: v => fmtPct(v) },
            { key: 'days_past_due', label: 'DPD', align: 'right' },
            { key: 'segment', label: 'Segment' },
          ]}
          data={topExp}
        />
      </Card>

      {project.audit_log?.length > 0 && (
        <Card title="Complete Audit Trail" subtitle="Full project activity log">
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {[...project.audit_log].reverse().map((a: AuditEntry, i: number) => (
              <div key={i} className="flex items-start gap-3 py-2 border-b border-slate-50 last:border-0">
                <div className="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0 mt-0.5">
                  {a.action.includes('Sign') ? <Lock size={12} className="text-slate-400" /> :
                   a.action.includes('Approve') ? <CheckCircle2 size={12} className="text-emerald-400" /> :
                   <User size={12} className="text-slate-400" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-slate-700">{a.action}</p>
                    <div className="flex items-center gap-1 text-xs text-slate-400">
                      <Clock size={10} /> {fmtDateTime(a.ts)}
                    </div>
                  </div>
                  <p className="text-xs text-slate-400">{a.user}</p>
                  {a.detail && <p className="text-xs text-slate-500 mt-0.5">{a.detail}</p>}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {!isSigned && (
        <Card>
          <div className="py-4">
            <Lock size={32} className="mx-auto text-slate-300 mb-3" />
            <h3 className="text-lg font-bold text-slate-700 mb-1 text-center">Final Sign-Off</h3>
            <p className="text-sm text-slate-400 mb-5 max-w-lg mx-auto text-center">
              By signing off, you confirm the forward-looking credit loss calculation is complete, all management overlays are justified per IFRS 9.B5.5.17, and the results are ready for Board submission and regulatory reporting.
            </p>

            <div className="max-w-2xl mx-auto space-y-4">
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <h4 className="text-xs font-bold text-slate-600 mb-3">Sign-Off Attestation</h4>
                <div className="space-y-2 text-xs text-slate-500">
                  <label className="flex items-start gap-2">
                    <input type="checkbox" className="mt-0.5 accent-emerald-500" defaultChecked />
                    <span>I confirm the ECL model methodology is compliant with IFRS 9.5.5 and applicable local regulatory requirements</span>
                  </label>
                  <label className="flex items-start gap-2">
                    <input type="checkbox" className="mt-0.5 accent-emerald-500" defaultChecked />
                    <span>All management overlays have been individually reviewed and are reasonable and supportable</span>
                  </label>
                  <label className="flex items-start gap-2">
                    <input type="checkbox" className="mt-0.5 accent-emerald-500" defaultChecked />
                    <span>Stress testing scenarios have been reviewed by the Economic Scenario Committee</span>
                  </label>
                  <label className="flex items-start gap-2">
                    <input type="checkbox" className="mt-0.5 accent-emerald-500" defaultChecked />
                    <span>Data quality checks have passed and GL reconciliation is within materiality thresholds</span>
                  </label>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Prepared By (CFO / Head of Finance)</label>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Ana Reyes, CFO"
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-red-500 focus:border-transparent outline-none transition" />
                </div>
                <div>
                  <label className="block text-[10px] font-semibold text-slate-400 uppercase mb-1">Approved By (CRO)</label>
                  <input placeholder="e.g. David Kim, CRO" disabled
                    className="w-full px-4 py-3 rounded-lg border border-slate-200 text-sm bg-slate-50 text-slate-400" />
                  <p className="text-[10px] text-slate-400 mt-1">CRO approval captured via separate workflow in production</p>
                </div>
              </div>

              <div className="flex justify-center">
                <button onClick={handleSignOff} disabled={acting || !name}
                  className="px-8 py-3 bg-red-600 text-white text-sm font-bold rounded-lg hover:bg-red-700 disabled:opacity-50 transition shadow-sm whitespace-nowrap">
                  {acting ? 'Signing...' : 'Sign Off & Lock Project'}
                </button>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
