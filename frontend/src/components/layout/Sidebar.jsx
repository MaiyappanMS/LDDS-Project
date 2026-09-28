import { NavLink } from 'react-router-dom';
import { Layers, LogOut } from 'lucide-react';
import { NAV } from './navItems';
import { useAuth } from '../../context/AuthContext';

export default function Sidebar() {
  const { role, currentUser, logout } = useAuth();
  return (
    <aside className="fixed inset-y-0 left-0 hidden w-60 flex-col border-r border-line bg-surface p-4 lg:flex">
      <div className="mb-8 flex items-center gap-2 px-2 text-lg font-bold"><Layers className="h-5 w-5 text-brand" aria-hidden />Learning Debt</div>
      <nav aria-label="Main" className="flex-1 space-y-1">
        {NAV[role].map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-brand-tint text-brand' : 'text-muted hover:bg-canvas hover:text-ink'}`}>
            <Icon className="h-4 w-4" aria-hidden />{label}
          </NavLink>
        ))}
      </nav>
      <div className="border-t border-line pt-3">
        <p className="truncate px-2 text-sm font-medium">{currentUser?.name}</p>
        <p className="truncate px-2 text-xs capitalize text-muted">{role?.toLowerCase()}</p>
        <button onClick={logout} className="mt-2 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm text-muted hover:bg-canvas hover:text-ink"><LogOut className="h-4 w-4" aria-hidden />Sign out</button>
      </div>
    </aside>
  );
}
