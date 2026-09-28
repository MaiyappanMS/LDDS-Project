import { Link } from 'react-router-dom';
import { Lock, CheckCircle2, AlertCircle, CircleDot, ArrowDown } from 'lucide-react';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import ProgressBar from '../ui/ProgressBar';
import DebtSeverity from './DebtSeverity';

const STATUS = {
  locked: { label: 'Locked', tone: 'neutral', icon: Lock },
  in_progress: { label: 'In progress', tone: 'brand', icon: CircleDot },
  needs_review: { label: 'Needs review', tone: 'high', icon: AlertCircle },
  mastered: { label: 'Mastered', tone: 'low', icon: CheckCircle2 },
};

export default function LearningPath({ steps }) {
  return (
    <ol className="space-y-2">
      {steps.map((s, i) => {
        const st = STATUS[s.status];
        const Icon = st.icon;
        return (
          <li key={`${s.conceptId}-${i}`}>
            <Card className={s.status === 'locked' ? 'opacity-70' : ''}>
              <div className="flex items-start gap-4">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-tint font-bold text-brand" aria-label={`Step ${s.step}`}>{s.step}</div>
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="font-semibold">{s.conceptId != null ? <Link to={`/student/concepts/${s.conceptId}`} className="hover:underline">{s.name}</Link> : s.name}</h3>
                    <Badge tone={st.tone}><Icon className="mr-1 h-3 w-3" aria-hidden />{st.label}</Badge>
                    {s.status !== 'mastered' && <DebtSeverity severity={s.severity} />}
                  </div>
                  <ProgressBar value={s.mastery} showValue label="Mastery" className="mt-3 max-w-md" />
                  {s.reason && <p className="mt-2 text-sm text-muted">{s.reason}</p>}
                </div>
              </div>
            </Card>
            {i < steps.length - 1 && <div className="flex justify-start pl-[26px] text-muted" aria-hidden><ArrowDown className="my-1 h-5 w-5" /></div>}
          </li>
        );
      })}
    </ol>
  );
}
