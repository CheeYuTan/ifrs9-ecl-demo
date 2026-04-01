import { Check, X, FolderPlus, Database, ShieldCheck, Satellite, Cpu, BarChart3, Layers, FileSignature } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Project } from '../lib/api';

const STEPS = [
  { key: 'create_project', label: 'Create', icon: FolderPlus },
  { key: 'data_processing', label: 'Data Proc', icon: Database },
  { key: 'data_control', label: 'Data QC', icon: ShieldCheck },
  { key: 'satellite_model', label: 'Satellite Model', icon: Satellite },
  { key: 'model_execution', label: 'Monte Carlo', icon: Cpu },
  { key: 'stress_testing', label: 'Stress Test', icon: BarChart3 },
  { key: 'overlays', label: 'Overlays', icon: Layers },
  { key: 'sign_off', label: 'Sign Off', icon: FileSignature },
];

interface Props {
  project: Project | null;
  activeStep: number;
  onStepClick: (idx: number) => void;
}

export default function Stepper({ project, activeStep, onStepClick }: Props) {
  const ss = project?.step_status || {};
  const cur = project?.current_step ?? 0;

  return (
    <div className="flex items-start justify-center gap-0 glass-card rounded-2xl px-6 py-5">
      {STEPS.map((s, i) => {
        const status = ss[s.key] || 'pending';
        const isActive = i === activeStep;
        const isCompleted = status === 'completed';
        const isRejected = status === 'rejected';
        const isReachable = i <= cur;
        const Icon = s.icon;

        let circleClass = 'bg-slate-100 dark:bg-slate-800 text-slate-400 border-2 border-slate-200 dark:border-slate-600';
        let labelClass = 'text-slate-400';
        if (isCompleted) {
          circleClass = 'gradient-brand text-white border-0 shadow-md glow-brand';
          labelClass = 'text-brand-dark font-bold';
        } else if (isRejected) {
          circleClass = 'bg-red-500 text-white border-0 shadow-md';
          labelClass = 'text-red-500 font-bold';
        } else if (isActive) {
          circleClass = 'bg-navy text-white border-0 shadow-lg ring-3 ring-brand/20';
          labelClass = 'text-navy font-bold';
        } else if (isReachable) {
          circleClass = 'bg-slate-500 text-white border-0';
          labelClass = 'text-slate-500';
        }

        const lineClass = isCompleted ? 'bg-gradient-to-r from-brand to-brand-dark' : 'bg-slate-200 dark:bg-slate-700';

        return (
          <div key={s.key} className="flex items-start" style={{ flex: i < STEPS.length - 1 ? 1 : 'none' }}>
            <motion.button
              whileHover={isReachable ? { scale: 1.05 } : {}}
              whileTap={isReachable ? { scale: 0.95 } : {}}
              onClick={() => isReachable && onStepClick(i)}
              className={`flex flex-col items-center ${isReachable ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'}`}
              disabled={!isReachable}
              title={`${s.label} — ${status}`}
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${circleClass}`}>
                {isCompleted ? <Check size={16} strokeWidth={3} /> : isRejected ? <X size={16} strokeWidth={3} /> : <Icon size={16} />}
              </div>
              <span className={`text-[10px] mt-2 text-center max-w-[72px] leading-tight transition-colors ${labelClass}`}>
                {s.label}
              </span>
            </motion.button>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-[3px] mt-[19px] mx-1.5 rounded-full transition-colors ${lineClass}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
