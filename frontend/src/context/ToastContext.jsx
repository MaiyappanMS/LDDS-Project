import { createContext, useCallback, useContext, useState } from 'react';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';

const ToastCtx = createContext(null);
export const useToast = () => useContext(ToastCtx);

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const remove = (id) => setItems((s) => s.filter((t) => t.id !== id));
  const push = useCallback((type, message) => {
    const id = Math.random().toString(36).slice(2);
    setItems((s) => [...s, { id, type, message }]);
    setTimeout(() => remove(id), 5000);
  }, []);
  const api = { success: (m) => push('success', m), error: (m) => push('error', m) };
  return (
    <ToastCtx.Provider value={api}>
      {children}
      <div className="fixed bottom-20 right-4 z-[60] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2 lg:bottom-4" aria-live="polite">
        {items.map((t) => (
          <div key={t.id} role="status" className={`flex items-start gap-2 rounded-lg border bg-surface p-3 text-sm shadow-card ${t.type === 'error' ? 'border-sev-high' : 'border-sev-low'}`}>
            {t.type === 'error' ? <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-sev-high" /> : <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-sev-low" />}
            <p className="flex-1">{t.message}</p>
            <button aria-label="Dismiss" onClick={() => remove(t.id)} className="text-muted"><X className="h-4 w-4" /></button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}
