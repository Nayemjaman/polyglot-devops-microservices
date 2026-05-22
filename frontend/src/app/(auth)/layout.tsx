import Link from "next/link";
import type { ReactNode } from "react";
import { Sparkles } from "lucide-react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="relative grid min-h-screen overflow-hidden lg:grid-cols-[0.92fr_1.08fr]">
      <div className="mesh-grid pointer-events-none absolute inset-0" />
      <section className="relative z-10 hidden border-r bg-slate-950 px-10 py-8 text-white lg:flex lg:flex-col">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-white text-slate-950">
            <Sparkles size={19} />
          </span>
          <span className="text-lg font-black">FinOps Mesh</span>
        </Link>
        <div className="mt-auto max-w-xl">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-teal-300">Secure workspace</p>
          <h1 className="mt-4 text-5xl font-black leading-tight">A clearer way to manage your money.</h1>
          <p className="mt-5 text-lg leading-8 text-white/70">
            Sign in to continue tracking budgets, spending, and reports from one focused workspace.
          </p>
        </div>
      </section>
      <section className="relative z-10 flex items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-md">{children}</div>
      </section>
    </main>
  );
}
