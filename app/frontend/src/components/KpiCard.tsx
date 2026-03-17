import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface Props {
  title: string;
  value: string;
  subtitle?: string;
  icon?: ReactNode;
  color?: string;
  trend?: 'up' | 'down' | 'neutral';
}

const colorMap: Record<string, string> = {
  blue: 'border-l-blue',
  green: 'border-l-stage1',
  amber: 'border-l-stage2',
  red: 'border-l-stage3',
  purple: 'border-l-purple',
  indigo: 'border-l-indigo',
  navy: 'border-l-navy',
  teal: 'border-l-teal',
};

export default function KpiCard({ title, value, subtitle, icon, color = 'blue' }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`bg-white rounded-xl border-l-4 ${colorMap[color] || 'border-l-blue'} shadow-sm hover:shadow-md transition-shadow p-5`}
    >
      <div className="flex items-start justify-between">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-slate-800 tracking-tight">{value}</p>
          {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
        </div>
        {icon && <div className="text-slate-300 ml-3 flex-shrink-0">{icon}</div>}
      </div>
    </motion.div>
  );
}
