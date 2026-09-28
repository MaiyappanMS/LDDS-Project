import MasteryChart from './MasteryChart';
export default function ConceptPerformanceChart({ data }) {
  return <MasteryChart data={[...data].sort((a, b) => a.mastery - b.mastery)} layout="horizontal" />;
}
