import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, RotateCcw, ChevronDown, ChevronLeft, ChevronRight,
  Plus, FolderOpen, Clock, CheckCircle2, FolderPlus, Database, ShieldCheck,
  Satellite, Cpu, BarChart3, Layers, FileSignature, Moon, Sun,
} from 'lucide-react';
import ErrorBoundary from './components/ErrorBoundary';
import SetupWizard from './components/SetupWizard';
import { Sidebar, type ViewType } from './components/Sidebar';
import { config } from './lib/config';
import { useToast } from './components/Toast';
import { useTheme } from './lib/theme';
import HelpPanel from './components/HelpPanel';
import ConfirmDialog from './components/ConfirmDialog';

const CreateProject = lazy(() => import('./pages/CreateProject'));
const DataProcessing = lazy(() => import('./pages/DataProcessing'));
const DataControl = lazy(() => import('./pages/DataControl'));
const SatelliteModel = lazy(() => import('./pages/SatelliteModel'));
const ModelExecution = lazy(() => import('./pages/ModelExecution'));
const Overlays = lazy(() => import('./pages/Overlays'));
const StressTesting = lazy(() => import('./pages/StressTesting'));
const SignOff = lazy(() => import('./pages/SignOff'));
const Admin = lazy(() => import('./pages/Admin'));
const DataMapping = lazy(() => import('./pages/DataMapping'));
const ModelRegistry = lazy(() => import('./pages/ModelRegistry'));
const GLJournals = lazy(() => import('./pages/GLJournals'));
const HazardModels = lazy(() => import('./pages/HazardModels'));
const Backtesting = lazy(() => import('./pages/Backtesting'));
const MarkovChains = lazy(() => import('./pages/MarkovChains'));
const AdvancedFeatures = lazy(() => import('./pages/AdvancedFeatures'));
const RegulatoryReports = lazy(() => import('./pages/RegulatoryReports'));
const ApprovalWorkflow = lazy(() => import('./pages/ApprovalWorkflow'));
const Attribution = lazy(() => import('./pages/Attribution'));
import { api, type Project, type Overlay } from './lib/api';

const STEPS = [
  { label: 'Create Project', key: 'create_project', icon: FolderPlus, short: 'Create' },
  { label: 'Data Processing', key: 'data_processing', icon: Database, short: 'Data' },
  { label: 'Data Control', key: 'data_control', icon: ShieldCheck, short: 'QC' },
  { label: 'Satellite Model', key: 'satellite_model', icon: Satellite, short: 'Satellite' },
  { label: 'Monte Carlo', key: 'model_execution', icon: Cpu, short: 'Monte Carlo' },
  { label: 'Stress Testing', key: 'stress_testing', icon: BarChart3, short: 'Stress' },
  { label: 'Overlays', key: 'overlays', icon: Layers, short: 'Overlays' },
  { label: 'Sign Off', key: 'sign_off', icon: FileSignature, short: 'Sign Off' },
];

const DEFAULT_PROJECT_ID = config.defaultProjectId;

