import { Lock, ArrowLeft, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

const STEP_NAMES = ['Create Project', 'Data Processing', 'Data Control', 'Satellite Model', 'Monte Carlo', 'Stress Testing', 'Overlays', 'Sign Off'];

interface Props {
  requiredStep?: number;
  onNavigate?: (step: number) => void;
}

export default function LockedBanner({ requiredStep, onNavigate }: Props) {
  const prevStep = requiredStep != null && requiredStep > 0 ? requiredStep - 1 : null;
  const prevName = prevStep != null ? STEP_NAMES[prevStep] : null;

  const handleNav = () => {
    if (prevStep == null) return;
    if (onNavigate) {
      onNavigate(prevStep);
    } else {
      window.dispatchEvent(new CustomEvent('ecl-navigate-step', { detail: { step: prevStep } }));
    }
  };

  return (
    <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-24">
      <div className="relative">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-50 dark:from-slate-800 dark:to-slate-900 flex items-center justify-center shadow-sm border border-slate-200 dark:border-slate-700">
          <Lock size={32} strokeWidth={1.5} className="text-slate-300" />
        </div>
        <div className="absolute -bottom-1 -right-1 w-8 h-8 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center shadow-sm">
          <ShieldCheck size={14} className="text-slate-400" />
        </div>
      </div>
      <h3 className="text-lg font-bold text-slate-600 dark:text-slate-300 mt-5 mb-1">Step Locked</h3>
      <p className="text-sm text-slate-400 max-w-xs text-center">Complete the previous step to unlock this section.</p>
      {prevName && (
        <button
          onClick={handleNav}
          className="mt-4 flex items-center gap-1.5 text-xs text-brand font-semibold bg-brand/5 px-4 py-2 rounded-xl border border-brand/10 hover:bg-brand/10 transition cursor-pointer">
          <ArrowLeft size={12} /> Go to &ldquo;{prevName}&rdquo; first
        </button>
      )}
    </motion.div>
  );
}
