export const Skeleton = ({ className = '' }) => <div aria-hidden className={`animate-pulse rounded-lg bg-line/60 ${className}`} />;
export const PageSkeleton = () => (
  <div role="status" aria-label="Loading" className="space-y-4">
    <Skeleton className="h-8 w-1/3" />
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
    <Skeleton className="h-64" />
  </div>
);
