"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  BarChart3,
  Bell,
  CreditCard,
  FileText,
  Landmark,
  Link as LinkIcon,
  Paperclip,
  RefreshCw,
  Trash2,
  WalletCards
} from "lucide-react";
import { LogoutButton } from "@/components/auth/logout-button";
import Link from "next/link";
import { updateMe } from "@/lib/auth-api";
import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Notice, Panel } from "@/components/ui/panel";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  financeApi,
  downloadReportFile,
  paginationPage,
  paginationTotalPages,
  type PaginatedResponse,
  type Budget,
  type BudgetAlertRule,
  type BudgetCategory,
  type Category,
  type ExportJob,
  type PaymentMethod,
  type RecurringTransaction,
  type Tag,
  type Transaction,
  type Wallet
} from "@/lib/finance-api";
import { persistUser, type AuthUser } from "@/lib/auth";
import { cn } from "@/lib/utils";

type SectionId = "overview" | "setup" | "transactions" | "budgets" | "reports";

type WorkspaceData = {
  wallets: Wallet[];
  categories: Category[];
  paymentMethods: PaymentMethod[];
  tags: Tag[];
  transactions: Transaction[];
  recurring: RecurringTransaction[];
  budgets: Budget[];
  exportJobs: ExportJob[];
};

type ListMeta = {
  page: number;
  totalPages: number;
};

type ListState<T> = {
  items: T[];
  meta: ListMeta;
};

const currentDate = new Date();
const initialYear = currentDate.getFullYear();
const initialMonth = currentDate.getMonth() + 1;

const navItems: Array<{ id: SectionId; label: string; icon: typeof BarChart3 }> = [
  { id: "overview", label: "Overview", icon: BarChart3 },
  { id: "setup", label: "Setup", icon: WalletCards },
  { id: "transactions", label: "Activity", icon: CreditCard },
  { id: "budgets", label: "Budgets", icon: Bell },
  { id: "reports", label: "Reports", icon: FileText }
];

const emptyData: WorkspaceData = {
  wallets: [],
  categories: [],
  paymentMethods: [],
  tags: [],
  transactions: [],
  recurring: [],
  budgets: [],
  exportJobs: []
};

function listState<T>(items: T[] = [], page = 1, totalPages = 1): ListState<T> {
  return { items, meta: { page, totalPages } };
}

function sectionFromHash(): SectionId {
  if (typeof window === "undefined") {
    return "overview";
  }
  const section = window.location.hash.replace("#", "");
  return navItems.some((item) => item.id === section) ? (section as SectionId) : "overview";
}

async function completeVisibleExportJobs(jobs: ExportJob[]) {
  return Promise.all(
    jobs.map(async (job) => {
      const id = job.id || job.export_job_id;
      if (!id || (job.status === "COMPLETED" && job.file?.id)) {
        return job;
      }
      if (job.status === "PENDING" || job.status === "PROCESSING" || !job.file?.id) {
        try {
          const response = await financeApi.reports.exportJob(id);
          return response.data;
        } catch {
          return job;
        }
      }
      return job;
    })
  );
}

export function FinanceWorkspace({ user }: { user: AuthUser }) {
  const [activeSection, setActiveSection] = useState<SectionId>(sectionFromHash);
  const [data, setData] = useState<WorkspaceData>(emptyData);
  const [year, setYear] = useState(initialYear);
  const [month, setMonth] = useState(initialMonth);
  const [isLoading, setIsLoading] = useState(true);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reportOutput, setReportOutput] = useState<unknown>(null);
  const [budgetOutput, setBudgetOutput] = useState<unknown>(null);
  const [transactionOutput, setTransactionOutput] = useState<unknown>(null);

  async function runAction(action: string, work: () => Promise<string | void>, refresh = true) {
    setBusyAction(action);
    setError(null);
    setMessage(null);
    try {
      const result = await work();
      setMessage(result || "Done");
      if (refresh) {
        await loadCoreData(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setBusyAction(null);
    }
  }

  async function loadCoreData(showLoader = true) {
    if (showLoader) {
      setIsLoading(true);
    }
    setError(null);
    try {
      const [wallets, categories, paymentMethods, tags, transactions, recurring, budgets, exportJobs] = await Promise.all([
        financeApi.wallets.list({ page_size: 100 }),
        financeApi.categories.list({ page_size: 100 }),
        financeApi.paymentMethods.list({ page_size: 100 }),
        financeApi.tags.list(),
        financeApi.transactions.list({ page_size: 20 }),
        financeApi.recurring.list({ page_size: 20 }),
        financeApi.budgets.list({ page_size: 50 }),
        financeApi.reports.exportJobs({ page_size: 10 })
      ]);
      const completedExportJobs = await completeVisibleExportJobs(exportJobs.data);
      setData({
        wallets: wallets.data,
        categories: categories.data,
        paymentMethods: paymentMethods.data,
        tags: tags.data,
        transactions: transactions.data,
        recurring: recurring.data,
        budgets: budgets.data,
        exportJobs: completedExportJobs
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load workspace data");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadCoreData();
  }, []);

  function chooseSection(section: SectionId) {
    setActiveSection(section);
    window.history.replaceState(null, "", `#${section}`);
  }

  const totals = useMemo(() => {
    const balance = data.wallets.reduce((sum, wallet) => sum + Number(wallet.current_balance || 0), 0);
    const expense = data.transactions
      .filter((item) => item.type === "EXPENSE")
      .reduce((sum, item) => sum + Number(item.amount || 0), 0);
    const income = data.transactions
      .filter((item) => item.type === "INCOME")
      .reduce((sum, item) => sum + Number(item.amount || 0), 0);
    return { balance, expense, income };
  }, [data.wallets, data.transactions]);

  return (
    <main className="aurora-surface relative min-h-screen overflow-hidden">
      <div className="soft-noise pointer-events-none absolute inset-0 opacity-70" />
      <div className="relative mx-auto flex w-full max-w-[1540px] flex-col gap-5 px-4 py-4 sm:px-6 lg:flex-row lg:py-6">
        <aside className="lg:sticky lg:top-6 lg:h-[calc(100vh-48px)] lg:w-72 lg:shrink-0">
          <div className="overflow-hidden rounded-lg border border-slate-800 bg-slate-950 text-white shadow-panel">
            <div className="border-b border-white/10 p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-teal-300">Finance workspace</p>
              <h1 className="mt-2 truncate text-2xl font-black">{user.first_name || user.username}</h1>
              <p className="mt-1 text-sm text-white/58">{user.email}</p>
            </div>
            <nav className="flex gap-2 overflow-x-auto p-3 lg:grid">
              {navItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => chooseSection(item.id)}
                  className={cn(
                    "flex h-11 min-w-max items-center gap-3 rounded-md px-3 text-left text-sm font-semibold transition lg:min-w-0",
                    activeSection === item.id ? "bg-white text-slate-950 shadow-sm" : "text-white/70 hover:bg-white/10 hover:text-white"
                  )}
                >
                  <item.icon size={18} />
                  {item.label}
                </button>
              ))}
            </nav>
            <div className="mx-3 mb-3 grid grid-cols-3 gap-2 rounded-md border border-white/10 bg-white/5 p-2 text-center text-xs text-white/72 lg:grid-cols-1 lg:text-left lg:text-sm">
              <span><b className="text-white">{data.wallets.length}</b> wallets</span>
              <span><b className="text-white">{data.transactions.length}</b> moves</span>
              <span><b className="text-white">{data.budgets.length}</b> budgets</span>
            </div>
            <div className="grid gap-3 border-t border-white/10 p-3">
              <Button type="button" variant="secondary" onClick={() => loadCoreData()} disabled={isLoading}>
                <RefreshCw size={16} />
                Refresh
              </Button>
              <LogoutButton />
            </div>
          </div>
        </aside>

        <section className="min-w-0 flex-1">
          <div className="mb-5 overflow-hidden rounded-lg border bg-slate-950 text-white shadow-panel">
            <div className="grid gap-5 p-5 md:grid-cols-[1fr_auto] md:items-end">
              <div>
                <p className="text-sm font-semibold text-teal-300">{human(activeSection)}</p>
                <h2 className="mt-2 text-balance text-3xl font-black tracking-normal sm:text-4xl">
                  Manage your money without switching context.
                </h2>
                <p className="mt-3 max-w-3xl text-sm leading-6 text-white/68 sm:text-base">
                  Create records, review status, and run reports from one responsive workspace.
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 rounded-md border border-white/10 bg-white/5 p-2 text-center">
                <MiniStat label="Income" value={money(totals.income)} />
                <MiniStat label="Expense" value={money(totals.expense)} />
                <MiniStat label="Balance" value={money(totals.balance)} />
              </div>
            </div>
          </div>
          <div className="mb-5 grid gap-3">
            {error ? <Notice tone="error">{error}</Notice> : null}
            {message ? <Notice tone="success">{message}</Notice> : null}
          </div>

          {activeSection === "overview" ? (
            <OverviewSection
              user={user}
              isLoading={isLoading}
              year={year}
              month={month}
              setYear={setYear}
              setMonth={setMonth}
              totals={totals}
              data={data}
              reportOutput={reportOutput}
              budgetOutput={budgetOutput}
              transactionOutput={transactionOutput}
              runAction={runAction}
              setReportOutput={setReportOutput}
              setBudgetOutput={setBudgetOutput}
              setTransactionOutput={setTransactionOutput}
              setMessage={setMessage}
            />
          ) : null}

          {activeSection === "setup" ? (
            <SetupSection data={data} runAction={runAction} busyAction={busyAction} />
          ) : null}

          {activeSection === "transactions" ? (
            <TransactionsSection data={data} runAction={runAction} busyAction={busyAction} />
          ) : null}

          {activeSection === "budgets" ? (
            <BudgetsSection data={data} runAction={runAction} busyAction={busyAction} setBudgetOutput={setBudgetOutput} />
          ) : null}

          {activeSection === "reports" ? (
            <ReportsSection
              data={data}
              year={year}
              month={month}
              setYear={setYear}
              setMonth={setMonth}
              output={reportOutput}
              setOutput={setReportOutput}
              runAction={runAction}
              busyAction={busyAction}
            />
          ) : null}
        </section>
      </div>
    </main>
  );
}

