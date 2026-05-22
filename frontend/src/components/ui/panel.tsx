import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

type PanelProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
};

export function Panel({ title, description, action, children, className }: PanelProps) {
  return (
    <section className={cn("overflow-hidden rounded-lg border bg-white shadow-sm", className)}>
      <div className="flex flex-col gap-3 border-b bg-white px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-5">
        <div>
          <h2 className="text-base font-black tracking-normal sm:text-lg">{title}</h2>
          {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-muted-foreground">{description}</p> : null}
        </div>
        {action}
      </div>
      <div className="p-4 sm:p-5">{children}</div>
    </section>
  );
}

export function Notice({ tone = "info", children }: { tone?: "info" | "error" | "success"; children: ReactNode }) {
  return (
    <div
      className={cn(
        "rounded-md border px-3 py-2 text-sm font-medium",
        tone === "info" && "border-sky-200 bg-sky-50 text-sky-800",
        tone === "error" && "border-red-200 bg-red-50 text-red-700",
        tone === "success" && "border-teal-200 bg-teal-50 text-teal-800"
      )}
    >
      {children}
    </div>
  );
}
