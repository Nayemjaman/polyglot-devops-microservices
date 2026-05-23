"use client";

import { useState, type ReactNode } from "react";
import { CreditCard, Landmark, WalletCards } from "lucide-react";
import { updateMe } from "@/lib/auth-api";
import { persistUser, type AuthUser } from "@/lib/auth";
import type { JsonValue } from "@/lib/finance-api";
import { financeApi } from "@/lib/finance-api";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Notice, Panel } from "@/components/ui/panel";
import { cn } from "@/lib/utils";
import type { RunAction, WorkspaceData } from "@/features/dashboard/types";

type PreviewOutput = JsonValue | null;

export function OverviewSection({
  user,
  isLoading,
  year,
  month,
  setYear,
  setMonth,
  totals,
  data,
  reportOutput,
  budgetOutput,
  transactionOutput,
  runAction,
  setReportOutput,
  setBudgetOutput,
  setTransactionOutput,
  setMessage,
  busyAction
}: {
  user: AuthUser;
  isLoading: boolean;
  year: number;
  month: number;
  setYear: (value: number) => void;
  setMonth: (value: number) => void;
  totals: { balance: number; income: number; expense: number };
  data: WorkspaceData;
  reportOutput: PreviewOutput;
  budgetOutput: PreviewOutput;
  transactionOutput: PreviewOutput;
  runAction: RunAction;
  setReportOutput: (value: PreviewOutput) => void;
  setBudgetOutput: (value: PreviewOutput) => void;
  setTransactionOutput: (value: PreviewOutput) => void;
  setMessage: (value: string | null) => void;
  busyAction: string | null;
}) {
  return (
    <div className="grid gap-5">
      <div className="grid gap-4 md:grid-cols-3">
        <Metric title="Total balance" value={money(totals.balance)} icon={WalletCards} tone="teal" />
        <Metric title="Recent income" value={money(totals.income)} icon={Landmark} tone="sky" />
        <Metric title="Recent expenses" value={money(totals.expense)} icon={CreditCard} tone="amber" />
      </div>

      <Panel
        title="Monthly pulse"
        description="Run live summaries for the selected month and inspect the returned data in a clean preview."
        action={<PeriodPicker year={year} month={month} setYear={setYear} setMonth={setMonth} />}
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <PulseButton action="reports-dashboard" busyAction={busyAction} onClick={() =>
            runAction("reports-dashboard", async () => {
              const response = await financeApi.reports.dashboard(year, month);
              setReportOutput(response.data);
              return response.message;
            }, false)
          }>
            Dashboard
          </PulseButton>
          <PulseButton action="budget-monthly" busyAction={busyAction} onClick={() =>
            runAction("budget-monthly", async () => {
              const response = await financeApi.budgets.monthlyStatus(year, month);
              setBudgetOutput(response.data);
              return response.message;
            }, false)
          }>
            Budget status
          </PulseButton>
          <PulseButton action="summary-monthly" busyAction={busyAction} onClick={() =>
            runAction("summary-monthly", async () => {
              const response = await financeApi.transactions.monthlySummary(year, month);
              setTransactionOutput(response.data);
              return response.message;
            }, false)
          }>
            Monthly summary
          </PulseButton>
          <PulseButton action="summary-category" busyAction={busyAction} onClick={() =>
            runAction("summary-category", async () => {
              const response = await financeApi.transactions.categorySummary(year, month);
              setTransactionOutput(response.data);
              return response.message;
            }, false)
          }>
            Category summary
          </PulseButton>
          <PulseButton action="summary-yearly" busyAction={busyAction} onClick={() =>
            runAction("summary-yearly", async () => {
              const response = await financeApi.transactions.yearlySummary(year);
              setTransactionOutput(response.data);
              return response.message;
            }, false)
          }>
            Yearly summary
          </PulseButton>
          <PulseButton action="summary-wallet" busyAction={busyAction} onClick={() =>
            runAction("summary-wallet", async () => {
              const response = await financeApi.transactions.walletSummary(year, month);
              setTransactionOutput(response.data);
              return response.message;
            }, false)
          }>
            Wallet summary
          </PulseButton>
        </div>
        <div className="mt-5 grid gap-4 lg:grid-cols-3">
          <ReportVisual title="Report preview" value={reportOutput} />
          <ReportVisual title="Budget preview" value={budgetOutput} />
          <ReportVisual title="Activity preview" value={transactionOutput} />
        </div>
      </Panel>

      <Panel title="Recent activity" description={isLoading ? "Loading..." : "Latest records from your workspace."}>
        <div className="grid gap-3">
          {data.transactions.slice(0, 6).map((item) => (
            <div key={item.id} className="flex flex-col gap-2 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-semibold">{item.title}</p>
                <p className="text-sm text-muted-foreground">
                  {item.type} · {item.wallet?.name} · {item.transaction_date}
                </p>
              </div>
              <span className="font-bold">{money(item.amount, item.currency_code)}</span>
            </div>
          ))}
          {!data.transactions.length ? <EmptyState text="Create a wallet, category, payment method, then add your first transaction." /> : null}
        </div>
      </Panel>

      <Panel title="Profile settings" description="Update your personal details and preferred money settings.">
        <ProfileForm user={user} setMessage={setMessage} />
      </Panel>
    </div>
  );
}