type RunAction = (action: string, work: () => Promise<string | void>, refresh?: boolean) => Promise<void>;

function OverviewSection({
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
  setMessage
}: {
  user: AuthUser;
  isLoading: boolean;
  year: number;
  month: number;
  setYear: (value: number) => void;
  setMonth: (value: number) => void;
  totals: { balance: number; income: number; expense: number };
  data: WorkspaceData;
  reportOutput: unknown;
  budgetOutput: unknown;
  transactionOutput: unknown;
  runAction: RunAction;
  setReportOutput: (value: unknown) => void;
  setBudgetOutput: (value: unknown) => void;
  setTransactionOutput: (value: unknown) => void;
  setMessage: (value: string | null) => void;
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
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              runAction(
                "reports-dashboard",
                async () => {
                  const response = await financeApi.reports.dashboard(year, month);
                  setReportOutput(response.data);
                  return response.message;
                },
                false
              )
            }
          >
            Dashboard
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              runAction(
                "budget-monthly",
                async () => {
                  const response = await financeApi.budgets.monthlyStatus(year, month);
                  setBudgetOutput(response.data);
                  return response.message;
                },
                false
              )
            }
          >
            Budget status
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              runAction(
                "summary-monthly",
                async () => {
                  const response = await financeApi.transactions.monthlySummary(year, month);
                  setTransactionOutput(response.data);
                  return response.message;
                },
                false
              )
            }
          >
            Monthly summary
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              runAction(
                "summary-category",
                async () => {
                  const response = await financeApi.transactions.categorySummary(year, month);
                  setTransactionOutput(response.data);
                  return response.message;
                },
                false
              )
            }
          >
            Category summary
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              runAction(
                "summary-yearly",
                async () => {
                  const response = await financeApi.transactions.yearlySummary(year);
                  setTransactionOutput(response.data);
                  return response.message;
                },
                false
              )
            }
          >
            Yearly summary
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              runAction(
                "summary-wallet",
                async () => {
                  const response = await financeApi.transactions.walletSummary(year, month);
                  setTransactionOutput(response.data);
                  return response.message;
                },
                false
              )
            }
          >
            Wallet summary
          </Button>
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

function SetupSection({ data, runAction, busyAction }: { data: WorkspaceData; runAction: RunAction; busyAction: string | null }) {
  const [selectedWalletId, setSelectedWalletId] = useState("");
  const [selectedCategoryId, setSelectedCategoryId] = useState("");
  const [selectedMethodId, setSelectedMethodId] = useState("");
  const [wallets, setWallets] = useState(listState(data.wallets));
  const [categories, setCategories] = useState(listState(data.categories));
  const [methods, setMethods] = useState(listState(data.paymentMethods));
  const [tagSearch, setTagSearch] = useState("");
  const selectedWallet = wallets.items.find((item) => item.id === selectedWalletId);
  const selectedCategory = categories.items.find((item) => item.id === selectedCategoryId);
  const selectedMethod = methods.items.find((item) => item.id === selectedMethodId);
  const filteredTags = data.tags.filter((tag) => tag.name.toLowerCase().includes(tagSearch.toLowerCase()));

  useEffect(() => {
    setWallets(listState(data.wallets));
    setCategories(listState(data.categories));
    setMethods(listState(data.paymentMethods));
  }, [data.wallets, data.categories, data.paymentMethods]);

  async function loadWallets(form: FormData, page = 1) {
    const response = await financeApi.wallets.list(listParams(form, page));
    setWallets(fromPaginated(response));
  }

  async function loadCategories(form: FormData, page = 1) {
    const response = await financeApi.categories.list(listParams(form, page));
    setCategories(fromPaginated(response));
  }

  async function loadMethods(form: FormData, page = 1) {
    const response = await financeApi.paymentMethods.list(listParams(form, page));
    setMethods(fromPaginated(response));
  }

  return (
    <div className="grid gap-5">
      <Panel title="Wallets" description="Create accounts that hold balances.">
        <WalletForm runAction={runAction} busyAction={busyAction} />
        <ListControls
          title="Filter wallets"
          typeOptions={["CASH", "BANK", "MOBILE_BANKING", "CARD", "SAVINGS", "INVESTMENT"]}
          meta={wallets.meta}
          onApply={(form) => runAction("filter-wallets", async () => { await loadWallets(form); return "Wallets filtered"; }, false)}
          onPage={(page, form) => runAction("page-wallets", async () => { await loadWallets(form, page); return "Wallet page loaded"; }, false)}
        />
        <EntityList
          items={wallets.items}
          render={(item) => `${item.name} · ${item.type} · ${money(item.current_balance, item.currency_code)}`}
          onSelect={(item) => setSelectedWalletId(item.id)}
          onDelete={(id) => runAction("delete-wallet", async () => (await financeApi.wallets.delete(id)).message)}
          onToggle={(item) =>
            runAction("update-wallet", async () => (await financeApi.wallets.update(item.id, { is_active: !item.is_active })).message)
          }
        />
        {selectedWallet ? <WalletEditForm wallet={selectedWallet} runAction={runAction} busyAction={busyAction} /> : null}
      </Panel>

      <Panel title="Categories" description="Group income and expenses.">
        <CategoryForm runAction={runAction} busyAction={busyAction} categories={categories.items} />
        <ListControls
          title="Filter categories"
          typeOptions={["EXPENSE", "INCOME"]}
          meta={categories.meta}
          onApply={(form) => runAction("filter-categories", async () => { await loadCategories(form); return "Categories filtered"; }, false)}
          onPage={(page, form) => runAction("page-categories", async () => { await loadCategories(form, page); return "Category page loaded"; }, false)}
        />
        <EntityList
          items={categories.items}
          render={(item) => `${item.name} · ${item.type} · ${item.is_active ? "active" : "inactive"}`}
          onSelect={(item) => setSelectedCategoryId(item.id)}
          onDelete={(id) => runAction("delete-category", async () => (await financeApi.categories.delete(id)).message)}
          onToggle={(item) =>
            runAction("update-category", async () => (await financeApi.categories.update(item.id, { is_active: !item.is_active })).message)
          }
        />
        {selectedCategory ? <CategoryEditForm category={selectedCategory} categories={categories.items} runAction={runAction} busyAction={busyAction} /> : null}
      </Panel>

      <Panel title="Payment methods" description="Track how money moved.">
        <PaymentMethodForm runAction={runAction} busyAction={busyAction} />
        <ListControls
          title="Filter payment methods"
          typeOptions={["CASH", "CARD", "BANK_TRANSFER", "MOBILE_BANKING", "OTHER"]}
          meta={methods.meta}
          onApply={(form) => runAction("filter-methods", async () => { await loadMethods(form); return "Payment methods filtered"; }, false)}
          onPage={(page, form) => runAction("page-methods", async () => { await loadMethods(form, page); return "Payment method page loaded"; }, false)}
        />
        <EntityList
          items={methods.items}
          render={(item) => `${item.name} · ${item.type} · ${item.is_active ? "active" : "inactive"}`}
          onSelect={(item) => setSelectedMethodId(item.id)}
          onDelete={(id) => runAction("delete-method", async () => (await financeApi.paymentMethods.delete(id)).message)}
          onToggle={(item) =>
            runAction(
              "update-method",
              async () => (await financeApi.paymentMethods.update(item.id, { is_active: !item.is_active })).message
            )
          }
        />
        {selectedMethod ? <PaymentMethodEditForm method={selectedMethod} runAction={runAction} busyAction={busyAction} /> : null}
      </Panel>

      <Panel title="Tags" description="Small labels for searching and grouping.">
        <TagForm runAction={runAction} busyAction={busyAction} />
        <div className="mb-4">
          <Input value={tagSearch} onChange={(event) => setTagSearch(event.target.value)} placeholder="Search tags" />
        </div>
        <EntityList
          items={filteredTags}
          render={(item) => item.name}
          onDelete={(id) => runAction("delete-tag", async () => (await financeApi.tags.delete(id)).message)}
        />
      </Panel>
    </div>
  );
}

