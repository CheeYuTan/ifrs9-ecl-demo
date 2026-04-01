import { useEffect, useState, useMemo, useCallback, type ErrorInfo, Component, type ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Lock, DollarSign, TrendingDown, Percent, Shield, User, Clock, CheckCircle2, ArrowRightLeft, RefreshCw, AlertTriangle, FileSignature } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { useChartTheme } from '../lib/chartTheme';
import KpiCard from '../components/KpiCard';
import Card from '../components/Card';
import DataTable from '../components/DataTable';
import DrillDownChart from '../components/DrillDownChart';
import ThreeLevelDrillDown from '../components/ThreeLevelDrillDown';
import LockedBanner from '../components/LockedBanner';
import NotebookLink from '../components/NotebookLink';
import PageLoader from '../components/PageLoader';
import ConfirmDialog from '../components/ConfirmDialog';
import { api, type Project, type AuditEntry } from '../lib/api';
import { fmtCurrency, fmtPct, fmtNumber, fmtDateTime } from '../lib/format';
import { config } from '../lib/config';
import { buildDrillDownData } from '../lib/chartUtils';
import StepDescription from '../components/StepDescription';
import HelpTooltip, { IFRS9_HELP } from '../components/HelpTooltip';

class ChartErrorBoundary extends Component<{ children: ReactNode; fallback?: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };
  static getDerivedStateFromError() { return { hasError: true }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('Chart render error:', error, info); }
  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex items-center gap-2 p-6 text-amber-600 bg-amber-50 rounded-lg border border-amber-200">
          <AlertTriangle size={16} /> <span className="text-sm">Chart failed to render. Try recomputing the attribution.</span>
        </div>
      );
    }
    return this.props.children;
  }
}

interface Props {
  project: Project | null;
  onSignOff: (name: string, attestation_data?: Record<string, any>) => Promise<void>;
}

