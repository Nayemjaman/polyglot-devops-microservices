import * as React from "react";
import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(({ className, ...props }, ref) => {
  return (
    <textarea
      ref={ref}
      className={cn(
        "min-h-24 w-full rounded-md border bg-white px-3 py-2 text-sm outline-none transition placeholder:text-muted-foreground focus:border-teal-500 focus:ring-4 focus:ring-teal-500/10",
        className
      )}
      {...props}
    />
  );
});

Textarea.displayName = "Textarea";
