import Link from "next/link";
import type { ReactNode } from "react";
import { Sparkles } from "lucide-react";

type AuthCardProps = {
  title: string;
  description: string;
  footer: ReactNode;
  children: ReactNode;
};

export function AuthCard({ title, description, footer, children }: AuthCardProps) {
  return (
    <div className="glass-panel rounded-lg border p-5 shadow-panel sm:p-7">
      <Link href="/" className="mb-8 flex items-center gap-3 lg:hidden">
        <span className="grid h-10 w-10 place-items-center rounded-md bg-slate-950 text-white">
          <Sparkles size={18} />
        </span>
        <span className="text-lg font-black">FinOps Mesh</span>
      </Link>
      <div className="mb-7">
        <h1 className="text-3xl font-black tracking-normal">{title}</h1>
        <p className="mt-2 leading-7 text-muted-foreground">{description}</p>
      </div>
      {children}
      <div className="mt-6 text-center text-sm text-muted-foreground">{footer}</div>
    </div>
  );
}
