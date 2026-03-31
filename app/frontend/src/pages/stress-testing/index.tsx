import { useEffect, useState, useMemo, useCallback } from 'react';
import { Zap, AlertTriangle, Shield, Dice5 } from 'lucide-react';
import KpiCard from '../../components/KpiCard';
import Card from '../../components/Card';
import LockedBanner from '../../components/LockedBanner';
import NotebookLink from '../../components/NotebookLink';
import PageLoader from '../../components/PageLoader';
import PageHeader from '../../components/PageHeader';
import ErrorDisplay from '../../components/ErrorDisplay';
import ApprovalForm from '../../components/ApprovalForm';
import StepDescription from '../../components/StepDescription';
import { api, type Project } from '../../lib/api';
import { fmtCurrency } from '../../lib/format';
import { buildScenarioColorMap, getScenarioLabels, pivotScenarioByProduct } from '../../lib/chartUtils';
import { SUB_TABS, type SubTabKey } from './types';
import MonteCarloTab from './MonteCarloTab';
import SensitivityTab from './SensitivityTab';
import VintageTab from './VintageTab';
import ConcentrationTab from './ConcentrationTab';
import MigrationTab from './MigrationTab';
import CapitalImpact from './CapitalImpact';

interface Props {
  project: Project | null;
  onApprove: (comment: string) => Promise<void>;
  onReject?: (comment: string) => Promise<void>;
}

