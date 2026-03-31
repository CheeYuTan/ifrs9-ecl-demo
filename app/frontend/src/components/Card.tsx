import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface Props {
  children: ReactNode;
  title?: ReactNode;
  subtitle?: string;
  className?: string;
  noPad?: boolean;
  accent?: 'brand' | 'blue' | 'purple' | 'amber' | 'red' | 'none';
  icon?: ReactNode;
  action?: ReactNode;
}

export default function Card({ children, title, subtitle, className = '', noPad, accent = 'none', icon, action }: Props) {
  const accentBar: Record<string, string> = {
    brand: 'from-brand to-brand-dark',
    blue: 'from-blue to-indigo',
    purple: 'from-purple to-indigo',
    amber: 'from-amber-400 to-orange-500',
    red: 'from-red-500 to-rose-600',
    none: '',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`relative glass-card rounded-2xl ${className}`}
    >
      {accent !== 'none' && (
        <div className={`absolute top-0 left-0 right-0 h-[2px] rounded-t-2xl bg-gradient-to-r ${accentBar[accent]}`} />
      )}
      {title && (
        <div className={`px-6 pt-5 pb-2 flex items-start justify-between ${accent !== 'none' ? 'pt-6' : ''}`}>
          <div className="flex items-center gap-3 min-w-0">
            {icon && <div className="flex-shrink-0 text-slate-400">{icon}</div>}
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200">{title}</h3>
              {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
            </div>
          </div>
          {action && <div className="flex-shrink-0 ml-3">{action}</div>}
        </div>
      )}
      <div className={noPad ? '' : `px-6 pb-5 ${!title ? (accent !== 'none' ? 'pt-6' : 'pt-5') : ''}`}>{children}</div>
    </motion.div>
  );
}
