import { ArrowUpRight, Landmark, ReceiptText, ShieldCheck, WalletCards } from "lucide-react";

const activities = [
  { label: "Income synced", value: "+$4,850", tone: "text-teal-700" },
  { label: "Groceries", value: "-$214", tone: "text-slate-700" },
  { label: "Budget saved", value: "$680", tone: "text-sky-700" },
  { label: "Export ready", value: "CSV", tone: "text-amber-700" }
];

export function FinanceTerminal() {
  return (
    <div className="relative mx-auto w-full max-w-xl animate-float-slow">
      <div className="absolute inset-x-8 -bottom-5 h-8 rounded-full bg-teal-900/15 blur-2xl" />
      <div className="glass-panel overflow-hidden rounded-lg border shadow-panel">
        <div className="flex items-center justify-between border-b bg-slate-950 px-4 py-3 text-white">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-300" />
            <span className="h-2.5 w-2.5 rounded-full bg-teal-300" />
          </div>
          <span className="text-xs text-white/70">live finance mesh</span>
        </div>

        <div className="grid gap-4 p-4 sm:p-5">
          <div className="rounded-md border bg-white p-4">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Net balance</p>
                <p className="text-3xl font-bold">$18,420.32</p>
              </div>
              <div className="rounded-md bg-teal-50 p-3 text-teal-700">
                <WalletCards size={24} />
              </div>
            </div>
            <div className="h-3 overflow-hidden rounded-full bg-muted">
              <div className="h-full w-[74%] rounded-full bg-primary" />
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
              <span>Budget health</span>
              <span>74% on track</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {activities.map((item) => (
              <div key={item.label} className="rounded-md border bg-white p-3">
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className={`mt-1 text-lg font-bold ${item.tone}`}>{item.value}</p>
              </div>
            ))}
          </div>

          <div className="rounded-md border bg-slate-950 p-4 text-white">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <ShieldCheck size={17} className="text-teal-300" />
                Protected account access
              </div>
              <ArrowUpRight size={17} className="text-white/60" />
            </div>
            <div className="relative overflow-hidden rounded-md border border-white/10 bg-white/5 p-3">
              <div className="absolute inset-y-0 left-1/2 w-16 -translate-x-1/2 animate-scan-line bg-white/10 blur-md" />
              <div className="relative grid gap-2 text-xs text-white/72">
                <span className="flex items-center gap-2">
                  <Landmark size={14} className="text-amber-300" />
                  your account is verified
                </span>
                <span className="flex items-center gap-2">
                  <ReceiptText size={14} className="text-sky-300" />
                  finance data is ready
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
