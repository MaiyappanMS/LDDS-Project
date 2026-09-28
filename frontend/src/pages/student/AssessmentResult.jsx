import { Link, useParams } from 'react-router-dom';
import PageHeader from '../../components/layout/PageHeader';
import Async from '../../components/ui/Async';
import Card from '../../components/ui/Card';
import AssessmentResult from '../../components/assessment/AssessmentResult';
import DebtCard from '../../components/learning-debt/DebtCard';
import { assessmentApi } from '../../api/assessmentApi';
import { learningDebtApi } from '../../api/learningDebtApi';
import { useApi } from '../../hooks/useApi';

function YourDebt({ subjectId }) {
  const debt = useApi(`debt:${subjectId}`, () => learningDebtApi.forSubject(subjectId), { ttl: 0 });
  return (
    <section aria-labelledby="debt-h" className="mt-8">
      <div className="mb-3 flex items-baseline justify-between">
        <h2 id="debt-h" className="text-xl font-bold">Your learning debt</h2>
        <Link to={`/student/learning-debt/${subjectId}`} className="text-sm font-medium text-brand hover:underline">See all and what it affects</Link>
      </div>
      <Async state={debt} skeleton={<div className="h-32 animate-pulse rounded-card bg-line/60" />} isEmpty={(d) => d.items.length === 0} empty={<Card className="text-sm text-muted">No learning debt found. Nice work.</Card>}>
        {(d) => <div className="grid gap-4 lg:grid-cols-2">{[...d.items].sort((a, b) => a.mastery - b.mastery).slice(0, 4).map((x) => <DebtCard key={x.conceptId} debt={x} compact />)}</div>}
      </Async>
    </section>
  );
}

export default function AssessmentResultPage() {
  const { id } = useParams();
  const state = useApi(`assessment:${id}`, () => assessmentApi.get(id), { ttl: 0 });
  return (
    <>
      <PageHeader title="Assessment result" crumbs={[{ label: 'Dashboard', to: '/student/dashboard' }, { label: 'Result' }]} />
      <Async state={state}>
        {(r) => (<><AssessmentResult result={r} />{r.subjectId != null && <YourDebt subjectId={r.subjectId} />}</>)}
      </Async>
    </>
  );
}
