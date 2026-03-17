import { useState, useEffect, useCallback, lazy, Suspense } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Zap, RotateCcw } from 'lucide-react';
import ErrorBoundary from './components/ErrorBoundary';
import Stepper from './components/Stepper';
import { config } from './lib/config';
import { useToast } from './components/Toast';

const CreateProject = lazy(() => import('./pages/CreateProject'));
const DataProcessing = lazy(() => import('./pages/DataProcessing'));
const DataControl = lazy(() => import('./pages/DataControl'));
const ModelExecution = lazy(() => import('./pages/ModelExecution'));
const Overlays = lazy(() => import('./pages/Overlays'));
const StressTesting = lazy(() => import('./pages/StressTesting'));
const SignOff = lazy(() => import('./pages/SignOff'));
import { api, type Project, type Overlay } from './lib/api';
import { fmtDateTime } from './lib/format';

const TABS = [
  { label: 'Create Project', key: 'create', stepKey: 'create_project' },
  { label: 'Data Processing', key: 'data', stepKey: 'data_processing' },
  { label: 'Data Control', key: 'dc', stepKey: 'data_control' },
  { label: 'Model Exec & Control', key: 'model', stepKey: 'model_control' },
  { label: 'Stress Testing', key: 'stress', stepKey: 'stress_testing' },
  { label: 'Overlays', key: 'overlays', stepKey: 'overlays' },
  { label: 'Sign Off', key: 'signoff', stepKey: 'sign_off' },
];

