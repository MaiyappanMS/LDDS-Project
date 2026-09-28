import { Link } from 'react-router-dom';
import ProgressBar from '../ui/ProgressBar';
export default function ConceptCard({ concept }) {
  return (
    <Link to={`/student/concepts/${concept.id}`} className="block rounded-lg border border-line bg-surface p-3 hover:border-brand">
      <div className="mb-2 text-sm font-medium">{concept.name}</div>
      <ProgressBar value={concept.mastery} showValue />
    </Link>
  );
}
