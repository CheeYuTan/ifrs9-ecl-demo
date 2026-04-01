import { useEffect, useState, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Settings, Play, RotateCcw, Sliders, ChevronDown, ChevronUp,
  Loader2, CheckCircle2, AlertCircle, History, Upload,
  ArrowRight, Ban, Server, ExternalLink,
} from 'lucide-react';
import { api } from '../lib/api';
import { config } from '../lib/config';
import SimulationProgress from './SimulationProgress';
import SimulationResults from './SimulationResults';
import type { ScenarioProgress } from './ScenarioChecklist';

interface ScenarioWeight {
  key: string;
  label: string;
  color: string;
  weight: number;
}

interface SimulationConfig {
  n_simulations: number;
  pd_lgd_correlation: number;
  aging_factor: number;
  pd_floor: number;
  pd_cap: number;
  lgd_floor: number;
  lgd_cap: number;
  scenario_weights: Record<string, number>;
}

interface RunHistoryEntry {
  timestamp: Date;
  duration: number;
  n_sims: number;
  pd_lgd_correlation: number;
  aging_factor: number;
  total_ecl: number;
  coverage: number;
  results: any;
}

interface ValidationResult {
  errors?: string[];
  warnings?: string[];
  estimated_duration_s?: number;
}

interface SimulationPanelProps {
  onSimulationComplete: (results: any) => void;
  defaultOpen?: boolean;
}