const DEFAULT_PROJECT_ID = config.defaultProjectId;

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [projectId, setProjectId] = useState(DEFAULT_PROJECT_ID);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const loadProject = useCallback(async () => {
    try {
      const p = await api.getProject(projectId);
      setProject(p);
    } catch {
      setProject(null);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => { loadProject(); }, [loadProject]);
  useEffect(() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }, [activeTab]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.altKey && e.key >= '1' && e.key <= '7') {
        const idx = parseInt(e.key) - 1;
        if (project && idx <= (project.current_step ?? 0)) {
          setActiveTab(idx);
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [project]);

  const refresh = async () => { await loadProject(); };

  const handleCreate = async (data: Parameters<typeof api.createProject>[0]) => {
    try {
      const p = await api.createProject(data);
      setProject(p);
      setProjectId(data.project_id);
      setActiveTab(1);
      toast('Project created successfully', 'success');
    } catch (e: any) {
      toast(`Failed to create project: ${e.message}`, 'error');
    }
  };

  const handleDataProcComplete = async () => {
    try {
      await api.advanceStep(projectId, 'data_processing', 'Data Analyst', 'Portfolio data reviewed and validated');
      await refresh();
      setActiveTab(2);
      toast('Data processing completed', 'success');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleDcApprove = async (comment: string) => {
    try {
      await api.advanceStep(projectId, 'data_control', 'Data Manager', comment || 'Approved');
      await api.advanceStep(projectId, 'model_execution', 'System', 'ECL engine triggered', 'in_progress');
      await refresh();
      setActiveTab(3);
      toast('Data control approved — ECL engine triggered', 'success');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleDcReject = async (comment: string) => {
    try {
      await api.advanceStep(projectId, 'data_control', 'Data Manager', comment, 'rejected');
      await refresh();
      toast('Data control rejected — please review and resubmit', 'error');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleModelApprove = async (comment: string) => {
    try {
      await api.advanceStep(projectId, 'model_execution', 'ECL Engine v3.2', 'Stressed PD/LGD/EAD computed across 8 plausible scenarios with Monte Carlo simulation');
      await api.advanceStep(projectId, 'model_control', 'Model Validator', comment || 'Model results reviewed and approved');
      await refresh();
      setActiveTab(4);
      toast('Model approved — proceeding to stress testing', 'success');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleModelReject = async (comment: string) => {
    try {
      await api.advanceStep(projectId, 'model_execution', 'Model Validator', comment, 'rejected');
      await refresh();
      toast('Model rejected — please review and recalculate', 'error');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleStressApprove = async (comment: string) => {
    try {
      await api.advanceStep(projectId, 'stress_testing', 'Risk Analyst', comment || 'Stress testing reviewed');
      await refresh();
      setActiveTab(5);
      toast('Stress testing approved', 'success');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleStressReject = async (comment: string) => {
    try {
      await api.advanceStep(projectId, 'stress_testing', 'Risk Analyst', comment, 'rejected');
      await refresh();
      toast('Stress testing rejected — please review scenarios', 'error');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleOverlaySubmit = async (overlays: Overlay[], comment: string) => {
    try {
      await api.saveOverlays(projectId, overlays, comment || 'Overlay package submitted');
      await refresh();
      setActiveTab(6);
      toast('Overlays submitted — ready for sign-off', 'success');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  const handleSignOff = async (name: string) => {
    try {
      await api.signOff(projectId, name);
      await refresh();
      toast('Project signed off and locked', 'success');
    } catch (e: any) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-3 border-brand border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-sm text-slate-400">Loading ECL Workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-navy text-white sticky top-0 z-50 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <img src={config.logoPath} alt={config.bankName} className="h-7 brightness-0 invert" />
            <div className="h-6 w-px bg-white/20" />
            <div>
              <h1 className="text-sm font-bold tracking-tight">{config.appTitle}</h1>
              <p className="text-[10px] text-white/40 font-medium">{config.appSubtitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-white/40">
            <Zap size={12} className="text-brand" />
            <span>Powered by <span className="text-white/70 font-semibold">{config.poweredBy}</span></span>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-5">
        {project && (
          <div className="mb-4 flex items-center gap-4 text-xs text-slate-500 bg-white rounded-lg shadow-sm px-4 py-2.5">
            <span className="font-bold text-slate-700">{project.project_name || project.project_id}</span>
            <span className="h-3 w-px bg-slate-200" />
            <span>ID: <span className="font-mono">{project.project_id}</span></span>
            <span className="h-3 w-px bg-slate-200" />
            <span>Reporting: <span className="font-semibold">{project.reporting_date}</span></span>
            <span className="h-3 w-px bg-slate-200" />
            <span>Type: <span className="font-semibold uppercase">{project.project_type}</span></span>
            {project.created_at && (
              <>
                <span className="h-3 w-px bg-slate-200" />
                <span>Created: {fmtDateTime(project.created_at)}</span>
              </>
            )}
            {project.signed_off_by ? (
              <>
                <span className="h-3 w-px bg-slate-200" />
                <span className="text-emerald-600 font-semibold">✓ Signed off by {project.signed_off_by}</span>
              </>
            ) : (
              <>
                <span className="ml-auto" />
                <button
                  onClick={async () => {
                    if (!window.confirm('Reset all workflow steps? This cannot be undone.')) return;
                    try {
                      await api.resetProject(projectId);
                      await refresh();
                      setActiveTab(0);
                      toast('Project reset to initial state', 'info');
                    } catch (e: any) {
                      toast(`Reset failed: ${e.message}`, 'error');
                    }
                  }}
                  className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-500 transition"
                  title="Reset all workflow steps"
                >
                  <RotateCcw size={11} /> Reset
                </button>
              </>
            )}
          </div>
        )}
        <Stepper project={project} activeStep={activeTab} onStepClick={setActiveTab} />

        <div className="mt-5 flex gap-1 bg-white rounded-xl shadow-sm p-1.5 overflow-x-auto">
          {TABS.map((t, i) => {
            const isActive = i === activeTab;
            const isReachable = !project || i <= (project.current_step ?? 0);
            const isCompleted = project?.step_status?.[t.stepKey] === 'completed';
            const isRejected = project?.step_status?.[t.stepKey] === 'rejected';
            return (
              <button
                key={t.key}
                onClick={() => isReachable && setActiveTab(i)}
                disabled={!isReachable}
                className={`relative px-4 py-2.5 text-xs font-semibold rounded-lg transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-navy text-white shadow-sm'
                    : isReachable
                    ? 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
                    : 'text-slate-300 cursor-not-allowed'
                }`}
              >
                <span className="mr-1.5">{isCompleted ? '✓' : isRejected ? '✗' : `${i + 1}.`}</span>{t.label}
              </button>
            );
          })}
        </div>

        <div className="mt-6 pb-10">
          <ErrorBoundary>
            <Suspense fallback={<div className="flex justify-center py-20"><div className="animate-spin w-8 h-8 border-2 border-brand border-t-transparent rounded-full" /></div>}>
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
              >
                {activeTab === 0 && <CreateProject project={project} onCreate={handleCreate} />}
              {activeTab === 1 && <DataProcessing project={project} onComplete={handleDataProcComplete} />}
              {activeTab === 2 && <DataControl project={project} onApprove={handleDcApprove} onReject={handleDcReject} />}
              {activeTab === 3 && <ModelExecution project={project} onApprove={handleModelApprove} onReject={handleModelReject} />}
              {activeTab === 4 && <StressTesting project={project} onApprove={handleStressApprove} onReject={handleStressReject} />}
              {activeTab === 5 && <Overlays project={project} onSubmit={handleOverlaySubmit} />}
              {activeTab === 6 && <SignOff project={project} onSignOff={handleSignOff} />}

              {activeTab > 0 && (
                <div className="mt-6 flex justify-between">
                  <button onClick={() => setActiveTab(activeTab - 1)}
                    className="px-4 py-2 text-xs font-semibold text-slate-500 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition">
                    ← Previous: {TABS[activeTab - 1]?.label}
                  </button>
                  {activeTab < TABS.length - 1 && project && activeTab < (project.current_step ?? 0) && (
                    <button onClick={() => setActiveTab(activeTab + 1)}
                      className="px-4 py-2 text-xs font-semibold text-slate-500 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition">
                      Next: {TABS[activeTab + 1]?.label} →
                    </button>
                  )}
                </div>
              )}
              </motion.div>
            </AnimatePresence>
            </Suspense>
          </ErrorBoundary>
        </div>
      </div>

      <footer className="border-t border-slate-200 bg-white">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <img src={config.logoPath} alt={config.bankName} className="h-4 opacity-30" />
            <span>{config.framework} ECL Workflow &mdash; {config.bankLegalName}</span>
          </div>
          <span>Databricks Lakebase &middot; FastAPI &middot; React</span>
        </div>
      </footer>
    </div>
  );
}
