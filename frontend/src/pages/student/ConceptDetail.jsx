import { Link, useNavigate, useParams } from 'react-router-dom';
import { BookOpenCheck } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Async from '../../components/ui/Async';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import ProgressBar from '../../components/ui/ProgressBar';
import { DifficultyBadge } from '../../components/ui/Badge';
import DebtSeverity from '../../components/learning-debt/DebtSeverity';
import { conceptApi } from '../../api/conceptApi';
import { normDebt } from '../../api/adapters';
import { useApi } from '../../hooks/useApi';

const Chips = ({ items }) => items.length
  ? <ul className="flex flex-wrap gap-2">{items.map((p, i) => <li key={p.id ?? i}><Link to={`/student/concepts/${p.id}`} className="rounded-lg border border-line bg-canvas px-3 py-1 text-sm hover:border-brand">{p.name ?? `Concept ${p.id}`}</Link></li>)}</ul>
  : <p className="text-sm text-muted">None</p>;

export default function ConceptDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const state = useApi(`concept:${id}`, () => conceptApi.get(id));
  return (
    <Async state={state}>
      {(c) => {
        const debt = c.debt && typeof c.debt === 'object' ? normDebt(c.debt) : null;
        const back = c.subjectId != null ? { label: 'Subject', to: `/student/subjects/${c.subjectId}` } : { label: 'Dashboard', to: '/student/dashboard' };
        return (
          <>
            <PageHeader title={c.name} subtitle={c.description} crumbs={[back, { label: c.name }]}
              actions={<Button size="lg" icon={BookOpenCheck} onClick={() => navigate(c.subjectId != null ? `/student/learning-path/${c.subjectId}` : back.to)}>Review concept</Button>} />
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardTitle>Where you stand</CardTitle>
                <div className="mb-3 flex items-center gap-2"><DifficultyBadge difficulty={c.difficulty} />{debt && <DebtSeverity severity={debt.severity} />}</div>
                {c.mastery != null ? <ProgressBar value={c.mastery} showValue label="Current mastery" /> : <p className="text-sm text-muted">No mastery recorded yet. Take an assessment.</p>}
                {debt?.action && <div className="mt-4 rounded-lg bg-canvas p-3 text-sm"><b>Recommended action</b><p className="mt-1">{debt.action}</p></div>}
              </Card>
              <Card><CardTitle>AI explanation</CardTitle>{c.explanation ? <p className="whitespace-pre-line text-sm leading-relaxed">{c.explanation}</p> : <p className="text-sm text-muted">No explanation is available for this concept yet.</p>}</Card>
              <Card><CardTitle>Prerequisites</CardTitle><Chips items={c.prerequisites} /></Card>
              <Card><CardTitle>Concepts that depend on this</CardTitle><Chips items={c.dependents} /></Card>
            </div>
          </>
        );
      }}
    </Async>
  );
}
