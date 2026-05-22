import Link from "next/link";
import { ArrowRight, BarChart3, CheckCircle2, Layers3, LockKeyhole, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FinanceTerminal } from "@/components/landing/finance-terminal";

const features = [
  {
    icon: Layers3,
    title: "Everything in one place",
    description: "View accounts, spending, budgets, and reports from one calm workspace."
  },
  {
    icon: BarChart3,
    title: "Decision ready",
    description: "Track cash flow, budget pressure, and exports from one responsive workspace."
  },
  {
    icon: LockKeyhole,
    title: "Session protected",
    description: "Your workspace stays private while you move between money tasks."
  }
];

const ticker = ["Monthly reports", "Smart budgets", "Secure sign in", "Quick summaries", "Spending trends", "Export center"];

export default function LandingPage() {
  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="mesh-grid pointer-events-none absolute inset-x-0 top-0 h-[720px]" />
      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-md bg-slate-950 text-white shadow-lg">
            <Sparkles size={19} />
          </span>
          <span className="text-lg font-black tracking-tight">FinOps Mesh</span>
        </Link>
        <nav className="hidden items-center gap-7 text-sm font-medium text-muted-foreground md:flex">
          <a href="#features" className="hover:text-foreground">Features</a>
          <a href="#platform" className="hover:text-foreground">Platform</a>
          <Link href="/login" className="hover:text-foreground">Login</Link>
        </nav>
        <Link href="/register">
          <Button className="hidden sm:inline-flex">Create account</Button>
        </Link>
      </header>

      <section className="relative z-10 mx-auto grid min-h-[calc(100vh-84px)] w-full max-w-7xl items-center gap-10 px-5 pb-16 pt-8 sm:px-8 lg:grid-cols-[1.02fr_0.98fr]">
        <div>
          <div className="mb-5 inline-flex items-center gap-2 rounded-md border bg-white/75 px-3 py-2 text-sm font-semibold text-teal-800 shadow-sm">
            <CheckCircle2 size={16} />
            Personal finance workspace
          </div>
          <h1 className="max-w-3xl text-balance text-5xl font-black leading-[1.02] tracking-normal text-slate-950 sm:text-6xl lg:text-7xl">
            FinOps Mesh
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-700">
            A polished place to understand spending, plan budgets, and keep your money decisions clear on every screen.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/register">
              <Button className="w-full sm:w-auto">
                Start free
                <ArrowRight size={17} />
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="secondary" className="w-full sm:w-auto">Sign in</Button>
            </Link>
          </div>
        </div>

        <FinanceTerminal />
      </section>

      <section id="platform" className="relative z-10 border-y bg-slate-950 py-4 text-white">
        <div className="overflow-hidden">
          <div className="flex w-max animate-ticker gap-3 whitespace-nowrap px-3">
            {[...ticker, ...ticker].map((item, index) => (
              <span key={`${item}-${index}`} className="rounded-md border border-white/10 bg-white/10 px-4 py-2 text-sm text-white/80">
                {item}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="relative z-10 mx-auto w-full max-w-7xl px-5 py-16 sm:px-8">
        <div className="grid gap-4 md:grid-cols-3">
          {features.map((feature) => (
            <article key={feature.title} className="rounded-lg border bg-white p-6 shadow-sm">
              <div className="mb-5 grid h-11 w-11 place-items-center rounded-md bg-teal-50 text-teal-700">
                <feature.icon size={22} />
              </div>
              <h2 className="text-xl font-bold">{feature.title}</h2>
              <p className="mt-3 leading-7 text-muted-foreground">{feature.description}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
