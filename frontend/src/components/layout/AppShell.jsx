import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import MobileNav from './MobileNav';

// Used for both /teacher/* and /student/*; nav items come from the signed-in role.
export default function AppShell() {
  return (
    <div className="min-h-screen">
      <Sidebar />
      <div className="lg:pl-60">
        <Topbar />
        <main className="mx-auto max-w-6xl px-4 pb-24 pt-6 lg:px-8 lg:pb-10"><Outlet /></main>
      </div>
      <MobileNav />
    </div>
  );
}
