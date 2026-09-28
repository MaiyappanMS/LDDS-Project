import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth, homeFor } from '../context/AuthContext';
import { PageSkeleton } from '../components/ui/Skeleton';

export function ProtectedRoute() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  if (loading) return <div className="p-8"><PageSkeleton /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location }} />;
  return <Outlet />;
}

// UI-level convenience only. The backend remains the authority on permissions.
export function RoleProtectedRoute({ role }) {
  const { role: current } = useAuth();
  if (current !== role) return <Navigate to={homeFor(current)} replace />;
  return <Outlet />;
}