function TransactionsSection({ data, runAction, busyAction }: { data: WorkspaceData; runAction: RunAction; busyAction: string | null }) {
  const [selectedTransactionId, setSelectedTransactionId] = useState("");
  const [transactionDetails, setTransactionDetails] = useState<unknown>(null);
  const [selectedRecurringId, setSelectedRecurringId] = useState("");
  const [transactions, setTransactions] = useState(listState(data.transactions));
  const [recurring, setRecurring] = useState(listState(data.recurring));
  const selectedTransaction = transactions.items.find((item) => item.id === selectedTransactionId) || transactions.items[0];
  const selectedRecurring = recurring.items.find((item) => item.id === selectedRecurringId);

  useEffect(() => {
    setTransactions(listState(data.transactions));
    setRecurring(listState(data.recurring));
  }, [data.transactions, data.recurring]);

  async function loadTransactions(form: FormData, page = 1) {
    const response = await financeApi.transactions.list({
      ...listParams(form, page),
      category_id: text(form, "category_id"),
      wallet_id: text(form, "wallet_id"),
      payment_method_id: text(form, "payment_method_id"),
      start_date: text(form, "start_date"),
      end_date: text(form, "end_date"),
      sort_by: text(form, "sort_by") || "transaction_date",
      sort_order: text(form, "sort_order") || "desc"
    });
    setTransactions(fromPaginated(response));
  }

  async function loadRecurring(form: FormData, page = 1) {
    const response = await financeApi.recurring.list({
      ...listParams(form, page),
      frequency: text(form, "frequency")
    });
    setRecurring(fromPaginated(response));
  }

  return (
    <div className="grid gap-5">
      <Panel title="Create transaction" description="Add income, expenses, transfers, and adjustments.">
        <TransactionForm data={data} runAction={runAction} busyAction={busyAction} />
      </Panel>

      <Panel title="Transactions" description="List, edit, delete, and inspect records.">
        <TransactionListControls
          data={data}
          meta={transactions.meta}
          onApply={(form) => runAction("filter-transactions", async () => { await loadTransactions(form); return "Transactions filtered"; }, false)}
          onPage={(page, form) => runAction("page-transactions", async () => { await loadTransactions(form, page); return "Transaction page loaded"; }, false)}
        />
        <div className="grid gap-3">
          {transactions.items.map((item) => (
            <div key={item.id} className="rounded-md border p-3">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <button type="button" className="text-left" onClick={() => setSelectedTransactionId(item.id)}>
                  <p className="font-semibold">{item.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {item.type} · {item.category?.name} · {item.wallet?.name}
                  </p>
                </button>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-bold">{money(item.amount, item.currency_code)}</span>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() =>
                      runAction(
                        "get-transaction",
                        async () => {
                          const response = await financeApi.transactions.get(item.id);
                          setSelectedTransactionId(item.id);
                          setTransactionDetails(response.data);
                          return response.message;
                        },
                        true
                      )
                    }
                  >
                    Details
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() =>
                      runAction("quick-update-transaction", async () =>
                        (await financeApi.transactions.update(item.id, { title: `${item.title} updated` })).message
                      )
                    }
                  >
                    Quick edit
                  </Button>
                  <IconDelete onClick={() => runAction("delete-transaction", async () => (await financeApi.transactions.delete(item.id)).message)} />
                </div>
              </div>
            </div>
          ))}
          {!data.transactions.length ? <EmptyState text="No transactions yet." /> : null}
        </div>
        {selectedTransaction ? (
          <div className="mt-5 grid gap-4 lg:grid-cols-[1fr_.9fr]">
            <TransactionEditForm transaction={selectedTransaction} data={data} runAction={runAction} busyAction={busyAction} />
            <DetailSummary title="Transaction details" value={transactionDetails || selectedTransaction} />
          </div>
        ) : null}
      </Panel>

      <Panel title="Attachments" description="Upload, list, and remove files for a selected transaction.">
        {selectedTransaction ? (
          <AttachmentManager transaction={selectedTransaction} runAction={runAction} />
        ) : (
          <EmptyState text="Create a transaction before adding attachments." />
        )}
      </Panel>

      <Panel title="Recurring transactions" description="Schedule repeated income or expenses.">
        <RecurringForm data={data} runAction={runAction} busyAction={busyAction} />
        <ListControls
          title="Filter recurring"
          typeName="frequency"
          typeOptions={["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]}
          meta={recurring.meta}
          onApply={(form) => runAction("filter-recurring", async () => { await loadRecurring(form); return "Recurring transactions filtered"; }, false)}
          onPage={(page, form) => runAction("page-recurring", async () => { await loadRecurring(form, page); return "Recurring page loaded"; }, false)}
        />
        <EntityList
          items={recurring.items}
          render={(item) => `${item.title} · ${item.frequency} · ${money(item.amount, item.currency_code)}`}
          onSelect={(item) => setSelectedRecurringId(item.id)}
          onDelete={(id) => runAction("delete-recurring", async () => (await financeApi.recurring.delete(id)).message)}
          onToggle={(item) =>
            runAction("update-recurring", async () => (await financeApi.recurring.update(item.id, { is_active: !item.is_active })).message)
          }
        />
        {selectedRecurring ? <RecurringEditForm recurring={selectedRecurring} data={data} runAction={runAction} busyAction={busyAction} /> : null}
      </Panel>
    </div>
  );
}

function BudgetsSection({
  data,
  runAction,
  busyAction,
  setBudgetOutput
}: {
  data: WorkspaceData;
  runAction: RunAction;
  busyAction: string | null;
  setBudgetOutput: (value: unknown) => void;
}) {
  const [selectedBudgetId, setSelectedBudgetId] = useState("");
  const [budgetCategories, setBudgetCategories] = useState<BudgetCategory[]>([]);
  const [alertRules, setAlertRules] = useState<BudgetAlertRule[]>([]);
  const [selectedBudgetCategoryId, setSelectedBudgetCategoryId] = useState("");
  const [selectedAlertRuleId, setSelectedAlertRuleId] = useState("");
  const [budgets, setBudgets] = useState(listState(data.budgets));
  const selectedBudget = budgets.items.find((item) => item.id === selectedBudgetId) || budgets.items[0];
  const selectedBudgetCategory = budgetCategories.find((item) => item.id === selectedBudgetCategoryId);
  const selectedAlertRule = alertRules.find((item) => item.id === selectedAlertRuleId);

  async function loadBudgetChildren(budgetId: string) {
    const [categories, rules] = await Promise.all([
      financeApi.budgets.categories.list(budgetId),
      financeApi.budgets.alertRules.list(budgetId)
    ]);
    setBudgetCategories(categories.data);
    setAlertRules(rules.data);
  }

  useEffect(() => {
    setBudgets(listState(data.budgets));
  }, [data.budgets]);

  useEffect(() => {
    if (selectedBudget?.id) {
      loadBudgetChildren(selectedBudget.id).catch(() => {
        setBudgetCategories([]);
        setAlertRules([]);
      });
    }
  }, [selectedBudget?.id]);

  async function loadBudgets(form: FormData, page = 1) {
    const response = await financeApi.budgets.list({
      ...listParams(form, page),
      year: text(form, "year"),
      month: text(form, "month"),
      status: text(form, "status")
    });
    setBudgets(fromPaginated(response));
  }

  return (
    <div className="grid gap-5">
      <Panel title="Monthly budget" description="Create and manage monthly spending plans.">
        <BudgetForm runAction={runAction} busyAction={busyAction} />
        <BudgetListControls
          meta={budgets.meta}
          onApply={(form) => runAction("filter-budgets", async () => { await loadBudgets(form); return "Budgets filtered"; }, false)}
          onPage={(page, form) => runAction("page-budgets", async () => { await loadBudgets(form, page); return "Budget page loaded"; }, false)}
        />
        <EntityList
          items={budgets.items}
          render={(item) => `${item.name} · ${item.month}/${item.year} · ${money(item.total_budget_amount, item.currency_code)} · ${item.status}`}
          onDelete={(id) => runAction("delete-budget", async () => (await financeApi.budgets.delete(id)).message)}
          onSelect={(item) => setSelectedBudgetId(item.id)}
          onToggle={(item) =>
            runAction("update-budget", async () =>
              (await financeApi.budgets.update(item.id, { status: item.status === "ACTIVE" ? "ARCHIVED" : "ACTIVE" })).message
            )
          }
        />
        {selectedBudget ? <BudgetEditForm budget={selectedBudget} runAction={runAction} busyAction={busyAction} /> : null}
      </Panel>

      {selectedBudget ? (
        <>
          <Panel title="Budget categories" description={`Allocate categories inside ${selectedBudget.name}.`}>
            <BudgetCategoryForm budget={selectedBudget} categories={data.categories} runAction={runAction} busyAction={busyAction} />
            <div className="mb-3 flex justify-end">
              <Button type="button" variant="secondary" size="sm" onClick={() => runAction("list-budget-categories", async () => {
                await loadBudgetChildren(selectedBudget.id);
                return "Budget categories loaded";
              }, false)}>
                Reload categories
              </Button>
            </div>
            <EntityList
              items={budgetCategories}
              render={(item) => `${item.category_name_snapshot} · ${money(item.budget_amount, selectedBudget.currency_code)} · alert ${item.alert_threshold_percentage}%`}
              onSelect={(item) => setSelectedBudgetCategoryId(item.id)}
              onDelete={(id) =>
                runAction(
                  "delete-budget-category",
                  async () => {
                    const response = await financeApi.budgets.categories.delete(selectedBudget.id, id);
                    await loadBudgetChildren(selectedBudget.id);
                    return response.message;
                  },
                  false
                )
              }
            />
            {selectedBudgetCategory ? (
              <BudgetCategoryEditForm
                budget={selectedBudget}
                budgetCategory={selectedBudgetCategory}
                runAction={runAction}
                busyAction={busyAction}
                reload={() => loadBudgetChildren(selectedBudget.id)}
              />
            ) : null}
          </Panel>
          <Panel title="Alert rules" description="Set budget warning thresholds.">
            <AlertRuleForm budget={selectedBudget} runAction={runAction} busyAction={busyAction} />
            <div className="mb-3 flex justify-end">
              <Button type="button" variant="secondary" size="sm" onClick={() => runAction("list-alerts", async () => {
                await loadBudgetChildren(selectedBudget.id);
                return "Alert rules loaded";
              }, false)}>
                Reload alerts
              </Button>
            </div>
            <EntityList
              items={alertRules}
              render={(item) => `${item.rule_type} · ${item.threshold_percentage}% · ${item.is_enabled ? "enabled" : "disabled"}`}
              onSelect={(item) => setSelectedAlertRuleId(item.id)}
              onDelete={(id) =>
                runAction(
                  "delete-alert",
                  async () => {
                    const response = await financeApi.budgets.alertRules.delete(selectedBudget.id, id);
                    await loadBudgetChildren(selectedBudget.id);
                    return response.message;
                  },
                  false
                )
              }
              onToggle={(item) =>
                runAction(
                  "toggle-alert",
                  async () => {
                    const response = await financeApi.budgets.alertRules.update(selectedBudget.id, item.id, { is_enabled: !item.is_enabled });
                    await loadBudgetChildren(selectedBudget.id);
                    return response.message;
                  },
                  false
                )
              }
            />
            {selectedAlertRule ? (
              <AlertRuleEditForm
                budget={selectedBudget}
                rule={selectedAlertRule}
                runAction={runAction}
                busyAction={busyAction}
                reload={() => loadBudgetChildren(selectedBudget.id)}
              />
            ) : null}
          </Panel>
          <Panel title="Budget usage" description="Run usage and category status requests.">
            <div className="flex flex-wrap gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  runAction("duplicate-budget", async () => {
                    const next = nextBudgetPeriod(selectedBudget.year, selectedBudget.month);
                    const response = await financeApi.budgets.create({
                      name: `${selectedBudget.name} copy`,
                      year: next.year,
                      month: next.month,
                      total_budget_amount: selectedBudget.total_budget_amount,
                      currency_code: selectedBudget.currency_code
                    });
                    return `Duplicated into ${response.data.month}/${response.data.year}`;
                  })
                }
              >
                Duplicate
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  runAction(
                    "share-budget",
                    async () => {
                      const shareText = `${selectedBudget.name}: ${money(selectedBudget.total_budget_amount, selectedBudget.currency_code)} for ${selectedBudget.month}/${selectedBudget.year}`;
                      if (typeof navigator !== "undefined" && navigator.clipboard) {
                        await navigator.clipboard.writeText(shareText);
                        return "Budget summary copied";
                      }
                      setBudgetOutput({ share: shareText });
                      return "Budget summary prepared";
                    },
                    false
                  )
                }
              >
                Share
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  runAction(
                    "budget-usage",
                    async () => {
                      const response = await financeApi.budgets.usage(selectedBudget.id);
                      setBudgetOutput(response.data);
                      return response.message;
                    },
                    false
                  )
                }
              >
                Usage
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  runAction(
                    "budget-get",
                    async () => {
                      const response = await financeApi.budgets.get(selectedBudget.id);
                      setBudgetOutput(response.data);
                      return response.message;
                    },
                    false
                  )
                }
              >
                Details
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  runAction(
                    "budget-category-status",
                    async () => {
                      const response = await financeApi.budgets.categoryStatus(selectedBudget.year, selectedBudget.month);
                      setBudgetOutput(response.data);
                      return response.message;
                    },
                    false
                  )
                }
              >
                Category status
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={() =>
                  runAction(
                    "budget-analytics",
                    async () => {
                      const [usage, categoryStatus, performance] = await Promise.all([
                        financeApi.budgets.usage(selectedBudget.id),
                        financeApi.budgets.categoryStatus(selectedBudget.year, selectedBudget.month),
                        financeApi.reports.budgetPerformance(selectedBudget.year, selectedBudget.month)
                      ]);
                      setBudgetOutput({
                        usage: usage.data,
                        categoryStatus: categoryStatus.data,
                        performance: performance.data
                      });
                      return "Budget analytics loaded";
                    },
                    false
                  )
                }
              >
                Analytics
              </Button>
            </div>
          </Panel>
        </>
      ) : null}
    </div>
  );
}

