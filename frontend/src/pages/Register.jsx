import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import AuthLayout from './AuthLayout';
import { Field, Select } from '../components/ui/Input';
import Button from '../components/ui/Button';
import { authApi } from '../api/authApi';
import { useAuth, homeFor } from '../context/AuthContext';
import { apiError } from '../api/client';
import { useToast } from '../context/ToastContext';

export default function Register() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm({ defaultValues: { role: 'STUDENT' } });

  const onSubmit = async ({ confirm, ...values }) => {
    setError('');
    try {
      await authApi.register(values);
    } catch (e) { return setError(apiError(e)); }
    try {
      const user = await login({ email: values.email, password: values.password, role: values.role });
      toast.success('Account created.');
      navigate(homeFor(user.role), { replace: true });
    } catch { toast.success('Account created. Sign in to continue.'); navigate('/login'); }
  };

  return (
    <AuthLayout title="Create your account" subtitle="It takes less than a minute.">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {error && <div role="alert" className="rounded-lg bg-sev-high-tint p-3 text-sm text-sev-high">{error}</div>}
        <Field label="Full name" autoComplete="name" error={errors.name?.message} {...register('name', { required: 'Enter your name' })} />
        <Field label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email', { required: 'Enter your email' })} />
        <Field label="Password" type="password" autoComplete="new-password" error={errors.password?.message} {...register('password', { required: 'Enter a password', minLength: { value: 8, message: 'Use at least 8 characters' } })} />
        <Field label="Confirm password" type="password" autoComplete="new-password" error={errors.confirm?.message} {...register('confirm', { validate: (v) => v === watch('password') || 'Passwords do not match' })} />
        <Select label="Role" {...register('role')}><option value="STUDENT">Student</option><option value="TEACHER">Teacher</option></Select>
        <Field label="College" error={errors.college?.message} {...register('college')} />
        <Button type="submit" loading={isSubmitting} className="w-full">Create account</Button>
      </form>
      <p className="mt-4 text-sm text-muted">Already registered? <Link to="/login" className="font-medium text-brand hover:underline">Sign in</Link></p>
    </AuthLayout>
  );
}
