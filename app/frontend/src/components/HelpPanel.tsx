import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle, X, BookOpen, ExternalLink, ChevronRight } from 'lucide-react';
import { config } from '../lib/config';

interface HelpLink {
  label: string;
  url: string;
}

interface HelpSection {
  title: string;
  content: string;
  links?: HelpLink[];
}

const PAGE_HELP: Record<string, { title: string; sections: HelpSection[] }> = {
  create_project: {
    title: 'Create Project',
    sections: [
      { title: 'What is an ECL Project?', content: 'An ECL project represents a single reporting-period calculation of Expected Credit Losses under IFRS 9. Each project tracks the full 8-step workflow from data ingestion to sign-off.' },
      { title: 'Key Fields', content: 'Project ID: Unique identifier (e.g., ECL-2025Q4). Reporting Date: The balance sheet date. Project Type: IFRS 9 or Basel III.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 9.5.5.1, an entity shall recognise a loss allowance for expected credit losses on financial assets measured at amortised cost.', links: [{ label: 'IFRS 9 Standard', url: 'https://www.ifrs.org/issued-standards/list-of-standards/ifrs-9-financial-instruments/' }] },
    ],
  },
  data_processing: {
    title: 'Data Processing',
    sections: [
      { title: 'Purpose', content: 'Review your loan portfolio data quality, completeness, and distribution before ECL calculation. Verify data loaded from the core banking system matches expectations.' },
      { title: 'What to Check', content: 'Total loan count and GCA match source system. Stage distribution is reasonable. Days past due (DPD) averages are within expected ranges.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 9.B5.5.49-51, the entity shall use reasonable and supportable information that is available without undue cost or effort, including historical, current and forward-looking information.' },
    ],
  },
  data_control: {
    title: 'Data Control',
    sections: [
      { title: 'Purpose', content: 'Validate data quality checks and GL reconciliation. Ensure data integrity before modeling begins.' },
      { title: 'Key Checks', content: `GL Reconciliation: Loan tape balance vs General Ledger (tolerance ±${config.governance.glReconciliationTolerancePct}%). DQ Score: Automated validation checks must pass ≥${config.governance.dqScoreThresholdPct}%. Critical failures must be zero.` },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 7.35I, an entity shall provide a reconciliation from the opening balance to the closing balance of the loss allowance.', links: [{ label: 'IFRS 7 Disclosure Requirements', url: 'https://www.ifrs.org/issued-standards/list-of-standards/ifrs-7-financial-instruments-disclosures/' }] },
    ],
  },
  satellite_model: {
    title: 'Satellite Model',
    sections: [
      { title: 'Purpose', content: 'Select and calibrate macroeconomic satellite models that link economic scenarios to credit risk parameters (PD, LGD).' },
      { title: 'Model Selection', content: 'Up to 8 model types are evaluated per product-cohort. Best model is auto-selected by lowest AIC (parametric) or CV-RMSE (tree-based). Review R², RMSE, and coefficients.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 9.5.5.17, an entity shall measure expected credit losses in a way that reflects an unbiased and probability-weighted amount determined by evaluating a range of possible outcomes.' },
    ],
  },
  model_execution: {
    title: 'Monte Carlo Execution',
    sections: [
      { title: 'Purpose', content: 'Run the ECL calculation engine with Monte Carlo simulation across multiple scenarios. Review probability-weighted ECL results.' },
      { title: 'Key Metrics', content: 'Total ECL: Probability-weighted across all scenarios. Coverage Ratio: ECL/GCA should be 1-8% for a typical portfolio. Stage distribution should align with credit quality.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 9.5.5.17, the estimate of expected credit losses shall reflect the time value of money and reasonable and supportable information about past events, current conditions and forecasts of future economic conditions.' },
    ],
  },
  stress_testing: {
    title: 'Stress Testing',
    sections: [
      { title: 'Purpose', content: 'Analyze ECL sensitivity to stress scenarios and parameter changes. Assess tail risk and capital adequacy under adverse conditions.' },
      { title: 'Analysis Types', content: 'Monte Carlo: Stochastic simulation with PD/LGD volatility. Sensitivity: Parameter shock analysis. Vintage: Historical cohort performance. Concentration: Product×Stage heatmap. Migration: Stage transfer simulation.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 9.B5.5.42, an entity shall consider multiple forward-looking scenarios. Stress testing validates the robustness of ECL estimates under extreme but plausible conditions.' },
    ],
  },
  overlays: {
    title: 'Management Overlays',
    sections: [
      { title: 'Purpose', content: 'Apply management overlays — post-model adjustments for risks not captured by the statistical model. Each overlay must be individually justified and approved.' },
      { title: 'Governance', content: 'Overlay cap: ≤15% of model ECL. Temporary overlays expire within 2 quarters. Permanent overlays trigger model redevelopment review. Maker-checker approval required.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 9.B5.5.17, management adjustments are permitted when model outputs do not fully capture all relevant risk factors. Overlays must be reasonable, supportable, and documented.' },
    ],
  },
  sign_off: {
    title: 'Sign-Off',
    sections: [
      { title: 'Purpose', content: 'Review final ECL, attribution waterfall, and sign off for regulatory reporting. Once signed, the project is permanently locked.' },
      { title: 'Attestation', content: 'The sign-off confirms: ECL methodology is IFRS 9 compliant, all overlays are justified, stress testing has been reviewed, and data quality checks have passed.' },
      { title: 'IFRS 9 Reference', content: 'Per IFRS 7.35F-35N, an entity shall disclose information about its credit risk management practices and how they relate to the recognition and measurement of expected credit losses.', links: [{ label: 'IFRS 7 Disclosure', url: 'https://www.ifrs.org/issued-standards/list-of-standards/ifrs-7-financial-instruments-disclosures/' }] },
    ],
  },
};

