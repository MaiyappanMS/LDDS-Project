import { Link } from 'react-router-dom';
import Card from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';
import DebtSeverity from './DebtSeverity';
import ConceptDependency from './ConceptDependency';

const STRIPE = { HIGH: 'border-l-sev-high', MEDIUM: 'border-l-sev-mid', LOW: 'border-l-sev-low' };
const NUM = { HIGH: 'text-sev-high', MEDIUM: 'text-sev-mid', LOW: 'text-sev-low' };

export default function DebtCard({ debt, compact = false }) {
  const names = debt.affected.map((a) => a.name).filter(Boolean);
  // Fallback wording is built only from real fields returned by the backend.
  const why = debt.reason || (names.length ? `${debt.name} is a prerequisite for ${names.join(', ')}.` : '');
  return (
    <Card className={`border-l-4 ${STRIPE[debt.severity]}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold">{debt.conceptId != null ? <Link to={`/student/concepts/${debt.conceptId}`} className="hover:underline">{debt.name}</Link> : debt.name}</h3>
          <div className="mt-1"><DebtSeverity severity={debt.severity} /></div>
        </div>
        <div className="text-right">
          <div className={`text-3xl font-bold tabular-nums ${NUM[debt.severity]}`}>{debt.mastery}%</div>
          <div className="text-xs text-muted">mastery</div>
        </div>
      </div>
      <ProgressBar value={debt.mastery} className="mt-3" />
      {!compact && (
        <div className="mt-4 space-y-4">
          {why && <div><h4 className="text-sm font-semibold">Why this matters</h4><p className="mt-1 text-sm text-muted">{why}</p></div>}
          <ConceptDependency affected={debt.affected} />
          <div className="rounded-lg bg-canvas p-3"><h4 className="text-sm font-semibold">Recommended action</h4><p className="mt-1 text-sm">{debt.action || `Review ${debt.name} first.`}</p></div>
        </div>
      )}
    </Card>
  );
}
