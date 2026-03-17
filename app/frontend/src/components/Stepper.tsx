import { Check, X } from 'lucide-react';
import type { Project } from '../lib/api';

const STEPS = [
  { key: 'create_project', label: 'Create' },
  { key: 'data_processing', label: 'Data Proc' },
  { key: 'data_control', label: 'Data QC' },
  { keys: ['model_execution', 'model_control'], label: 'Model Exec & QC' },
  { key: 'stress_testing', label: 'Stress Test' },
  { key: 'overlays', label: 'Overlays' },
  { key: 'sign_off', label: 'Sign Off' },
];

interface Props {
  project: Project | null;
  activeStep: number;
  onStepClick: (idx: number) => void;
}

export default function Stepper({ project, activeStep, onStepClick }: Props) {
  const ss = project?.step_status || {};
  const cur = project?.current_step ?? 0;

  const getStepStatus = (step: typeof STEPS[number]) => {
    if ('keys' in step && step.keys) {
      const statuses = step.keys.map(k => ss[k] || 'pending');
      if (statuses.every(s => s === 'completed')) return 'completed';
      if (statuses.some(s => s === 'rejected')) return 'rejected';
      if (statuses.some(s => s === 'in_progress')) return 'in_progress';
      return 'pending';
    }
    return ss[(step as any).key] || 'pending';
  };

  return (
    <div className="flex items-start justify-center gap-0 bg-white rounded-xl shadow-sm px-6 py-4">
      {STEPS.map((s, i) => {
        const status = getStepStatus(s);
        const isActive = i === activeStep;
        const isCompleted = status === 'completed';
        const isRejected = status === 'rejected';
        const isReachable = i <= cur;

        let bg = 'bg-slate-200 text-slate-400';
        if (isCompleted) bg = 'bg-brand text-white';
        else if (isRejected) bg = 'bg-red-500 text-white';
        else if (isActive) bg = 'bg-navy text-white ring-4 ring-brand-light';
        else if (isReachable) bg = 'bg-slate-400 text-white';

        return (
          <div key={s.key} className="flex items-start" style={{ flex: i < STEPS.length - 1 ? 1 : 'none' }}>
            <button
              onClick={() => isReachable && onStepClick(i)}
              className={`flex flex-col items-center ${isReachable ? 'cursor-pointer' : 'cursor-not-allowed opacity-60'}`}
              disabled={!isReachable}
              title={`${s.label} — ${status}`}
            >
              <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold transition-all ${bg}`}>
                {isCompleted ? <Check size={16} strokeWidth={3} /> : isRejected ? <X size={16} strokeWidth={3} /> : i + 1}
              </div>
              <span className={`text-[10px] font-semibold mt-1.5 text-center max-w-[72px] leading-tight ${isActive ? 'text-navy' : isCompleted ? 'text-brand-dark' : 'text-slate-400'}`}>
                {s.label}
              </span>
            </button>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mt-[18px] mx-1 rounded ${isCompleted ? 'bg-brand' : 'bg-slate-200'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
