import { Layers } from 'lucide-react';
export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="hidden flex-col justify-between bg-brand p-10 text-white lg:flex">
        <div className="flex items-center gap-2 text-lg font-bold"><Layers className="h-5 w-5" aria-hidden />Learning Debt</div>
        <div>
          <p className="max-w-md text-3xl font-bold leading-tight">Find the concept gaps that quietly hold everything else back.</p>
          <p className="mt-3 max-w-md text-white/80">A weak foundation compounds. See what you are missing, what it affects, and what to learn first.</p>
        </div>
        <div />
      </div>
      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-bold">{title}</h1>
          <p className="mb-6 mt-1 text-muted">{subtitle}</p>
          {children}
        </div>
      </div>
    </div>
  );
}
