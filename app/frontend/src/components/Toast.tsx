import { useState, useRef, useEffect, createContext, useContext, useCallback, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle, CheckCircle2, Info } from 'lucide-react';

interface ToastItem {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastCtx {
  toast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const Ctx = createContext<ToastCtx>({ toast: () => {} });

export const useToast = () => useContext(Ctx);

let nextId = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    return () => { timersRef.current.forEach(t => clearTimeout(t)); timersRef.current.clear(); };
  }, []);

  const toast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = ++nextId;
    setItems(prev => [...prev, { id, message, type }]);
    const timer = setTimeout(() => {
      setItems(prev => prev.filter(t => t.id !== id));
      timersRef.current.delete(id);
    }, 5000);
    timersRef.current.set(id, timer);
  }, []);

  const dismiss = (id: number) => setItems(prev => prev.filter(t => t.id !== id));

  const colors = {
    error: 'bg-red-600 text-white border-red-700',
    success: 'bg-emerald-600 text-white border-emerald-700',
    info: 'bg-slate-800 text-white border-slate-700',
  };

  const icons = {
    error: AlertCircle,
    success: CheckCircle2,
    info: Info,
  };

  return (
    <Ctx.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2.5 max-w-sm" role="status" aria-live="polite" aria-atomic="false">
        <AnimatePresence>
          {items.map(t => {
            const Icon = icons[t.type];
            return (
              <motion.div key={t.id}
                initial={{ opacity: 0, x: 60, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: 60, scale: 0.9 }}
                className={`flex items-start gap-3 px-4 py-3.5 rounded-2xl shadow-2xl border ${colors[t.type]}`}>
                <Icon size={16} className="mt-0.5 flex-shrink-0 opacity-80" />
                <p className="text-sm flex-1 font-medium">{t.message}</p>
                <button onClick={() => dismiss(t.id)} aria-label="Dismiss notification" className="opacity-50 hover:opacity-100 transition mt-0.5 focus-visible:ring-2 focus-visible:ring-white rounded">
                  <X size={14} />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </Ctx.Provider>
  );
}
