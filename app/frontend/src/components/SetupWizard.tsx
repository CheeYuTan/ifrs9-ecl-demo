import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Zap, CheckCircle2, XCircle, Database, Building2, FolderPlus,
  ChevronRight, ChevronLeft, Loader2, RefreshCw, Download,
  Globe, DollarSign, Calendar, Palette, ArrowRight,
  Server, Table2, Shield, Sparkles, ExternalLink,
} from 'lucide-react';
import { api, type SetupStatus } from '../lib/api';

interface SetupWizardProps {
  onComplete: () => void;
}

const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '\u20AC', name: 'Euro' },
  { code: 'GBP', symbol: '\u00A3', name: 'British Pound' },
  { code: 'JPY', symbol: '\u00A5', name: 'Japanese Yen' },
  { code: 'CHF', symbol: 'CHF', name: 'Swiss Franc' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
  { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar' },
  { code: 'HKD', symbol: 'HK$', name: 'Hong Kong Dollar' },
  { code: 'MYR', symbol: 'RM', name: 'Malaysian Ringgit' },
  { code: 'PHP', symbol: '\u20B1', name: 'Philippine Peso' },
  { code: 'INR', symbol: '\u20B9', name: 'Indian Rupee' },
  { code: 'ZAR', symbol: 'R', name: 'South African Rand' },
  { code: 'BRL', symbol: 'R$', name: 'Brazilian Real' },
  { code: 'AED', symbol: 'AED', name: 'UAE Dirham' },
  { code: 'SAR', symbol: 'SAR', name: 'Saudi Riyal' },
  { code: 'NGN', symbol: '\u20A6', name: 'Nigerian Naira' },
  { code: 'KES', symbol: 'KSh', name: 'Kenyan Shilling' },
];

const THEME_COLORS = [
  { name: 'Teal', value: '#14B8A6', gradient: 'from-teal-500 to-emerald-500' },
  { name: 'Blue', value: '#3B82F6', gradient: 'from-blue-500 to-indigo-500' },
  { name: 'Violet', value: '#8B5CF6', gradient: 'from-violet-500 to-purple-500' },
  { name: 'Rose', value: '#F43F5E', gradient: 'from-rose-500 to-pink-500' },
  { name: 'Amber', value: '#F59E0B', gradient: 'from-amber-500 to-orange-500' },
  { name: 'Emerald', value: '#10B981', gradient: 'from-emerald-500 to-green-500' },
];

const WIZARD_STEPS = [
  { label: 'Welcome', icon: Sparkles },
  { label: 'Data Connection', icon: Database },
  { label: 'Organization', icon: Building2 },
  { label: 'First Project', icon: FolderPlus },
];

function StepIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div className="flex items-center gap-0 w-full max-w-md mx-auto">
      {Array.from({ length: total }, (_, i) => {
        const isComplete = i < current;
        const isActive = i === current;
        const StepIcon = WIZARD_STEPS[i].icon;
        return (
          <div key={i} className="flex items-center" style={{ flex: i < total - 1 ? 1 : 'none' }}>
            <div className="relative flex flex-col items-center">
              <motion.div
                animate={{
                  scale: isActive ? 1.1 : 1,
                  boxShadow: isActive ? `0 0 24px color-mix(in srgb, var(--color-brand) 40%, transparent)` : '0 0 0px transparent',
                }}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 ${
                  isComplete
                    ? 'gradient-brand text-white'
                    : isActive
                    ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-slate-100 ring-2 ring-brand/50'
                    : 'bg-slate-100 dark:bg-white/[0.06] text-slate-400 dark:text-white/30 border border-slate-200 dark:border-white/[0.08]'
                }`}
              >
                {isComplete ? <CheckCircle2 size={18} /> : <StepIcon size={18} />}
              </motion.div>
              <span className={`text-[11px] mt-1.5 font-semibold ${
                isComplete ? 'text-brand' : isActive ? 'text-slate-800 dark:text-white' : 'text-slate-500 dark:text-slate-300 dark:text-white/25'
              }`}>
                {WIZARD_STEPS[i].label}
              </span>
            </div>
            {i < total - 1 && (
              <div className={`flex-1 h-[2px] mx-3 rounded-full transition-colors duration-500 ${
                isComplete ? 'bg-gradient-to-r from-brand/60 to-brand/30' : 'bg-slate-200 dark:bg-white/[0.06]'
              }`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function TableStatusRow({ name, exists, rowCount }: { name: string; exists: boolean; rowCount: number }) {
  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${
      exists ? 'bg-emerald-500/[0.08] border border-emerald-500/20' : 'bg-red-500/[0.06] border border-red-500/15'
    }`}>
      {exists ? (
        <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
      ) : (
        <XCircle size={16} className="text-red-400 flex-shrink-0" />
      )}
      <span className="text-sm font-mono text-slate-700 dark:text-slate-200 flex-1">{name}</span>
      {exists ? (
        <span className="text-xs text-emerald-400/80 font-medium">{rowCount.toLocaleString()} rows</span>
      ) : (
        <span className="text-xs text-red-400/70 font-medium">Not found</span>
      )}
    </div>
  );
}

export default function SetupWizard({ onComplete }: SetupWizardProps) {
  const [step, setStep] = useState(0);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [loading, setLoading] = useState(true);

  // Step 2 state: Data Connection
  const [connectionStatus, setConnectionStatus] = useState<any>(null);
  const [tableValidation, setTableValidation] = useState<any>(null);
  const [checkingConnection, setCheckingConnection] = useState(false);
  const [checkingTables, setCheckingTables] = useState(false);
  const [seedingData, setSeedingData] = useState(false);

  // Step 3 state: Organization
  const [orgName, setOrgName] = useState('');
  const [currencyCode, setCurrencyCode] = useState('USD');
  const [reportingFreq, setReportingFreq] = useState<'quarterly' | 'monthly'>('quarterly');
  const [themeColor, setThemeColor] = useState('#14B8A6');
  const [savingOrg, setSavingOrg] = useState(false);

  // Step 4 state: First Project
  const [projectId, setProjectId] = useState('');
  const [projectName, setProjectName] = useState('');
  const [reportingDate, setReportingDate] = useState('');
  const [projectDesc, setProjectDesc] = useState('');
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectCreated, setProjectCreated] = useState(false);

  const loadStatus = useCallback(async () => {
    try {
      const status = await api.setupStatus();
      setSetupStatus(status);
    } catch {
      // Wizard will still show with defaults
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
    generateProjectDefaults();
  }, [loadStatus]);

  // Restore saved step from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('ecl_setup_step');
    if (saved) {
      const parsed = parseInt(saved, 10);
      if (!isNaN(parsed) && parsed >= 0 && parsed <= 3) setStep(parsed);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('ecl_setup_step', String(step));
  }, [step]);

  function generateProjectDefaults() {
    const now = new Date();
    const quarter = Math.ceil((now.getMonth() + 1) / 3);
    const year = now.getFullYear();
    const defaultId = `Q${quarter}-${year}-IFRS9`;
    const lastDayOfQuarter = new Date(year, quarter * 3, 0);
    const dateStr = lastDayOfQuarter.toISOString().split('T')[0];

    setProjectId(defaultId);
    setProjectName(`IFRS 9 ECL — Q${quarter} ${year}`);
    setReportingDate(dateStr);
    setProjectDesc(`Quarterly IFRS 9 expected credit loss calculation for Q${quarter} ${year}.`);
  }

  async function checkConnection() {
    setCheckingConnection(true);
    try {
      const health = await api.healthCheck();
      const conn = await api.adminTestConnection();
      setConnectionStatus({ ...health, ...conn });
    } catch (e: any) {
      setConnectionStatus({ connected: false, error: e.message });
    } finally {
      setCheckingConnection(false);
    }
  }

  async function checkTables() {
    setCheckingTables(true);
    try {
      const result = await api.setupValidateTables();
      setTableValidation(result);
    } catch (e: any) {
      setTableValidation({ error: e.message });
    } finally {
      setCheckingTables(false);
    }
  }

  async function seedSampleData() {
    setSeedingData(true);
    try {
      await api.setupSeedSampleData();
      await checkTables();
    } catch {
      // Error handled via table check
    } finally {
      setSeedingData(false);
    }
  }

  async function saveOrganization() {
    setSavingOrg(true);
    try {
      const currency = CURRENCIES.find(c => c.code === currencyCode);
      await api.adminSaveConfig({
        app_settings: {
          organization_name: orgName,
          currency_code: currencyCode,
          currency_symbol: currency?.symbol || '$',
          reporting_frequency: reportingFreq,
          theme_color: themeColor,
        },
      });
      setStep(3);
    } catch {
      // Proceed anyway
      setStep(3);
    } finally {
      setSavingOrg(false);
    }
  }

  async function createFirstProject() {
    setCreatingProject(true);
    try {
      await api.createProject({
        project_id: projectId,
        project_name: projectName,
        project_type: 'ifrs9',
        description: projectDesc,
        reporting_date: reportingDate,
      });
      setProjectCreated(true);
    } catch {
      // Still allow completion
    } finally {
      setCreatingProject(false);
    }
  }

  async function finishSetup() {
    try {
      await api.setupComplete();
    } catch {
      // Complete anyway
    }
    localStorage.removeItem('ecl_setup_step');
    onComplete();
  }

  function skipSetup() {
    localStorage.removeItem('ecl_setup_step');
    api.setupComplete().catch(() => {});
    onComplete();
  }

  if (loading) {
    return (
      <div className="fixed inset-0 z-[200] bg-slate-50/95 dark:bg-[#0B0F1A]/95 backdrop-blur-xl flex items-center justify-center">
        <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center">
          <div className="w-16 h-16 rounded-2xl gradient-brand flex items-center justify-center mx-auto mb-4 animate-pulse">
            <Zap size={28} className="text-white" />
          </div>
          <p className="text-slate-400 dark:text-white/50 text-sm font-medium">Checking setup status...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-[200] bg-slate-50/95 dark:bg-[#0B0F1A]/95 backdrop-blur-xl overflow-y-auto">
      {/* Background orbs */}
      <div className="fixed top-0 left-1/4 w-[600px] h-[600px] rounded-full blur-[120px] pointer-events-none" style={{ background: `color-mix(in srgb, var(--color-brand) 3%, transparent)` }} />
      <div className="fixed bottom-0 right-1/4 w-[500px] h-[500px] rounded-full bg-blue-500/[0.04] blur-[100px] pointer-events-none" />

      <div className="relative z-10 min-h-screen flex flex-col">
        {/* Header */}
        <div className="pt-8 pb-6 px-6">
          <div className="max-w-3xl mx-auto">
            <StepIndicator current={step} total={4} />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex items-start justify-center px-6 pb-12">
          <div className="w-full max-w-4xl">
            <AnimatePresence mode="wait">
              {step === 0 && (
                <WelcomeStep
                  key="welcome"
                  setupStatus={setupStatus}
                  onNext={() => { setStep(1); checkConnection(); checkTables(); }}
                />
              )}
              {step === 1 && (
                <DataConnectionStep
                  key="data"
                  connectionStatus={connectionStatus}
                  tableValidation={tableValidation}
                  checkingConnection={checkingConnection}
                  checkingTables={checkingTables}
                  seedingData={seedingData}
                  onCheckConnection={checkConnection}
                  onCheckTables={checkTables}
                  onSeedData={seedSampleData}
                  onNext={() => setStep(2)}
                  onBack={() => setStep(0)}
                />
              )}
              {step === 2 && (
                <OrganizationStep
                  key="org"
                  orgName={orgName}
                  setOrgName={setOrgName}
                  currencyCode={currencyCode}
                  setCurrencyCode={setCurrencyCode}
                  reportingFreq={reportingFreq}
                  setReportingFreq={setReportingFreq}
                  themeColor={themeColor}
                  setThemeColor={setThemeColor}
                  saving={savingOrg}
                  onSave={saveOrganization}
                  onBack={() => setStep(1)}
                />
              )}
              {step === 3 && (
                <FirstProjectStep
                  key="project"
                  projectId={projectId}
                  setProjectId={setProjectId}
                  projectName={projectName}
                  setProjectName={setProjectName}
                  reportingDate={reportingDate}
                  setReportingDate={setReportingDate}
                  projectDesc={projectDesc}
                  setProjectDesc={setProjectDesc}
                  creating={creatingProject}
                  created={projectCreated}
                  onCreate={createFirstProject}
                  onFinish={finishSetup}
                  onBack={() => setStep(2)}
                />
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Skip link */}
        <div className="pb-6 text-center">
          <button onClick={skipSetup} className="text-xs text-slate-400 dark:text-white/20 hover:text-slate-500 dark:hover:text-slate-300 transition font-medium">
            Skip Setup — I'll configure manually
          </button>
        </div>
      </div>
    </div>
  );
}


/* ─── Step 0: Welcome ────────────────────────────────────────────────────── */

function WelcomeStep({
  setupStatus,
  onNext,
}: {
  setupStatus: SetupStatus | null;
  onNext: () => void;
}) {
  const prerequisites = [
    { label: 'Databricks workspace access', hint: 'Active workspace with Unity Catalog enabled', icon: Globe },
    { label: 'Lakebase database provisioned', hint: 'PostgreSQL-compatible database in your workspace', icon: Server },
    { label: 'Unity Catalog tables with loan data', hint: 'loan_tape, borrower_master, payment_history, etc.', icon: Table2 },
    { label: 'Databricks Jobs configured', hint: 'Optional — for automated pipeline execution', icon: Calendar, optional: true },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="grid grid-cols-1 lg:grid-cols-2 gap-8"
    >
      {/* Left panel — illustration */}
      <div className="flex flex-col justify-center">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.4 }}
          className="relative mb-8"
        >
          <div className="w-24 h-24 rounded-3xl gradient-brand flex items-center justify-center shadow-2xl mx-auto lg:mx-0">
            <Zap size={48} strokeWidth={2} className="text-white drop-shadow-lg" />
          </div>
          <div className="absolute -inset-4 rounded-3xl bg-brand/10 blur-2xl -z-10" />
        </motion.div>
        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-3 text-center lg:text-left">
          Welcome to IFRS 9<br />ECL Workspace
        </h1>
        <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed max-w-md text-center lg:text-left">
          Set up your forward-looking credit loss management platform in minutes.
          This wizard will guide you through connecting your data, configuring your
          organization, and creating your first ECL project.
        </p>
        <div className="mt-6 flex items-center gap-3 text-center lg:text-left justify-center lg:justify-start">
          <a
            href="https://docs.databricks.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand/70 hover:text-brand transition font-medium flex items-center gap-1"
          >
            <ExternalLink size={12} /> Documentation
          </a>
        </div>
      </div>

      {/* Right panel — prerequisites */}
      <div className="bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] rounded-3xl p-8">
        <h2 className="text-lg font-bold text-slate-900 dark:text-white mb-1">Prerequisites</h2>
        <p className="text-xs text-slate-400 dark:text-white/30 mb-6">Ensure these are ready before proceeding</p>

        <div className="space-y-3">
          {prerequisites.map((p, i) => {
            const Icon = p.icon;
            return (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.15 + i * 0.08 }}
                className="flex items-start gap-3 p-3 rounded-xl bg-slate-50 dark:bg-white/[0.02] border border-slate-100 dark:border-white/[0.04] hover:border-slate-300 dark:hover:border-white/[0.08] transition"
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  p.optional ? 'bg-amber-500/10 text-amber-400/60' : 'bg-brand/10 text-brand/60'
                }`}>
                  <Icon size={16} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                    {p.label}
                    {p.optional && <span className="text-[11px] text-amber-400/60 ml-2 font-medium">(optional)</span>}
                  </p>
                  <p className="text-xs text-slate-400 dark:text-white/30 mt-0.5">{p.hint}</p>
                </div>
              </motion.div>
            );
          })}
        </div>

        {setupStatus && (
          <div className="mt-6 p-3 rounded-xl bg-gray-50 dark:bg-white/[0.02] border border-gray-200 dark:border-white/[0.04]">
            <p className="text-[11px] text-slate-500 dark:text-slate-300 dark:text-white/30 uppercase tracking-wider font-bold mb-2">Current Status</p>
            <div className="grid grid-cols-2 gap-2">
              {Object.entries(setupStatus.steps).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2">
                  {val.complete ? (
                    <CheckCircle2 size={12} className="text-emerald-400" />
                  ) : (
                    <XCircle size={12} className="text-slate-300 dark:text-white/20" />
                  )}
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 capitalize">{key.replace(/_/g, ' ')}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={onNext}
          className="mt-8 w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl gradient-brand text-white font-bold text-sm shadow-lg hover:opacity-80 transition"
        >
          Get Started <ArrowRight size={16} />
        </motion.button>
      </div>
    </motion.div>
  );
}


/* ─── Step 1: Data Connection & Mapping ──────────────────────────────────── */

function DataConnectionStep({
  connectionStatus,
  tableValidation,
  checkingConnection,
  checkingTables,
  seedingData,
  onCheckConnection,
  onCheckTables,
  onSeedData,
  onNext,
  onBack,
}: {
  connectionStatus: any;
  tableValidation: any;
  checkingConnection: boolean;
  checkingTables: boolean;
  seedingData: boolean;
  onCheckConnection: () => void;
  onCheckTables: () => void;
  onSeedData: () => void;
  onNext: () => void;
  onBack: () => void;
}) {
  const isConnected = connectionStatus?.connected || connectionStatus?.lakebase === 'connected';
  const inputTables = tableValidation?.input_tables || [];
  const allInputPresent = tableValidation?.all_input_present;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="grid grid-cols-1 lg:grid-cols-5 gap-8"
    >
      {/* Left description */}
      <div className="lg:col-span-2 flex flex-col justify-center">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500 flex items-center justify-center mb-6">
          <Database size={28} className="text-white" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">Data Connection</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
          Verify your Lakebase connection and check that the required input tables
          are present in your schema. If you're evaluating the platform, you can
          load sample data for a demo.
        </p>
        <div className="mt-6 space-y-2">
          <div className="flex items-center gap-2 text-xs text-slate-400 dark:text-white/30">
            <Shield size={12} /> <span>Connection uses auto-injected credentials</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400 dark:text-white/30">
            <Table2 size={12} /> <span>5 input tables + 5 processed tables</span>
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="lg:col-span-3 space-y-5">
        {/* Connection Status */}
        <div className="bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Lakebase Connection</h3>
            <button
              onClick={onCheckConnection}
              disabled={checkingConnection}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-white/[0.06] text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-gray-200 dark:hover:bg-white/[0.1] transition disabled:opacity-40"
            >
              {checkingConnection ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
              Test
            </button>
          </div>
          {connectionStatus ? (
            <div className={`flex items-center gap-3 px-4 py-3 rounded-xl ${
              isConnected ? 'bg-emerald-500/[0.08] border border-emerald-500/20' : 'bg-red-500/[0.06] border border-red-500/15'
            }`}>
              {isConnected ? (
                <CheckCircle2 size={18} className="text-emerald-400" />
              ) : (
                <XCircle size={18} className="text-red-400" />
              )}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">
                  {isConnected ? 'Connected' : 'Connection Failed'}
                </p>
                <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
                  {isConnected
                    ? `Schema: ${connectionStatus.schema || 'expected_credit_loss'}`
                    : connectionStatus.error || 'Unable to connect'}
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gray-50 dark:bg-white/[0.02] border border-gray-200 dark:border-white/[0.04]">
              {checkingConnection ? (
                <Loader2 size={18} className="text-brand animate-spin" />
              ) : (
                <Database size={18} className="text-slate-300 dark:text-white/20" />
              )}
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {checkingConnection ? 'Testing connection...' : 'Click Test to verify connection'}
              </p>
            </div>
          )}
        </div>

        {/* Table Validation */}
        <div className="bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Required Tables</h3>
              {tableValidation && !tableValidation.error && (
                <p className="text-xs text-slate-400 dark:text-white/30 mt-0.5">
                  {tableValidation.input_found}/{tableValidation.input_total} input tables found
                </p>
              )}
            </div>
            <button
              onClick={onCheckTables}
              disabled={checkingTables}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-white/[0.06] text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-gray-200 dark:hover:bg-white/[0.1] transition disabled:opacity-40"
            >
              {checkingTables ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
              Auto-detect
            </button>
          </div>

          {tableValidation && !tableValidation.error ? (
            <div className="space-y-2">
              {inputTables.map((t: any) => (
                <TableStatusRow key={t.table} name={t.prefixed_name} exists={t.exists} rowCount={t.row_count} />
              ))}
            </div>
          ) : checkingTables ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={20} className="text-brand animate-spin" />
              <span className="ml-2 text-sm text-slate-500 dark:text-slate-400">Scanning tables...</span>
            </div>
          ) : (
            <div className="text-center py-6 text-slate-400 dark:text-white/30 text-sm">
              Click Auto-detect to scan your schema
            </div>
          )}

          {/* Seed sample data option */}
          {tableValidation && !allInputPresent && (
            <div className="mt-4 p-4 rounded-xl bg-amber-500/[0.06] border border-amber-500/15">
              <p className="text-xs text-amber-300/80 font-semibold mb-2">Missing tables detected</p>
              <p className="text-xs text-slate-500 dark:text-slate-400 mb-3">
                Load sample data to explore the platform with realistic demo data (84K+ loans).
              </p>
              <button
                onClick={onSeedData}
                disabled={seedingData}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500/20 text-amber-300 text-xs font-bold hover:bg-amber-500/30 transition disabled:opacity-40"
              >
                {seedingData ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
                {seedingData ? 'Seeding data...' : 'Load Sample Data'}
              </button>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-2">
          <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-slate-400 dark:text-white/40 hover:text-slate-600 dark:hover:text-slate-300 transition font-medium">
            <ChevronLeft size={16} /> Back
          </button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onNext}
            disabled={!isConnected}
            className="flex items-center gap-2 px-6 py-3 rounded-2xl gradient-brand text-white font-bold text-sm shadow-lg disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition"
          >
            Continue <ChevronRight size={16} />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}


/* ─── Step 2: Organization Setup ─────────────────────────────────────────── */

function OrganizationStep({
  orgName, setOrgName,
  currencyCode, setCurrencyCode,
  reportingFreq, setReportingFreq,
  themeColor, setThemeColor,
  saving,
  onSave,
  onBack,
}: {
  orgName: string; setOrgName: (v: string) => void;
  currencyCode: string; setCurrencyCode: (v: string) => void;
  reportingFreq: 'quarterly' | 'monthly'; setReportingFreq: (v: 'quarterly' | 'monthly') => void;
  themeColor: string; setThemeColor: (v: string) => void;
  saving: boolean;
  onSave: () => void;
  onBack: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="grid grid-cols-1 lg:grid-cols-5 gap-8"
    >
      {/* Left description */}
      <div className="lg:col-span-2 flex flex-col justify-center">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-500 flex items-center justify-center mb-6">
          <Building2 size={28} className="text-white" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">Organization</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
          Configure your institution's identity. This information appears on
          regulatory reports, dashboards, and sign-off documents.
        </p>
      </div>

      {/* Right form */}
      <div className="lg:col-span-3 space-y-5">
        <div className="bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] rounded-2xl p-6 space-y-5">
          {/* Organization Name */}
          <div>
            <label htmlFor="setup-org-name" className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">
              <Building2 size={12} className="inline mr-1.5 -mt-0.5" aria-hidden="true" />
              Organization Name
            </label>
            <input
              id="setup-org-name"
              type="text"
              value={orgName}
              onChange={e => setOrgName(e.target.value)}
              placeholder="e.g. Horizon Bank, Acme Financial"
              className="w-full px-4 py-3 rounded-xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-white/20 focus:outline-none focus:border-brand/40 focus:ring-1 focus:ring-brand/20 transition"
            />
          </div>

          {/* Currency */}
          <div>
            <label htmlFor="setup-currency" className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">
              <DollarSign size={12} className="inline mr-1.5 -mt-0.5" aria-hidden="true" />
              Reporting Currency
            </label>
            <select
              id="setup-currency"
              value={currencyCode}
              onChange={e => setCurrencyCode(e.target.value)}
              className="w-full px-4 py-3 rounded-xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white text-sm focus:outline-none focus:border-brand/40 focus:ring-1 focus:ring-brand/20 transition appearance-none"
            >
              {CURRENCIES.map(c => (
                <option key={c.code} value={c.code} className="bg-white dark:bg-slate-900 text-slate-800 dark:text-white">
                  {c.symbol} — {c.name} ({c.code})
                </option>
              ))}
            </select>
          </div>

          {/* Reporting Frequency */}
          <div>
            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2" id="setup-freq-label">
              <Calendar size={12} className="inline mr-1.5 -mt-0.5" aria-hidden="true" />
              Reporting Frequency
            </label>
            <div className="flex gap-3">
              {(['quarterly', 'monthly'] as const).map(freq => (
                <button
                  key={freq}
                  onClick={() => setReportingFreq(freq)}
                  className={`flex-1 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                    reportingFreq === freq
                      ? 'bg-brand/20 border border-brand/30 text-brand'
                      : 'bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] text-slate-400 dark:text-white/40 hover:text-slate-600 dark:hover:text-slate-300 hover:border-gray-300 dark:hover:border-white/[0.1]'
                  }`}
                >
                  {freq.charAt(0).toUpperCase() + freq.slice(1)}
                </button>
              ))}
            </div>
          </div>

          {/* Theme Color */}
          <div>
            <label className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2" id="setup-color-label">
              <Palette size={12} className="inline mr-1.5 -mt-0.5" aria-hidden="true" />
              Brand Color
            </label>
            <div className="flex gap-3 flex-wrap">
              {THEME_COLORS.map(c => (
                <button
                  key={c.value}
                  onClick={() => setThemeColor(c.value)}
                  className={`w-10 h-10 rounded-xl bg-gradient-to-br ${c.gradient} transition-all focus-visible:ring-2 focus-visible:ring-white ${
                    themeColor === c.value ? 'ring-2 ring-white/40 scale-110 shadow-lg' : 'opacity-60 hover:opacity-80'
                  }`}
                  aria-label={`${c.name} theme color`}
                  aria-pressed={themeColor === c.value}
                  title={c.name}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between pt-2">
          <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-slate-400 dark:text-white/40 hover:text-slate-600 dark:hover:text-slate-300 transition font-medium">
            <ChevronLeft size={16} /> Back
          </button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={onSave}
            disabled={saving || !orgName.trim()}
            className="flex items-center gap-2 px-6 py-3 rounded-2xl gradient-brand text-white font-bold text-sm shadow-lg disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : null}
            Save & Continue <ChevronRight size={16} />
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}


/* ─── Step 3: First Project ──────────────────────────────────────────────── */

function FirstProjectStep({
  projectId, setProjectId,
  projectName, setProjectName,
  reportingDate, setReportingDate,
  projectDesc, setProjectDesc,
  creating,
  created,
  onCreate,
  onFinish,
  onBack,
}: {
  projectId: string; setProjectId: (v: string) => void;
  projectName: string; setProjectName: (v: string) => void;
  reportingDate: string; setReportingDate: (v: string) => void;
  projectDesc: string; setProjectDesc: (v: string) => void;
  creating: boolean;
  created: boolean;
  onCreate: () => void;
  onFinish: () => void;
  onBack: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className="grid grid-cols-1 lg:grid-cols-5 gap-8"
    >
      {/* Left description */}
      <div className="lg:col-span-2 flex flex-col justify-center">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center mb-6">
          <FolderPlus size={28} className="text-white" />
        </div>
        <h2 className="text-2xl font-extrabold text-slate-900 dark:text-white mb-2">First Project</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed">
          Create your first ECL project. Each project represents one reporting
          period and tracks the full workflow from data processing through sign-off.
        </p>
        <div className="mt-4 p-3 rounded-xl bg-gray-50 dark:bg-white/[0.02] border border-gray-200 dark:border-white/[0.04]">
          <p className="text-[11px] text-slate-500 dark:text-slate-300 dark:text-white/30 uppercase tracking-wider font-bold mb-1">Workflow Steps</p>
          <div className="space-y-1">
            {['Data Processing', 'Data Control', 'Satellite Model', 'Monte Carlo', 'Stress Testing', 'Overlays', 'Sign Off'].map((s, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-slate-400 dark:text-white/30">
                <div className="w-4 h-4 rounded bg-slate-100 dark:bg-white/[0.04] flex items-center justify-center text-[9px] font-bold text-slate-400 dark:text-white/20">{i + 1}</div>
                {s}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right form */}
      <div className="lg:col-span-3 space-y-5">
        {!created ? (
          <div className="bg-gray-50 dark:bg-white/[0.03] border border-gray-200 dark:border-white/[0.06] rounded-2xl p-6 space-y-5">
            <div>
              <label htmlFor="setup-project-id" className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">Project ID</label>
              <input
                id="setup-project-id"
                type="text"
                value={projectId}
                onChange={e => setProjectId(e.target.value)}
                placeholder="e.g. Q1-2026-IFRS9"
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white text-sm font-mono placeholder:text-slate-400 dark:placeholder:text-white/20 focus:outline-none focus:border-brand/40 focus:ring-1 focus:ring-brand/20 transition"
              />
            </div>

            <div>
              <label htmlFor="setup-project-name" className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">Project Name</label>
              <input
                id="setup-project-name"
                type="text"
                value={projectName}
                onChange={e => setProjectName(e.target.value)}
                placeholder="e.g. IFRS 9 ECL — Q1 2026"
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-white/20 focus:outline-none focus:border-brand/40 focus:ring-1 focus:ring-brand/20 transition"
              />
            </div>

            <div>
              <label htmlFor="setup-reporting-date" className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">Reporting Date</label>
              <input
                id="setup-reporting-date"
                type="date"
                value={reportingDate}
                onChange={e => setReportingDate(e.target.value)}
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white text-sm focus:outline-none focus:border-brand/40 focus:ring-1 focus:ring-brand/20 transition dark:[color-scheme:dark]"
              />
            </div>

            <div>
              <label htmlFor="setup-project-desc" className="block text-xs font-bold text-slate-500 dark:text-slate-400 mb-2">Description</label>
              <textarea
                id="setup-project-desc"
                value={projectDesc}
                onChange={e => setProjectDesc(e.target.value)}
                rows={2}
                placeholder="Brief description of this ECL reporting period..."
                className="w-full px-4 py-3 rounded-xl bg-white dark:bg-white/[0.04] border border-slate-200 dark:border-white/[0.08] text-slate-800 dark:text-white text-sm placeholder:text-slate-400 dark:placeholder:text-white/20 focus:outline-none focus:border-brand/40 focus:ring-1 focus:ring-brand/20 transition resize-none"
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onCreate}
              disabled={creating || !projectId.trim() || !projectName.trim()}
              className="w-full flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl gradient-brand text-white font-bold text-sm shadow-lg disabled:opacity-30 disabled:cursor-not-allowed hover:opacity-80 transition"
            >
              {creating ? <Loader2 size={16} className="animate-spin" /> : <FolderPlus size={16} />}
              {creating ? 'Creating...' : 'Create Project'}
            </motion.button>
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-gray-50 dark:bg-white/[0.03] border border-emerald-500/20 rounded-2xl p-8 text-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.1 }}
              className="w-20 h-20 rounded-3xl gradient-brand flex items-center justify-center mx-auto mb-5 shadow-xl"
            >
              <CheckCircle2 size={40} className="text-white" />
            </motion.div>
            <h3 className="text-xl font-extrabold text-slate-900 dark:text-white mb-2">Project Created!</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-1 font-mono">{projectId}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">{projectName}</p>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onFinish}
              className="inline-flex items-center gap-2 px-8 py-4 rounded-2xl gradient-brand text-white font-bold text-sm shadow-xl hover:opacity-80 transition"
            >
              <Sparkles size={18} /> Launch Workspace
            </motion.button>
          </motion.div>
        )}

        {/* Navigation */}
        {!created && (
          <div className="flex items-center justify-between pt-2">
            <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-slate-400 dark:text-white/40 hover:text-slate-600 dark:hover:text-slate-300 transition font-medium">
              <ChevronLeft size={16} /> Back
            </button>
            <button onClick={onFinish} className="text-xs text-slate-300 dark:text-white/20 hover:text-slate-500 dark:hover:text-slate-300 transition font-medium">
              Skip — I'll create a project later
            </button>
          </div>
        )}
      </div>
    </motion.div>
  );
}
