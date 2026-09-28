import { useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { PlayCircle } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Async from '../../components/ui/Async';
import ProgressBar from '../../components/ui/ProgressBar';
import DebtCard from '../../components/learning-debt/DebtCard';
import ConceptGraph from '../../components/concepts/ConceptGraph';
import { subjectApi } from '../../api/subjectApi';
import { assessmentApi } from '../../api/assessmentApi';
import { learningDebtApi } from '../../api/learningDebtApi';
import { apiError } from '../../api/client';
import { useApi } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

export default function StudentSubjectPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [starting, setStarting] = useState(false);
  const subject = useApi(`subject:${id}`, () => subjectApi.get(id));
  const debt = useApi(`debt:${id}`, () => learningDebtApi.forSubject(id));
  const graph = useApi(`graph:${id}`, () => subjectApi.graph(id));

  const start = async () => {
    setStarting(true);
    try { navigate(`/student/assessment/${await assessmentApi.create(Number(id) || id)}`); }
    catch (e) { toast.error(apiError(e)); setStarting(false); }
  };

  return (
    <Async state={subject}>
      {(s) => (
        <>
          <PageHeader title={s.name} subtitle={s.description} crumbs={[{ label: 'Dashboard', to: '/student/dashboard' }, { label: s.name }]}
            actions={<Button size="lg" icon={PlayCircle} loading={starting} onClick={start}>Start assessment</Button>} />
          <div className="space-y-6">
            <Async state={debt} skeleton={<div className="h-32 animate-pulse rounded-card bg-line/60" />}>
              {(d) => {
                const weak = [...d.items].sort((a, b) => a.mastery - b.mastery).slice(0, 3);
                const overall = d.overallMastery ?? s.mastery;
                return (
                  <>
                    {overall != null && <Card><ProgressBar value={overall} showValue label="Overall mastery" /></Card>}
                    <section aria-labelledby="weak-h">
                      <div className="mb-3 flex items-baseline justify-between"><h2 id="weak-h" className="text-lg font-semibold">Weak concepts</h2>
                        <div className="flex gap-4 text-sm font-medium"><Link className="text-brand hover:underline" to={`/student/learning-debt/${id}`}>Full learning debt</Link><Link className="text-brand hover:underline" to={`/student/learning-path/${id}`}>Learning path</Link></div></div>
                      {weak.length ? <div className="grid gap-4 lg:grid-cols-3">{weak.map((w) => <DebtCard key={w.conceptId} debt={w} compact />)}</div>
                        : <Card className="text-sm text-muted">No learning debt yet. Take an assessment to find out where you stand.</Card>}
                    </section>
                  </>
                );
              }}
            </Async>
            <Card>
              <CardTitle hint="Select a concept to open it">Concept map</CardTitle>
              <Async state={graph} skeleton={<div className="h-64 animate-pulse rounded-lg bg-line/60" />} isEmpty={(g) => g.nodes.length === 0} empty={<p className="text-sm text-muted">No concepts have been added to this subject yet.</p>}>
                {(g) => <ConceptGraph graph={g} height={380} onSelect={(nid) => nid && navigate(`/student/concepts/${nid}`)} />}
              </Async>
            </Card>
          </div>
        </>
      )}
    </Async>
  );
}
