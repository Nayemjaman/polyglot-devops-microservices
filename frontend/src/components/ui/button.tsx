import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
};

export function Button({ className, variant = "primary", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold transition focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-60",
        size === "md" && "h-11 px-5",
        size === "sm" && "h-9 px-3",
        variant === "primary" &&
          "bg-slate-950 text-white shadow-glow hover:bg-slate-800",
        variant === "secondary" &&
          "border bg-white text-foreground shadow-sm hover:border-teal-300 hover:bg-teal-50",
        variant === "ghost" && "text-foreground hover:bg-white/70",
        variant === "danger" && "border border-red-200 bg-red-50 text-red-700 hover:bg-red-100",
        className
      )}
      {...props}
    />
  );
}
