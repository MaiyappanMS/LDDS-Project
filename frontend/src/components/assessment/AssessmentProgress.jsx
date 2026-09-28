import ProgressBar from '../ui/ProgressBar';
export default function AssessmentProgress({ current, total, answered }) {
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm"><span>Question {current + 1} of {total}</span><span className="text-muted">{answered} answered</span></div>
      <ProgressBar tone="brand" value={Math.round(((current + 1) / total) * 100)} className="" />
    </div>
  );
}
