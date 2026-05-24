import { apiBlobRequest, apiRequest } from "@/lib/api";

export type ApiResponse<T> = {
  message: string;
  data: T;
};

export type PaginatedResponse<T> = {
  message: string;
  data: T[];
  pagination?: {
    page: number;
    page_size?: number;
    pageSize?: number;
    total_items?: number;
    totalItems?: number;
    total_pages?: number;
    totalPages?: number;
  };
};

export function paginationTotalPages(response: PaginatedResponse<unknown>) {
  return response.pagination?.total_pages ?? response.pagination?.totalPages ?? 1;
}

export function paginationPage(response: PaginatedResponse<unknown>) {
  return response.pagination?.page ?? 1;
}

export type Wallet = {
  id: string;
  name: string;
  type: string;
  currency_code: string;
  opening_balance: string;
  current_balance: string;
  is_default: boolean;
  is_active: boolean;
};

export type Category = {
  id: string;
  name: string;
  type: string;
  icon?: string | null;
  color?: string | null;
  parent_category_id?: string | null;
  is_system?: boolean;
  is_active: boolean;
};

export type PaymentMethod = {
  id: string;
  name: string;
  type: string;
  is_active: boolean;
};

export type Tag = {
  id: string;
  name: string;
};

export type Ref = {
  id: string;
  name: string;
  type?: string | null;
};

export type Attachment = {
  id: string;
  file_url?: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
};

export type Transaction = {
  id: string;
  wallet: Ref;
  category: Ref;
  payment_method: Ref;
  type: string;
  amount: string;
  currency_code: string;
  title: string;
  description?: string | null;
  transaction_date: string;
  tags: string[];
  attachments: Attachment[];
  is_deleted: boolean;
};

export type RecurringTransaction = {
  id: string;
  wallet: Ref;
  category: Ref;
  type: string;
  amount: string;
  currency_code: string;
  title: string;
  description?: string | null;
  frequency: string;
  start_date: string;
  end_date?: string | null;
  next_run_date: string;
  is_active: boolean;
};

export type BudgetCategory = {
  id: string;
  budget_id: string;
  category_id: string;
  category_name_snapshot: string;
  budget_amount: string;
  alert_threshold_percentage: string;
};

export type BudgetAlertRule = {
  id: string;
  budget_id: string;
  rule_type: string;
  threshold_percentage: string;
  is_enabled: boolean;
};

export type Budget = {
  id: string;
  name: string;
  year: number;
  month: number;
  total_budget_amount: string;
  currency_code: string;
  status: string;
  categories?: BudgetCategory[];
  alert_rules?: BudgetAlertRule[];
};

export type ReportFile = {
  id: string;
  file_url?: string | null;
  file_name: string;
  file_type: string;
  file_size: number;
};

export type ExportJob = {
  id?: string;
  export_job_id?: string;
  report_snapshot_id: string;
  report_type: string;
  export_type: string;
  status: string;
  error_message?: string | null;
  requested_at: string;
  file?: ReportFile | null;
};

export type QueryValue = string | number | boolean | undefined | null;
export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };
export type ReportData = { [key: string]: JsonValue };
export type MonthlySummary = ReportData;
export type YearlySummary = ReportData;
export type CategorySummary = ReportData;
export type WalletSummary = ReportData;
export type DashboardReport = ReportData;
export type BudgetMonthlyStatus = ReportData;
export type BudgetCategoryStatus = ReportData;
export type BudgetUsage = ReportData;
export type ReportResult = ReportData;

export function query(params: Record<string, QueryValue>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  });
  const value = search.toString();
  return value ? `?${value}` : "";
}

