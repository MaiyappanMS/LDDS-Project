import { Pencil, Trash2 } from 'lucide-react';
import { Table, Th, Td } from '../ui/Table';
import Badge, { DifficultyBadge } from '../ui/Badge';
import Button from '../ui/Button';

// Teacher review table. names: id -> concept name, to resolve prerequisite ids.
export default function ConceptList({ concepts, names, onEdit, onDelete }) {
  return (
    <Table>
      <thead><tr><Th>Concept</Th><Th>Difficulty</Th><Th>Prerequisites</Th><Th>Status</Th><Th><span className="sr-only">Actions</span></Th></tr></thead>
      <tbody>
        {concepts.map((c) => (
          <tr key={c.id}>
            <Td><div className="font-medium">{c.name}</div>{c.description && <p className="mt-0.5 max-w-sm text-xs text-muted">{c.description}</p>}</Td>
            <Td><DifficultyBadge difficulty={c.difficulty} /></Td>
            <Td>{c.prerequisites.length ? <div className="flex flex-wrap gap-1">{c.prerequisites.map((p) => <Badge key={p.id} tone="brand">{p.name ?? names[p.id] ?? p.id}</Badge>)}</div> : <span className="text-muted">None</span>}</Td>
            <Td><Badge>{c.status}</Badge></Td>
            <Td className="whitespace-nowrap text-right">
              <Button size="sm" variant="ghost" icon={Pencil} aria-label={`Edit ${c.name}`} onClick={() => onEdit(c)} />
              <Button size="sm" variant="ghost" icon={Trash2} aria-label={`Delete ${c.name}`} onClick={() => onDelete(c)} />
            </Td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
