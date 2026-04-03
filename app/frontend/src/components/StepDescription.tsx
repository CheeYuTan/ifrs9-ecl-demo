import { motion } from 'framer-motion';
import { Info, BookOpen } from 'lucide-react';
import type { ReactNode } from 'react';

interface Props {
  description: string;
  ifrsRef?: string;
  tips?: string[];
  icon?: ReactNode;
}

export default function StepDescription({ description, ifrsRef, tips, icon }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: 0.1 }}
      className="rounded-xl bg-gradient-to-r from-brand/5 via-blue-50/50 dark:via-blue-900/20 to-transparent border border-brand/10 px-5 py-3.5 mb-5"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-brand/10 flex items-center justify-center mt-0.5">
          {icon || <Info size={16} className="text-brand" />}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">{description}</p>
          {tips && tips.length > 0 && (
            <ul className="mt-2 space-y-1">
              {tips.map((tip, i) => (
                <li key={i} className="text-xs text-slate-500 flex items-start gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-brand/40 mt-1.5 flex-shrink-0" />
                  {tip}
                </li>
              ))}
            </ul>
          )}
          {ifrsRef && (
            <div className="mt-2 flex items-center gap-1.5 text-[11px] text-brand/70 font-medium">
              <BookOpen size={11} />
              <span>{ifrsRef}</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