const STEP_KEYS = [
  'create_project', 'data_processing', 'data_control', 'satellite_model',
  'model_execution', 'stress_testing', 'overlays', 'sign_off',
];

export default function HelpPanel({ activeStep }: { activeStep: number }) {
  const [open, setOpen] = useState(false);
  const stepKey = STEP_KEYS[activeStep] || 'create_project';
  const help = PAGE_HELP[stepKey];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '?' && !e.ctrlKey && !e.metaKey && !(e.target instanceof HTMLInputElement) && !(e.target instanceof HTMLTextAreaElement)) {
        setOpen(prev => !prev);
      }
      if (e.key === 'Escape' && open) setOpen(false);
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open]);

  if (!help) return null;

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 w-12 h-12 rounded-full gradient-brand text-white shadow-xl hover:shadow-2xl hover:scale-105 transition-all flex items-center justify-center glow-brand"
        aria-label="Open help panel"
      >
        <HelpCircle size={22} />
      </button>

      <AnimatePresence>
        {open && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/30 backdrop-blur-sm"
              onClick={() => setOpen(false)}
            />
            <motion.div
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="fixed top-0 right-0 bottom-0 z-50 w-[380px] max-w-[90vw] bg-white dark:bg-slate-800 shadow-2xl border-l border-slate-200 dark:border-slate-700 flex flex-col"
            >
              <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg gradient-brand flex items-center justify-center">
                    <BookOpen size={16} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-800 dark:text-slate-100">{help.title}</h3>
                    <p className="text-[10px] text-slate-400">Step {activeStep + 1} of 8</p>
                  </div>
                </div>
                <button
                  onClick={() => setOpen(false)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 dark:hover:text-slate-300 transition"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-5 space-y-5">
                {help.sections.map((section, i) => (
                  <div key={i}>
                    <h4 className="text-xs font-bold text-slate-700 dark:text-slate-200 mb-1.5 flex items-center gap-1.5">
                      <ChevronRight size={12} className="text-brand" />
                      {section.title}
                    </h4>
                    <p className="text-xs text-slate-500 leading-relaxed">{section.content}</p>
                    {section.links && section.links.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {section.links.map((link, j) => (
                          <a
                            key={j}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-brand hover:underline"
                          >
                            <ExternalLink size={10} /> {link.label}
                          </a>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <div className="border-t border-slate-100 dark:border-slate-700 px-5 py-3">
                <p className="text-[10px] text-slate-400 text-center">
                  Press <kbd className="px-1.5 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-[10px] font-mono">?</kbd> to toggle help
                </p>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
