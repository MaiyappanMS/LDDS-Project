import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Wand2, Check } from 'lucide-react';
import SubjectHeader from '../../components/layout/SubjectHeader';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge, { DifficultyBadge } from '../../components/ui/Badge';
import { Select, Field } from '../../components/ui/Input';
import { EmptyState } from '../../components/ui/States';
import { conceptApi } from '../../api/conceptApi';
import { questionApi } from '../../api/questionApi';
import { apiError } from '../../api/client';
import { useApi } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

export default function Questions() {
  const { id } = useParams();
  const toast = useToast();
  const concepts = useApi(`concepts:${id}`, () => conceptApi.bySubject(id));
  const stored = useApi(`questions:${id}`, () => questionApi.bySubject(id), { ttl: 0 });
  const [generated, setGenerated] = useState(null);
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues: { count: 3, difficulty: 'mixed' } });

  const onSubmit = async (v) => {
    setGenerated(null);
    try {
      const list = await questionApi.generate({ subjectId: Number(id) || id, conceptId: Number(v.conceptId) || v.conceptId, count: Number(v.count), difficulty: v.difficulty });
      setGenerated(list);
      await stored.reload();
      toast.success(`Generated ${list.length} questions.`);
    } catch (e) { toast.error(apiError(e)); }
  };

  const questions = generated ?? stored.data;

  return (
    <>
      <SubjectHeader subjectId={id} section="Questions" />
      <Card className="mb-6">
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:items-end" noValidate>
          <Select label="Concept" error={errors.conceptId?.message} {...register('conceptId', { required: 'Choose a concept' })}>
            <option value="">{concepts.loading ? 'Loading concepts…' : 'Select concept'}</option>
            {concepts.data?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </Select>
          <Field label="Number of questions" type="number" min={1} max={20} error={errors.count?.message} {...register('count', { required: 'Enter a number', min: { value: 1, message: 'At least 1' }, max: { value: 20, message: 'At most 20' } })} />
          <Select label="Difficulty" {...register('difficulty')}><option value="mixed">Mixed</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></Select>
          <Button type="submit" icon={Wand2} loading={isSubmitting}>{isSubmitting ? 'Generating…' : 'Generate questions'}</Button>
        </form>
        {concepts.error && <p role="alert" className="mt-3 text-sm text-sev-high">{concepts.error}</p>}
        {isSubmitting && <p className="mt-3 text-sm text-muted" aria-live="polite">AI is writing questions. This can take a moment.</p>}
      </Card>
      {generated && (
        <div className="mb-3 flex items-center justify-between text-sm">
          <span className="font-medium text-muted">Showing {generated.length} newly generated question{generated.length === 1 ? '' : 's'}</span>
          <button type="button" className="font-medium text-brand hover:underline" onClick={() => setGenerated(null)}>Show all {stored.data?.length ?? ''} subject questions</button>
        </div>
      )}
      {questions && questions.length === 0 && <EmptyState title="No questions yet" body="Select a concept above and click Generate questions." />}
      <div className="space-y-4">
        {questions?.map((q, i) => (
          <Card key={q.id ?? i}>
            <div className="mb-2 flex flex-wrap items-center gap-2"><span className="text-sm text-muted">Question {i + 1}</span>{q.difficulty && <DifficultyBadge difficulty={q.difficulty} />}{q.conceptName && <Badge tone="brand" className="!normal-case">{q.conceptName}</Badge>}</div>
            <p className="font-medium">{q.text}</p>
            <ul className="mt-3 space-y-1.5">
              {q.options.map((o) => {
                const right = String(q.correct).trim() === o.key || String(q.correct).trim() === o.text;
                return <li key={o.key} className={`flex items-center gap-2 rounded-lg border px-3 py-2 text-sm ${right ? 'border-sev-low bg-sev-low-tint' : 'border-line'}`}><span className="font-semibold">{o.key}.</span>{o.text}{right && <Check className="ml-auto h-4 w-4 text-sev-low" aria-label="Correct answer" />}</li>;
              })}
            </ul>
            {q.explanation && <p className="mt-3 text-sm text-muted"><b className="text-ink">Explanation:</b> {q.explanation}</p>}
          </Card>
        ))}
      </div>
    </>
  );
}

