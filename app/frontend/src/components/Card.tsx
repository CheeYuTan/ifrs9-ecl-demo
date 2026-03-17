import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

interface Props {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
  noPad?: boolean;
}

export default function Card({ children, title, subtitle, className = '', noPad }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={`bg-white rounded-xl shadow-sm ${className}`}
    >
      {title && (
        <div className="px-6 pt-5 pb-2">
          <h3 className="text-sm font-bold text-slate-700">{title}</h3>
          {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className={noPad ? '' : 'px-6 pb-5'}>{children}</div>
    </motion.div>
  );
}
