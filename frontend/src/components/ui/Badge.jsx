import { difficultyTone } from './tone';
const T = {
  neutral: 'bg-canvas text-muted',
  brand: 'bg-brand-tint text-brand',
  high: 'bg-sev-high-tint text-sev-high',
  mid: 'bg-sev-mid-tint text-sev-mid',
  low: 'bg-sev-low-tint text-sev-low',
};
export default function Badge({ tone = 'neutral', children, className = '' }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${T[tone]} ${className}`}>{children}</span>;
}
export const DifficultyBadge = ({ difficulty }) => <Badge tone={difficultyTone(difficulty)}>{difficulty}</Badge>;
