import { useParams } from 'react-router-dom';
import { Route } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import LearningPath from '../../components/learning-debt/LearningPath';
import { learningDebtApi } from '../../api/learningDebtApi';
import { useApi } from '../../hooks/useApi';

export default function LearningPathPage() {
  const { id } = useParams();
  const state = useApi(`path:${id}`, () => learningDebtApi.path(id));
  return (
    <>
      <PageHeader title="Your learning path" subtitle="Work through these in order. Each step unlocks the ones after it."
        crumbs={[{ label: 'Dashboard', to: '/student/dashboard' }, { label: 'Subject', to: `/student/subjects/${id}` }, { label: 'Learning path' }]} />
      <Async state={state} isEmpty={(d) => d.length === 0} empty={<EmptyState icon={Route} title="No learning path yet" body="Take an assessment and your personalised path will appear here." />}>
        {(steps) => <LearningPath steps={steps} />}
      </Async>
    </>
  );
}