export default function SignOff({ project, onSignOff }: Props) {
  const ct = useChartTheme();
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [eclCohortByProduct, setEclCohortByProduct] = useState<Record<string, any[]>>({});
  const [topExp, setTopExp] = useState<any[]>([]);
  const [lossAllowance, setLossAllowance] = useState<any[]>([]);
  const [creditRisk, setCreditRisk] = useState<any[]>([]);
  const [attribution, setAttribution] = useState<any>(null);
  const [attrLoading, setAttrLoading] = useState(false);
  const [attrError, setAttrError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState('');
  const [acting, setActing] = useState(false);
  const [showSignOffConfirm, setShowSignOffConfirm] = useState(false);
  const [attestations, setAttestations] = useState([false, false, false, false]);
  const [hashStatus, setHashStatus] = useState<{status: string; match?: boolean; stored_hash?: string} | null>(null);
  const allAttested = attestations.every(Boolean);

  const loadAttribution = useCallback(async () => {
    if (!project) return;
    setAttrLoading(true);
    setAttrError(null);
    try {
      const attr = await api.getAttribution(project.project_id);
      if (attr && attr.waterfall_data) setAttribution(attr);
    } catch (e: any) {
      const msg = e?.message || 'Unknown error';
      if (!msg.includes('404') && !msg.includes('Not Found')) {
        setAttrError(`Failed to load attribution: ${msg}`);
      }
    }
    finally { setAttrLoading(false); }
  }, [project]);

  const isSigned = !!project?.signed_off_by;

  useEffect(() => {
    if (project && isSigned) {
      api.verifyHash(project.project_id).then(setHashStatus).catch(() => setHashStatus({ status: 'error' }));
    }
  }, [project, isSigned]);

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
      .then(async ([ep, te, la, cr]) => {
        setEclProduct(ep); setTopExp(te); setLossAllowance(la); setCreditRisk(cr);
        const cohortMap: Record<string, any[]> = {};
        for (const row of ep) {
          try { cohortMap[row.product_type] = await api.eclByCohort(row.product_type); } catch { /* skip */ }
        }
        setEclCohortByProduct(cohortMap);
      })
      .finally(() => setLoading(false));
    loadAttribution();
  }, [project, loadAttribution]);

  const handleRecomputeAttribution = async () => {
    if (!project) return;
    setAttrLoading(true);
    setAttrError(null);
    try {
      const attr = await api.computeAttribution(project.project_id);
      setAttribution(attr);
    } catch (e: any) {
      setAttrError(`Attribution computation failed: ${e?.message || 'Unknown error'}`);
    }
    finally { setAttrLoading(false); }
  };

  const reconciliation = useMemo(() => {
    if (attribution) {
      const sv = (obj: any, key: string) => Number(obj?.[key] ?? 0);
      const rows = [
        { movement: `Opening balance`, s1: sv(attribution.opening_ecl, 'stage1'), s2: sv(attribution.opening_ecl, 'stage2'), s3: sv(attribution.opening_ecl, 'stage3'), bold: true },
        { movement: 'New originations', s1: sv(attribution.new_originations, 'stage1'), s2: sv(attribution.new_originations, 'stage2'), s3: sv(attribution.new_originations, 'stage3') },
        { movement: 'Derecognitions / repayments', s1: sv(attribution.derecognitions, 'stage1'), s2: sv(attribution.derecognitions, 'stage2'), s3: sv(attribution.derecognitions, 'stage3') },
        { movement: 'Stage transfers (net)', s1: sv(attribution.stage_transfers, 'stage1'), s2: sv(attribution.stage_transfers, 'stage2'), s3: sv(attribution.stage_transfers, 'stage3') },
        { movement: 'Model parameter changes', s1: sv(attribution.model_changes, 'stage1'), s2: sv(attribution.model_changes, 'stage2'), s3: sv(attribution.model_changes, 'stage3') },
        { movement: 'Macro scenario changes', s1: sv(attribution.macro_changes, 'stage1'), s2: sv(attribution.macro_changes, 'stage2'), s3: sv(attribution.macro_changes, 'stage3') },
        { movement: 'Management overlays', s1: sv(attribution.management_overlays, 'stage1'), s2: sv(attribution.management_overlays, 'stage2'), s3: sv(attribution.management_overlays, 'stage3') },
        { movement: 'Write-offs', s1: sv(attribution.write_offs, 'stage1'), s2: sv(attribution.write_offs, 'stage2'), s3: sv(attribution.write_offs, 'stage3') },
        { movement: 'Unwind of discount', s1: sv(attribution.unwind_discount, 'stage1'), s2: sv(attribution.unwind_discount, 'stage2'), s3: sv(attribution.unwind_discount, 'stage3') },
        { movement: `Closing balance`, s1: sv(attribution.closing_ecl, 'stage1'), s2: sv(attribution.closing_ecl, 'stage2'), s3: sv(attribution.closing_ecl, 'stage3'), bold: true },
      ];
      return rows.map(r => ({ ...r, total: r.s1 + r.s2 + r.s3 }));
    }

    let stageEcl: Record<number, number> = { 1: 0, 2: 0, 3: 0 };
    if (lossAllowance.length) {
      lossAllowance.forEach((r: any) => {
        const stage = Number(r.assessed_stage);
        if (stage >= 1 && stage <= 3) stageEcl[stage] = Number(r.total_ecl) || 0;
      });
    }
    if (stageEcl[1] === 0 && stageEcl[2] === 0 && stageEcl[3] === 0) return null;
    const closing = { s1: stageEcl[1], s2: stageEcl[2], s3: stageEcl[3] };
    // Illustrative growth factors for opening balance estimation when no prior-period data exists.
    // Stage 1: 8% growth (low-risk portfolio expansion), Stage 2: 15% (SICR migration),
    // Stage 3: 22% (default accumulation). These are replaced by actual attribution data when available.
    const growth = { s1: 1.08, s2: 1.15, s3: 1.22 };
    const opening = { s1: closing.s1 / growth.s1, s2: closing.s2 / growth.s2, s3: closing.s3 / growth.s3 };
    const remeasurement = { s1: closing.s1 - opening.s1, s2: closing.s2 - opening.s2, s3: closing.s3 - opening.s3 };
    const rows = [
      { movement: 'Opening balance (estimated)', s1: opening.s1, s2: opening.s2, s3: opening.s3, bold: true },
      { movement: 'Net change (remeasurement)', s1: remeasurement.s1, s2: remeasurement.s2, s3: remeasurement.s3 },
      { movement: 'Closing balance', s1: closing.s1, s2: closing.s2, s3: closing.s3, bold: true },
    ];
    return rows.map(r => ({ ...r, total: r.s1 + r.s2 + r.s3 }));
  }, [lossAllowance, attribution]);

  if (!project || project.current_step < 7) return <LockedBanner requiredStep={7} />;
  if (loading) return <PageLoader />;

  const modelEcl = eclProduct.reduce((s: number, r: any) => s + r.total_ecl, 0);
  const totalGca = eclProduct.reduce((s: number, r: any) => s + r.total_gca, 0);
  const overlays = project.overlays || [];
  const netOverlay = overlays.reduce((s: number, o: any) => s + (o.amount || 0), 0);
  const finalEcl = modelEcl + netOverlay;

  const handleSignOff = () => {
    if (!name) return;
    setShowSignOffConfirm(true);
  };

  const confirmSignOff = async () => {
    setShowSignOffConfirm(false);
    setActing(true);
    try {
      const attestation_data = {
        items: attestations.map((checked, i) => ({
          checked,
          label: ['ECL model methodology compliant with IFRS 9.5.5',
                  'All management overlays individually reviewed and reasonable',
                  'Stress testing scenarios reviewed by Economic Scenario Committee',
                  'Data quality checks passed and GL reconciliation within materiality'][i],
        })),
        signed_by: name,
        signed_at: new Date().toISOString(),
      };
      await onSignOff(name, attestation_data);
    } catch {
      // Error is handled by parent via toast
    } finally {
      setActing(false);
    }
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
          {hashStatus && (
            <div className={`mt-3 flex items-center gap-2 text-sm ${hashStatus.status === 'valid' ? 'text-emerald-700' : hashStatus.status === 'invalid' ? 'text-red-600' : 'text-gray-500'}`}>
              {hashStatus.status === 'valid' ? (
                <><Shield size={14} /> ECL hash verified — results have not been tampered with</>
              ) : hashStatus.status === 'invalid' ? (
                <><AlertTriangle size={14} /> ECL hash mismatch — results may have been modified after sign-off</>
              ) : hashStatus.status === 'not_computed' ? (
                <><Shield size={14} /> No ECL hash available for this project</>
              ) : null}
              {hashStatus.stored_hash && (
                <span className="ml-2 font-mono text-xs opacity-50" title={hashStatus.stored_hash}>
                  SHA-256: {hashStatus.stored_hash.slice(0, 12)}...
                </span>
              )}
            </div>
          )}
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

      <StepDescription
        description="Review final ECL, attribution waterfall, and sign off for regulatory reporting. Once signed, the project is permanently locked and ready for Board submission."
        ifrsRef="Per IFRS 7.35F-35N — disclose credit risk management practices and how they relate to ECL recognition and measurement."
        tips={[
          'Review the attribution waterfall to understand ECL movement drivers',
          'Verify all management overlays are individually justified',
          'Sign-off permanently locks the project — this cannot be undone',
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title={<span className="flex items-center gap-1">Final ECL <HelpTooltip content={IFRS9_HELP.ECL} size={12} /></span>} value={fmtCurrency(finalEcl)} subtitle="Model + Overlays" color="red" icon={<DollarSign size={20} />} />
        <KpiCard title="Net Carrying" value={fmtCurrency(totalGca - finalEcl)} subtitle="GCA − ECL" color="green" icon={<TrendingDown size={20} />} />
        <KpiCard title={<span className="flex items-center gap-1">Coverage <HelpTooltip content={IFRS9_HELP.COVERAGE_RATIO} size={12} /></span>} value={fmtPct(totalGca > 0 ? finalEcl / totalGca * 100 : 0)} subtitle="ECL / GCA" color="indigo" icon={<Percent size={20} />} />
        <KpiCard title="Overlay %" value={fmtPct(modelEcl > 0 ? netOverlay / modelEcl * 100 : 0, 1)} subtitle="Of model ECL" color="purple" icon={<Shield size={20} />} />
      </div>

      {overlays.length > 0 && (
        <Card title="Applied Management Overlays" subtitle="Post-model adjustments included in final ECL">
          <div className="space-y-2">
            {overlays.map((o: any, i: number) => (
              <div key={i} className="flex items-center justify-between py-2 px-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-700">
                <div className="flex items-center gap-3 min-w-0">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${(o.amount || 0) > 0 ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>
                    {(o.amount || 0) > 0 ? 'Uplift' : 'Reduction'}
                  </span>
                  <span className="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{o.reason || o.product || `Overlay ${i + 1}`}</span>
                  {o.product && <span className="text-xs text-slate-500">{o.product}</span>}
                </div>
                <span className={`text-sm font-bold font-mono ${(o.amount || 0) > 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                  {(o.amount || 0) >= 0 ? '+' : ''}{fmtCurrency(o.amount || 0)}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between pt-2 border-t border-slate-200">
              <span className="text-sm font-bold text-slate-700 dark:text-slate-200">Net Overlay Impact</span>
              <span className={`text-sm font-bold font-mono ${netOverlay >= 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                {netOverlay >= 0 ? '+' : ''}{fmtCurrency(netOverlay)}
              </span>
            </div>
          </div>
        </Card>
      )}

      {attrError && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
          <AlertTriangle size={14} className="text-red-500 flex-shrink-0" />
          <p className="text-xs text-red-700 flex-1">{attrError}</p>
          <button onClick={() => setAttrError(null)} aria-label="Dismiss error" className="text-red-400 hover:text-red-600 text-xs font-bold focus-visible:ring-2 focus-visible:ring-red-400 rounded">Dismiss</button>
        </motion.div>
      )}

      {attrLoading && !attribution && (
        <Card title="ECL Attribution Waterfall" subtitle="Loading attribution data...">
          <div className="animate-pulse space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex gap-3">
                <div className="h-3 w-24 bg-slate-200 rounded" />
                <div className="h-3 w-20 bg-slate-200 rounded" />
                <div className="h-3 w-20 bg-slate-200 rounded" />
              </div>
              <div className="h-7 w-24 bg-slate-200 rounded-lg" />
            </div>
            <div className="flex items-end gap-1 h-[340px] pt-8 pb-12 px-4">
              {[0.6, 0.3, 0.2, 0.15, 0.25, 0.1, 0.08, 0.12, 0.05, 0.03, 0.02, 0.55].map((h, i) => (
                <div key={i} className="flex-1 bg-slate-200 rounded-t" style={{ height: `${h * 100}%` }} />
              ))}
            </div>
          </div>
        </Card>
      )}

      {attribution?.waterfall_data && (
        <Card title="ECL Attribution Waterfall" subtitle="Decomposition of ECL movement from opening to closing balance — computed from portfolio data">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4 text-xs" role="legend" aria-label="Waterfall chart legend">
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-blue-500 inline-block" /> Opening / Closing</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-red-400 inline-block" /> Increase</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-emerald-400 inline-block" /> Decrease</span>
            </div>
            <button onClick={handleRecomputeAttribution} disabled={attrLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-brand bg-brand/5 border border-brand/20 rounded-lg hover:bg-brand/10 transition disabled:opacity-50">
              <RefreshCw size={12} className={attrLoading ? 'animate-spin' : ''} /> {attrLoading ? 'Computing...' : 'Recompute'}
            </button>
          </div>
          <ChartErrorBoundary>
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={attribution.waterfall_data} margin={{ top: 10, right: 20, left: 20, bottom: 60 }}
                aria-label="ECL Attribution Waterfall Chart">
                <CartesianGrid strokeDasharray="3 3" stroke={ct.grid} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: ct.axis }} angle={-30} textAnchor="end" interval={0} height={70} />
                <YAxis tick={{ fontSize: 11, fill: ct.axis }} tickFormatter={(v: number) => {
                  if (Math.abs(v) >= 1e6) return `${(v / 1e6).toFixed(1)}M`;
                  if (Math.abs(v) >= 1e3) return `${(v / 1e3).toFixed(0)}K`;
                  return v.toFixed(0);
                }} />
                <Tooltip
                  formatter={(value: any) => [fmtCurrency(Number(value ?? 0)), 'Amount']}
                  labelStyle={{ fontWeight: 600 }}
                  contentStyle={{ borderRadius: 12, border: `1px solid ${ct.tooltip.border}`, background: ct.tooltip.bg, color: ct.tooltip.text, boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                />
                <ReferenceLine y={0} stroke={ct.reference} strokeDasharray="3 3" />
                <Bar dataKey="base" stackId="stack" fill="transparent" />
                <Bar dataKey="value" stackId="stack" radius={[4, 4, 0, 0]}>
                  {attribution.waterfall_data.map((entry: any, idx: number) => {
                    let fill = '#64748B';
                    if (entry.category === 'anchor') fill = '#3B82F6';
                    else if (entry.value > 0) fill = '#F87171';
                    else if (entry.value < 0) fill = '#34D399';
                    return <Cell key={idx} fill={fill} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </ChartErrorBoundary>
          {attribution.residual && Math.abs(attribution.residual.total) > 0.01 && (
            <p className="text-xs text-slate-500 mt-2 text-center">
              Residual balancing item: {fmtCurrency(attribution.residual.total)} (rounding / timing differences)
            </p>
          )}
        </Card>
      )}

      {reconciliation && (
        <Card title="IFRS 7.35I — Loss Allowance Reconciliation" subtitle={attribution ? "Computed from portfolio attribution engine" : "Estimated from closing ECL (run attribution for precise decomposition)"}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm" aria-label="IFRS 7.35I Loss Allowance Reconciliation">
              <thead>
                <tr className="border-b-2 border-slate-200">
                  <th scope="col" className="text-left py-2.5 px-3 text-xs font-semibold text-slate-600 dark:text-slate-300">Movement Type</th>
                  <th scope="col" className="text-right py-2.5 px-3 text-xs font-semibold text-emerald-700"><span className="inline-flex items-center gap-1">Stage 1 <HelpTooltip content={IFRS9_HELP.STAGE_1} size={11} position="bottom" /></span></th>
                  <th scope="col" className="text-right py-2.5 px-3 text-xs font-semibold text-amber-700"><span className="inline-flex items-center gap-1">Stage 2 <HelpTooltip content={IFRS9_HELP.STAGE_2} size={11} position="bottom" /></span></th>
                  <th scope="col" className="text-right py-2.5 px-3 text-xs font-semibold text-red-700"><span className="inline-flex items-center gap-1">Stage 3 <HelpTooltip content={IFRS9_HELP.STAGE_3} size={11} position="bottom" /></span></th>
                  <th scope="col" className="text-right py-2.5 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200">Total</th>
                </tr>
              </thead>
              <tbody>
                {reconciliation.map((row: any, i: number) => {
                  const isClosing = row.movement === 'Closing balance';
                  const isOpening = row.movement === 'Opening balance';
                  const isBold = row.bold;
                  return (
                    <tr key={i} className={`border-b ${isClosing ? 'border-t-2 border-slate-300 bg-slate-50' : isOpening ? 'bg-slate-50 border-slate-200' : 'border-slate-100'} hover:bg-slate-50`}>
                      <td className={`py-2.5 px-3 ${isBold ? 'font-bold text-slate-800 dark:text-slate-100' : 'text-slate-600 dark:text-slate-300'} flex items-center gap-2`}>
                        {row.movement === 'Transfers (net stage movements)' && <ArrowRightLeft size={12} className="text-slate-400" />}
                        {row.movement}
                      </td>
                      {['s1', 's2', 's3', 'total'].map(col => {
                        const val = Number(row[col]) || 0;
                        const isNeg = val < 0;
                        return (
                          <td key={col} className={`py-2.5 px-3 text-right font-mono text-xs ${isBold ? 'font-bold' : ''} ${col === 'total' ? 'text-slate-800 dark:text-slate-100 font-semibold' : isNeg ? 'text-red-600' : 'text-slate-700 dark:text-slate-200'}`}>
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
          <div className={`mt-4 rounded-lg p-3 flex items-start gap-2 ${attribution ? 'bg-emerald-50 border border-emerald-200' : 'bg-amber-50 border border-amber-200'}`}>
            <Shield size={14} className={`flex-shrink-0 mt-0.5 ${attribution ? 'text-emerald-500' : 'text-amber-500'}`} />
            <p className={`text-xs ${attribution ? 'text-emerald-700' : 'text-amber-700'}`}>
              {attribution
                ? 'Per IFRS 7.35I — this reconciliation is computed from the attribution engine using actual portfolio data: originations, derecognitions, stage migrations, model recalibration, macro scenario shifts, management overlays, write-offs, and discount unwind.'
                : 'Estimated reconciliation based on closing ECL. Click "Recompute" in the waterfall chart above to generate a precise attribution from portfolio data.'}
            </p>
          </div>
        </Card>
      )}

      <NotebookLink notebooks={['01_generate_data', '02_run_data_processing', '03a_satellite_model', '03b_run_ecl_calculation', '04_sync_to_lakebase']} />

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

      {eclProduct.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card title="ECL Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
            <DrillDownChart
              data={buildDrillDownData(eclProduct, eclCohortByProduct)}
              dataKey="total_ecl"
              nameKey="product_type"
              title="ECL by Product → Cohort"
              formatValue={(v) => fmtCurrency(v)}
              fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
            />
          </Card>
          <Card title="GCA Drill-Down" subtitle="Click a product → drill by risk band, age group, etc.">
            <DrillDownChart
              data={buildDrillDownData(eclProduct, eclCohortByProduct)}
              dataKey="total_gca"
              nameKey="product_type"
              title="GCA by Product → Cohort"
              formatValue={(v) => fmtCurrency(v)}
              fetchByDimension={(product, dim) => api.eclByCohort(product, dim)}
            />
          </Card>
        </div>
      )}

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

      {lossAllowance.length > 0 && (
        <Card title="Loss Allowance Stage Drill-Down" subtitle="Stage → Product → Cohort">
          <ThreeLevelDrillDown
            level0Data={lossAllowance.map((s: any) => ({
              ...s,
              name: `Stage ${s.assessed_stage}`,
              ecl: Number(s.total_ecl) || 0,
            }))}
            level0Key="assessed_stage"
            level0Label="Stage"
            dataKey="ecl"
            title="Loss Allowance by Stage"
            formatValue={(v) => fmtCurrency(v)}
            level0Colors={{ 1: '#10B981', 2: '#F59E0B', 3: '#EF4444' }}
            fetchProductData={async (stage) => {
              const data = await api.eclByStageProduct(Number(stage));
              return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0, name: r.product_type }));
            }}
            fetchCohortData={async (product, dim) => {
              const data = await api.eclByCohort(product, dim || 'risk_band');
              return data.map((r: any) => ({ ...r, ecl: Number(r.total_ecl) || 0 }));
            }}
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
                    <p className="text-sm font-medium text-slate-700 dark:text-slate-200">{a.action}</p>
                    <div className="flex items-center gap-1 text-xs text-slate-400">
                      <Clock size={10} /> {fmtDateTime(a.ts)}
                    </div>
                  </div>
                  <p className="text-xs text-slate-500">{a.user}</p>
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
            <Lock size={32} className="mx-auto text-slate-400 mb-3" />
            <h3 className="text-lg font-bold text-slate-700 dark:text-slate-200 mb-1 text-center">Final Sign-Off</h3>
            <p className="text-sm text-slate-500 mb-5 max-w-lg mx-auto text-center">
              By signing off, you confirm the forward-looking credit loss calculation is complete, all management overlays are justified per IFRS 9.B5.5.17, and the results are ready for Board submission and regulatory reporting.
            </p>

            <div className="max-w-2xl mx-auto space-y-4">
              <div className="bg-slate-50 dark:bg-slate-800/60 rounded-lg p-4 border border-slate-200 dark:border-slate-700">
                <h4 className="text-xs font-bold text-slate-600 dark:text-slate-300 mb-3">Sign-Off Attestation</h4>
                <div className="space-y-2 text-xs text-slate-500 dark:text-slate-400">
                  {[
                    'I confirm the ECL model methodology is compliant with IFRS 9.5.5 and applicable local regulatory requirements',
                    'All management overlays have been individually reviewed and are reasonable and supportable',
                    'Stress testing scenarios have been reviewed by the Economic Scenario Committee',
                    'Data quality checks have passed and GL reconciliation is within materiality thresholds',
                  ].map((text, i) => (
                    <label key={i} className="flex items-start gap-2 cursor-pointer">
                      <input type="checkbox" className="mt-0.5 brand-range"
                        checked={attestations[i]}
                        onChange={() => setAttestations(prev => { const next = [...prev]; next[i] = !next[i]; return next; })} />
                      <span>{text}</span>
                    </label>
                  ))}
                </div>
                {!allAttested && (
                  <p className="text-[10px] text-amber-600 dark:text-amber-400 mt-2 flex items-center gap-1">
                    <AlertTriangle size={10} /> All attestations must be checked before signing off
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="signoff-prepared-by" className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Prepared By (CFO / Head of Finance)</label>
                  <input id="signoff-prepared-by" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. Ana Reyes, CFO"
                    className="form-input py-3" />
                </div>
                <div>
                  <label htmlFor="signoff-approved-by" className="block text-[10px] font-semibold text-slate-500 uppercase mb-1">Approved By (CRO)</label>
                  <input id="signoff-approved-by" placeholder="e.g. David Kim, CRO" disabled
                    className="form-input py-3 bg-slate-50 dark:bg-slate-800/40 text-slate-500 cursor-not-allowed" />
                  <p id="cro-help" className="text-[10px] text-slate-500 mt-1">CRO approval captured via separate workflow in production</p>
                </div>
              </div>

              <div className="flex justify-center">
                <button onClick={handleSignOff} disabled={acting || !name || !allAttested}
                  className="px-8 py-3 bg-red-600 text-white text-sm font-bold rounded-lg hover:bg-red-700 disabled:opacity-50 transition shadow-sm whitespace-nowrap"
                  title={!allAttested ? 'Complete all attestation checkboxes first' : !name ? 'Enter your name first' : ''}>
                  {acting ? 'Signing...' : 'Sign Off & Lock Project'}
                </button>
              </div>
            </div>
          </div>
        </Card>
      )}

      <ConfirmDialog
        open={showSignOffConfirm}
        title="Sign Off & Lock Project"
        description={`You are about to sign off and permanently lock this ECL project as "${name}". This action cannot be undone. The project will be frozen for regulatory submission.`}
        confirmLabel="Sign Off & Lock"
        variant="danger"
        icon={<FileSignature size={16} className="text-red-500" />}
        onConfirm={confirmSignOff}
        onCancel={() => setShowSignOffConfirm(false)}
        loading={acting}
      />
    </div>
  );
}
