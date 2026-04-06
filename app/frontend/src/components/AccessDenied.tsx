import { Shield } from 'lucide-react';

interface Props {
  message?: string;
  showBack?: boolean;
}

export default function AccessDenied({
  message = "You don't have permission to access this page.",
  showBack = false,
}: Props) {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-2xl shadow-lg px-10 py-12 max-w-md">
        <div className="w-14 h-14 rounded-2xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center mx-auto mb-5">
          <Shield size={28} className="text-red-500 dark:text-red-400" />
        </div>
        <h2 className="text-xl font-extrabold text-slate-800 dark:text-white mb-2">
          Access Denied
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-300">{message}</p>
        {showBack && (
          <button
            onClick={() => window.history.back()}
            className="mt-6 px-5 py-2.5 text-xs font-bold text-white bg-slate-700 dark:bg-slate-600 rounded-xl hover:opacity-80 transition"
          >
            Go Back
          </button>
        )}
      </div>
    </div>
  );
}
