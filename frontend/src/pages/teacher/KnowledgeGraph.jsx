import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Network } from 'lucide-react';
import SubjectHeader from '../../components/layout/SubjectHeader';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import { Drawer } from '../../components/ui/Modal';
import { DifficultyBadge } from '../../components/ui/Badge';
import ConceptGraph from '../../components/concepts/ConceptGraph';
import { subjectApi } from '../../api/subjectApi';
import { useApi } from '../../hooks/useApi';

export default function KnowledgeGraph() {
  const { id } = useParams();
  const state = useApi(`graph:${id}`, () => subjectApi.graph(id), { ttl: 0 });
  const [selected, setSelected] = useState(null);
  return (
    <>
      <SubjectHeader subjectId={id} section="Knowledge graph" />
      <Async state={state} isEmpty={(g) => g.nodes.length === 0} empty={<EmptyState icon={Network} title="No concepts to graph yet" body="Upload a syllabus first. Prerequisite relationships appear here." />}>
        {(g) => {
          const node = g.nodes.find((n) => String(n.id) === String(selected));
          const name = (nid) => g.nodes.find((n) => String(n.id) === String(nid))?.name;
          const prereqs = node ? g.edges.filter((e) => String(e.target) === String(node.id)).map((e) => name(e.source)) : [];
          const deps = node ? g.edges.filter((e) => String(e.source) === String(node.id)).map((e) => name(e.target)) : [];
          const List = ({ items }) => items.length ? <ul className="mt-1 list-inside list-disc text-sm">{items.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="mt-1 text-sm text-muted">None</p>;
          return (
            <div>
              <p className="mb-2 text-sm text-muted">Arrows point from a prerequisite to the concept that depends on it. Scroll to zoom, drag to pan, select a node for details.</p>
              <div className="relative">
                <ConceptGraph graph={g} selectedId={selected} onSelect={setSelected} />
                <Drawer open={!!node} onClose={() => setSelected(null)} title={node?.name ?? ''}>
                  {node && (
                    <div className="space-y-4">
                      <DifficultyBadge difficulty={node.difficulty} />
                      {node.description && <p className="text-sm text-muted">{node.description}</p>}
                      <div><h4 className="text-sm font-semibold">Prerequisites</h4><List items={prereqs} /></div>
                      <div><h4 className="text-sm font-semibold">Dependent concepts</h4><List items={deps} /></div>
                    </div>
                  )}
                </Drawer>
              </div>
            </div>
          );
        }}
      </Async>
    </>
  );
}
