import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Send } from 'lucide-react';
import Async from '../../components/ui/Async';
import Button from '../../components/ui/Button';
import Card, { CardTitle } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/States';
import { ConfirmDialog } from '../../components/ui/Modal';
import QuestionCard from '../../components/assessment/QuestionCard';
import QuestionNavigator from '../../components/assessment/QuestionNavigator';
import AssessmentProgress from '../../components/assessment/AssessmentProgress';
import { assessmentApi } from '../../api/assessmentApi';
import { apiError } from '../../api/client';
import { useApi, invalidate } from '../../hooks/useApi';
import { useToast } from '../../context/ToastContext';

function Quiz({ id, questions }) {
  const navigate = useNavigate();
  const toast = useToast();
  const storeKey = `ldds_answers_${id}`;
  const [current, setCurrent] = useState(0);
  const [answers, setAnswers] = useState(() => { try { return JSON.parse(sessionStorage.getItem(storeKey)) || {}; } catch { return {}; } });
  const [confirm, setConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const lock = useRef(false); // blocks duplicate submissions even on fast double taps

  useEffect(() => { sessionStorage.setItem(storeKey, JSON.stringify(answers)); }, [answers, storeKey]);

  const q = questions[current];
  const answered = questions.filter((x) => answers[x.id] != null).length;
  const last = current === questions.length - 1;

  const submit = async () => {
    if (lock.current) return;
    lock.current = true; setSubmitting(true);
    try {
      await assessmentApi.submit(id, answers);
      sessionStorage.removeItem(storeKey);
      invalidate('overview'); invalidate('debt'); invalidate('assessment');
      navigate(`/student/assessment/${id}/result`, { replace: true });
    } catch (e) {
      toast.error(apiError(e));
      lock.current = false; setSubmitting(false); setConfirm(false);
    }
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_260px]">
      <div className="space-y-4">
        <AssessmentProgress current={current} total={questions.length} answered={answered} />
        <QuestionCard question={q} index={current} total={questions.length} selected={answers[q.id]} onSelect={(k) => setAnswers((a) => ({ ...a, [q.id]: k }))} />
        <div className="flex justify-between gap-3">
          <Button variant="secondary" icon={ChevronLeft} disabled={current === 0} onClick={() => setCurrent((c) => c - 1)}>Previous</Button>
          {last ? <Button icon={Send} onClick={() => setConfirm(true)}>Submit assessment</Button>
            : <Button onClick={() => setCurrent((c) => c + 1)}>Next<ChevronRight className="h-4 w-4" aria-hidden /></Button>}
        </div>
      </div>
      <Card className="h-fit">
        <CardTitle>Questions</CardTitle>
        <QuestionNavigator questions={questions} current={current} answers={answers} onJump={setCurrent} />
        <Button variant="secondary" className="mt-4 w-full" onClick={() => setConfirm(true)}>Review and submit</Button>
      </Card>
      <ConfirmDialog open={confirm} onClose={() => !submitting && setConfirm(false)} onConfirm={submit} loading={submitting} confirmLabel="Submit answers" title="Submit assessment?"
        message={answered < questions.length ? `You have ${questions.length - answered} unanswered question${questions.length - answered === 1 ? '' : 's'}. You cannot change your answers after submitting.` : 'You cannot change your answers after submitting.'} />
    </div>
  );
}

export default function Assessment() {
  const { id } = useParams();
  const state = useApi(`assessment-q:${id}`, () => assessmentApi.questions(id), { ttl: 0 });
  return (
    <Async state={state} isEmpty={(d) => d.length === 0} empty={<EmptyState title="This assessment has no questions" body="Ask your teacher to generate questions for this subject." />}>
      {(qs) => <Quiz id={id} questions={qs} />}
    </Async>
  );
}