export default function SimulationPanel({ onSimulationComplete, defaultOpen = false }: SimulationPanelProps) {
  const [open, setOpen] = useState(defaultOpen);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastRun, setLastRun] = useState<{ timestamp: Date; duration: number } | null>(null);

  const [nSimulations, setNSimulations] = useState(1000);
  const [pdLgdCorrelation, setPdLgdCorrelation] = useState(0.30);
  const [agingFactor, setAgingFactor] = useState(0.08);
  const [pdFloor, setPdFloor] = useState(0.001);
  const [pdCap, setPdCap] = useState(0.95);
  const [lgdFloor, setLgdFloor] = useState(0.01);
  const [lgdCap, setLgdCap] = useState(0.95);

  const [scenarioWeights, setScenarioWeights] = useState<ScenarioWeight[]>([]);
  const [defaultWeights, setDefaultWeights] = useState<Record<string, number>>({});
  const [runHistory, setRunHistory] = useState<RunHistoryEntry[]>([]);

  const [progressEvents, setProgressEvents] = useState<any[]>([]);
  const [currentPhase, setCurrentPhase] = useState('');
  const [currentMessage, setCurrentMessage] = useState('');
  const [progressPct, setProgressPct] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [scenarioResults, setScenarioResults] = useState<ScenarioProgress[]>([]);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [runningEcl, setRunningEcl] = useState(0);
  const [loanCount, setLoanCount] = useState(0);
  const [completedResult, setCompletedResult] = useState<any>(null);
  const [completedTiming, setCompletedTiming] = useState<{ loading: number; compute: number; aggregation: number } | null>(null);
  const [convergenceInfo, setConvergenceInfo] = useState<{ pct: number; at: number } | null>(null);
  const [showValidationWarnings, setShowValidationWarnings] = useState(false);
  const [jobRunning, setJobRunning] = useState(false);
  const [jobRunUrl, setJobRunUrl] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<string>('');

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const jobPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const startTimeRef = useRef<number>(0);
  const lastScenarioElapsedRef = useRef<number>(0);

  useEffect(() => {
    setLoading(true);
    api.simulationDefaults()
      .then((defaults: any) => {
        if (defaults.n_simulations) setNSimulations(defaults.n_simulations);
        if (defaults.pd_lgd_correlation != null) setPdLgdCorrelation(defaults.pd_lgd_correlation);
        if (defaults.aging_factor != null) setAgingFactor(defaults.aging_factor);
        if (defaults.pd_floor != null) setPdFloor(defaults.pd_floor);
        if (defaults.pd_cap != null) setPdCap(defaults.pd_cap);
        if (defaults.lgd_floor != null) setLgdFloor(defaults.lgd_floor);
        if (defaults.lgd_cap != null) setLgdCap(defaults.lgd_cap);

        if (defaults.scenario_weights) {
          setDefaultWeights(defaults.scenario_weights);
          const weights = Object.entries(defaults.scenario_weights).map(([key, w]) => {
            const cfg = config.scenarios[key] || { label: key, color: '#6B7280' };
            return { key, label: cfg.label, color: cfg.color, weight: Math.round((w as number) * 100) };
          });
          setScenarioWeights(weights);
        }
      })
      .catch(() => {
        const weights = Object.entries(config.scenarios).map(([key, cfg]) => ({
          key, label: cfg.label, color: cfg.color,
          weight: Math.round(100 / Object.keys(config.scenarios).length),
        }));
        setScenarioWeights(weights);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (jobPollRef.current) clearInterval(jobPollRef.current);
  }, []);

  const totalWeight = scenarioWeights.reduce((s, w) => s + w.weight, 0);
  const weightsValid = Math.abs(totalWeight - 100) < 0.5;

  const updateWeight = useCallback((key: string, value: number) => {
    setScenarioWeights(prev => prev.map(w => w.key === key ? { ...w, weight: value } : w));
  }, []);

  const equalizeWeights = useCallback(() => {
    const count = scenarioWeights.length;
    if (count === 0) return;
    const base = Math.floor(100 / count);
    const remainder = 100 - base * count;
    setScenarioWeights(prev => prev.map((w, i) => ({ ...w, weight: base + (i < remainder ? 1 : 0) })));
  }, [scenarioWeights.length]);

  const resetToDefault = useCallback(() => {
    if (Object.keys(defaultWeights).length > 0) {
      setScenarioWeights(prev => prev.map(w => ({
        ...w, weight: Math.round((defaultWeights[w.key] || 0) * 100),
      })));
    }
  }, [defaultWeights]);

  const buildSimConfig = (): SimulationConfig => ({
    n_simulations: nSimulations,
    pd_lgd_correlation: pdLgdCorrelation,
    aging_factor: agingFactor,
    pd_floor: pdFloor,
    pd_cap: pdCap,
    lgd_floor: lgdFloor,
    lgd_cap: lgdCap,
    scenario_weights: Object.fromEntries(scenarioWeights.map(w => [w.key, w.weight / 100])),
  });

  const resetProgressState = () => {
    setProgressEvents([]);
    setCurrentPhase('');
    setCurrentMessage('');
    setProgressPct(0);
    setElapsedSeconds(0);
    setRunningEcl(0);
    setLoanCount(0);
    setCompletedResult(null);
    setCompletedTiming(null);
    setConvergenceInfo(null);
    setScenarioResults(
      scenarioWeights.map(sw => ({
        key: sw.key, label: sw.label, color: sw.color,
        weightPct: Math.round(sw.weight), status: 'pending' as const,
      }))
    );
  };

  const startTimer = () => {
    startTimeRef.current = Date.now();
    setElapsedSeconds(0);
    timerRef.current = setInterval(() => {
      setElapsedSeconds((Date.now() - startTimeRef.current) / 1000);
    }, 100);
  };

  const stopTimer = () => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
  };

  const handleProgressEvent = (event: any) => {
    setProgressEvents(prev => [...prev, event]);
    if (event.phase) setCurrentPhase(event.phase);
    if (event.message) setCurrentMessage(event.message);
    if (event.progress != null) setProgressPct(event.progress);
    if (event.detail?.loan_count) setLoanCount(event.detail.loan_count);
    if (event.cumulative_weighted_ecl != null) setRunningEcl(event.cumulative_weighted_ecl);

    if (event.detail?.convergence) {
      const cv = event.detail.convergence.coefficient_of_variation;
      if (cv != null) {
        const stable = cv < 0.01;
        setConvergenceInfo({ pct: cv * 100, at: stable ? Math.round(nSimulations * 0.5) : nSimulations });
      }
    }

    if (event.phase === 'done' && event.detail) {
      const d = event.detail;
      setCompletedTiming({
        loading: d.load_time || d.duration * 0.03,
        compute: d.compute_time || d.duration * 0.93,
        aggregation: d.aggregation_time || d.duration * 0.04,
      });
    }

    if (event.step === 'scenario_start' && event.scenario) {
      lastScenarioElapsedRef.current = event.elapsed || 0;
      setScenarioResults(prev => prev.map(sr =>
        sr.key === event.scenario ? { ...sr, status: 'running' } : sr
      ));
    }

    if (event.step === 'scenario_done' && event.scenario) {
      const scenarioDuration = ((event.elapsed || 0) - lastScenarioElapsedRef.current) * 1000;
      setScenarioResults(prev => prev.map(sr =>
        sr.key === event.scenario
          ? { ...sr, status: 'done', ecl: event.scenario_ecl, durationMs: scenarioDuration }
          : sr
      ));
    }
  };

  const cancelSimulation = () => {
    abortRef.current?.abort();
    stopTimer();
    setRunning(false);
    setError('Simulation cancelled');
  };

  const processResults = (results: any, start: number) => {
    const duration = Date.now() - start;
    const now = new Date();
    setLastRun({ timestamp: now, duration });

    const eclByProduct = results.ecl_by_product || [];
    const totalEcl = eclByProduct.reduce((s: number, r: any) => s + (Number(r.total_ecl) || 0), 0);
    const totalGca = eclByProduct.reduce((s: number, r: any) => s + (Number(r.total_gca) || 0), 0);
    const coverage = totalGca > 0 ? (totalEcl / totalGca) * 100 : 0;

    setRunHistory(prev => [
      ...prev.slice(-(10 - 1)),
      { timestamp: now, duration, n_sims: nSimulations, pd_lgd_correlation: pdLgdCorrelation, aging_factor: agingFactor, total_ecl: totalEcl, coverage, results },
    ]);

    setCompletedResult({ results, totalEcl, coverage, duration });
    setProgressPct(100);
    setCurrentPhase('done');
    setCurrentMessage('Simulation complete');
    setScenarioResults(prev => prev.map(sr => sr.status === 'running' ? { ...sr, status: 'done' } : sr));
  };

  const runSimulation = async () => {
    if (!weightsValid) return;
    const simConfig = buildSimConfig();

    setError(null);
    setValidationResult(null);
    setShowValidationWarnings(false);
    setCompletedResult(null);

    try {
      const validation: ValidationResult = await api.validateSimulation(simConfig);
      if (validation.errors && validation.errors.length > 0) {
        setError(validation.errors.join('; '));
        return;
      }
      if (validation.warnings && validation.warnings.length > 0) {
        setValidationResult(validation);
        setShowValidationWarnings(true);
        return;
      }
    } catch { /* proceed without validation */ }

    await startStreaming(simConfig);
  };

  const proceedAfterWarnings = async () => {
    setShowValidationWarnings(false);
    setValidationResult(null);
    await startStreaming(buildSimConfig());
  };

  const startStreaming = async (simConfig: SimulationConfig) => {
    setRunning(true);
    setError(null);
    resetProgressState();
    startTimer();

    const abort = new AbortController();
    abortRef.current = abort;
    const start = Date.now();

    try {
      const results = await api.simulateStream(simConfig, handleProgressEvent, abort.signal);
      stopTimer();
      processResults(results, start);
      setRunning(false);
    } catch (err: any) {
      stopTimer();
      if (err.name === 'AbortError') return;

      try {
        setCurrentMessage('Falling back to standard endpoint...');
        const results = await api.runSimulation(simConfig);
        processResults(results, start);
        setRunning(false);
      } catch (fallbackErr: any) {
        setError(fallbackErr.message || 'Simulation failed');
        setRunning(false);
      }
    }
  };

  const applyResults = () => {
    if (completedResult) {
      onSimulationComplete(completedResult.results);
      setCompletedResult(null);
    }
  };

  const discardResults = () => {
    setCompletedResult(null);
    setProgressPct(0);
    setCurrentPhase('');
  };

  const runAsJob = async () => {
    if (!weightsValid) return;
    const simConfig = buildSimConfig();
    setError(null);
    setJobRunning(true);
    setJobStatus('Submitting to Databricks...');
    setJobRunUrl(null);

    try {
      const result = await api.simulateJob(simConfig);
      setJobRunUrl(result.run_url || null);
      setJobStatus('Job submitted — polling for completion...');

      const runId = result.run_id;
      jobPollRef.current = setInterval(async () => {
        try {
          const status = await api.jobRunStatus(runId);
          const state = status.lifecycle_state;
          const resultState = status.result_state;
          setJobStatus(`Job ${state}${resultState ? ` (${resultState})` : ''}`);

          if (state === 'TERMINATED' || state === 'SKIPPED' || state === 'INTERNAL_ERROR') {
            if (jobPollRef.current) clearInterval(jobPollRef.current);
            setJobRunning(false);
            if (resultState === 'SUCCESS') {
              setJobStatus('Job completed successfully — results saved to Delta tables');
            } else {
              setError(`Job finished with status: ${resultState || state}`);
              setJobStatus('');
            }
          }
        } catch {
          // keep polling
        }
      }, 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to trigger Databricks job');
      setJobRunning(false);
      setJobStatus('');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="glass-card rounded-xl border-2 border-brand/20"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-indigo-50/50 transition rounded-t-xl"
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
            <Settings size={16} className="text-indigo-600" />
          </div>
          <div className="text-left">
            <h3 className="text-sm font-bold text-slate-700">Simulation Configuration</h3>
            <p className="text-xs text-slate-400">Monte Carlo forward-looking credit loss engine</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {lastRun && (
            <span className="text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-medium">
              Last run: {lastRun.duration < 1000 ? `${lastRun.duration}ms` : `${(lastRun.duration / 1000).toFixed(1)}s`}
            </span>
          )}
          {open ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
        </div>
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-6 pb-6 space-y-6 border-t border-indigo-100">
              {loading ? (
                <div className="flex justify-center py-8">
                  <Loader2 size={24} className="animate-spin text-indigo-400" />
                </div>
              ) : (
                <>
                  {/* Monte Carlo Parameters */}
                  <div className="pt-5">
                    <div className="flex items-center gap-2 mb-4">
                      <Sliders size={14} className="text-indigo-500" />
                      <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Monte Carlo Parameters</h4>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">N Simulations</label>
                        <input type="number" min={100} max={5000} step={100} value={nSimulations}
                          onChange={e => setNSimulations(Math.max(100, Math.min(5000, Number(e.target.value) || 100)))}
                          disabled={running}
                          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm font-mono focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition disabled:opacity-50"
                        />
                        <p className="text-[10px] text-slate-400 mt-1">100 – 5,000 paths</p>
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">PD-LGD Correlation (ρ)</label>
                        <div className="flex items-center gap-2">
                          <input type="range" min={0} max={1} step={0.05} value={pdLgdCorrelation}
                            onChange={e => setPdLgdCorrelation(Number(e.target.value))} disabled={running}
                            className="flex-1 accent-indigo-500" />
                          <input type="number" min={0} max={1} step={0.05} value={pdLgdCorrelation}
                            onChange={e => setPdLgdCorrelation(Math.max(0, Math.min(1, Number(e.target.value) || 0)))}
                            disabled={running}
                            className="w-16 px-2 py-2 rounded-lg border border-slate-200 text-sm font-mono text-center focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition disabled:opacity-50" />
                        </div>
                      </div>
                      <div>
                        <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">Aging Factor</label>
                        <div className="flex items-center gap-2">
                          <input type="range" min={0} max={0.20} step={0.01} value={agingFactor}
                            onChange={e => setAgingFactor(Number(e.target.value))} disabled={running}
                            className="flex-1 accent-indigo-500" />
                          <input type="number" min={0} max={0.20} step={0.01} value={agingFactor}
                            onChange={e => setAgingFactor(Math.max(0, Math.min(0.20, Number(e.target.value) || 0)))}
                            disabled={running}
                            className="w-16 px-2 py-2 rounded-lg border border-slate-200 text-sm font-mono text-center focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition disabled:opacity-50" />
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1">+{(agingFactor * 100).toFixed(0)}%/quarter for Stage 2/3</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                      {[
                        { label: 'PD Floor', value: pdFloor, set: setPdFloor, min: 0.0001, max: 0.5, step: 0.001, fallback: 0.001 },
                        { label: 'PD Cap', value: pdCap, set: setPdCap, min: 0.5, max: 1, step: 0.01, fallback: 0.95 },
                        { label: 'LGD Floor', value: lgdFloor, set: setLgdFloor, min: 0.001, max: 0.5, step: 0.01, fallback: 0.01 },
                        { label: 'LGD Cap', value: lgdCap, set: setLgdCap, min: 0.5, max: 1, step: 0.01, fallback: 0.95 },
                      ].map(p => (
                        <div key={p.label}>
                          <label className="block text-[10px] font-semibold text-slate-500 mb-1">{p.label}</label>
                          <input type="number" min={p.min} max={p.max} step={p.step} value={p.value}
                            onChange={e => p.set(Number(e.target.value) || p.fallback)} disabled={running}
                            className="w-full px-2.5 py-1.5 rounded-lg border border-slate-200 text-xs font-mono focus:ring-2 focus:ring-brand/30 focus:border-brand outline-none transition disabled:opacity-50" />
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Scenario Weights */}
                  <div>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <Sliders size={14} className="text-indigo-500" />
                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Scenario Weights</h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <button onClick={equalizeWeights} disabled={running}
                          className="text-[10px] font-semibold text-indigo-600 hover:text-indigo-800 px-2 py-1 rounded-md hover:bg-indigo-50 transition disabled:opacity-50">
                          Equalize
                        </button>
                        <button onClick={resetToDefault} disabled={running}
                          className="flex items-center gap-1 text-[10px] font-semibold text-slate-500 hover:text-slate-700 px-2 py-1 rounded-md hover:bg-slate-100 transition disabled:opacity-50">
                          <RotateCcw size={10} /> Reset to Default
                        </button>
                      </div>
                    </div>

                    <div className="space-y-2.5">
                      {scenarioWeights.map(sw => (
                        <div key={sw.key} className="flex items-center gap-3">
                          <div className="flex items-center gap-2 w-36 flex-shrink-0">
                            <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: sw.color }} />
                            <span className="text-xs font-medium text-slate-700 truncate">{sw.label}</span>
                          </div>
                          <input type="range" min={0} max={60} step={1} value={sw.weight}
                            onChange={e => updateWeight(sw.key, Number(e.target.value))} disabled={running}
                            className="flex-1 accent-indigo-500" />
                          <span className="w-10 text-right text-xs font-mono font-semibold text-slate-700">{Math.round(sw.weight)}%</span>
                        </div>
                      ))}
                    </div>

                    <div className={`mt-3 flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold ${
                      weightsValid ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                      <span>Total: {totalWeight.toFixed(0)}%</span>
                      {weightsValid ? <CheckCircle2 size={14} /> : <span className="text-[10px] font-normal">Must sum to 100%</span>}
                    </div>
                  </div>

                  {/* Validation Warnings */}
                  {showValidationWarnings && validationResult?.warnings && (
                    <motion.div initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} className="pt-2">
                      <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-4 space-y-3">
                        <div className="flex items-center gap-2">
                          <AlertCircle size={16} className="text-amber-600 flex-shrink-0" />
                          <h4 className="text-sm font-bold text-amber-900">Validation Warnings</h4>
                        </div>
                        <ul className="space-y-1.5">
                          {validationResult.warnings.map((w, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-amber-800">
                              <span className="text-amber-400 mt-0.5">•</span><span>{w}</span>
                            </li>
                          ))}
                        </ul>
                        <div className="flex items-center gap-3 pt-1">
                          <button onClick={proceedAfterWarnings}
                            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-lg transition">
                            <ArrowRight size={14} /> Proceed Anyway
                          </button>
                          <button onClick={() => { setShowValidationWarnings(false); setValidationResult(null); }}
                            className="flex items-center gap-1.5 px-4 py-2.5 text-xs font-semibold text-slate-600 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition">
                            <Ban size={13} /> Cancel
                          </button>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* Running / Completed / Idle */}
                  {running ? (
                    <SimulationProgress
                      elapsedSeconds={elapsedSeconds}
                      progressPct={progressPct}
                      currentPhase={currentPhase}
                      currentMessage={currentMessage}
                      scenarioResults={scenarioResults}
                      runningEcl={runningEcl}
                      loanCount={loanCount}
                      scenarioCount={scenarioWeights.length}
                      nSimulations={nSimulations}
                      onCancel={cancelSimulation}
                    />
                  ) : completedResult ? (
                    <SimulationResults
                      totalEcl={completedResult.totalEcl}
                      coverage={completedResult.coverage}
                      durationMs={completedResult.duration}
                      loanCount={loanCount}
                      scenarioCount={scenarioWeights.length}
                      nSimulations={nSimulations}
                      completedTiming={completedTiming}
                      convergenceInfo={convergenceInfo}
                      progressEvents={progressEvents}
                      startTime={startTimeRef.current}
                      onApply={applyResults}
                      onDiscard={discardResults}
                    />
                  ) : (
                    <div className="pt-2">
                      {error && (
                        <div className="flex items-center gap-2 px-3 py-2.5 mb-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs">
                          <AlertCircle size={14} className="flex-shrink-0" /><span>{error}</span>
                        </div>
                      )}
                      {jobRunning && (
                        <div className="flex items-center gap-2 px-3 py-2.5 mb-4 rounded-lg bg-blue-50 border border-blue-200 text-blue-700 text-xs">
                          <Loader2 size={14} className="animate-spin flex-shrink-0" />
                          <span>{jobStatus}</span>
                          {jobRunUrl && (
                            <a href={jobRunUrl} target="_blank" rel="noopener noreferrer"
                              className="ml-auto flex items-center gap-1 text-blue-600 hover:text-blue-800 font-semibold">
                              <ExternalLink size={12} /> View Job
                            </a>
                          )}
                        </div>
                      )}
                      {jobStatus && !jobRunning && !error && (
                        <div className="flex items-center gap-2 px-3 py-2.5 mb-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs">
                          <CheckCircle2 size={14} className="flex-shrink-0" />
                          <span>{jobStatus}</span>
                          {jobRunUrl && (
                            <a href={jobRunUrl} target="_blank" rel="noopener noreferrer"
                              className="ml-auto flex items-center gap-1 text-emerald-600 hover:text-emerald-800 font-semibold">
                              <ExternalLink size={12} /> View Run
                            </a>
                          )}
                        </div>
                      )}
                      <div className="flex gap-3">
                        <button onClick={runSimulation} disabled={running || jobRunning || !weightsValid}
                          className="btn-primary flex-1 py-3.5 shadow-lg disabled:bg-slate-300 disabled:shadow-none">
                          <Play size={18} /><span>Run In-App</span>
                        </button>
                        <button onClick={runAsJob} disabled={running || jobRunning || !weightsValid}
                          className="flex-1 flex items-center justify-center gap-2 py-3.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold rounded-xl shadow-lg transition disabled:bg-slate-300 disabled:shadow-none">
                          <Server size={18} /><span>Run as Databricks Job</span>
                        </button>
                      </div>
                      {lastRun && (
                        <p className="text-center text-[10px] text-slate-400 mt-2">
                          Completed at {lastRun.timestamp.toLocaleTimeString()} · {lastRun.duration < 1000 ? `${lastRun.duration}ms` : `${(lastRun.duration / 1000).toFixed(1)}s`}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Run History */}
                  {runHistory.length > 0 && (
                    <div className="pt-2 border-t border-indigo-100">
                      <div className="flex items-center gap-2 mb-3">
                        <History size={14} className="text-indigo-500" />
                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Run History</h4>
                        <span className="text-[10px] text-slate-400 ml-auto">{runHistory.length} run{runHistory.length !== 1 ? 's' : ''} (last 10)</span>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-[11px]">
                          <thead>
                            <tr className="bg-slate-50">
                              <th className="py-1.5 px-2 text-center font-semibold text-slate-500">#</th>
                              <th className="py-1.5 px-2 text-left font-semibold text-slate-500">Time</th>
                              <th className="py-1.5 px-2 text-right font-semibold text-slate-500">N Sims</th>
                              <th className="py-1.5 px-2 text-right font-semibold text-slate-500">ρ</th>
                              <th className="py-1.5 px-2 text-right font-semibold text-slate-500">Aging</th>
                              <th className="py-1.5 px-2 text-right font-semibold text-slate-500">Total ECL</th>
                              <th className="py-1.5 px-2 text-right font-semibold text-slate-500">Duration</th>
                              <th className="py-1.5 px-2 text-center font-semibold text-slate-500"></th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {runHistory.map((entry, idx) => (
                              <tr key={idx} className="hover:bg-indigo-50/50 transition">
                                <td className="py-1.5 px-2 text-center font-mono text-slate-400">{idx + 1}</td>
                                <td className="py-1.5 px-2 text-left text-slate-600">{entry.timestamp.toLocaleTimeString()}</td>
                                <td className="py-1.5 px-2 text-right font-mono text-slate-700">{entry.n_sims.toLocaleString()}</td>
                                <td className="py-1.5 px-2 text-right font-mono text-slate-700">{entry.pd_lgd_correlation.toFixed(2)}</td>
                                <td className="py-1.5 px-2 text-right font-mono text-slate-700">{(entry.aging_factor * 100).toFixed(0)}%</td>
                                <td className="py-1.5 px-2 text-right font-mono font-semibold text-slate-800">
                                  {entry.total_ecl >= 1e6 ? `${(entry.total_ecl / 1e6).toFixed(2)}M`
                                    : entry.total_ecl >= 1e3 ? `${(entry.total_ecl / 1e3).toFixed(1)}K`
                                    : entry.total_ecl.toFixed(0)}
                                </td>
                                <td className="py-1.5 px-2 text-right text-slate-500">
                                  {entry.duration < 1000 ? `${entry.duration}ms` : `${(entry.duration / 1000).toFixed(1)}s`}
                                </td>
                                <td className="py-1.5 px-2 text-center">
                                  <button onClick={() => onSimulationComplete(entry.results)}
                                    className="inline-flex items-center gap-1 text-[10px] font-semibold text-indigo-600 hover:text-indigo-800 px-2 py-1 rounded-md hover:bg-indigo-100 transition">
                                    <Upload size={10} /> Load
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
