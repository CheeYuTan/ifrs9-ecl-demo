import { motion } from 'framer-motion';
import { Inbox } from 'lucide-react';
import type { ReactNode } from 'react';

interface ActionButton {
  label: string;
  onClick: () => void;
}

interface Props {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode | ActionButton;
  className?: string;
}

function isActionButton(action: unknown): action is ActionButton {
  return typeof action === 'object' && action !== null && 'label' in action && 'onClick' in action;
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className = '',
}: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col items-center justify-center py-16 px-6 text-center ${className}`}
    >
      <div className="w-16 h-16 rounded-2xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-5">
        {icon || <Inbox size={28} className="text-slate-400" />}
      </div>
      <h3 className="text-base font-bold text-slate-700 dark:text-slate-200 mb-1.5">{title}</h3>
      {description && (
        <p className="text-sm text-slate-500 max-w-md leading-relaxed">{description}</p>
      )}
      {action && (
        <div className="mt-5">
          {isActionButton(action) ? (
            <button
              onClick={action.onClick}
              className="px-5 py-2.5 gradient-brand text-white text-sm font-bold rounded-xl hover:opacity-80 transition shadow-lg"
            >
              {action.label}
            </button>
          ) : (
            action
          )}
        </div>
      )}
    </motion.div>
  );
}
