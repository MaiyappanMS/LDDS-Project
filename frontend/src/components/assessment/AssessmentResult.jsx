import Card, { CardTitle } from '../ui/Card';
import ProgressBar from '../ui/ProgressBar';
import MasteryChart from '../charts/MasteryChart';

const Stat = ({ label, value }) => (
  <Card><div className="text-3xl font-bold tabular-nums">{value}</div><div className="mt-1 text-sm text-muted">{label}</div></Card>
);

export default function AssessmentResult({ result }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Score" value={`${result.score}%`} />
        <Stat label="Overall mastery" value={result.overallMastery != null ? `${result.overallMastery}%` : '–'} />
        <Stat label="Correct" value={result.correct} />
        <Stat label="Incorrect" value={result.incorrect} />
      </div>
      {result.concepts.length > 0 && (
        <Card>
          <CardTitle>Concept-level performance</CardTitle>
          <div className="mb-4 space-y-3">{result.concepts.map((c) => <ProgressBar key={c.id ?? c.name} label={c.name} value={c.mastery} showValue />)}</div>
          <MasteryChart data={result.concepts} />
        </Card>
      )}
    </div>
  );
}
