import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { Plus, BookOpen, Users } from 'lucide-react';
import PageHeader from '../../components/layout/PageHeader';
import Card from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Async from '../../components/ui/Async';
import { EmptyState } from '../../components/ui/States';
import { Modal } from '../../components/ui/Modal';
import { Field, Textarea } from '../../components/ui/Input';
import { subjectApi } from '../../api/subjectApi';
import { apiError } from '../../api/client';
import { useApi, invalidate } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

function CreateSubjectModal({ open, onClose }) {
  const navigate = useNavigate();
  const toast = useToast();
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();
  const onSubmit = async (values) => {
    try {
      const s = await subjectApi.create(values);
      invalidate('subjects');
      toast.success('Subject created.');
      reset();
      onClose();
      navigate(`/teacher/subjects/${s.id}`);
    } catch (e) { toast.error(apiError(e)); }
  };
  return (
    <Modal open={open} onClose={onClose} title="Create subject">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        <Field label="Subject name" error={errors.name?.message} {...register('name', { required: 'Enter a subject name' })} />
        <Textarea label="Description" {...register('description')} />
        <Field label="Semester" placeholder="e.g. 3" {...register('semester')} />
        <div className="flex justify-end gap-2"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button type="submit" loading={isSubmitting}>Create subject</Button></div>
      </form>
    </Modal>
  );
}

export default function Subjects() {
  const [open, setOpen] = useState(false);
  const state = useApi('subjects', subjectApi.list);
  const create = <Button icon={Plus} onClick={() => setOpen(true)}>Create subject</Button>;
  return (
    <>
      <PageHeader title="Subjects" subtitle="Each subject has its own syllabus, concepts, and assessments." actions={create} />
      <Async state={state} isEmpty={(d) => d.length === 0} empty={<EmptyState icon={BookOpen} title="No subjects yet" body="Create your first subject, then upload its syllabus." action={create} />}>
        {(subjects) => (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {subjects.map((s) => (
              <Link key={s.id} to={`/teacher/subjects/${s.id}`} className="group">
                <Card className="h-full transition-shadow group-hover:shadow-md">
                  <h2 className="font-semibold">{s.name}</h2>
                  <p className="mt-1 line-clamp-2 text-sm text-muted">{s.description || 'No description'}</p>
                  <div className="mt-4 flex items-center gap-4 text-sm text-muted">
                    {s.semester !== '' && <span>Semester {s.semester}</span>}
                    {s.studentCount != null && <span className="flex items-center gap-1"><Users className="h-4 w-4" aria-hidden />{s.studentCount}</span>}
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </Async>
      <CreateSubjectModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}
