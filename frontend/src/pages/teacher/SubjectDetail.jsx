import { Link, useParams } from 'react-router-dom';
import { Upload, Users, Layers } from 'lucide-react';
import SubjectHeader from '../../components/layout/SubjectHeader';
import Card, { CardTitle } from '../../components/ui/Card';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import { Table, Th, Td } from '../../components/ui/Table';
import { DifficultyBadge } from '../../components/ui/Badge';
import { subjectApi } from '../../api/subjectApi';
import { conceptApi } from '../../api/conceptApi';
import { useApi } from '../../hooks/useApi';

export default function SubjectDetail() {
  const { id } = useParams();
  const subject = useApi(`subject:${id}`, () => subjectApi.get(id));
  const concepts = useApi(`concepts:${id}`, () => conceptApi.bySubject(id));
  return (
    <>
      <SubjectHeader subjectId={id} />
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardTitle hint={concepts.data ? `${concepts.data.length} concepts` : ''}>Syllabus concepts</CardTitle>
          <Async state={concepts} skeleton={<div className="h-24" />} isEmpty={(d) => d.length === 0}
            empty={<EmptyState icon={Upload} title="No syllabus has been uploaded yet." body="Upload a syllabus and AI will detect its concepts." action={<Link className="text-sm font-medium text-brand hover:underline" to={`/teacher/subjects/${id}/syllabus`}>Upload syllabus</Link>} />}>
            {(list) => (
              <ul className="divide-y divide-line">
                {list.slice(0, 8).map((c) => <li key={c.id} className="flex items-center justify-between py-2"><span>{c.name}</span><DifficultyBadge difficulty={c.difficulty} /></li>)}
                {list.length > 8 && <li className="pt-3 text-sm"><Link to={`/teacher/subjects/${id}/concepts`} className="text-brand hover:underline">View all {list.length}</Link></li>}
              </ul>
            )}
          </Async>
        </Card>
        <Card>
          <CardTitle>Assessment statistics</CardTitle>
          <Async state={subject} skeleton={<div className="h-24" />}>
            {(s) => s.stats && Object.keys(s.stats).length
              ? <dl className="space-y-2 text-sm">{Object.entries(s.stats).map(([k, v]) => <div key={k} className="flex justify-between"><dt className="capitalize text-muted">{k.replace(/_/g, ' ')}</dt><dd className="font-medium tabular-nums">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</dd></div>)}</dl>
              : <p className="text-sm text-muted">No assessments have been taken yet.</p>}
          </Async>
        </Card>
        <Card className="lg:col-span-3">
          <CardTitle hint="Enrolled students"><span className="inline-flex items-center gap-2"><Users className="h-4 w-4" aria-hidden />Students</span></CardTitle>
          <Async state={subject} skeleton={<div className="h-16" />} isEmpty={(s) => s.students.length === 0} empty={<p className="text-sm text-muted">No students are enrolled yet.</p>}>
            {(s) => <Table><thead><tr><Th>Name</Th><Th>Email</Th><Th>Mastery</Th></tr></thead><tbody>{s.students.map((u) => <tr key={u.id}><Td>{u.name}</Td><Td>{u.email}</Td><Td className="tabular-nums">{u.mastery != null ? `${u.mastery}%` : '–'}</Td></tr>)}</tbody></Table>}
          </Async>
        </Card>
      </div>
      <div className="mt-6 flex flex-wrap gap-3 text-sm">
        <Link className="inline-flex items-center gap-2 font-medium text-brand hover:underline" to={`/teacher/subjects/${id}/knowledge-graph`}><Layers className="h-4 w-4" aria-hidden />Open knowledge graph</Link>
      </div>
    </>
  );
}
