import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { Plus, Sparkles, CheckCircle2 } from 'lucide-react';
import SubjectHeader from '../../components/layout/SubjectHeader';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import { ConfirmDialog } from '../../components/ui/Modal';
import ConceptList from '../../components/concepts/ConceptList';
import ConceptEditor from '../../components/concepts/ConceptEditor';
import { conceptApi } from '../../api/conceptApi';
import { subjectApi } from '../../api/subjectApi';
import { apiError } from '../../api/client';
import { useApi, invalidate } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

export default function ConceptReview() {
  const { id } = useParams();
  const toast = useToast();
  const subject = useApi(`subject:${id}`, () => subjectApi.get(id));
  const state = useApi(`concepts:${id}`, () => conceptApi.bySubject(id), { ttl: 0 });
  const [editor, setEditor] = useState({ open: false, concept: null });
  const [deleting, setDeleting] = useState(null);
  const [busy, setBusy] = useState(false);
  const [approving, setApproving] = useState(false);

  const refresh = async () => {
    invalidate(`concepts:${id}`);
    invalidate(`graph:${id}`);
    invalidate(`subject:${id}`);
    await Promise.all([state.reload(), subject.reload()]);
  };
  const remove = async () => {
    setBusy(true);
    try { await conceptApi.remove(deleting.id); toast.success('Concept deleted.'); setDeleting(null); await refresh(); }
    catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };
  const approve = async () => {
    setApproving(true);
    try {
      await subjectApi.approveGraph(id);
      toast.success('Concept graph approved for student assessments.');
      await refresh();
    } catch (e) { toast.error(apiError(e)); } finally { setApproving(false); }
  };
  const hasConcepts = (state.data?.length ?? 0) > 0;
  const isApproved = subject.data?.graphApproved;
  const add = (
    <div className="flex flex-wrap items-center gap-2">
      {hasConcepts && (
        isApproved
          ? <Badge tone="low" className="h-9 px-3 text-xs"><CheckCircle2 className="mr-1.5 h-3.5 w-3.5" aria-hidden />Graph approved</Badge>
          : <Button variant="secondary" icon={CheckCircle2} loading={approving} onClick={approve}>Approve graph</Button>
      )}
      <Button icon={Plus} onClick={() => setEditor({ open: true, concept: null })}>Add concept</Button>
    </div>
  );
  // Keep the open editor in sync with refreshed data.
  const current = editor.concept ? state.data?.find((c) => c.id === editor.concept.id) ?? editor.concept : null;

  return (
    <>
      <SubjectHeader subjectId={id} section="Concepts" actions={add} />
      <p className="mb-4 flex items-center gap-2 text-sm text-muted"><Sparkles className="h-4 w-4" aria-hidden />AI suggested these concepts and prerequisites. Correct anything that looks wrong.</p>

      <Async state={state} isEmpty={(d) => d.length === 0} empty={<EmptyState title="No concepts yet" body="Upload a syllabus to detect concepts, or add one manually." action={add} />}>
        {(list) => {
          const names = Object.fromEntries(list.map((c) => [c.id, c.name]));
          return (
            <>
              <Card className="p-2"><ConceptList concepts={list} names={names} onEdit={(c) => setEditor({ open: true, concept: c })} onDelete={setDeleting} /></Card>
              <ConceptEditor open={editor.open} concept={current} concepts={list} subjectId={id} onClose={() => setEditor({ open: false, concept: null })} onChanged={refresh} />
            </>
          );
        }}
      </Async>
      {/* Editor for the empty state */}
      {state.data?.length === 0 && <ConceptEditor open={editor.open} concept={null} concepts={[]} subjectId={id} onClose={() => setEditor({ open: false, concept: null })} onChanged={refresh} />}
      <ConfirmDialog open={!!deleting} onClose={() => setDeleting(null)} onConfirm={remove} loading={busy} title="Delete concept?" message={deleting ? `"${deleting.name}" and its prerequisite links will be removed. This cannot be undone.` : ''} />
    </>
  );
}