function ReportsSection({
  data,
  year,
  month,
  setYear,
  setMonth,
  output,
  setOutput,
  runAction,
  busyAction
}: {
  data: WorkspaceData;
  year: number;
  month: number;
  setYear: (value: number) => void;
  setMonth: (value: number) => void;
  output: unknown;
  setOutput: (value: unknown) => void;
  runAction: RunAction;
  busyAction: string | null;
}) {
  const [exportJobs, setExportJobs] = useState(listState(data.exportJobs));
  useEffect(() => {
    setExportJobs(listState(data.exportJobs));
  }, [data.exportJobs]);

  async function loadExportJobs(form: FormData, page = 1) {
    const response = await financeApi.reports.exportJobs({
      ...listParams(form, page),
      status: text(form, "status"),
      export_type: text(form, "export_type")
    });
    const completedJobs = await completeVisibleExportJobs(response.data);
    setExportJobs({ items: completedJobs, meta: { page: paginationPage(response), totalPages: paginationTotalPages(response) } });
  }

  const reportButtons = [
    ["Monthly", () => financeApi.reports.monthly(year, month)],
    ["Yearly", () => financeApi.reports.yearly(year)],
    ["Income vs expense", () => financeApi.reports.incomeVsExpense(year, month)],
    ["Category", () => financeApi.reports.categoryWise(year, month)],
    ["Wallet", () => financeApi.reports.walletWise(year, month)],
    ["Budget", () => financeApi.reports.budgetPerformance(year, month)],
    ["Savings", () => financeApi.reports.savings(year, month)],
    ["Monthly trend", () => financeApi.reports.dashboardMonthly(year)]
  ] as const;

  return (
    <div className="grid gap-5">
      <Panel title="Reports" description="Generate every available report for the selected period." action={<PeriodPicker year={year} month={month} setYear={setYear} setMonth={setMonth} />}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {reportButtons.map(([label, request]) => (
            <Button
              key={label}
              type="button"
              variant="secondary"
              onClick={() =>
                runAction(
                  `report-${label}`,
                  async () => {
                    const response = await request();
                    setOutput(response.data);
                    return response.message;
                  },
                  false
                )
              }
            >
              {label}
            </Button>
          ))}
        </div>
        <div className="mt-5">
          <ReportVisual title="Report result" value={output} />
        </div>
      </Panel>

      <Panel title="Export center" description="Create export jobs, check status, and download completed files.">
        <ExportForm runAction={runAction} busyAction={busyAction} year={year} month={month} />
        <ExportListControls
          meta={exportJobs.meta}
          onApply={(form) => runAction("filter-exports", async () => { await loadExportJobs(form); return "Export jobs filtered"; }, false)}
          onPage={(page, form) => runAction("page-exports", async () => { await loadExportJobs(form, page); return "Export job page loaded"; }, false)}
        />
        <div className="mt-5 grid gap-3">
          {exportJobs.items.map((job) => {
            const id = job.id || job.export_job_id || "";
            return (
              <div key={id} className="flex flex-col gap-3 rounded-md border p-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-semibold">{job.report_type} · {job.export_type}</p>
                  <p className="text-sm text-muted-foreground">{job.status}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="secondary"
                    onClick={() =>
                      runAction(
                        "export-job",
                        async () => {
                          if (job.file?.id) {
                            await downloadReportFile(job.file);
                            return "Download started";
                          }
                          const response = await financeApi.reports.exportJob(id);
                          setOutput(response.data);
                          setExportJobs((current) => ({
                            ...current,
                            items: current.items.map((item) => ((item.id || item.export_job_id) === id ? response.data : item))
                          }));
                          if (response.data.file?.id) {
                            await downloadReportFile(response.data.file);
                          }
                          return response.message;
                        },
                        false
                      )
                    }
                  >
                    {job.file?.id ? "Download" : "Prepare"}
                  </Button>
                </div>
              </div>
            );
          })}
          {!exportJobs.items.length ? <EmptyState text="No export jobs yet." /> : null}
        </div>
      </Panel>
    </div>
  );
}

function WalletForm({ runAction, busyAction }: { runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create wallet"
      busy={busyAction === "create-wallet"}
      onSubmit={(form) =>
        runAction("create-wallet", async () => {
          const response = await financeApi.wallets.create({
            name: text(form, "name"),
            type: text(form, "type"),
            currency_code: text(form, "currency_code"),
            opening_balance: text(form, "opening_balance"),
            is_default: checkbox(form, "is_default")
          });
          return response.message;
        })
      }
    >
      <Field label="Name"><Input name="name" placeholder="Main wallet" required /></Field>
      <Field label="Type"><EnumSelect name="type" values={["CASH", "BANK", "MOBILE_BANKING", "CARD", "SAVINGS", "INVESTMENT"]} /></Field>
      <Field label="Currency"><Input name="currency_code" defaultValue="USD" maxLength={3} required /></Field>
      <Field label="Opening balance"><Input name="opening_balance" type="number" min="0" step="0.01" defaultValue="0" required /></Field>
      <label className="flex items-center gap-2 text-sm font-medium"><input name="is_default" type="checkbox" /> Default wallet</label>
    </SimpleForm>
  );
}