export async function downloadReportFile(file: ReportFile) {
  const blob = await apiBlobRequest(`/api/reports/files/${file.id}/download`);
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = file.file_name || `report-${file.id}.${file.file_type.toLowerCase()}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function idempotencyHeaders() {
  const random =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return { "Idempotency-Key": random };
}

export const financeApi = {
  wallets: {
    list: (params: Record<string, QueryValue> = {}) => apiRequest<PaginatedResponse<Wallet>>(`/api/wallets${query(params)}`),
    create: (body: unknown) => apiRequest<ApiResponse<Wallet>>("/api/wallets", { method: "POST", body: JSON.stringify(body) }),
    get: (id: string) => apiRequest<ApiResponse<Wallet>>(`/api/wallets/${id}`),
    update: (id: string, body: unknown) =>
      apiRequest<ApiResponse<Wallet>>(`/api/wallets/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/wallets/${id}`, { method: "DELETE" })
  },
  categories: {
    list: (params: Record<string, QueryValue> = {}) => apiRequest<PaginatedResponse<Category>>(`/api/categories${query(params)}`),
    create: (body: unknown) => apiRequest<ApiResponse<Category>>("/api/categories", { method: "POST", body: JSON.stringify(body) }),
    get: (id: string) => apiRequest<ApiResponse<Category>>(`/api/categories/${id}`),
    update: (id: string, body: unknown) =>
      apiRequest<ApiResponse<Category>>(`/api/categories/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/categories/${id}`, { method: "DELETE" })
  },
  paymentMethods: {
    list: (params: Record<string, QueryValue> = {}) =>
      apiRequest<PaginatedResponse<PaymentMethod>>(`/api/payment-methods${query(params)}`),
    create: (body: unknown) =>
      apiRequest<ApiResponse<PaymentMethod>>("/api/payment-methods", { method: "POST", body: JSON.stringify(body) }),
    get: (id: string) => apiRequest<ApiResponse<PaymentMethod>>(`/api/payment-methods/${id}`),
    update: (id: string, body: unknown) =>
      apiRequest<ApiResponse<PaymentMethod>>(`/api/payment-methods/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/payment-methods/${id}`, { method: "DELETE" })
  },
  tags: {
    list: () => apiRequest<ApiResponse<Tag[]>>("/api/tags"),
    create: (body: unknown) => apiRequest<ApiResponse<Tag>>("/api/tags", { method: "POST", body: JSON.stringify(body) }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/tags/${id}`, { method: "DELETE" })
  },
  transactions: {
    list: (params: Record<string, QueryValue> = {}) =>
      apiRequest<PaginatedResponse<Transaction>>(`/api/transactions${query(params)}`),
    create: (body: unknown) =>
      apiRequest<ApiResponse<Transaction>>("/api/transactions", {
        method: "POST",
        headers: idempotencyHeaders(),
        body: JSON.stringify(body)
      }),
    get: (id: string) => apiRequest<ApiResponse<Transaction>>(`/api/transactions/${id}`),
    update: (id: string, body: unknown) =>
      apiRequest<ApiResponse<Transaction>>(`/api/transactions/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/transactions/${id}`, { method: "DELETE" }),
    monthlySummary: (year: number, month: number) =>
      apiRequest<ApiResponse<MonthlySummary>>(`/api/transactions/summary/monthly${query({ year, month })}`),
    yearlySummary: (year: number) => apiRequest<ApiResponse<YearlySummary>>(`/api/transactions/summary/yearly${query({ year })}`),
    categorySummary: (year: number, month: number, type = "EXPENSE") =>
      apiRequest<ApiResponse<CategorySummary>>(`/api/transactions/summary/category-wise${query({ year, month, type })}`),
    walletSummary: (year: number, month: number) =>
      apiRequest<ApiResponse<WalletSummary>>(`/api/transactions/summary/wallet-wise${query({ year, month })}`)
  },
  attachments: {
    list: (transactionId: string) => apiRequest<ApiResponse<Attachment[]>>(`/api/transactions/${transactionId}/attachments`),
    upload: (transactionId: string, file: File) => {
      const body = new FormData();
      body.append("file", file);
      return apiRequest<ApiResponse<Attachment>>(`/api/transactions/${transactionId}/attachments`, { method: "POST", body });
    },
    delete: (transactionId: string, attachmentId: string) =>
      apiRequest<ApiResponse<null>>(`/api/transactions/${transactionId}/attachments/${attachmentId}`, { method: "DELETE" })
  },
  recurring: {
    list: (params: Record<string, QueryValue> = {}) =>
      apiRequest<PaginatedResponse<RecurringTransaction>>(`/api/recurring-transactions${query(params)}`),
    create: (body: unknown) =>
      apiRequest<ApiResponse<RecurringTransaction>>("/api/recurring-transactions", { method: "POST", body: JSON.stringify(body) }),
    update: (id: string, body: unknown) =>
      apiRequest<ApiResponse<RecurringTransaction>>(`/api/recurring-transactions/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body)
      }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/recurring-transactions/${id}`, { method: "DELETE" })
  },
  budgets: {
    list: (params: Record<string, QueryValue> = {}) => apiRequest<PaginatedResponse<Budget>>(`/api/budgets${query(params)}`),
    create: (body: unknown) => apiRequest<ApiResponse<Budget>>("/api/budgets", { method: "POST", body: JSON.stringify(body) }),
    get: (id: string) => apiRequest<ApiResponse<Budget>>(`/api/budgets/${id}`),
    update: (id: string, body: unknown) =>
      apiRequest<ApiResponse<Budget>>(`/api/budgets/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: string) => apiRequest<ApiResponse<null>>(`/api/budgets/${id}`, { method: "DELETE" }),
    monthlyStatus: (year: number, month: number) => apiRequest<ApiResponse<BudgetMonthlyStatus>>(`/api/budgets/status/monthly${query({ year, month })}`),
    categoryStatus: (year: number, month: number) =>
      apiRequest<ApiResponse<BudgetCategoryStatus>>(`/api/budgets/status/category-wise${query({ year, month })}`),
    usage: (id: string) => apiRequest<ApiResponse<BudgetUsage>>(`/api/budgets/${id}/usage`),
    categories: {
      list: (budgetId: string) => apiRequest<ApiResponse<BudgetCategory[]>>(`/api/budgets/${budgetId}/categories`),
      create: (budgetId: string, body: unknown) =>
        apiRequest<ApiResponse<BudgetCategory>>(`/api/budgets/${budgetId}/categories`, { method: "POST", body: JSON.stringify(body) }),
      update: (budgetId: string, categoryId: string, body: unknown) =>
        apiRequest<ApiResponse<BudgetCategory>>(`/api/budgets/${budgetId}/categories/${categoryId}`, {
          method: "PATCH",
          body: JSON.stringify(body)
        }),
      delete: (budgetId: string, categoryId: string) =>
        apiRequest<ApiResponse<null>>(`/api/budgets/${budgetId}/categories/${categoryId}`, { method: "DELETE" })
    },
    alertRules: {
      list: (budgetId: string) => apiRequest<ApiResponse<BudgetAlertRule[]>>(`/api/budgets/${budgetId}/alert-rules`),
      create: (budgetId: string, body: unknown) =>
        apiRequest<ApiResponse<BudgetAlertRule>>(`/api/budgets/${budgetId}/alert-rules`, { method: "POST", body: JSON.stringify(body) }),
      update: (budgetId: string, ruleId: string, body: unknown) =>
        apiRequest<ApiResponse<BudgetAlertRule>>(`/api/budgets/${budgetId}/alert-rules/${ruleId}`, {
          method: "PATCH",
          body: JSON.stringify(body)
        }),
      delete: (budgetId: string, ruleId: string) =>
        apiRequest<ApiResponse<null>>(`/api/budgets/${budgetId}/alert-rules/${ruleId}`, { method: "DELETE" })
    }
  },
  reports: {
    dashboard: (year: number, month: number) => apiRequest<ApiResponse<DashboardReport>>(`/api/reports/dashboard${query({ year, month })}`),
    dashboardMonthly: (year: number) => apiRequest<ApiResponse<ReportResult>>(`/api/reports/dashboard/monthly-summary${query({ year })}`),
    monthly: (year: number, month: number) => apiRequest<ApiResponse<ReportResult>>(`/api/reports/monthly${query({ year, month })}`),
    yearly: (year: number) => apiRequest<ApiResponse<ReportResult>>(`/api/reports/yearly${query({ year })}`),
    incomeVsExpense: (year: number, month?: number) =>
      apiRequest<ApiResponse<ReportResult>>(`/api/reports/income-vs-expense${query({ year, month })}`),
    categoryWise: (year: number, month: number, type = "EXPENSE") =>
      apiRequest<ApiResponse<ReportResult>>(`/api/reports/category-wise${query({ year, month, type })}`),
    walletWise: (year: number, month: number) => apiRequest<ApiResponse<ReportResult>>(`/api/reports/wallet-wise${query({ year, month })}`),
    budgetPerformance: (year: number, month: number) =>
      apiRequest<ApiResponse<ReportResult>>(`/api/reports/budget-performance${query({ year, month })}`),
    savings: (year: number, month: number) => apiRequest<ApiResponse<ReportResult>>(`/api/reports/savings${query({ year, month })}`),
    export: (body: unknown) =>
      apiRequest<ApiResponse<ExportJob>>("/api/reports/export", {
        method: "POST",
        headers: idempotencyHeaders(),
        body: JSON.stringify(body)
      }),
    exportJobs: (params: Record<string, QueryValue> = {}) =>
      apiRequest<PaginatedResponse<ExportJob>>(`/api/reports/export-jobs${query(params)}`),
    exportJob: (id: string) => apiRequest<ApiResponse<ExportJob>>(`/api/reports/export-jobs/${id}`),
    downloadUrl: (id: string) => `/api/reports/files/${id}/download`
  }
};
