import type { ReactNode } from "react";

type FieldProps = {
  label: string;
  error?: string;
  children: ReactNode;
};

export function Field({ label, error, children }: FieldProps) {
  return (
    <label className="grid gap-2 text-sm font-medium text-foreground">
      <span>{label}</span>
      {children}
      {error ? <span className="text-xs font-medium text-destructive">{error}</span> : null}
    </label>
  );
}