function WalletEditForm({ wallet, runAction, busyAction }: { wallet: Wallet; runAction: RunAction; busyAction: string | null }) {
  const [details, setDetails] = useState<unknown>(null);
  return (
    <EditShell title={`Edit ${wallet.name}`}>
      <div className="mb-3 flex justify-end">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() =>
            runAction(
              "wallet-details",
              async () => {
                const response = await financeApi.wallets.get(wallet.id);
                setDetails(response.data);
                return response.message;
              },
              false
            )
          }
        >
          Fetch details
        </Button>
      </div>
      <SimpleForm
        button="Update wallet"
        busy={busyAction === "edit-wallet"}
        onSubmit={(form) =>
          runAction("edit-wallet", async () => {
            const response = await financeApi.wallets.update(wallet.id, {
              name: text(form, "name"),
              type: text(form, "type"),
              currency_code: text(form, "currency_code"),
              is_default: checkbox(form, "is_default"),
              is_active: checkbox(form, "is_active")
            });
            return response.message;
          })
        }
      >
        <Field label="Name"><Input name="name" defaultValue={wallet.name} required /></Field>
        <Field label="Type"><EnumSelect name="type" values={["CASH", "BANK", "MOBILE_BANKING", "CARD", "SAVINGS", "INVESTMENT"]} defaultValue={wallet.type} /></Field>
        <Field label="Currency"><Input name="currency_code" defaultValue={wallet.currency_code} maxLength={3} required /></Field>
        <label className="flex items-center gap-2 text-sm font-medium"><input name="is_default" type="checkbox" defaultChecked={wallet.is_default} /> Default</label>
        <label className="flex items-center gap-2 text-sm font-medium"><input name="is_active" type="checkbox" defaultChecked={wallet.is_active} /> Active</label>
      </SimpleForm>
      {details ? <DetailSummary title="Wallet details" value={details} /> : null}
    </EditShell>
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

function CategoryForm({ runAction, busyAction, categories }: { runAction: RunAction; busyAction: string | null; categories: Category[] }) {
  return (
    <SimpleForm
      button="Create category"
      busy={busyAction === "create-category"}
      onSubmit={(form) =>
        runAction("create-category", async () => {
          const parent = text(form, "parent_category_id");
          const response = await financeApi.categories.create({
            name: text(form, "name"),
            type: text(form, "type"),
            icon: text(form, "icon") || null,
            color: text(form, "color") || null,
            parent_category_id: parent || null
          });
          return response.message;
        })
      }
    >
      <Field label="Name"><Input name="name" placeholder="Groceries" required /></Field>
      <Field label="Type"><EnumSelect name="type" values={["EXPENSE", "INCOME"]} /></Field>
      <Field label="Icon"><Input name="icon" placeholder="shopping-bag" /></Field>
      <Field label="Color"><Input name="color" placeholder="#14b8a6" /></Field>
      <Field label="Parent"><OptionSelect name="parent_category_id" items={categories} placeholder="No parent" /></Field>
    </SimpleForm>
  );
}

function CategoryEditForm({
  category,
  categories,
  runAction,
  busyAction
}: {
  category: Category;
  categories: Category[];
  runAction: RunAction;
  busyAction: string | null;
}) {
  const [details, setDetails] = useState<unknown>(null);
  return (
    <EditShell title={`Edit ${category.name}`}>
      <div className="mb-3 flex justify-end">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() =>
            runAction(
              "category-details",
              async () => {
                const response = await financeApi.categories.get(category.id);
                setDetails(response.data);
                return response.message;
              },
              false
            )
          }
        >
          Fetch details
        </Button>
      </div>
      <SimpleForm
        button="Update category"
        busy={busyAction === "edit-category"}
        onSubmit={(form) =>
          runAction("edit-category", async () => {
            const parent = text(form, "parent_category_id");
            const response = await financeApi.categories.update(category.id, {
              name: text(form, "name"),
              icon: text(form, "icon") || null,
              color: text(form, "color") || null,
              parent_category_id: parent || null,
              is_active: checkbox(form, "is_active")
            });
            return response.message;
          })
        }
      >
        <Field label="Name"><Input name="name" defaultValue={category.name} required /></Field>
        <Field label="Icon"><Input name="icon" defaultValue={category.icon || ""} /></Field>
        <Field label="Color"><Input name="color" defaultValue={category.color || ""} /></Field>
        <Field label="Parent"><OptionSelect name="parent_category_id" items={categories.filter((item) => item.id !== category.id)} placeholder="No parent" defaultValue={category.parent_category_id || ""} /></Field>
        <label className="flex items-center gap-2 text-sm font-medium"><input name="is_active" type="checkbox" defaultChecked={category.is_active} /> Active</label>
      </SimpleForm>
      {details ? <DetailSummary title="Category details" value={details} /> : null}
    </EditShell>
  );
}

function PaymentMethodForm({ runAction, busyAction }: { runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create method"
      busy={busyAction === "create-method"}
      onSubmit={(form) =>
        runAction("create-method", async () => {
          const response = await financeApi.paymentMethods.create({ name: text(form, "name"), type: text(form, "type") });
          return response.message;
        })
      }
    >
      <Field label="Name"><Input name="name" placeholder="Visa card" required /></Field>
      <Field label="Type"><EnumSelect name="type" values={["CASH", "CARD", "BANK_TRANSFER", "MOBILE_BANKING", "OTHER"]} /></Field>
    </SimpleForm>
  );
}

function PaymentMethodEditForm({ method, runAction, busyAction }: { method: PaymentMethod; runAction: RunAction; busyAction: string | null }) {
  const [details, setDetails] = useState<unknown>(null);
  return (
    <EditShell title={`Edit ${method.name}`}>
      <div className="mb-3 flex flex-wrap justify-end gap-2">
        <Link href={`/dashboard/payment-methods/${method.id}`}>
          <Button type="button" variant="secondary" size="sm">
            <LinkIcon size={15} />
            Open page
          </Button>
        </Link>
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() =>
            runAction(
              "payment-method-details",
              async () => {
                const response = await financeApi.paymentMethods.get(method.id);
                setDetails(response.data);
                return response.message;
              },
              false
            )
          }
        >
          Fetch details
        </Button>
      </div>
      <SimpleForm
        button="Update method"
        busy={busyAction === "edit-method"}
        onSubmit={(form) =>
          runAction("edit-method", async () => {
            const response = await financeApi.paymentMethods.update(method.id, {
              name: text(form, "name"),
              type: text(form, "type"),
              is_active: checkbox(form, "is_active")
            });
            return response.message;
          })
        }
      >
        <Field label="Name"><Input name="name" defaultValue={method.name} required /></Field>
        <Field label="Type"><EnumSelect name="type" values={["CASH", "CARD", "BANK_TRANSFER", "MOBILE_BANKING", "OTHER"]} defaultValue={method.type} /></Field>
        <label className="flex items-center gap-2 text-sm font-medium"><input name="is_active" type="checkbox" defaultChecked={method.is_active} /> Active</label>
      </SimpleForm>
      {details ? <DetailSummary title="Payment method details" value={details} /> : null}
    </EditShell>
  );
}

function TagForm({ runAction, busyAction }: { runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create tag"
      busy={busyAction === "create-tag"}
      onSubmit={(form) =>
        runAction("create-tag", async () => {
          const response = await financeApi.tags.create({ name: text(form, "name") });
          return response.message;
        })
      }
    >
      <Field label="Name"><Input name="name" placeholder="family" required /></Field>
    </SimpleForm>
  );
}

function TransactionForm({ data, runAction, busyAction }: { data: WorkspaceData; runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create transaction"
      busy={busyAction === "create-transaction"}
      onSubmit={(form) =>
        runAction("create-transaction", async () => {
          const response = await financeApi.transactions.create({
            wallet_id: text(form, "wallet_id") || null,
            category_id: text(form, "category_id") || null,
            payment_method_id: text(form, "payment_method_id") || null,
            type: text(form, "type"),
            amount: text(form, "amount"),
            currency_code: text(form, "currency_code"),
            title: text(form, "title"),
            description: text(form, "description") || null,
            transaction_date: text(form, "transaction_date"),
            tags: text(form, "tags").split(",").map((tag) => tag.trim()).filter(Boolean),
            from_wallet_id: text(form, "from_wallet_id") || null,
            to_wallet_id: text(form, "to_wallet_id") || null
          });
          return response.message;
        })
      }
    >
      <Field label="Title"><Input name="title" placeholder="Lunch" required /></Field>
      <Field label="Type"><EnumSelect name="type" values={["EXPENSE", "INCOME", "TRANSFER", "ADJUSTMENT"]} /></Field>
      <Field label="Wallet"><OptionSelect name="wallet_id" items={data.wallets} required /></Field>
      <Field label="Category"><OptionSelect name="category_id" items={data.categories} required /></Field>
      <Field label="Payment method"><OptionSelect name="payment_method_id" items={data.paymentMethods} required /></Field>
      <Field label="Amount"><Input name="amount" type="number" min="0.01" step="0.01" required /></Field>
      <Field label="Currency"><Input name="currency_code" defaultValue="USD" maxLength={3} required /></Field>
      <Field label="Date"><Input name="transaction_date" type="date" defaultValue={isoToday()} required /></Field>
      <Field label="Transfer from"><OptionSelect name="from_wallet_id" items={data.wallets} placeholder="Optional" /></Field>
      <Field label="Transfer to"><OptionSelect name="to_wallet_id" items={data.wallets} placeholder="Optional" /></Field>
      <Field label="Tags"><Input name="tags" placeholder="food, family" /></Field>
      <Field label="Notes"><Textarea name="description" placeholder="Optional note" /></Field>
    </SimpleForm>
  );
}

