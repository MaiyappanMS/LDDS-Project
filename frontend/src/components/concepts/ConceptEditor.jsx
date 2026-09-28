import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { X, Plus } from 'lucide-react';
import { Modal, ConfirmDialog } from '../ui/Modal';
import { Field, Select, Textarea } from '../ui/Input';
import Button from '../ui/Button';
import Badge from '../ui/Badge';
import { conceptApi } from '../../api/conceptApi';
import { apiError } from '../../api/client';
import { useToast } from '../../context/ToastContext';

const DIFFS = ['beginner', 'intermediate', 'advanced'];

// Create (concept = null) or edit a concept, including its prerequisite relationships.
export default function ConceptEditor({ open, onClose, concept, concepts, subjectId, onChanged }) {
  const toast = useToast();
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();
  const [prereqs, setPrereqs] = useState([]);
  const [toAdd, setToAdd] = useState('');
  const [removing, setRemoving] = useState(null);
  const [busy, setBusy] = useState(false);
  const names = Object.fromEntries(concepts.map((c) => [c.id, c.name]));

  useEffect(() => {
    if (!open) return;
    reset({ name: concept?.name ?? '', description: concept?.description ?? '', difficulty: DIFFS.includes(concept?.difficulty) ? concept.difficulty : 'beginner' });
    setPrereqs(concept?.prerequisites ?? []);
    setToAdd('');
  }, [open, concept, reset]);

  const save = async (values) => {
    try {
      if (concept) await conceptApi.update(concept.id, values);
      else await conceptApi.create({ ...values, subject_id: Number.isNaN(Number(subjectId)) ? subjectId : Number(subjectId) });
      toast.success(concept ? 'Concept updated.' : 'Concept added.');
      await onChanged();
      onClose();
    } catch (e) { toast.error(apiError(e)); }
  };

  const addPrereq = async () => {
    if (!toAdd) return;
    setBusy(true);
    try {
      await conceptApi.addPrerequisite(concept.id, Number(toAdd));
      setPrereqs((p) => [...p, { id: Number(toAdd), name: names[toAdd] }]);
      setToAdd('');
      toast.success('Prerequisite added.');
      onChanged();
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const removePrereq = async () => {
    setBusy(true);
    try {
      await conceptApi.removePrerequisite(concept.id, removing.id);
      setPrereqs((p) => p.filter((x) => x.id !== removing.id));
      setRemoving(null);
      toast.success('Prerequisite removed.');
      onChanged();
    } catch (e) { toast.error(apiError(e)); } finally { setBusy(false); }
  };

  const options = concepts.filter((c) => c.id !== concept?.id && !prereqs.some((p) => p.id === c.id));

  return (
    <>
      <Modal open={open} onClose={onClose} title={concept ? 'Edit concept' : 'Add concept'}>
        <form onSubmit={handleSubmit(save)} className="space-y-4">
          <Field label="Name" error={errors.name?.message} {...register('name', { required: 'Enter a concept name' })} />
          <Textarea label="Description" {...register('description')} />
          <Select label="Difficulty" {...register('difficulty')}>{DIFFS.map((d) => <option key={d} value={d} className="capitalize">{d}</option>)}</Select>

          {concept && (
            <div>
              <p className="mb-1 text-sm font-medium">Prerequisites</p>
              <div className="mb-2 flex flex-wrap gap-2">
                {prereqs.length === 0 && <span className="text-sm text-muted">None</span>}
                {prereqs.map((p) => (
                  <Badge key={p.id} tone="brand" className="gap-1 !normal-case">{p.name ?? names[p.id] ?? p.id}
                    <button type="button" aria-label={`Remove prerequisite ${p.name ?? names[p.id]}`} onClick={() => setRemoving(p)}><X className="h-3 w-3" /></button>
                  </Badge>
                ))}
              </div>
              <div className="flex gap-2">
                <select aria-label="Add prerequisite" value={toAdd} onChange={(e) => setToAdd(e.target.value)} className="h-10 flex-1 rounded-lg border border-line bg-surface px-3 text-sm">
                  <option value="">Choose a concept…</option>
                  {options.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                <Button variant="secondary" icon={Plus} loading={busy} disabled={!toAdd} onClick={addPrereq}>Add</Button>
              </div>
            </div>
          )}
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="secondary" onClick={onClose}>Cancel</Button>
            <Button type="submit" loading={isSubmitting}>{concept ? 'Save changes' : 'Add concept'}</Button>
          </div>
        </form>
      </Modal>
      <ConfirmDialog open={!!removing} onClose={() => setRemoving(null)} onConfirm={removePrereq} loading={busy} confirmLabel="Remove" title="Remove prerequisite?"
        message={removing ? `"${concept?.name}" will no longer depend on "${removing.name ?? names[removing.id]}".` : ''} />
    </>
  );
}
