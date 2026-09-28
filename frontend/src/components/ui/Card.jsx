export default function Card({ as: Tag = 'div', className = '', children, ...rest }) {
  return <Tag className={`rounded-card bg-surface p-5 shadow-card ${className}`} {...rest}>{children}</Tag>;
}
export const CardTitle = ({ children, hint }) => (
  <div className="mb-3 flex items-baseline justify-between gap-2">
    <h2 className="text-base font-semibold">{children}</h2>
    {hint && <span className="text-sm text-muted">{hint}</span>}
  </div>
);
