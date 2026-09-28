import { subjectApi } from '../../api/subjectApi';
import { useApi } from '../../hooks/useApi';
import PageHeader from './PageHeader';
import Tabs from '../ui/Tabs';

// Shared header + section tabs for every /teacher/subjects/:id/* page.
export default function SubjectHeader({ subjectId, section, actions }) {
  const { data: subject } = useApi(`subject:${subjectId}`, () => subjectApi.get(subjectId));
  const base = `/teacher/subjects/${subjectId}`;
  return (
    <>
      <PageHeader
        title={subject?.name ?? 'Subject'}
        subtitle={subject?.description}
        crumbs={[{ label: 'Subjects', to: '/teacher/subjects' }, { label: subject?.name ?? 'Subject', to: section ? base : undefined }, ...(section ? [{ label: section }] : [])]}
        actions={actions}
      />
      <Tabs items={[
        { to: base, label: 'Overview', end: true },
        { to: `${base}/syllabus`, label: 'Syllabus' },
        { to: `${base}/concepts`, label: 'Concepts' },
        { to: `${base}/knowledge-graph`, label: 'Knowledge graph' },
        { to: `${base}/questions`, label: 'Questions' },
      ]} />
    </>
  );
}
