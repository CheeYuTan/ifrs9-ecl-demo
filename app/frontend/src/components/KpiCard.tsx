import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface Props {
  title: ReactNode;
  value: string;
  subtitle?: string;
  icon?: ReactNode;
  color?: string;
}

const themes: Record<string, { bg: string; iconBg: string; border: string }> = {
  blue: { bg: 'from-blue-50 to-white dark:from-blue-950/30 dark:to-transparent', iconBg: 'bg-blue-500/10 text-blue-600 dark:text-blue-400', border: 'border-blue-100/50 dark:border-blue-800/30' },
  green: { bg: 'from-emerald-50 to-white dark:from-emerald-950/30 dark:to-transparent', iconBg: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400', border: 'border-emerald-100/50 dark:border-emerald-800/30' },
  amber: { bg: 'from-amber-50 to-white dark:from-amber-950/30 dark:to-transparent', iconBg: 'bg-amber-500/10 text-amber-600 dark:text-amber-400', border: 'border-amber-100/50 dark:border-amber-800/30' },
  red: { bg: 'from-red-50 to-white dark:from-red-950/30 dark:to-transparent', iconBg: 'bg-red-500/10 text-red-600 dark:text-red-400', border: 'border-red-100/50 dark:border-red-800/30' },
  purple: { bg: 'from-purple-50 to-white dark:from-purple-950/30 dark:to-transparent', iconBg: 'bg-purple-500/10 text-purple-600 dark:text-purple-400', border: 'border-purple-100/50 dark:border-purple-800/30' },
  indigo: { bg: 'from-indigo-50 to-white dark:from-indigo-950/30 dark:to-transparent', iconBg: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400', border: 'border-indigo-100/50 dark:border-indigo-800/30' },
  navy: { bg: 'from-slate-50 to-white dark:from-slate-950/30 dark:to-transparent', iconBg: 'bg-slate-500/10 text-slate-600 dark:text-slate-300', border: 'border-slate-100/50 dark:border-slate-800/30' },
  teal: { bg: 'from-teal-50 to-white dark:from-teal-950/30 dark:to-transparent', iconBg: 'bg-teal-500/10 text-teal-600 dark:text-teal-400', border: 'border-teal-100/50 dark:border-teal-800/30' },
};

export default function KpiCard({ title, value, subtitle, icon, color = 'blue' }: Props) {
  const t = themes[color] || themes.blue;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ y: -2, transition: { duration: 0.15 } }}
      className={`relative overflow-hidden bg-gradient-to-br ${t.bg} rounded-2xl border ${t.border} p-5 shadow-sm hover:shadow-lg transition-shadow group`}
    >
      <div className="absolute -top-8 -right-8 w-24 h-24 rounded-full bg-gradient-to-br from-current/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="relative flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-1.5">{title}</p>
          <p className="text-2xl font-extrabold text-slate-800 dark:text-slate-100 tracking-tight">{value}</p>
          {subtitle && <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1.5">{subtitle}</p>}
        </div>
        {icon && (
          <div className={`w-11 h-11 rounded-xl ${t.iconBg} flex items-center justify-center flex-shrink-0 ml-3`}>
            {icon}
          </div>
        )}
      </div>
    </motion.div>
  );
}