function TransactionEditForm({
  transaction,
  data,
  runAction,
  busyAction
}: {
  transaction: Transaction;
  data: WorkspaceData;
  runAction: RunAction;
  busyAction: string | null;
}) {
  return (
    <EditShell title={`Edit ${transaction.title}`}>
      <SimpleForm
        button="Update transaction"
        busy={busyAction === "edit-transaction"}
        onSubmit={(form) =>
          runAction("edit-transaction", async () => {
            const response = await financeApi.transactions.update(transaction.id, {
              wallet_id: text(form, "wallet_id") || null,
              category_id: text(form, "category_id") || null,
              payment_method_id: text(form, "payment_method_id") || null,
              amount: text(form, "amount"),
              currency_code: text(form, "currency_code"),
              title: text(form, "title"),
              description: text(form, "description") || null,
              transaction_date: text(form, "transaction_date"),
              tags: text(form, "tags").split(",").map((tag) => tag.trim()).filter(Boolean)
            });
            return response.message;
          })
        }
      >
        <Field label="Title"><Input name="title" defaultValue={transaction.title} required /></Field>
        <Field label="Wallet"><OptionSelect name="wallet_id" items={data.wallets} required defaultValue={transaction.wallet?.id} /></Field>
        <Field label="Category"><OptionSelect name="category_id" items={data.categories} required defaultValue={transaction.category?.id} /></Field>
        <Field label="Payment method"><OptionSelect name="payment_method_id" items={data.paymentMethods} required defaultValue={transaction.payment_method?.id} /></Field>
        <Field label="Amount"><Input name="amount" type="number" min="0.01" step="0.01" defaultValue={transaction.amount} required /></Field>
        <Field label="Currency"><Input name="currency_code" defaultValue={transaction.currency_code} maxLength={3} required /></Field>
        <Field label="Date"><Input name="transaction_date" type="date" defaultValue={transaction.transaction_date} required /></Field>
        <Field label="Tags"><Input name="tags" defaultValue={transaction.tags?.join(", ") || ""} /></Field>
        <Field label="Notes"><Textarea name="description" defaultValue={transaction.description || ""} /></Field>
      </SimpleForm>
    </EditShell>
  );
}

function AttachmentManager({ transaction, runAction }: { transaction: Transaction; runAction: RunAction }) {
  const [attachments, setAttachments] = useState(transaction.attachments || []);

  async function load() {
    const response = await financeApi.attachments.list(transaction.id);
    setAttachments(response.data);
    return response.message;
  }

  return (
    <div className="grid gap-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <Input
          type="file"
          onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            if (!file) return;
            runAction(
              "upload-attachment",
              async () => {
                const response = await financeApi.attachments.upload(transaction.id, file);
                await load();
                return response.message;
              },
              false
            );
          }}
        />
        <Button type="button" variant="secondary" onClick={() => runAction("list-attachments", load, false)}>
          <Paperclip size={16} />
          List files
        </Button>
      </div>
      <EntityList
        items={attachments}
        render={(item) => `${item.file_name} · ${Math.round((item.file_size || 0) / 1024)} KB`}
        onDelete={(id) =>
          runAction(
            "delete-attachment",
            async () => {
              const response = await financeApi.attachments.delete(transaction.id, id);
              await load();
              return response.message;
            },
            false
          )
        }
      />
    </div>
  );
}

