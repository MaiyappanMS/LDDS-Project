import { Loader2 } from 'lucide-react';
const V = {
  primary: 'bg-brand text-white hover:bg-brand-dark',
  secondary: 'bg-surface text-ink border border-line hover:bg-canvas',
  danger: 'bg-sev-high text-white hover:opacity-90',
  ghost: 'text-muted hover:bg-canvas hover:text-ink',
};
const S = { sm: 'h-8 px-3 text-sm', md: 'h-10 px-4 text-sm', lg: 'h-12 px-6 text-base' };
export default function Button({ variant = 'primary', size = 'md', loading = false, icon: Icon, children, className = '', disabled, type = 'button', ...rest }) {
  return (
    <button type={type} disabled={disabled || loading} className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60 ${V[variant]} ${S[size]} ${className}`} {...rest}>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : Icon ? <Icon className="h-4 w-4" aria-hidden /> : null}
      {children}
    </button>
  );
}
