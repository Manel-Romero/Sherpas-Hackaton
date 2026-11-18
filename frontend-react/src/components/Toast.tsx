import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  text: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
      <AnimatePresence>
        {toasts.map((t) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 15, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="pointer-events-auto p-3.5 rounded-2xl liquid-glass-elevated border border-black/10 dark:border-white/12 shadow-xl flex items-center justify-between gap-3 text-xs font-medium text-slate-800 dark:text-[#f8fafc]"
          >
            <div className="flex items-center gap-2.5">
              {t.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-[#526e5e] dark:text-[#8ba898] shrink-0" />
              ) : t.type === 'error' ? (
                <AlertCircle className="w-4 h-4 text-[#875f52] dark:text-[#b38a7c] shrink-0" />
              ) : (
                <Info className="w-4 h-4 text-[#7d7568] dark:text-[#b0a89a] shrink-0" />
              )}
              <span className="leading-snug">{t.text}</span>
            </div>
            <button
              onClick={() => onDismiss(t.id)}
              className="p-1 text-slate-400 hover:text-slate-700 dark:text-white/40 dark:hover:text-white rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};
