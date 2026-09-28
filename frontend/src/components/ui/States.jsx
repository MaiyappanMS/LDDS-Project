import { AlertTriangle, Inbox } from 'lucide-react';
import Button from './Button';
import Card from './Card';

export function EmptyState({ icon: Icon = Inbox, title, body, action }) {
  return (
    <Card className="flex flex-col items-center py-10 text-center">
      <Icon className="mb-3 h-8 w-8 text-muted" aria-hidden />
      <h3 className="font-semibold">{title}</h3>
      {body && <p className="mt-1 max-w-sm text-sm text-muted">{body}</p>}
      {action && <div className="mt-4">{action}</div>}
    </Card>
  );
}
export function ErrorState({ message = 'Something went wrong.', onRetry }) {
  return (
    <Card role="alert" className="flex flex-col items-center border border-sev-high/30 py-10 text-center">
      <AlertTriangle className="mb-3 h-8 w-8 text-sev-high" aria-hidden />
      <p className="max-w-md text-sm">{message}</p>
      {onRetry && <Button variant="secondary" className="mt-4" onClick={onRetry}>Try again</Button>}
    </Card>
  );
}