export default function StressTesting({ project, onApprove, onReject }: Props) {
  const [sensitivity, setSensitivity] = useState<any[]>([]);
  const [scenComp, setScenComp] = useState<any[]>([]);
  const [stageData, setStageData] = useState<any[]>([]);
  const [vintageData, setVintageData] = useState<any[]>([]);
  const [concData, setConcData] = useState<any[]>([]);
  const [mcDist, setMcDist] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [pdShock, setPdShock] = useState(0);
  const [lgdShock, setLgdShock] = useState(0);
  const [eadShock, setEadShock] = useState(0);
  const [migrationPct, setMigrationPct] = useState(0);
  const [activeSubTab, setActiveSubTab] = useState<SubTabKey>('montecarlo');

  const [error, setError] = useState<string | null>(null);
  const [eclProduct, setEclProduct] = useState<any[]>([]);
  const [eclCohortByProduct, setEclCohortByProduct] = useState<Record<string, any[]>>({});

  const [sensMode, setSensMode] = useState<'quick' | 'full'>('quick');
  const [simDefaults, setSimDefaults] = useState<any>(null);
  const [fullSimLoading, setFullSimLoading] = useState(false);
  const [fullSimResult, setFullSimResult] = useState<any>(null);
  const [fullSimError, setFullSimError] = useState<string | null>(null);

  const locked = !project || project.current_step < 5;

  const SCENARIO_COLORS = useMemo(() => buildScenarioColorMap([...scenComp, ...mcDist]), [scenComp, mcDist]);

  const SCENARIO_LABELS = useMemo(() => getScenarioLabels(), []);

  useEffect(() => {
    if (locked) return;
    Promise.all([
      api.sensitivityData(),
      api.scenarioComparison(),
      api.stressByStage(),
      api.vintagePerformance(),
      api.concentrationByProductStage(),
      api.mcDistribution().catch(() => []),
    ]).then(([sens, sc, st, vp, cp, mc]) => {
      setSensitivity(sens || []);
      setScenComp(sc || []);
      setStageData(st || []);
      setVintageData(vp || []);
      setConcData(cp || []);
      setMcDist(mc || []);
    }).catch(err => {
      console.error('Stress testing data load error:', err);
      setError(String(err));
    }).finally(() => setLoading(false));

    api.eclByProduct().then(async (ep) => {
      setEclProduct(ep);
      const cohortMap: Record<string, any[]> = {};
      for (const row of ep) {
        try { cohortMap[row.product_type] = await api.eclByCohort(row.product_type); } catch { /* skip */ }
      }
      setEclCohortByProduct(cohortMap);
    }).catch(() => {});
  }, [project, locked]);

  useEffect(() => {
    if (locked) return;
    api.simulationDefaults().then(setSimDefaults).catch(() => {});
  }, [locked]);

  const runStressedSimulation = useCallback(async () => {
    if (!simDefaults) return;
    setFullSimLoading(true);
    setFullSimError(null);
    setFullSimResult(null);
    try {
      const pdMult = 1 + pdShock / 100;
      const lgdMult = 1 + lgdShock / 100;
      const stressedConfig = {
        n_simulations: simDefaults.n_simulations || 1000,
        pd_lgd_correlation: simDefaults.pd_lgd_correlation || 0.30,
        aging_factor: (simDefaults.aging_factor || 0.08) * (1 + Math.max(0, pdShock) / 200),
        pd_floor: (simDefaults.pd_floor || 0.001) * pdMult,
        pd_cap: Math.min((simDefaults.pd_cap || 0.95) * pdMult, 1.0),
        lgd_floor: (simDefaults.lgd_floor || 0.01) * lgdMult,
        lgd_cap: Math.min((simDefaults.lgd_cap || 0.95) * lgdMult, 1.0),
        scenario_weights: simDefaults.scenario_weights || undefined,
      };
      const result = await api.runSimulation(stressedConfig);
      setFullSimResult({ ...result, eadShock });
    } catch (err: unknown) {
      setFullSimError(err instanceof Error ? err.message : 'Simulation failed');
    } finally {
      setFullSimLoading(false);
    }
  }, [simDefaults, pdShock, lgdShock, eadShock]);

  const fullSimEcl = useMemo(() => {
    if (!fullSimResult) return null;
    const stages = fullSimResult.loss_allowance_by_stage || fullSimResult.stage_summary || [];
    const rawTotal = stages.reduce((s: number, r: Record<string, unknown>) => s + (Number(r.total_ecl) || 0), 0);
    const eadMult = 1 + (fullSimResult.eadShock || 0) / 100;
    return rawTotal * eadMult;
  }, [fullSimResult]);

  const scenarioByProduct = useMemo(() => pivotScenarioByProduct(scenComp), [scenComp]);

  const migrationSimData = useMemo(() => {
    if (!stageData.length) return [];
    return stageData.map(s => {
      const stage = s.assessed_stage;
      let adjustedEcl = Number(s.base_ecl) || 0;
      if (stage === 1 && migrationPct > 0) {
        adjustedEcl = adjustedEcl * (1 - migrationPct / 100);
      } else if (stage === 2) {
        const s1 = stageData.find(x => x.assessed_stage === 1);
        const migratedGca = (Number(s1?.total_gca) || 0) * (migrationPct / 100);
        const totalGca = Number(s.total_gca) || 0;
        const baseEclVal = Number(s.base_ecl) || 0;
        const s2CoverageRate = totalGca > 0 ? baseEclVal / totalGca : 0;
        adjustedEcl = baseEclVal + migratedGca * s2CoverageRate;
      }
      return {
        name: `Stage ${stage}`,
        stage,
        base_ecl: Number(s.base_ecl) || 0,
        adjusted_ecl: adjustedEcl,
        loan_count: Number(s.loan_count) || 0,
        total_gca: Number(s.total_gca) || 0,
      };
    });
  }, [stageData, migrationPct]);

  // Monte Carlo distribution chart data
  const mcChartData = useMemo(() => {
    if (!mcDist.length) return [];
    return mcDist.map(d => ({
      scenario: SCENARIO_LABELS[d.scenario] || d.scenario,
      scenarioKey: d.scenario,
      weight: Number(d.weight) || 0,
      mean: Number(d.ecl_mean) || 0,
      p50: Number(d.ecl_p50) || 0,
      p75: Number(d.ecl_p75) || 0,
      p95: Number(d.ecl_p95) || 0,
      p99: Number(d.ecl_p99) || 0,
      pd_mult: Number(d.avg_pd_multiplier) || 1,
      lgd_mult: Number(d.avg_lgd_multiplier) || 1,
      pd_vol: Number(d.pd_vol) || 0,
      lgd_vol: Number(d.lgd_vol) || 0,
      n_sims: Number(d.n_simulations) || 0,
      spread: (Number(d.ecl_p95) || 0) - (Number(d.ecl_p50) || 0),
    })).sort((a, b) => b.weight - a.weight);
  }, [mcDist]);

  const stepSt = project?.step_status?.stress_testing || 'pending';

  if (locked) return <LockedBanner requiredStep={5} />;
  if (loading) return <PageLoader />;
  if (error) return <ErrorDisplay message={error} onRetry={() => {
    setError(null); setLoading(true);
    Promise.all([
      api.sensitivityData(), api.scenarioComparison(), api.stressByStage(),
      api.vintagePerformance(), api.concentrationByProductStage(), api.mcDistribution().catch(() => []),
    ]).then(([sens, sc, st, vp, cp, mc]) => {
      setSensitivity(sens || []); setScenComp(sc || []); setStageData(st || []);
      setVintageData(vp || []); setConcData(cp || []); setMcDist(mc || []);
    }).catch(e => setError(String(e))).finally(() => setLoading(false));
  }} />;

  const baseEcl = sensitivity.reduce((s, r) => s + (Number(r.base_ecl) || 0), 0);
  const baseGca = sensitivity.reduce((s, r) => s + (Number(r.total_gca) || 0), 0);

  // Stress testing applies proportional shocks to the base ECL.
  const stressedData = sensitivity.map(r => {
    const baseEclVal = Number(r.base_ecl) || 0;
    const pdFactor = 1 + pdShock / 100;
    const lgdFactor = 1 + lgdShock / 100;
    const eadFactor = 1 + eadShock / 100;
    const combinedFactor = pdFactor * lgdFactor * eadFactor;
    const stressedEcl = baseEclVal * combinedFactor;
    const safeStressed = isFinite(stressedEcl) ? stressedEcl : baseEclVal;
    return {
      product_type: r.product_type,
      loan_count: Number(r.loan_count) || 0,
      base_ecl: baseEclVal,
      stressed_ecl: safeStressed,
      delta: safeStressed - baseEclVal,
      delta_pct: baseEclVal > 0 ? ((safeStressed - baseEclVal) / baseEclVal * 100) : 0,
    };
  });

  const totalStressedEcl = stressedData.reduce((s, r) => s + r.stressed_ecl, 0);
  const totalDelta = totalStressedEcl - baseEcl;
  const deltaPct = baseEcl > 0 ? (totalDelta / baseEcl * 100) : 0;

  const shockSum = Math.abs(pdShock) + Math.abs(lgdShock) + Math.abs(eadShock) || 1;
  const sensitivityWaterfall = [
    { name: 'Base ECL', value: baseEcl, fill: '#1A1F36' },
    { name: `Stressed PD (${pdShock >= 0 ? '+' : ''}${pdShock}%)`, value: totalDelta * (Math.abs(pdShock) / shockSum), fill: pdShock >= 0 ? '#EF4444' : '#10B981' },
    { name: `Stressed LGD (${lgdShock >= 0 ? '+' : ''}${lgdShock}%)`, value: totalDelta * (Math.abs(lgdShock) / shockSum), fill: lgdShock >= 0 ? '#EF4444' : '#10B981' },
    { name: `EAD (${eadShock >= 0 ? '+' : ''}${eadShock}%)`, value: totalDelta * (Math.abs(eadShock) / shockSum), fill: eadShock >= 0 ? '#EF4444' : '#10B981' },
    { name: 'Stressed ECL', value: totalStressedEcl, fill: '#DC2626' },
  ];

  const migrationTotalDelta = migrationSimData.reduce((s, r) => s + (r.adjusted_ecl - r.base_ecl), 0);

  // MC summary KPIs
  const mcWeightedMean = mcChartData.reduce((s, d) => s + d.mean * d.weight, 0);
  const mcP95Max = mcChartData.length > 0 ? Math.max(...mcChartData.map(d => d.p95)) : 0;
  const mcP99Max = mcChartData.length > 0 ? Math.max(...mcChartData.map(d => d.p99)) : 0;
  const nScenarios = mcChartData.length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Stress Testing & Scenario Analysis"
        subtitle={`Forward-looking credit loss simulation across ${nScenarios} plausible scenarios with stochastic Stressed PD / Stressed LGD`}
        status={stepSt}
      />

      <StepDescription
        description="Analyze ECL sensitivity to stress scenarios and parameter changes. Assess tail risk through Monte Carlo simulation, vintage analysis, concentration heatmaps, and stage migration scenarios."
        ifrsRef="Per IFRS 9.B5.5.42 — consider multiple forward-looking scenarios to validate ECL robustness under extreme but plausible conditions."
        tips={[
          'Use Monte Carlo tab for stochastic PD/LGD distribution analysis',
          'Sensitivity sliders apply proportional shocks — use presets for standard stress scenarios',
          'Reverse stress test shows what scenario would breach CET1 minimum',
        ]}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <KpiCard title="Weighted ECL" value={fmtCurrency(mcWeightedMean || baseEcl)} subtitle={`${nScenarios} plausible scenarios`} color="blue" icon={<Shield size={20} />} />
        <KpiCard title="Worst P95" value={fmtCurrency(mcP95Max)} subtitle="95th percentile (tail risk)" color="red" icon={<Zap size={20} />} />
        <KpiCard title="Worst P99" value={fmtCurrency(mcP99Max)} subtitle="99th percentile (extreme)" color="amber" icon={<AlertTriangle size={20} />} />
        <KpiCard title="Plausible Scenarios" value={String(nScenarios)} subtitle="Economic paths modeled" color="purple" icon={<Dice5 size={20} />} />
      </div>

      <NotebookLink notebooks={['03b_run_ecl_calculation', '03a_satellite_model']} />

      <div className="flex gap-1 bg-white dark:bg-slate-800/80 rounded-xl shadow-sm p-1.5 overflow-x-auto">
        {SUB_TABS.map(t => (
          <button key={t.key} onClick={() => setActiveSubTab(t.key)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
              activeSubTab === t.key ? 'bg-navy text-white shadow-sm' : 'text-slate-500 hover:bg-slate-50'
            }`}>
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      {/* ── Monte Carlo Tab ─────────────────────────────────────────── */}
      {activeSubTab === 'montecarlo' && (
        <MonteCarloTab
          mcChartData={mcChartData}
          SCENARIO_COLORS={SCENARIO_COLORS}
          SCENARIO_LABELS={SCENARIO_LABELS}
          scenarioByProduct={scenarioByProduct}
          eclProduct={eclProduct}
          eclCohortByProduct={eclCohortByProduct}
          nScenarios={nScenarios}
        />
      )}

      {/* ── Sensitivity Tab ──────────────────────────────────────────── */}
      {activeSubTab === 'sensitivity' && (
        <SensitivityTab
          pdShock={pdShock} lgdShock={lgdShock} eadShock={eadShock}
          setPdShock={setPdShock} setLgdShock={setLgdShock} setEadShock={setEadShock}
          sensMode={sensMode} setSensMode={setSensMode}
          baseEcl={baseEcl} baseGca={baseGca}
          totalStressedEcl={totalStressedEcl} totalDelta={totalDelta} deltaPct={deltaPct}
          stressedData={stressedData} sensitivityWaterfall={sensitivityWaterfall}
          eclCohortByProduct={eclCohortByProduct}
          simDefaults={simDefaults}
          fullSimLoading={fullSimLoading} fullSimResult={fullSimResult}
          fullSimEcl={fullSimEcl} fullSimError={fullSimError}
          runStressedSimulation={runStressedSimulation}
        />
      )}

      {/* ── Vintage Tab ──────────────────────────────────────────────── */}
      {activeSubTab === 'vintage' && (
        <VintageTab vintageData={vintageData} />
      )}

      {/* ── Concentration Tab ────────────────────────────────────────── */}
      {activeSubTab === 'concentration' && (
        <ConcentrationTab
          concData={concData}
          sensitivity={sensitivity}
          eclProduct={eclProduct}
          eclCohortByProduct={eclCohortByProduct}
          stageData={stageData}
        />
      )}

      {/* ── Migration Tab ────────────────────────────────────────────── */}
      {activeSubTab === 'migration' && (
        <MigrationTab
          migrationPct={migrationPct} setMigrationPct={setMigrationPct}
          migrationSimData={migrationSimData}
          migrationTotalDelta={migrationTotalDelta}
          baseEcl={baseEcl}
          stageData={stageData}
        />
      )}

      {/* Capital Impact & Reverse Stress Testing */}
      <CapitalImpact baseEcl={baseEcl} />

      {stepSt !== 'completed' && (
        <Card>
          <ApprovalForm
            onApprove={(c) => onApprove(c || 'Stress testing reviewed and approved')}
            onReject={onReject}
            approveLabel="✓ Approve Stress Testing"
            title="Stress Testing Review"
            description="Confirm that Monte Carlo simulation, sensitivity analysis, vintage trends, concentration risk, and stage migration simulations have been reviewed."
            placeholder="Stress testing review comments (required for rejection)..."
          />
        </Card>
      )}
    </div>
  );
}