function ProfileForm({ user, setMessage }: { user: AuthUser; setMessage: (value: string | null) => void }) {
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  async function submit(form: FormData) {
    setIsSaving(true);
    setError(null);
    try {
      const response = await updateMe({
        first_name: text(form, "first_name"),
        last_name: text(form, "last_name"),
        profile: {
          phone: text(form, "phone"),
          avatar_url: text(form, "avatar_url"),
          country: text(form, "country"),
          currency_code: text(form, "currency_code"),
          timezone: text(form, "timezone"),
          date_of_birth: text(form, "date_of_birth") || null
        }
      });
      persistUser(response.user);
      setMessage("Profile updated successfully");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update profile");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <SimpleForm button="Save profile" busy={isSaving} onSubmit={submit}>
      <Field label="First name"><Input name="first_name" defaultValue={user.first_name} /></Field>
      <Field label="Last name"><Input name="last_name" defaultValue={user.last_name} /></Field>
      <Field label="Phone"><Input name="phone" defaultValue={user.profile?.phone || ""} /></Field>
      <Field label="Country"><Input name="country" defaultValue={user.profile?.country || ""} /></Field>
      <Field label="Currency"><Input name="currency_code" defaultValue={user.profile?.currency_code || "USD"} maxLength={3} /></Field>
      <Field label="Timezone"><Input name="timezone" defaultValue={user.profile?.timezone || ""} placeholder="Asia/Dhaka" /></Field>
      <Field label="Birth date"><Input name="date_of_birth" type="date" defaultValue={user.profile?.date_of_birth || ""} /></Field>
      <Field label="Avatar URL"><Input name="avatar_url" defaultValue={user.profile?.avatar_url || ""} /></Field>
      {error ? <div className="sm:col-span-2 xl:col-span-3 2xl:col-span-4"><Notice tone="error">{error}</Notice></div> : null}
    </SimpleForm>
  );
}

function SimpleForm({
  children,
  button,
  busy,
  onSubmit
}: {
  children: ReactNode;
  button: string;
  busy: boolean;
  onSubmit: (form: FormData) => void;
}) {
  return (
    <form
      className="mb-5 grid gap-4 rounded-md border bg-slate-50/80 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,.7)] sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(new FormData(event.currentTarget));
        event.currentTarget.reset();
      }}
    >
      {children}
      <div className="flex items-end sm:col-span-2 xl:col-span-1">
        <Button type="submit" disabled={busy} className="w-full">
          {busy ? "Working..." : button}
        </Button>
      </div>
    </form>
  );
}

