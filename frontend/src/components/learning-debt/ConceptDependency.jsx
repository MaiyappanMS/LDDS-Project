import { Link } from 'react-router-dom';
import { ArrowDown } from 'lucide-react';

// Shows "this weak concept -> affects -> these concepts" so the impact is visible at a glance.
export default function ConceptDependency({ affected }) {
  if (!affected?.length) return null;
  return (
    <div>
      <div className="flex items-center gap-1 text-sm text-muted"><ArrowDown className="h-4 w-4" aria-hidden />Affects</div>
      <ul className="mt-2 flex flex-wrap gap-2">
        {affected.map((a, i) => (
          <li key={a.id ?? i}>
            {a.id != null ? <Link to={`/student/concepts/${a.id}`} className="rounded-lg border border-line bg-canvas px-3 py-1 text-sm hover:border-brand">{a.name ?? `Concept ${a.id}`}</Link>
              : <span className="rounded-lg border border-line bg-canvas px-3 py-1 text-sm">{a.name}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
