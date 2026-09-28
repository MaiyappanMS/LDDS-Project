import { Link } from 'react-router-dom';
import { Users, BookOpen, Gauge, AlertTriangle, ClipboardCheck } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Card, { CardTitle } from '../../components/ui/Card';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import { Table, Th, Td } from '../../components/ui/Table';
import ConceptPerformanceChart from '../../components/charts/ConceptPerformanceChart';
import MasteryChart from '../../components/charts/MasteryChart';
import DebtChart from '../../components/charts/DebtChart';
import ProgressBar from '../../components/ui/ProgressBar';
import { formatDate } from '../../components/ui/tone';
import { learningDebtApi } from '../../api/learningDebtApi';
import { subjectApi } from '../../api/subjectApi';
import { useApi } from '../../hooks/useApi';

const Stat = ({ icon: Icon, label, value }) => (
  <Card>
    <div className="flex items-center gap-2 text-sm text-muted"><Icon className="h-4 w-4" aria-hidden />{label}</div>
    <div className="mt-2 text-3xl font-bold tabular-nums">{value}</div>
  </Card>
);

export default function TeacherDashboard() {
  const state = useApi('overview:teacher', async () => {
    const [overview, subjects] = await Promise.all([learningDebtApi.teacherOverview(), subjectApi.list().catch(() => null)]);
    return { o: overview, subjects };
  });
  return (
    <>
      <PageHeader title="Teacher dashboard" subtitle="How your classes are doing, and where the biggest gaps are." actions={<Link to="/teacher/subjects" className="inline-flex h-10 items-center rounded-lg bg-brand px-4 text-sm font-medium text-white hover:bg-brand-dark">Manage subjects</Link>} />
      <Async state={state}>
        {({ o, subjects }) => {
          const stats = [
            { icon: Users, label: 'Total students', value: o.totalStudents },
            { icon: BookOpen, label: 'Total subjects', value: o.totalSubjects ?? subjects?.length },
            { icon: Gauge, label: 'Average mastery', value: o.avgMastery != null ? `${o.avgMastery}%` : null },
            { icon: AlertTriangle, label: 'Students with high debt', value: o.highDebtStudents },
            { icon: ClipboardCheck, label: 'Assessments taken', value: o.assessmentCount },
          ].filter((s) => s.value != null);
          const perf = o.concepts.length ? o.concepts : o.weakConcepts;
          const hasAnything = stats.length || perf.length || o.debtDistribution || o.studentPerformance.length || o.recent.length;
          if (!hasAnything) return <EmptyState title="No class data yet" body="Create a subject, upload a syllabus, and have students take an assessment to see results here." />;
          return (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">{stats.map((s) => <Stat key={s.label} {...s} />)}</div>
              <div className="grid gap-6 lg:grid-cols-3">
                {perf.length > 0 && <Card className="lg:col-span-2"><CardTitle hint="Lowest first">Concept performance</CardTitle><ConceptPerformanceChart data={perf} /></Card>}
                {o.debtDistribution && <Card><CardTitle>Learning debt distribution</CardTitle><DebtChart distribution={o.debtDistribution} /></Card>}
              </div>
              <div className="grid gap-6 lg:grid-cols-2">
                {o.weakConcepts.length > 0 && (
                  <Card><CardTitle>Weakest concepts</CardTitle><div className="space-y-3">{o.weakConcepts.map((c) => <ProgressBar key={c.id ?? c.name} label={c.name} value={c.mastery} showValue />)}</div></Card>
                )}
                {o.studentPerformance.length > 0 && <Card><CardTitle>Student performance</CardTitle><MasteryChart data={o.studentPerformance} /></Card>}
              </div>
              {o.recent.length > 0 && (
                <Card>
                  <CardTitle>Recent assessments</CardTitle>
                  <Table><thead><tr><Th>Student</Th><Th>Subject</Th><Th>Score</Th><Th>Date</Th></tr></thead>
                    <tbody>{o.recent.map((r, i) => <tr key={r.id ?? i}><Td>{r.student}</Td><Td>{r.subject}</Td><Td className="tabular-nums">{r.score != null ? `${r.score}%` : '–'}</Td><Td>{formatDate(r.date)}</Td></tr>)}</tbody></Table>
                </Card>
              )}
            </div>
          );
        }}
      </Async>
    </>
  );
}
