import { useMemo } from 'react';
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import { TONE_HEX, masteryTone, difficultyTone } from '../ui/tone';

// Layered left-to-right layout: a node sits one column right of its deepest prerequisite.
function layout(nodes, edges) {
  const ids = new Set(nodes.map((n) => n.id));
  const preds = new Map(nodes.map((n) => [n.id, []]));
  edges.forEach((e) => ids.has(e.source) && preds.get(e.target)?.push(e.source));
  const depth = new Map();
  const visit = (id, stack = new Set()) => {
    if (depth.has(id)) return depth.get(id);
    if (stack.has(id)) return 0; // cycle guard
    stack.add(id);
    const d = Math.max(-1, ...(preds.get(id) || []).map((p) => visit(p, stack))) + 1;
    stack.delete(id);
    depth.set(id, d);
    return d;
  };
  nodes.forEach((n) => visit(n.id));
  const rows = {};
  return nodes.map((n) => {
    const d = depth.get(n.id);
    rows[d] = (rows[d] ?? -1) + 1;
    return { n, x: d * 270, y: rows[d] * 110 };
  });
}

export default function ConceptGraph({ graph, selectedId, onSelect, height = 520 }) {
  const { nodes, edges } = useMemo(() => {
    const placed = layout(graph.nodes, graph.edges);
    const nodes = placed.map(({ n, x, y }) => {
      const tone = n.mastery != null ? masteryTone(n.mastery) : difficultyTone(n.difficulty);
      const color = TONE_HEX[tone] || '#5B6779';
      return {
        id: String(n.id),
        position: { x, y },
        data: { label: (
          <div className="text-left">
            <div className="text-sm font-semibold">{n.name}</div>
            <div className="text-xs text-muted capitalize">{n.difficulty}{n.mastery != null ? ` · ${n.mastery}% mastery` : ''}</div>
          </div>
        ) },
        style: { width: 210, borderRadius: 10, padding: 10, background: '#fff', border: `2px solid ${color}`, boxShadow: String(selectedId) === String(n.id) ? '0 0 0 3px rgba(47,75,143,0.35)' : 'none' },
        draggable: false,
      };
    });
    const edges = graph.edges.map((e, i) => {
      const active = selectedId != null && (String(e.source) === String(selectedId) || String(e.target) === String(selectedId));
      return { id: `e${i}`, source: String(e.source), target: String(e.target), markerEnd: { type: MarkerType.ArrowClosed, color: active ? '#2F4B8F' : '#9AA5B5' }, style: { stroke: active ? '#2F4B8F' : '#9AA5B5', strokeWidth: active ? 2.5 : 1.5 } };
    });
    return { nodes, edges };
  }, [graph, selectedId]);

  return (
    <div style={{ height }} className="overflow-hidden rounded-card border border-line bg-surface" role="group" aria-label="Knowledge graph of concepts and prerequisites">
      <ReactFlow nodes={nodes} edges={edges} fitView minZoom={0.2} nodesDraggable={false} nodesConnectable={false} onNodeClick={(_, node) => onSelect?.(node.id)} onPaneClick={() => onSelect?.(null)} proOptions={{ hideAttribution: true }}>
        <Background color="#DDE2EA" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