function RecurringForm({ data, runAction, busyAction }: { data: WorkspaceData; runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create recurring"
      busy={busyAction === "create-recurring"}
      onSubmit={(form) =>
        runAction("create-recurring", async () => {
          const response = await financeApi.recurring.create({
            wallet_id: text(form, "wallet_id"),
            category_id: text(form, "category_id"),
            type: text(form, "type"),
            amount: text(form, "amount"),
            currency_code: text(form, "currency_code"),
            title: text(form, "title"),
            description: text(form, "description") || null,
            frequency: text(form, "frequency"),
            start_date: text(form, "start_date"),
            end_date: text(form, "end_date") || null,
            next_run_date: text(form, "next_run_date"),
            is_active: checkbox(form, "is_active")
          });
          return response.message;
        })
      }
    >
      <Field label="Title"><Input name="title" placeholder="Rent" required /></Field>
      <Field label="Type"><EnumSelect name="type" values={["EXPENSE", "INCOME"]} /></Field>
      <Field label="Wallet"><OptionSelect name="wallet_id" items={data.wallets} required /></Field>
      <Field label="Category"><OptionSelect name="category_id" items={data.categories} required /></Field>
      <Field label="Frequency"><EnumSelect name="frequency" values={["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]} /></Field>
      <Field label="Amount"><Input name="amount" type="number" min="0.01" step="0.01" required /></Field>
      <Field label="Currency"><Input name="currency_code" defaultValue="USD" maxLength={3} required /></Field>
      <Field label="Start"><Input name="start_date" type="date" defaultValue={isoToday()} required /></Field>
      <Field label="Next run"><Input name="next_run_date" type="date" defaultValue={isoToday()} required /></Field>
      <Field label="End"><Input name="end_date" type="date" /></Field>
      <Field label="Notes"><Textarea name="description" /></Field>
      <label className="flex items-center gap-2 text-sm font-medium"><input name="is_active" type="checkbox" defaultChecked /> Active</label>
    </SimpleForm>
  );
}

function RecurringEditForm({
  recurring,
  data,
  runAction,
  busyAction
}: {
  recurring: RecurringTransaction;
  data: WorkspaceData;
  runAction: RunAction;
  busyAction: string | null;
}) {
  return (
    <EditShell title={`Edit ${recurring.title}`}>
      <SimpleForm
        button="Update recurring"
        busy={busyAction === "edit-recurring"}
        onSubmit={(form) =>
          runAction("edit-recurring", async () => {
            const response = await financeApi.recurring.update(recurring.id, {
              wallet_id: text(form, "wallet_id"),
              category_id: text(form, "category_id"),
              amount: text(form, "amount"),
              currency_code: text(form, "currency_code"),
              title: text(form, "title"),
              description: text(form, "description") || null,
              frequency: text(form, "frequency"),
              start_date: text(form, "start_date"),
              end_date: text(form, "end_date") || null,
              next_run_date: text(form, "next_run_date"),
              is_active: checkbox(form, "is_active")
            });
            return response.message;
          })
        }
      >
        <Field label="Title"><Input name="title" defaultValue={recurring.title} required /></Field>
        <Field label="Wallet"><OptionSelect name="wallet_id" items={data.wallets} required defaultValue={recurring.wallet?.id} /></Field>
        <Field label="Category"><OptionSelect name="category_id" items={data.categories} required defaultValue={recurring.category?.id} /></Field>
        <Field label="Frequency"><EnumSelect name="frequency" values={["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]} defaultValue={recurring.frequency} /></Field>
        <Field label="Amount"><Input name="amount" type="number" min="0.01" step="0.01" defaultValue={recurring.amount} required /></Field>
        <Field label="Currency"><Input name="currency_code" defaultValue={recurring.currency_code} maxLength={3} required /></Field>
        <Field label="Start"><Input name="start_date" type="date" defaultValue={recurring.start_date} required /></Field>
        <Field label="Next run"><Input name="next_run_date" type="date" defaultValue={recurring.next_run_date} required /></Field>
        <Field label="End"><Input name="end_date" type="date" defaultValue={recurring.end_date || ""} /></Field>
        <Field label="Notes"><Textarea name="description" defaultValue={recurring.description || ""} /></Field>
        <label className="flex items-center gap-2 text-sm font-medium"><input name="is_active" type="checkbox" defaultChecked={recurring.is_active} /> Active</label>
      </SimpleForm>
    </EditShell>
  );
}

function BudgetForm({ runAction, busyAction }: { runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create budget"
      busy={busyAction === "create-budget"}
      onSubmit={(form) =>
        runAction("create-budget", async () => {
          const response = await financeApi.budgets.create({
            name: text(form, "name"),
            year: numberValue(form, "year"),
            month: numberValue(form, "month"),
            total_budget_amount: text(form, "total_budget_amount"),
            currency_code: text(form, "currency_code")
          });
          return response.message;
        })
      }
    >
      <Field label="Name"><Input name="name" placeholder="May budget" required /></Field>
      <Field label="Year"><Input name="year" type="number" defaultValue={initialYear} required /></Field>
      <Field label="Month"><Input name="month" type="number" min="1" max="12" defaultValue={initialMonth} required /></Field>
      <Field label="Amount"><Input name="total_budget_amount" type="number" min="0.01" step="0.01" required /></Field>
      <Field label="Currency"><Input name="currency_code" defaultValue="USD" maxLength={3} required /></Field>
    </SimpleForm>
  );
}

function BudgetEditForm({ budget, runAction, busyAction }: { budget: Budget; runAction: RunAction; busyAction: string | null }) {
  return (
    <EditShell title={`Edit ${budget.name}`}>
      <SimpleForm
        button="Update budget"
        busy={busyAction === "edit-budget"}
        onSubmit={(form) =>
          runAction("edit-budget", async () => {
            const response = await financeApi.budgets.update(budget.id, {
              name: text(form, "name"),
              total_budget_amount: text(form, "total_budget_amount"),
              status: text(form, "status")
            });
            return response.message;
          })
        }
      >
        <Field label="Name"><Input name="name" defaultValue={budget.name} required /></Field>
        <Field label="Amount"><Input name="total_budget_amount" type="number" min="0.01" step="0.01" defaultValue={budget.total_budget_amount} required /></Field>
        <Field label="Status"><EnumSelect name="status" values={["ACTIVE", "ARCHIVED"]} defaultValue={budget.status} /></Field>
      </SimpleForm>
    </EditShell>
  );
}

function BudgetCategoryForm({
  budget,
  categories,
  runAction,
  busyAction
}: {
  budget: Budget;
  categories: Category[];
  runAction: RunAction;
  busyAction: string | null;
}) {
  return (
    <SimpleForm
      button="Add category"
      busy={busyAction === "create-budget-category"}
      onSubmit={(form) =>
        runAction("create-budget-category", async () => {
          const response = await financeApi.budgets.categories.create(budget.id, {
            category_id: text(form, "category_id"),
            category_name_snapshot: text(form, "category_name_snapshot"),
            budget_amount: text(form, "budget_amount"),
            alert_threshold_percentage: text(form, "alert_threshold_percentage")
          });
          return response.message;
        })
      }
    >
      <Field label="Category"><OptionSelect name="category_id" items={categories} required /></Field>
      <Field label="Name snapshot"><Input name="category_name_snapshot" placeholder="Groceries" required /></Field>
      <Field label="Amount"><Input name="budget_amount" type="number" min="0.01" step="0.01" required /></Field>
      <Field label="Alert %"><Input name="alert_threshold_percentage" type="number" min="1" max="100" defaultValue="80" required /></Field>
    </SimpleForm>
  );
}

function BudgetCategoryEditForm({
  budget,
  budgetCategory,
  runAction,
  busyAction,
  reload
}: {
  budget: Budget;
  budgetCategory: BudgetCategory;
  runAction: RunAction;
  busyAction: string | null;
  reload: () => Promise<void>;
}) {
  return (
    <EditShell title={`Edit ${budgetCategory.category_name_snapshot}`}>
      <SimpleForm
        button="Update allocation"
        busy={busyAction === "edit-budget-category"}
        onSubmit={(form) =>
          runAction(
            "edit-budget-category",
            async () => {
              const response = await financeApi.budgets.categories.update(budget.id, budgetCategory.id, {
                category_name_snapshot: text(form, "category_name_snapshot"),
                budget_amount: text(form, "budget_amount"),
                alert_threshold_percentage: text(form, "alert_threshold_percentage")
              });
              await reload();
              return response.message;
            },
            false
          )
        }
      >
        <Field label="Name"><Input name="category_name_snapshot" defaultValue={budgetCategory.category_name_snapshot} required /></Field>
        <Field label="Amount"><Input name="budget_amount" type="number" min="0.01" step="0.01" defaultValue={budgetCategory.budget_amount} required /></Field>
        <Field label="Alert %"><Input name="alert_threshold_percentage" type="number" min="1" max="100" defaultValue={budgetCategory.alert_threshold_percentage} required /></Field>
      </SimpleForm>
    </EditShell>
  );
}

function AlertRuleForm({ budget, runAction, busyAction }: { budget: Budget; runAction: RunAction; busyAction: string | null }) {
  return (
    <SimpleForm
      button="Create alert"
      busy={busyAction === "create-alert"}
      onSubmit={(form) =>
        runAction("create-alert", async () => {
          const response = await financeApi.budgets.alertRules.create(budget.id, {
            rule_type: text(form, "rule_type"),
            threshold_percentage: text(form, "threshold_percentage"),
            is_enabled: checkbox(form, "is_enabled")
          });
          return response.message;
        })
      }
    >
      <Field label="Rule type"><Input name="rule_type" defaultValue="THRESHOLD" required /></Field>
      <Field label="Threshold %"><Input name="threshold_percentage" type="number" min="1" max="100" defaultValue="80" required /></Field>
      <label className="flex items-center gap-2 text-sm font-medium"><input name="is_enabled" type="checkbox" defaultChecked /> Enabled</label>
    </SimpleForm>
  );
}

function AlertRuleEditForm({
  budget,
  rule,
  runAction,
  busyAction,
  reload
}: {
  budget: Budget;
  rule: BudgetAlertRule;
  runAction: RunAction;
  busyAction: string | null;
  reload: () => Promise<void>;
}) {
  return (
    <EditShell title={`Edit ${rule.rule_type}`}>
      <SimpleForm
        button="Update alert"
        busy={busyAction === "edit-alert"}
        onSubmit={(form) =>
          runAction(
            "edit-alert",
            async () => {
              const response = await financeApi.budgets.alertRules.update(budget.id, rule.id, {
                threshold_percentage: text(form, "threshold_percentage"),
                is_enabled: checkbox(form, "is_enabled")
              });
              await reload();
              return response.message;
            },
            false
          )
        }
      >
        <Field label="Threshold %"><Input name="threshold_percentage" type="number" min="1" max="100" defaultValue={rule.threshold_percentage} required /></Field>
        <label className="flex items-center gap-2 text-sm font-medium"><input name="is_enabled" type="checkbox" defaultChecked={rule.is_enabled} /> Enabled</label>
      </SimpleForm>
    </EditShell>
  );
}

function ExportForm({
  runAction,
  busyAction,
  year,
  month
}: {
  runAction: RunAction;
  busyAction: string | null;
  year: number;
  month: number;
}) {
  return (
    <SimpleForm
      button="Create export"
      busy={busyAction === "create-export"}
      onSubmit={(form) =>
        runAction("create-export", async () => {
          const response = await financeApi.reports.export({
            report_type: text(form, "report_type"),
            export_type: text(form, "export_type"),
            year: numberValue(form, "year"),
            month: numberValue(form, "month"),
            filters: {}
          });
          return response.message;
        })
      }
    >
      <Field label="Report"><EnumSelect name="report_type" values={["MONTHLY", "YEARLY", "INCOME_VS_EXPENSE", "CATEGORY_WISE", "WALLET_WISE", "BUDGET_PERFORMANCE", "SAVINGS"]} /></Field>
      <Field label="File type"><EnumSelect name="export_type" values={["CSV", "PDF", "XLSX"]} /></Field>
      <Field label="Year"><Input name="year" type="number" defaultValue={year} required /></Field>
      <Field label="Month"><Input name="month" type="number" min="1" max="12" defaultValue={month} required /></Field>
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

function ListControls({
  title,
  typeOptions = [],
  typeName = "type",
  meta,
  onApply,
  onPage
}: {
  title: string;
  typeOptions?: string[];
  typeName?: string;
  meta: ListMeta;
  onApply: (form: FormData) => void;
  onPage: (page: number, form: FormData) => void;
}) {
  return (
    <form
      className="mb-4 grid gap-3 rounded-md border bg-white p-3 sm:grid-cols-2 lg:grid-cols-5"
      onSubmit={(event) => {
        event.preventDefault();
        onApply(new FormData(event.currentTarget));
      }}
    >
      <div className="text-sm font-black lg:self-center">{title}</div>
      <Input name="search" placeholder="Search" />
      {typeOptions.length ? (
        <Select name={typeName}>
          <option value="">All</option>
          {typeOptions.map((item) => (
            <option key={item} value={item}>{human(item)}</option>
          ))}
        </Select>
      ) : null}
      <Select name="is_active">
        <option value="">Any status</option>
        <option value="true">Active</option>
        <option value="false">Inactive</option>
      </Select>
      <Select name="page_size" defaultValue="10">
        <option value="5">5</option>
        <option value="10">10</option>
        <option value="20">20</option>
        <option value="50">50</option>
      </Select>
      <div className="flex flex-wrap gap-2 sm:col-span-2 lg:col-span-5">
        <Button type="submit" size="sm">Apply</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page <= 1} onClick={(event) => onPage(meta.page - 1, new FormData(event.currentTarget.form!))}>Prev</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page >= meta.totalPages} onClick={(event) => onPage(meta.page + 1, new FormData(event.currentTarget.form!))}>Next</Button>
        <span className="self-center text-xs font-semibold text-muted-foreground">Page {meta.page} of {meta.totalPages}</span>
      </div>
    </form>
  );
}

function TransactionListControls({
  data,
  meta,
  onApply,
  onPage
}: {
  data: WorkspaceData;
  meta: ListMeta;
  onApply: (form: FormData) => void;
  onPage: (page: number, form: FormData) => void;
}) {
  return (
    <form
      className="mb-4 grid gap-3 rounded-md border bg-white p-3 sm:grid-cols-2 xl:grid-cols-6"
      onSubmit={(event) => {
        event.preventDefault();
        onApply(new FormData(event.currentTarget));
      }}
    >
      <Input name="search" placeholder="Search title or notes" />
      <EnumOptional name="type" values={["INCOME", "EXPENSE", "TRANSFER", "ADJUSTMENT"]} label="All types" />
      <OptionSelect name="wallet_id" items={data.wallets} placeholder="All wallets" />
      <OptionSelect name="category_id" items={data.categories} placeholder="All categories" />
      <OptionSelect name="payment_method_id" items={data.paymentMethods} placeholder="All methods" />
      <Select name="page_size" defaultValue="10"><option value="10">10</option><option value="20">20</option><option value="50">50</option></Select>
      <Input name="start_date" type="date" />
      <Input name="end_date" type="date" />
      <Select name="sort_by" defaultValue="transaction_date"><option value="transaction_date">Date</option><option value="created_at">Created</option></Select>
      <Select name="sort_order" defaultValue="desc"><option value="desc">Newest</option><option value="asc">Oldest</option></Select>
      <div className="flex flex-wrap gap-2 sm:col-span-2 xl:col-span-2">
        <Button type="submit" size="sm">Apply</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page <= 1} onClick={(event) => onPage(meta.page - 1, new FormData(event.currentTarget.form!))}>Prev</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page >= meta.totalPages} onClick={(event) => onPage(meta.page + 1, new FormData(event.currentTarget.form!))}>Next</Button>
        <span className="self-center text-xs font-semibold text-muted-foreground">Page {meta.page} of {meta.totalPages}</span>
      </div>
    </form>
  );
}

function BudgetListControls({ meta, onApply, onPage }: { meta: ListMeta; onApply: (form: FormData) => void; onPage: (page: number, form: FormData) => void }) {
  return (
    <form className="mb-4 grid gap-3 rounded-md border bg-white p-3 sm:grid-cols-2 lg:grid-cols-6" onSubmit={(event) => { event.preventDefault(); onApply(new FormData(event.currentTarget)); }}>
      <Input name="search" placeholder="Search budgets" />
      <Input name="year" type="number" placeholder="Year" />
      <Input name="month" type="number" min="1" max="12" placeholder="Month" />
      <EnumOptional name="status" values={["ACTIVE", "ARCHIVED"]} label="Any status" />
      <Select name="page_size" defaultValue="10"><option value="10">10</option><option value="20">20</option><option value="50">50</option></Select>
      <div className="flex flex-wrap gap-2">
        <Button type="submit" size="sm">Apply</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page <= 1} onClick={(event) => onPage(meta.page - 1, new FormData(event.currentTarget.form!))}>Prev</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page >= meta.totalPages} onClick={(event) => onPage(meta.page + 1, new FormData(event.currentTarget.form!))}>Next</Button>
      </div>
    </form>
  );
}

