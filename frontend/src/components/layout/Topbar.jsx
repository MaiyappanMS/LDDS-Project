import { Layers, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export default function Topbar() {
  const { currentUser, logout } = useAuth();
  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-surface/95 px-4 backdrop-blur lg:px-8">
      <div className="flex items-center gap-2 font-bold lg:hidden"><Layers className="h-5 w-5 text-brand" aria-hidden />Learning Debt</div>
      <p className="hidden text-sm text-muted lg:block">Signed in as <span className="font-medium text-ink">{currentUser?.name}</span></p>
      <button onClick={logout} aria-label="Sign out" className="rounded-lg p-2 text-muted hover:bg-canvas lg:hidden"><LogOut className="h-4 w-4" /></button>
    </header>
  );
}
