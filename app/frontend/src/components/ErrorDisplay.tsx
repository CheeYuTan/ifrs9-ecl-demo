import { useState } from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, RefreshCw, ChevronDown, ChevronUp, Bug } from 'lucide-react';

interface ErrorDisplayProps {
  title?: string;
  message: string;
  technicalDetails?: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export default function ErrorDisplay({
  title = 'Something went wrong',
  message,
  technicalDetails,
  onRetry,
  onDismiss,
}: ErrorDisplayProps) {
  const [showDetails, setShowDetails] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-red-200 bg-red-50 overflow-hidden"
    >
      <div className="px-5 py-4 flex items-start gap-3">
        <div className="w-9 h-9 rounded-xl bg-red-100 flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertTriangle size={16} className="text-red-500" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-bold text-red-800">{title}</h4>
          <p className="text-xs text-red-600 mt-0.5">{message}</p>
          <div className="flex items-center gap-3 mt-3">
            {onRetry && (
              <button
                onClick={onRetry}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold bg-red-600 text-white hover:bg-red-700 transition shadow-sm"
              >
                <RefreshCw size={12} /> Retry
              </button>
            )}
            <a
              href="mailto:support@example.com?subject=IFRS9 ECL Error Report"
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold text-red-600 bg-red-100 hover:bg-red-200 transition"
            >
              <Bug size={12} /> Report Issue
            </a>
            {technicalDetails && (
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex items-center gap-1 text-xs text-red-400 hover:text-red-600 transition ml-auto"
              >
                {showDetails ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                {showDetails ? 'Hide' : 'Show'} Details
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                className="text-xs text-red-400 hover:text-red-600 transition ml-auto"
              >
                Dismiss
              </button>
            )}
          </div>
        </div>
      </div>
      {showDetails && technicalDetails && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="border-t border-red-200 bg-red-100/50 dark:bg-red-900/20 px-5 py-3"
        >
          <p className="text-[11px] font-bold text-red-500 dark:text-red-300 uppercase tracking-wider mb-1">Technical Details</p>
          <pre className="text-xs text-red-700 dark:text-red-300 whitespace-pre-wrap font-mono bg-white/60 dark:bg-slate-800/60 rounded-lg p-3 max-h-40 overflow-y-auto">
            {technicalDetails}
          </pre>
        </motion.div>
      )}
    </motion.div>
  );
}
