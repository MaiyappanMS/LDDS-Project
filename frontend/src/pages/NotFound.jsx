import { Link } from 'react-router-dom';
export default function NotFound() {
  return <div className="flex min-h-screen flex-col items-center justify-center gap-3 p-6 text-center"><h1 className="text-2xl font-bold">Page not found</h1><p className="text-muted">The page you are looking for does not exist.</p><Link to="/" className="font-medium text-brand hover:underline">Go home</Link></div>;
}
