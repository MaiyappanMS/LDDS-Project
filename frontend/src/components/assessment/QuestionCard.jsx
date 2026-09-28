import Card from '../ui/Card';

export default function QuestionCard({ question, index, total, selected, onSelect }) {
  return (
    <Card>
      <fieldset>
        <legend className="mb-4 text-sm text-muted">Question {index + 1} of {total}</legend>
        <p className="mb-5 text-lg font-medium leading-snug">{question.text}</p>
        <div className="space-y-2">
          {question.options.map((o) => {
            const on = selected === o.key;
            return (
              <label key={o.key} className={`flex min-h-[52px] cursor-pointer items-center gap-3 rounded-lg border p-3 transition-colors ${on ? 'border-brand bg-brand-tint' : 'border-line hover:border-brand/50'}`}>
                <input type="radio" name={`q-${question.id}`} value={o.key} checked={on} onChange={() => onSelect(o.key)} className="sr-only" />
                <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${on ? 'bg-brand text-white' : 'bg-canvas text-muted'}`}>{o.key}</span>
                <span className="text-sm sm:text-base">{o.text}</span>
              </label>
            );
          })}
        </div>
      </fieldset>
    </Card>
  );
}
