import { NavLink } from 'react-router-dom';
import { NAV } from './navItems';
import { useAuth } from '../../context/AuthContext';

export default function MobileNav() {
  const { role } = useAuth();
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-30 flex border-t border-line bg-surface lg:hidden">
      {NAV[role].map(({ to, label, icon: Icon }) => (
        <NavLink key={to} to={to} className={({ isActive }) => `flex flex-1 flex-col items-center gap-0.5 py-2 text-xs ${isActive ? 'text-brand' : 'text-muted'}`}>
          <Icon className="h-5 w-5" aria-hidden />{label}
        </NavLink>
      ))}
    </nav>
  );
}