function PulseButton({
  action,
  busyAction,
  children,
  onClick
}: {
  action: string;
  busyAction: string | null;
  children: ReactNode;
  onClick: () => void;
}) {
  const isBusy = busyAction === action;
  return (
    <Button type="button" variant="secondary" disabled={isBusy} onClick={onClick}>
      {isBusy ? "Working..." : children}
    </Button>
  );
}

function Metric({ title, value, icon: Icon, tone }: { title: string; value: string; icon: typeof WalletCards; tone: "teal" | "sky" | "amber" }) {
  return (
    <div className="overflow-hidden rounded-lg border bg-white shadow-sm">
      <div
        className={cn(
          "h-1",
          tone === "teal" && "bg-teal-500",
          tone === "sky" && "bg-sky-500",
          tone === "amber" && "bg-amber-400"
        )}
      />
      <div className="p-5">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="mt-2 text-3xl font-black">{value}</p>
          </div>
          <div
            className={cn(
              "grid h-12 w-12 place-items-center rounded-md",
              tone === "teal" && "bg-teal-50 text-teal-700",
              tone === "sky" && "bg-sky-50 text-sky-700",
              tone === "amber" && "bg-amber-50 text-amber-700"
            )}
          >
            <Icon size={24} />
          </div>
        </div>
      </div>
    </div>
  );
}

function PeriodPicker({
  year,
  month,
  setYear,
  setMonth
}: {
  year: number;
  month: number;
  setYear: (value: number) => void;
  setMonth: (value: number) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      <Input type="number" value={year} onChange={(event) => setYear(Number(event.target.value))} aria-label="Year" />
      <Input type="number" min={1} max={12} value={month} onChange={(event) => setMonth(Number(event.target.value))} aria-label="Month" />
    </div>
  );
}

function ReportVisual({ title, value }: { title: string; value: PreviewOutput }) {
  const rows = flattenNumbers(value).slice(0, 8);
  const max = Math.max(...rows.map((row) => Math.abs(row.value)), 1);
  return (
    <div className="overflow-hidden rounded-md border bg-white shadow-sm">
      <div className="flex items-center justify-between border-b bg-slate-50 px-3 py-2">
        <span className="text-sm font-bold">{title}</span>
        <span className="rounded-full bg-sky-50 px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-sky-700">
          Visual
        </span>
      </div>
      {rows.length ? (
        <div className="grid gap-3 p-3">
          {rows.map((row) => (
            <div key={row.label} className="grid gap-1">
              <div className="flex justify-between gap-3 text-xs font-semibold">
                <span className="truncate">{human(row.label)}</span>
                <span>{row.value.toLocaleString()}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-teal-500" style={{ width: `${Math.max(6, (Math.abs(row.value) / max) * 100)}%` }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 text-sm text-muted-foreground">Run a request to show chart-ready values.</div>
      )}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <div className="rounded-md border border-dashed bg-slate-50 px-3 py-6 text-center text-sm text-muted-foreground">{text}</div>;
}

function text(form: FormData, key: string) {
  return String(form.get(key) || "").trim();
}

function money(value: string | number, currency = "USD") {
  const amount = Number(value || 0);
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
}

function flattenNumbers(value: JsonValue | null, prefix = ""): Array<{ label: string; value: number }> {
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => flattenNumbers(item, `${prefix}${index + 1}.`));
  }
  return Object.entries(value).flatMap(([key, item]) => {
    const label = prefix ? `${prefix}${key}` : key;
    if (typeof item === "number") {
      return [{ label, value: item }];
    }
    if (typeof item === "string" && item.trim() !== "" && !Number.isNaN(Number(item))) {
      return [{ label, value: Number(item) }];
    }
    if (item && typeof item === "object") {
      return flattenNumbers(item, label + ".");
    }
    return [];
  });
}

function human(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (match) => match.toUpperCase());
}
