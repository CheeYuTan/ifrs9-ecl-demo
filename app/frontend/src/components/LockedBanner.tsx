import { Lock, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';

const STEP_NAMES = ['Create Project', 'Data Processing', 'Data Control', 'Model Execution & Control', 'Stress Testing', 'Overlays', 'Sign Off'];

interface Props {
  requiredStep?: number;
}

export default function LockedBanner({ requiredStep }: Props) {
  const prevName = requiredStep != null && requiredStep > 0 ? STEP_NAMES[requiredStep - 1] : null;
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-24 text-slate-400"
    >
      <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
        <Lock size={28} strokeWidth={1.5} className="text-slate-300" />
      </div>
      <h3 className="text-lg font-semibold text-slate-500 mb-1">Step Locked</h3>
      <p className="text-sm">Complete the previous step to unlock this section.</p>
      {prevName && (
        <div className="mt-3 flex items-center gap-1.5 text-xs text-brand font-semibold">
          <ArrowLeft size={12} /> Go to "{prevName}" and complete it first
        </div>
      )}
    </motion.div>
  );
}