function ExportListControls({ meta, onApply, onPage }: { meta: ListMeta; onApply: (form: FormData) => void; onPage: (page: number, form: FormData) => void }) {
  return (
    <form className="mt-5 grid gap-3 rounded-md border bg-white p-3 sm:grid-cols-2 lg:grid-cols-5" onSubmit={(event) => { event.preventDefault(); onApply(new FormData(event.currentTarget)); }}>
      <EnumOptional name="status" values={["PENDING", "PROCESSING", "COMPLETED", "FAILED"]} label="Any status" />
      <EnumOptional name="export_type" values={["CSV", "PDF", "XLSX"]} label="Any file type" />
      <Select name="page_size" defaultValue="10"><option value="10">10</option><option value="20">20</option><option value="50">50</option></Select>
      <Button type="submit" size="sm">Apply</Button>
      <div className="flex flex-wrap gap-2">
        <Button type="button" variant="secondary" size="sm" disabled={meta.page <= 1} onClick={(event) => onPage(meta.page - 1, new FormData(event.currentTarget.form!))}>Prev</Button>
        <Button type="button" variant="secondary" size="sm" disabled={meta.page >= meta.totalPages} onClick={(event) => onPage(meta.page + 1, new FormData(event.currentTarget.form!))}>Next</Button>
      </div>
    </form>
  );
}

function EntityList<T extends { id: string }>({
  items,
  render,
  onDelete,
  onToggle,
  onSelect
}: {
  items: T[];
  render: (item: T) => string;
  onDelete?: (id: string) => void;
  onToggle?: (item: T) => void;
  onSelect?: (item: T) => void;
}) {
  return (
    <div className="grid gap-2">
      {items.map((item) => (
        <div key={item.id} className="group flex flex-col gap-3 rounded-md border bg-white p-3 transition hover:border-teal-300 hover:shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <button type="button" className="min-w-0 text-left text-sm font-semibold leading-6" onClick={() => onSelect?.(item)}>
            {render(item)}
          </button>
          <div className="flex flex-wrap gap-2">
            {onToggle ? (
              <Button type="button" variant="secondary" size="sm" onClick={() => onToggle(item)}>
                Quick edit
              </Button>
            ) : null}
            {onDelete ? <IconDelete onClick={() => onDelete(item.id)} /> : null}
          </div>
        </div>
      ))}
      {!items.length ? <EmptyState text="No records yet." /> : null}
    </div>
  );
}

function EditShell({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="mt-5 rounded-md border border-teal-200 bg-teal-50/60 p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-sm font-black text-teal-950">{title}</h3>
        <span className="rounded-full bg-white px-2 py-1 text-[11px] font-bold uppercase tracking-wide text-teal-700">
          Selected
        </span>
      </div>
      {children}
    </div>
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

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 rounded-md bg-white/8 px-3 py-2">
      <p className="text-xs text-white/55">{label}</p>
      <p className="truncate text-sm font-black">{value}</p>
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

function EnumSelect({ name, values, defaultValue }: { name: string; values: string[]; defaultValue?: string }) {
  return (
    <Select name={name} required defaultValue={defaultValue}>
      {values.map((value) => (
        <option key={value} value={value}>{human(value)}</option>
      ))}
    </Select>
  );
}

function EnumOptional({ name, values, label }: { name: string; values: string[]; label: string }) {
  return (
    <Select name={name}>
      <option value="">{label}</option>
      {values.map((value) => (
        <option key={value} value={value}>{human(value)}</option>
      ))}
    </Select>
  );
}

function OptionSelect({
  name,
  items,
  placeholder = "Select",
  required = false,
  defaultValue = ""
}: {
  name: string;
  items: Array<{ id: string; name: string }>;
  placeholder?: string;
  required?: boolean;
  defaultValue?: string;
}) {
  return (
    <Select name={name} required={required} defaultValue={defaultValue}>
      <option value="">{placeholder}</option>
      {items.map((item) => (
        <option key={item.id} value={item.id}>{item.name}</option>
      ))}
    </Select>
  );
}

function IconDelete({ onClick }: { onClick: () => void }) {
  return (
    <Button type="button" variant="danger" size="sm" onClick={onClick} className="px-3">
      <Trash2 size={16} />
      Delete
    </Button>
  );
}

function ReportVisual({ title, value }: { title: string; value: unknown }) {
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

function DetailSummary({ title, value }: { title: string; value: unknown }) {
  const fields = summaryFields(value);
  return (
    <div className="overflow-hidden rounded-md border bg-white shadow-sm">
      <div className="border-b bg-slate-50 px-3 py-2 text-sm font-bold">{title}</div>
      {fields.length ? (
        <div className="grid gap-2 p-3 sm:grid-cols-2">
          {fields.map(([key, item]) => (
            <div key={key} className="rounded-md border bg-white p-3">
              <p className="text-[11px] font-bold uppercase tracking-wide text-muted-foreground">{human(key)}</p>
              <p className="mt-1 break-words text-sm font-semibold">{String(item)}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 text-sm text-muted-foreground">No details to show.</div>
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

function numberValue(form: FormData, key: string) {
  return Number(text(form, key));
}

function checkbox(form: FormData, key: string) {
  return form.get(key) === "on";
}

function money(value: string | number, currency = "USD") {
  const amount = Number(value || 0);
  try {
    return new Intl.NumberFormat("en", { style: "currency", currency }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
}

function isoToday() {
  return new Date().toISOString().slice(0, 10);
}

function nextBudgetPeriod(year: number, month: number) {
  if (month >= 12) {
    return { year: year + 1, month: 1 };
  }
  return { year, month: month + 1 };
}

function listParams(form: FormData, page = 1) {
  const active = text(form, "is_active");
  return {
    page,
    page_size: text(form, "page_size") || 10,
    search: text(form, "search"),
    type: text(form, "type"),
    is_active: active === "" ? undefined : active
  };
}

function fromPaginated<T>(response: PaginatedResponse<T>): ListState<T> {
  return listState(response.data, paginationPage(response as PaginatedResponse<unknown>), paginationTotalPages(response as PaginatedResponse<unknown>));
}

function flattenNumbers(value: unknown, prefix = ""): Array<{ label: string; value: number }> {
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((item, index) => flattenNumbers(item, `${prefix}${index + 1}.`));
  }
  return Object.entries(value as Record<string, unknown>).flatMap(([key, item]) => {
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

function summaryFields(value: unknown): Array<[string, string | number | boolean]> {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return [];
  }
  return Object.entries(value as Record<string, unknown>)
    .filter(([, item]) => ["string", "number", "boolean"].includes(typeof item))
    .slice(0, 10) as Array<[string, string | number | boolean]>;
}

function human(value: string) {
  return value.replaceAll("_", " ").toLowerCase().replace(/\b\w/g, (match) => match.toUpperCase());
}
