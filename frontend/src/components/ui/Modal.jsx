import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import Button from './Button';

function useEscape(open, onClose) {
  useEffect(() => {
    if (!open) return;
    const h = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', h);
    return () => document.removeEventListener('keydown', h);
  }, [open, onClose]);
}

export function Modal({ open, onClose, title, children, footer }) {
  const ref = useRef(null);
  useEscape(open, onClose);
  useEffect(() => { if (open) ref.current?.focus(); }, [open]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-0 sm:items-center sm:p-4" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div ref={ref} tabIndex={-1} role="dialog" aria-modal="true" aria-label={title} className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-card bg-surface p-5 shadow-xl sm:rounded-card">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button aria-label="Close" onClick={onClose} className="rounded p-1 text-muted hover:bg-canvas"><X className="h-5 w-5" /></button>
        </div>
        {children}
        {footer && <div className="mt-5 flex justify-end gap-2">{footer}</div>}
      </div>
    </div>
  );
}

export function ConfirmDialog({ open, onClose, onConfirm, title, message, confirmLabel = 'Delete', loading }) {
  return (
    <Modal open={open} onClose={onClose} title={title} footer={<><Button variant="secondary" onClick={onClose}>Cancel</Button><Button variant="danger" loading={loading} onClick={onConfirm}>{confirmLabel}</Button></>}>
      <p className="text-sm text-muted">{message}</p>
    </Modal>
  );
}

export function Drawer({ open, onClose, title, children }) {
  useEscape(open, onClose);
  if (!open) return null;
  return (
    <aside role="complementary" aria-label={title} className="absolute inset-y-0 right-0 z-10 w-full max-w-xs overflow-y-auto border-l border-line bg-surface p-4 shadow-lg">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold">{title}</h3>
        <button aria-label="Close panel" onClick={onClose} className="rounded p-1 text-muted hover:bg-canvas"><X className="h-4 w-4" /></button>
      </div>
      {children}
    </aside>
  );
}