function ProjectSelector({
  projects, currentId, onSelect, onNew,
}: {
  projects: Project[];
  currentId: string;
  onSelect: (id: string) => void;
  onNew: () => void;
}) {
  const [open, setOpen] = useState(false);
  const current = projects.find(p => p.project_id === currentId);

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} aria-expanded={open} aria-haspopup="listbox" aria-label="Select ECL project"
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.06] border border-white/[0.08] text-white text-xs font-medium hover:bg-white/[0.1] transition focus-visible:ring-2 focus-visible:ring-brand">
        <FolderOpen size={13} className="text-brand" />
        <span className="max-w-[180px] truncate">{current?.project_name || currentId}</span>
        <ChevronDown size={12} className={`transition-transform ${open ? 'rotate-180' : ''} text-white/40`} />
      </button>
      <AnimatePresence>
        {open && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
            <motion.div initial={{ opacity: 0, y: -4, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -4, scale: 0.97 }} transition={{ duration: 0.15 }}
              className="absolute top-full right-0 mt-2 w-80 glass-card rounded-2xl z-50 overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-700">
                <p className="text-[11px] font-bold text-slate-500 dark:text-slate-300 uppercase tracking-wider">ECL Projects</p>
              </div>
              <div className="max-h-72 overflow-y-auto p-1.5">
                {projects.map(p => {
                  const isCurrent = p.project_id === currentId;
                  const isSigned = !!p.signed_off_by;
                  return (
                    <button key={p.project_id} onClick={() => { onSelect(p.project_id); setOpen(false); }}
                      className={`w-full text-left px-3 py-2.5 rounded-xl flex items-center gap-3 transition ${isCurrent ? 'bg-brand/8 ring-1 ring-brand/20' : 'hover:bg-slate-50 dark:hover:bg-slate-800/50'}`}>
                      <div className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${isSigned ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-600'}`}>
                        {isSigned ? <CheckCircle2 size={14} /> : <Clock size={14} />}
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate">{p.project_name || p.project_id}</p>
                        <p className="text-[11px] text-slate-500 dark:text-slate-300">
                          {p.reporting_date} &middot; Step {(p.current_step ?? 0) + 1}/8
                          {isSigned && <span className="text-emerald-700 ml-1 font-semibold">Signed</span>}
                        </p>
                      </div>
                    </button>
                  );
                })}
              </div>
              <div className="border-t border-slate-100 dark:border-slate-700 p-2">
                <button onClick={() => { onNew(); setOpen(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold text-brand hover:bg-brand/5 transition">
                  <Plus size={14} /> New Project
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

function HeroStepper({ project, activeStep, onStepClick }: { project: Project | null; activeStep: number; onStepClick: (i: number) => void }) {
  const ss = project?.step_status || {};
  const cur = project?.current_step ?? 0;

  return (
    <nav aria-label="Workflow steps" className="flex items-center justify-center gap-0 w-full max-w-5xl mx-auto">
      {STEPS.map((s, i) => {
        const status = ss[s.key] || 'pending';
        const isActive = i === activeStep;
        const isCompleted = status === 'completed';
        const isRejected = status === 'rejected';
        const isReachable = i <= cur;
        const Icon = s.icon;

        let circleClass = 'bg-white/[0.04] text-white/20 border border-white/[0.06]';
        let labelClass = 'text-white/25';
        let glowClass = '';
        let ringExtra = '';
        if (isCompleted) {
          circleClass = 'gradient-brand text-white border-0';
          labelClass = 'text-brand font-bold';
          glowClass = 'glow-brand animate-glow-pulse';
        } else if (isRejected) {
          circleClass = 'bg-red-500/90 text-white border-0';
          labelClass = 'text-red-400 font-bold';
          glowClass = 'shadow-[0_0_20px_rgba(239,68,68,0.3)]';
        } else if (isActive) {
          circleClass = 'bg-white text-navy border-0';
          labelClass = 'text-white font-bold';
          glowClass = 'shadow-[0_0_30px_rgba(255,255,255,0.15)]';
          ringExtra = 'active';
        } else if (isReachable) {
          circleClass = 'bg-white/[0.08] text-white/50 border border-white/[0.12]';
          labelClass = 'text-white/40 font-medium';
        }

        const lineClass = isCompleted
          ? 'bg-gradient-to-r from-brand/60 to-brand/30 stepper-line-animated'
          : 'bg-white/[0.06]';

        return (
          <div key={s.key} className="flex items-center" style={{ flex: i < STEPS.length - 1 ? 1 : 'none' }}>
            <motion.button
              whileHover={isReachable ? { scale: 1.1, y: -2 } : {}}
              whileTap={isReachable ? { scale: 0.92 } : {}}
              onClick={() => isReachable && onStepClick(i)}
              className={`relative flex flex-col items-center group ${isReachable ? 'cursor-pointer' : 'cursor-not-allowed'} focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-[#0B0F1A] rounded-2xl`}
              disabled={!isReachable}
              aria-label={`Step ${i + 1}: ${s.label} — ${isCompleted ? 'completed' : isRejected ? 'rejected' : isActive ? 'current' : 'pending'}`}
              aria-current={isActive ? 'step' : undefined}
            >
              {isActive && (
                <motion.div
                  className="absolute -inset-2 rounded-2xl bg-white/[0.04]"
                  layoutId="activeStepBg"
                  transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                />
              )}
              <div className={`step-icon-ring ${ringExtra} relative`}>
                <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 ${circleClass} ${glowClass}`}>
                  {isCompleted ? (
                    <CheckCircle2 size={24} strokeWidth={2.5} />
                  ) : isRejected ? (
                    <span className="text-lg font-black">!</span>
                  ) : (
                    <Icon size={22} strokeWidth={isActive ? 2.5 : 1.8} className={`transition-all duration-300 ${isActive ? '' : 'group-hover:scale-110'}`} />
                  )}
                </div>
                {isActive && (
                  <motion.div
                    className="absolute -bottom-0.5 left-1/2 w-6 h-1 rounded-full gradient-brand"
                    initial={{ scaleX: 0, x: '-50%' }}
                    animate={{ scaleX: 1, x: '-50%' }}
                    transition={{ delay: 0.1, duration: 0.3 }}
                  />
                )}
              </div>
              <span className={`text-[11px] mt-2.5 text-center max-w-[72px] leading-tight transition-colors duration-300 ${labelClass}`}>
                {s.short}
              </span>
              {isActive && (
                <motion.span
                  className="text-[9px] text-brand/60 font-semibold mt-0.5"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  Current
                </motion.span>
              )}
            </motion.button>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-[2px] mx-2 rounded-full transition-colors duration-500 ${lineClass}`} />
            )}
          </div>
        );
      })}
    </nav>
  );
}

function SuspenseFallback({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex justify-center py-20">
      <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center animate-pulse">
        {children}
      </div>
    </div>
  );
}

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [project, setProject] = useState<Project | null>(null);
  const [projectId, setProjectId] = useState(DEFAULT_PROJECT_ID);
  const [activeTab, setActiveTab] = useState(0);
  const [activeView, setActiveView] = useState<ViewType>('workflow');
  const [loading, setLoading] = useState(true);
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [setupChecked, setSetupChecked] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [resetLoading, setResetLoading] = useState(false);
  const { toast } = useToast();
  const { isDark, toggleMode } = useTheme();

  const loadProjects = useCallback(async () => {
    try { setProjects(await api.listProjects()); } catch { /* */ }
  }, []);

  const loadProject = useCallback(async () => {
    try { setProject(await api.getProject(projectId)); }
    catch { setProject(null); }
    finally { setLoading(false); }
  }, [projectId]);

  useEffect(() => {
    api.setupStatus().then(status => {
      if (!status.is_configured) setShowSetupWizard(true);
      setSetupChecked(true);
    }).catch(() => setSetupChecked(true));
  }, []);

  useEffect(() => { loadProjects(); loadProject(); }, [loadProjects, loadProject]);
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }, [activeTab]);

  useEffect(() => {
    const handler = (e: Event) => {
      const step = (e as CustomEvent).detail?.step;
      if (typeof step === 'number' && step >= 0 && step < STEPS.length) {
        setActiveTab(step);
      }
    };
    window.addEventListener('ecl-navigate-step', handler);
    return () => window.removeEventListener('ecl-navigate-step', handler);
  }, []);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.altKey && e.key >= '1' && e.key <= '8') {
        const idx = parseInt(e.key) - 1;
        if (project && idx <= (project.current_step ?? 0)) {
          setActiveView('workflow');
          setActiveTab(idx);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [project]);

  const refresh = async () => { await loadProject(); await loadProjects(); };
  const handleSelectProject = (id: string) => { setProjectId(id); setLoading(true); setActiveTab(0); };
  const handleNewProject = () => { setProject(null); setActiveTab(0); setActiveView('workflow'); };

  const handleCreate = async (data: Parameters<typeof api.createProject>[0]) => {
    try { const p = await api.createProject(data); setProject(p); setProjectId(data.project_id); setActiveTab(1); await loadProjects(); toast('Project created', 'success'); }
    catch (e: any) { toast(`Failed: ${e.message}`, 'error'); }
  };

  const makeHandler = (step: string, role: string, nextTab: number, successMsg: string) => async (comment: string) => {
    try { await api.advanceStep(projectId, step, role, comment || successMsg); await refresh(); setActiveTab(nextTab); toast(successMsg, 'success'); }
    catch (e: any) { toast(`Error: ${e.message}`, 'error'); }
  };

  const makeRejectHandler = (step: string, role: string) => async (comment: string) => {
    try { await api.advanceStep(projectId, step, role, comment, 'rejected'); await refresh(); toast(`${step.replace(/_/g, ' ')} rejected`, 'error'); }
    catch (e: any) { toast(`Error: ${e.message}`, 'error'); }
  };

  const handleDataProcComplete = async () => {
    try { await api.advanceStep(projectId, 'data_processing', 'Data Analyst', 'Portfolio data reviewed'); await refresh(); setActiveTab(2); toast('Data processing completed', 'success'); }
    catch (e: any) { toast(`Error: ${e.message}`, 'error'); }
  };

  const handleDcApprove = makeHandler('data_control', 'Data Manager', 3, 'Data control approved');
  const handleDcReject = makeRejectHandler('data_control', 'Data Manager');
  const handleSatelliteApprove = makeHandler('satellite_model', 'Model Analyst', 4, 'Satellite models approved');
  const handleSatelliteReject = makeRejectHandler('satellite_model', 'Model Analyst');
  const handleModelApprove = makeHandler('model_execution', 'Model Validator', 5, 'Model approved');
  const handleModelReject = makeRejectHandler('model_execution', 'Model Validator');
  const handleStressApprove = makeHandler('stress_testing', 'Risk Analyst', 6, 'Stress testing approved');
  const handleStressReject = makeRejectHandler('stress_testing', 'Risk Analyst');

  const handleOverlaySubmit = async (overlays: Overlay[], comment: string) => {
    try { await api.saveOverlays(projectId, overlays, comment || 'Overlays submitted'); await refresh(); setActiveTab(7); toast('Overlays submitted', 'success'); }
    catch (e: any) { toast(`Error: ${e.message}`, 'error'); }
  };

  const handleSignOff = async (name: string, attestation_data?: Record<string, any>) => {
    try { await api.signOff(projectId, name, attestation_data); await refresh(); toast('Project signed off', 'success'); }
    catch (e: any) { toast(`Error: ${e.message}`, 'error'); }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-[#0B0F1A] flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 rounded-3xl gradient-brand opacity-20 animate-ping" />
            <div className="absolute -inset-3 rounded-3xl bg-brand/10 blur-xl animate-pulse" />
            <div className="relative w-20 h-20 rounded-3xl gradient-brand flex items-center justify-center shadow-xl animate-glow-pulse">
              <Zap size={36} strokeWidth={2.5} className="text-white drop-shadow-lg" />
            </div>
          </div>
          <p className="text-base font-semibold text-slate-500 dark:text-slate-300 dark:text-white/40 tracking-wide">Loading ECL Workspace...</p>
        </div>
      </div>
    );
  }

  const curStep = project?.current_step ?? 0;
  const canGoNext = activeTab < STEPS.length - 1 && project && activeTab < curStep;
  const canGoPrev = activeTab > 0;

  const isWorkflow = activeView === 'workflow';

  const renderSecondaryView = () => {
    switch (activeView) {
      case 'data-mapping':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <DataMapping />
          </Suspense>
        );
      case 'admin':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <Admin />
          </Suspense>
        );
      case 'attribution':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <Attribution />
          </Suspense>
        );
      case 'models':
        return (
          <Suspense fallback={<SuspenseFallback><Database size={20} className="text-white" /></SuspenseFallback>}>
            <ModelRegistry />
          </Suspense>
        );
      case 'backtesting':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <Backtesting />
          </Suspense>
        );
      case 'hazard':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <HazardModels />
          </Suspense>
        );
      case 'markov':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <MarkovChains />
          </Suspense>
        );
      case 'reports':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <RegulatoryReports project={project} />
          </Suspense>
        );
      case 'approvals':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <ApprovalWorkflow />
          </Suspense>
        );
      case 'advanced':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <AdvancedFeatures />
          </Suspense>
        );
      case 'gl-journals':
        return (
          <Suspense fallback={<SuspenseFallback><Zap size={20} className="text-white" /></SuspenseFallback>}>
            <GLJournals project={project} />
          </Suspense>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-[#0B0F1A] flex">
      {/* Skip to content link */}
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-1/2 focus:-translate-x-1/2 focus:z-[999] focus:px-6 focus:py-3 focus:bg-brand focus:text-white focus:rounded-xl focus:text-sm focus:font-bold focus:shadow-lg">
        Skip to main content
      </a>

      {/* Setup Wizard Overlay */}
      {setupChecked && showSetupWizard && (
        <SetupWizard onComplete={() => { setShowSetupWizard(false); loadProjects(); loadProject(); }} />
      )}

      {/* Sidebar */}
      <Sidebar activeView={activeView} onNavigate={setActiveView} />

      {/* Main content */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Header */}
        <header className="gradient-hero gradient-mesh relative overflow-hidden" role="banner">
          <div className="absolute top-0 left-1/4 w-96 h-96 rounded-full bg-brand/[0.03] blur-[100px] pointer-events-none" />
          <div className="absolute top-0 right-1/4 w-64 h-64 rounded-full bg-blue-500/[0.04] blur-[80px] pointer-events-none" />

          <div className="relative z-10 max-w-[1400px] mx-auto px-6 pt-5 pb-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="hidden lg:block">
                <div className="hero-logo-container relative">
                  <div className="w-12 h-12 rounded-2xl gradient-brand flex items-center justify-center shadow-xl animate-glow-pulse">
                    <Zap size={24} strokeWidth={2.5} className="text-white drop-shadow-lg" />
                  </div>
                </div>
              </div>
              {/* Mobile: extra left padding for hamburger */}
              <div className="lg:hidden w-8" />
              <div>
                <h1 className="text-lg font-extrabold text-slate-800 dark:text-white tracking-tight leading-tight">{config.appTitle}</h1>
                <p className="text-xs text-slate-500 dark:text-slate-300 dark:text-white/35 font-medium tracking-wide">{config.appSubtitle}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {projects.length > 0 && (
                <ProjectSelector projects={projects} currentId={projectId} onSelect={handleSelectProject} onNew={handleNewProject} />
              )}
              <div className="h-6 w-px bg-slate-200 dark:bg-white/[0.08]" />
              <button onClick={toggleMode} aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'} title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                className="flex items-center justify-center w-9 h-9 rounded-xl bg-slate-100 dark:bg-white/[0.06] border border-slate-200 dark:border-white/[0.08] text-slate-500 dark:text-white/60 hover:bg-slate-200 dark:hover:bg-white/[0.12] hover:text-slate-800 dark:hover:text-white transition-all duration-200 focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:ring-offset-white dark:focus-visible:ring-offset-[#0B0F1A]">
                {isDark ? <Sun size={16} /> : <Moon size={16} />}
              </button>
              <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-300 dark:text-white/25">
                <div className="w-2 h-2 rounded-full bg-brand animate-pulse" />
                <span className="hidden sm:inline">Powered by <span className="text-slate-500 dark:text-white/45 font-semibold">{config.poweredBy}</span></span>
              </div>
            </div>
          </div>

          {/* Stepper in hero — only for workflow view */}
          {isWorkflow && project && (
            <div className="relative z-10 pb-8 pt-4 px-6">
              <HeroStepper project={project} activeStep={activeTab} onStepClick={setActiveTab} />
              <div className="text-center mt-5">
                <p className="text-white/30 text-[11px] uppercase tracking-[0.2em] font-semibold">
                  Step {activeTab + 1} of {STEPS.length}
                </p>
                <h2 className="text-white text-xl font-extrabold mt-1 tracking-tight">{STEPS[activeTab].label}</h2>
              </div>
            </div>
          )}

          <div className={`absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t to-transparent ${isDark ? 'from-[#0F172A]' : 'from-[#F1F5F9]'}`} />
        </header>

        {/* Content Area */}
        <main id="main-content" role="main" className="content-area flex-1">
          <div className="max-w-[1400px] mx-auto px-6 py-6">
            {isWorkflow ? (
              <>
                {project && (
                  <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }}
                    className="mb-5 flex items-center gap-3 text-xs glass-card rounded-2xl px-5 py-3">
                    <div className="w-7 h-7 rounded-lg gradient-brand flex items-center justify-center flex-shrink-0">
                      <FolderOpen size={12} className="text-white" />
                    </div>
                    <span className="font-bold text-slate-700 dark:text-slate-200">{project.project_name || project.project_id}</span>
                    <span className="h-3 w-px bg-slate-200" />
                    <span className="text-slate-500 dark:text-slate-300 font-mono">{project.project_id}</span>
                    <span className="h-3 w-px bg-slate-200" />
                    <span className="text-slate-500 dark:text-slate-400 font-semibold">{project.reporting_date}</span>
                    <span className="h-3 w-px bg-slate-200" />
                    <span className="text-slate-500 dark:text-slate-400 font-semibold uppercase">{project.project_type}</span>
                    {project.signed_off_by ? (
                      <span className="ml-auto text-emerald-600 font-semibold flex items-center gap-1">
                        <CheckCircle2 size={12} /> Signed off by {project.signed_off_by}
                      </span>
                    ) : (
                      <button onClick={async () => {
                        if (!window.confirm('This will reset all workflow steps. Any unsaved progress will be lost. Continue?')) return;
                        try {
                          await api.resetProject(projectId);
                          await refresh();
                          setActiveTab(0);
                          toast('Project reset', 'info');
                        } catch (e: any) {
                          toast(`Reset failed: ${e.message}`, 'error');
                        }
                      }} aria-label="Reset all workflow steps" className="ml-auto flex items-center gap-1 text-slate-500 dark:text-slate-300 hover:text-red-500 transition focus-visible:ring-2 focus-visible:ring-brand rounded-lg">
                        <RotateCcw size={11} /> Reset
                      </button>
                    )}
                  </motion.div>
                )}

                <ErrorBoundary>
                  <Suspense fallback={<div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>}>
                    <AnimatePresence mode="wait">
                      <motion.div key={activeTab} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.2 }}>
                        {activeTab === 0 && <CreateProject project={project} onCreate={handleCreate} onSelectProject={handleSelectProject} />}
                        {activeTab === 1 && <DataProcessing project={project} onComplete={handleDataProcComplete} />}
                        {activeTab === 2 && <DataControl project={project} onApprove={handleDcApprove} onReject={handleDcReject} />}
                        {activeTab === 3 && <SatelliteModel project={project} onApprove={handleSatelliteApprove} onReject={handleSatelliteReject} />}
                        {activeTab === 4 && <ModelExecution project={project} onApprove={handleModelApprove} onReject={handleModelReject} />}
                        {activeTab === 5 && <StressTesting project={project} onApprove={handleStressApprove} onReject={handleStressReject} />}
                        {activeTab === 6 && <Overlays project={project} onSubmit={handleOverlaySubmit} />}
                        {activeTab === 7 && <SignOff project={project} onSignOff={handleSignOff} />}
                      </motion.div>
                    </AnimatePresence>
                  </Suspense>
                </ErrorBoundary>

                {activeTab > 0 && (
                  <div className="mt-8 flex justify-between items-center">
                    {canGoPrev ? (
                      <button onClick={() => setActiveTab(activeTab - 1)}
                        className="group flex items-center gap-2 px-5 py-3 text-sm font-semibold text-slate-500 dark:text-slate-400 glass-card rounded-2xl hover:shadow-md transition">
                        <ChevronLeft size={16} className="group-hover:-translate-x-0.5 transition-transform" />
                        {STEPS[activeTab - 1]?.label}
                      </button>
                    ) : <div />}
                    {canGoNext ? (
                      <button onClick={() => setActiveTab(activeTab + 1)}
                        className="group flex items-center gap-2 px-5 py-3 text-sm font-bold text-white gradient-brand rounded-2xl shadow-lg glow-brand hover:opacity-80 transition">
                        {STEPS[activeTab + 1]?.label}
                        <ChevronRight size={16} className="group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    ) : <div />}
                  </div>
                )}

                <HelpPanel activeStep={activeTab} />

                <div className="h-10" />
              </>
            ) : (
              <ErrorBoundary>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeView}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                  >
                    {renderSecondaryView()}
                  </motion.div>
                </AnimatePresence>
              </ErrorBoundary>
            )}
          </div>
        </main>

        <footer className="bg-white dark:bg-[#0B0F1A] border-t border-slate-100 dark:border-white/[0.04]">
          <div className="max-w-[1400px] mx-auto px-6 py-4 flex items-center justify-between text-[11px] text-slate-300 dark:text-white/20">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded gradient-brand opacity-40" />
              <span>{config.framework} ECL Workflow &mdash; {config.bankLegalName}</span>
            </div>
            <span>Databricks Lakebase &middot; FastAPI &middot; React</span>
          </div>
        </footer>

        <ConfirmDialog
          open={showResetConfirm}
          title="Reset Project"
          description="This will reset all workflow steps back to the beginning. Any unsaved progress will be lost. This action cannot be undone."
          confirmLabel="Reset Project"
          variant="danger"
          loading={resetLoading}
          onConfirm={async () => {
            setResetLoading(true);
            try {
              await api.resetProject(projectId);
              await refresh();
              setActiveTab(0);
              toast('Project reset', 'info');
            } catch (e: any) {
              toast(`Reset failed: ${e.message}`, 'error');
            } finally {
              setResetLoading(false);
              setShowResetConfirm(false);
            }
          }}
          onCancel={() => setShowResetConfirm(false)}
        />
      </div>
    </div>
  );
}
