import { forwardRef, useId } from 'react';
const base = 'w-full rounded-lg border border-line bg-surface px-3 text-sm placeholder:text-muted/70 focus-visible:ring-offset-0';
export const Field = forwardRef(function Field({ label, error, hint, className = '', ...rest }, ref) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <input id={id} ref={ref} aria-invalid={!!error} aria-describedby={error ? `${id}-e` : undefined} className={`${base} h-10 ${error ? 'border-sev-high' : ''}`} {...rest} />
      {hint && !error && <p className="mt-1 text-xs text-muted">{hint}</p>}
      {error && <p id={`${id}-e`} className="mt-1 text-xs text-sev-high">{error}</p>}
    </div>
  );
});
export const Select = forwardRef(function Select({ label, error, children, className = '', ...rest }, ref) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <select id={id} ref={ref} aria-invalid={!!error} className={`${base} h-10 ${error ? 'border-sev-high' : ''}`} {...rest}>{children}</select>
      {error && <p className="mt-1 text-xs text-sev-high">{error}</p>}
    </div>
  );
});
export const Textarea = forwardRef(function Textarea({ label, error, className = '', ...rest }, ref) {
  const id = useId();
  return (
    <div className={className}>
      <label htmlFor={id} className="mb-1 block text-sm font-medium">{label}</label>
      <textarea id={id} ref={ref} rows={3} className={`${base} py-2 ${error ? 'border-sev-high' : ''}`} {...rest} />
      {error && <p className="mt-1 text-xs text-sev-high">{error}</p>}
    </div>
  );
});
