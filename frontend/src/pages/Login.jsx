import { useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import AuthLayout from './AuthLayout';
import { Field, Select } from '../components/ui/Input';
import Button from '../components/ui/Button';
import { useAuth, homeFor } from '../context/AuthContext';
import { apiError } from '../api/client';

export default function Login() {
  const { login, isAuthenticated, role } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [error, setError] = useState(params.get('expired') ? 'Your session has expired. Sign in again.' : '');
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues: { role: 'STUDENT' } });

  if (isAuthenticated) return <Navigate to={homeFor(role)} replace />;

  const onSubmit = async (values) => {
    setError('');
    try {
      const user = await login(values);
      navigate(homeFor(user.role), { replace: true });
    } catch (e) { setError(e.message?.startsWith('Login response') ? e.message : apiError(e)); }
  };

  return (
    <AuthLayout title="Sign in" subtitle="Continue to your dashboard.">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {error && <div role="alert" className="rounded-lg bg-sev-high-tint p-3 text-sm text-sev-high">{error}</div>}
        <Field label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email', { required: 'Enter your email' })} />
        <Field label="Password" type="password" autoComplete="current-password" error={errors.password?.message} {...register('password', { required: 'Enter your password' })} />
        <Select label="I am a" {...register('role')}><option value="STUDENT">Student</option><option value="TEACHER">Teacher</option></Select>
        <Button type="submit" loading={isSubmitting} className="w-full">Sign in</Button>
      </form>
      <p className="mt-4 text-sm text-muted">No account yet? <Link to="/register" className="font-medium text-brand hover:underline">Create one</Link></p>
    </AuthLayout>
  );
}
