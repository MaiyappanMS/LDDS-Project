import { NavLink } from 'react-router-dom';
export default function Tabs({ items }) {
  return (
    <nav aria-label="Sections" className="-mx-1 mb-6 flex gap-1 overflow-x-auto border-b border-line px-1">
      {items.map((t) => (
        <NavLink key={t.to} to={t.to} end={t.end} className={({ isActive }) => `whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium ${isActive ? 'border-brand text-brand' : 'border-transparent text-muted hover:text-ink'}`}>{t.label}</NavLink>
      ))}
    </nav>
  );
}
