import { useState } from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, PlusCircle } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Card, { CardTitle } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import ConceptCard from '../../components/concepts/ConceptCard';
import ProgressChart from '../../components/charts/ProgressChart';
import ProgressBar from '../../components/ui/ProgressBar';
import { Table, Th, Td } from '../../components/ui/Table';
import { formatDate, masteryTone } from '../../components/ui/tone';
import { learningDebtApi } from '../../api/learningDebtApi';
import { subjectApi } from '../../api/subjectApi';
import { apiError } from '../../api/client';
import { useApi, invalidate } from '../../hooks/useApi';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';

const NUM = { high: 'text-sev-high', mid: 'text-sev-mid', low: 'text-sev-low' };

export default function StudentDashboard() {
  const { currentUser } = useAuth();
  const toast = useToast();
  const [enrollingId, setEnrollingId] = useState(null);
  const overview = useApi('overview:student', learningDebtApi.studentOverview);
  const subjects = useApi('subjects', subjectApi.list);
  const available = useApi('subjects:available', () => subjectApi.available().catch(() => []));

  const handleEnroll = async (subjectId) => {
    setEnrollingId(subjectId);
    try {
      await subjectApi.enroll(subjectId);
      toast.success('Enrolled in subject.');
      invalidate('subjects');
      invalidate('overview:student');
      await Promise.all([subjects.reload(), available.reload(), overview.reload()]);
    } catch (e) {
      toast.error(apiError(e));
    } finally {
      setEnrollingId(null);
    }
  };

  return (
    <>
      <PageHeader title={`Welcome${currentUser?.name ? `, ${currentUser.name.split(' ')[0]}` : ''}`} subtitle="See where your foundations are weak and what to learn first." />
      <div className="space-y-6">
        <Async state={overview} skeleton={<div className="h-40 animate-pulse rounded-card bg-line/60" />}>
          {(o) => (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                {o.overallMastery != null && <Card><p className="text-sm text-muted">Overall mastery</p><p className={`mt-1 text-5xl font-bold tabular-nums ${NUM[masteryTone(o.overallMastery)]}`}>{o.overallMastery}%</p><ProgressBar value={o.overallMastery} className="mt-3" /></Card>}
                {o.debtCount != null && <Card><p className="text-sm text-muted">Learning debt</p><p className="mt-1 text-5xl font-bold tabular-nums">{o.debtCount}<span className="ml-2 text-lg font-medium text-muted">concept{o.debtCount === 1 ? '' : 's'}</span></p><p className="mt-3 text-sm text-muted">Concepts that are holding back what you learn next.</p></Card>}
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                <Card><CardTitle>Weak concepts</CardTitle>{o.weak.length ? <div className="space-y-2">{o.weak.map((c) => <ConceptCard key={c.id ?? c.name} concept={c} />)}</div> : <p className="text-sm text-muted">No weak concepts found.</p>}</Card>
                <Card><CardTitle>Strong concepts</CardTitle>{o.strong.length ? <div className="space-y-2">{o.strong.map((c) => <ConceptCard key={c.id ?? c.name} concept={c} />)}</div> : <p className="text-sm text-muted">Take an assessment to find your strengths.</p>}</Card>
              </div>
              {o.progress.length > 1 && <Card><CardTitle>Progress</CardTitle><ProgressChart data={o.progress} /></Card>}
              {o.recent.length > 0 && (
                <Card><CardTitle>Recent assessments</CardTitle>
                  <Table><thead><tr><Th>Subject</Th><Th>Score</Th><Th>Date</Th></tr></thead><tbody>{o.recent.map((r, i) => <tr key={r.id ?? i}><Td><Link className="text-brand hover:underline" to={`/student/assessment/${r.id}/result`}>{r.subject || `Assessment ${r.id}`}</Link></Td><Td className="tabular-nums">{r.score != null ? `${r.score}%` : '–'}</Td><Td>{formatDate(r.date)}</Td></tr>)}</tbody></Table>
                </Card>
              )}
            </>
          )}
        </Async>

        <section aria-labelledby="my-subjects">
          <h2 id="my-subjects" className="mb-3 text-lg font-semibold">Your subjects</h2>
          <Async state={subjects} isEmpty={(d) => d.length === 0} empty={<EmptyState icon={BookOpen} title="No enrolled subjects yet" body={available.data?.length ? 'Enroll in one of the available subjects below to get started.' : 'Your teacher has not added a subject for you yet.'} />}>
            {(list) => (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {list.map((s) => (
                  <Card key={s.id}>
                    <h3 className="font-semibold">{s.name}</h3>
                    <p className="mt-1 line-clamp-2 text-sm text-muted">{s.description || 'No description'}</p>
                    {s.mastery != null && <ProgressBar value={s.mastery} showValue label="Mastery" className="mt-3" />}
                    <div className="mt-4 flex flex-wrap gap-x-4 gap-y-1 text-sm font-medium">
                      <Link className="text-brand hover:underline" to={`/student/subjects/${s.id}`}>Open</Link>
                      <Link className="text-brand hover:underline" to={`/student/learning-debt/${s.id}`}>Learning debt</Link>
                      <Link className="text-brand hover:underline" to={`/student/learning-path/${s.id}`}>Learning path</Link>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </Async>
        </section>

        {available.data?.length > 0 && (
          <section aria-labelledby="avail-subjects">
            <h2 id="avail-subjects" className="mb-3 text-lg font-semibold">Available subjects to enroll</h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {available.data.map((s) => (
                <Card key={s.id}>
                  <h3 className="font-semibold">{s.name}</h3>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{s.description || 'No description'}</p>
                  {s.semester !== '' && <p className="mt-2 text-xs text-muted">Semester {s.semester}</p>}
                  <div className="mt-4">
                    <Button size="sm" icon={PlusCircle} loading={enrollingId === s.id} onClick={() => handleEnroll(s.id)}>Enroll</Button>
                  </div>
                </Card>
              ))}
            </div>
          </section>
        )}
      </div>
    </>
  );
}

