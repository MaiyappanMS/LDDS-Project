import { Link } from 'react-router-dom';
import PageHeader from '../components/layout/PageHeader';
import Card, { CardTitle } from '../components/ui/Card';
import Async from '../components/ui/Async';
import { useAuth } from '../context/AuthContext';
import { subjectApi } from '../api/subjectApi';
import { useApi } from '../hooks/useApi';

// Read-only: no profile-update endpoint is defined in the API spec.
export default function ProfilePage({ role }) {
  const { currentUser: u } = useAuth();
  const subjects = useApi('subjects', subjectApi.list);
  const isTeacher = role === 'TEACHER';
  const rows = [['Name', u.name], ['Email', u.email], ['College', u.college || 'Not provided']];
  return (
    <>
      <PageHeader title="Profile" />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardTitle>Account</CardTitle>
          <dl className="space-y-3 text-sm">{rows.map(([k, v]) => <div key={k} className="flex justify-between gap-4"><dt className="text-muted">{k}</dt><dd className="font-medium">{v}</dd></div>)}</dl>
        </Card>
        <Card>
          <CardTitle>{isTeacher ? 'Subjects managed' : 'Subjects'}</CardTitle>
          <Async state={subjects} skeleton={<div className="h-16" />} isEmpty={(d) => d.length === 0} empty={<p className="text-sm text-muted">No subjects yet.</p>}>
            {(list) => <ul className="space-y-2 text-sm">{list.map((s) => <li key={s.id}><Link className="text-brand hover:underline" to={isTeacher ? `/teacher/subjects/${s.id}` : `/student/subjects/${s.id}`}>{s.name}</Link></li>)}</ul>}
          </Async>
        </Card>
        {u.stats && !isTeacher && (
          <Card className="lg:col-span-2"><CardTitle>Assessment statistics</CardTitle>
            <dl className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">{Object.entries(u.stats).map(([k, v]) => <div key={k}><dt className="capitalize text-muted">{k.replace(/_/g, ' ')}</dt><dd className="text-xl font-bold">{String(v)}</dd></div>)}</dl>
          </Card>
        )}
      </div>
    </>
  );
}
