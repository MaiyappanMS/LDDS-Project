import { masteryTone } from './tone';
const BG = { high: 'bg-sev-high', mid: 'bg-sev-mid', low: 'bg-sev-low', brand: 'bg-brand' };
export default function ProgressBar({ value = 0, tone, label, showValue = false, className = '' }) {
  const v = Math.max(0, Math.min(100, value));
  const t = tone || masteryTone(v);
  return (
    <div className={className}>
      {(label || showValue) && (
        <div className="mb-1 flex justify-between text-sm">
          <span>{label}</span>{showValue && <span className="font-medium tabular-nums">{v}%</span>}
        </div>
      )}
      <div role="progressbar" aria-valuenow={v} aria-valuemin={0} aria-valuemax={100} aria-label={label || 'Progress'} className="h-2 w-full overflow-hidden rounded-full bg-canvas">
        <div className={`h-full rounded-full transition-all duration-500 ${BG[t]}`} style={{ width: `${v}%` }} />
      </div>
    </div>
  );
}
