import Card, { CardTitle } from '../ui/Card';
import Badge, { DifficultyBadge } from '../ui/Badge';

// result: raw syllabus record from the upload/poll response (may carry extracted text and status).
export default function SyllabusAnalysis({ result, concepts }) {
  const text = result?.extracted_text ?? result?.text ?? result?.content;
  const status = result?.status ?? result?.processing_status;
  const nameOf = Object.fromEntries(concepts.map((c) => [c.id, c.name]));
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2"><h2 className="text-lg font-semibold">Syllabus analysis</h2><Badge tone="low">{status ? String(status) : 'Analysis complete'}</Badge></div>
      {text && <Card><CardTitle>Extracted syllabus text</CardTitle><pre className="max-h-64 overflow-auto whitespace-pre-wrap text-sm text-muted">{text}</pre></Card>}
      <Card>
        <CardTitle hint={`${concepts.length} found`}>Detected concepts</CardTitle>
        <ul className="divide-y divide-line">
          {concepts.map((c) => (
            <li key={c.id} className="flex flex-wrap items-start justify-between gap-2 py-3">
              <div>
                <p className="font-medium">{c.name}</p>
                {c.prerequisites.length > 0 && <p className="mt-0.5 text-sm text-muted">Prerequisite{c.prerequisites.length > 1 ? 's' : ''}: {c.prerequisites.map((p) => p.name ?? nameOf[p.id] ?? p.id).join(', ')}</p>}
              </div>
              <DifficultyBadge difficulty={c.difficulty} />
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
