import { PageSkeleton } from './Skeleton';
import { ErrorState } from './States';

/** Handles loading / error / empty for a useApi() state. Never renders a blank screen. */
export default function Async({ state, children, skeleton, isEmpty, empty }) {
  if (state.loading && !state.data) return skeleton || <PageSkeleton />;
  if (state.error) return <ErrorState message={state.error} onRetry={state.reload} />;
  if (state.data == null) return null;
  if (isEmpty && isEmpty(state.data)) return empty;
  return children(state.data);
}
