export default function QuestionNavigator({ questions, current, answers, onJump }) {
  return (
    <nav aria-label="Question navigator" className="grid grid-cols-5 gap-2 sm:grid-cols-8 lg:grid-cols-5">
      {questions.map((q, i) => {
        const done = answers[q.id] != null;
        return (
          <button key={q.id} onClick={() => onJump(i)} aria-label={`Question ${i + 1}${done ? ', answered' : ', not answered'}`} aria-current={i === current ? 'step' : undefined}
            className={`h-10 rounded-lg border text-sm font-medium ${i === current ? 'border-brand ring-2 ring-brand/30' : 'border-line'} ${done ? 'bg-brand text-white' : 'bg-surface text-ink'}`}>{i + 1}</button>
        );
      })}
    </nav>
  );
}
