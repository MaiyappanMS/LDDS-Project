import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { CheckCircle2, Sparkles } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Async from '../../components/ui/Async';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/States';
import DebtCard from '../../components/learning-debt/DebtCard';
import { learningDebtApi } from '../../api/learningDebtApi';
import { apiError } from '../../api/client';
import { useApi, invalidate } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

const ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export default function LearningDebtPage() {
  const { id } = useParams();
  const toast = useToast();
  const [explaining, setExplaining] = useState(false);
  const debt = useApi(`debt:${id}`, () => learningDebtApi.forSubject(id));
  const path = useApi(`path:${id}`, () => learningDebtApi.path(id));

  const generateExplanations = async () => {
    setExplaining(true);
    try {
      await learningDebtApi.explain(id);
      invalidate(`debt:${id}`);
      await debt.reload();
      toast.success('AI explanations updated.');
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setExplaining(false);
    }
  };

  return (
    <>
      <PageHeader title="Learning debt" subtitle="Concepts you have not mastered that other concepts depend on."
        crumbs={[{ label: 'Dashboard', to: '/student/dashboard' }, { label: 'Subject', to: `/student/subjects/${id}` }, { label: 'Learning debt' }]}
        actions={debt.data?.items?.length ? <Button variant="secondary" icon={Sparkles} loading={explaining} onClick={generateExplanations}>Explain with AI</Button> : null} />
      <Async state={debt} isEmpty={(d) => d.items.length === 0} empty={<EmptyState icon={CheckCircle2} title="No learning debt" body="Take an assessment, or keep it up if you already have." action={<Link className="text-sm font-medium text-brand hover:underline" to={`/student/subjects/${id}`}>Back to subject</Link>} />}>
        {(d) => {
          const items = [...d.items].sort((a, b) => ORDER[a.severity] - ORDER[b.severity] || a.mastery - b.mastery);
          const high = items.filter((i) => i.severity === 'HIGH').length;
          const steps = (path.data || []).filter((s) => s.status !== 'mastered').sort((a, b) => a.step - b.step);
          return (
            <div className="space-y-6">
              <Card>
                <p className="text-lg"><b className="text-3xl tabular-nums">{items.length}</b> concept{items.length === 1 ? '' : 's'} in debt{high > 0 && <span className="text-sev-high">, {high} high</span>}</p>
              </Card>
              <div className="space-y-4">{items.map((x) => <DebtCard key={x.conceptId} debt={x} />)}</div>
              {steps.length > 0 && (
                <Card>
                  <CardTitle hint="Start at the top">Recommended learning order</CardTitle>
                  <ol className="list-inside list-decimal space-y-1.5">{steps.map((s) => <li key={s.conceptId}><Link className="hover:underline" to={`/student/concepts/${s.conceptId}`}>{s.name}</Link><span className="ml-2 text-sm text-muted">{s.mastery}%</span></li>)}</ol>
                  <Link className="mt-4 inline-block text-sm font-medium text-brand hover:underline" to={`/student/learning-path/${id}`}>Open full learning path</Link>
                </Card>
              )}
            </div>
          );
        }}
      </Async>
    </>
  );
}

