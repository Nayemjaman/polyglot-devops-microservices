import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

export const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, ...props }, ref) => {
  return (
    <input
      ref={ref}
      className={cn(
        "h-11 w-full rounded-md border bg-white px-3 text-sm outline-none transition placeholder:text-muted-foreground focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10",
        className
      )}
      {...props}
    />
  );
});

Input.displayName = "Input";
