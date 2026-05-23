import type {
  Budget,
  Category,
  ExportJob,
  PaymentMethod,
  RecurringTransaction,
  Tag,
  Transaction,
  Wallet
} from "@/lib/finance-api";

export type SectionId = "overview" | "setup" | "transactions" | "budgets" | "reports";

export type WorkspaceData = {
  wallets: Wallet[];
  categories: Category[];
  paymentMethods: PaymentMethod[];
  tags: Tag[];
  transactions: Transaction[];
  recurring: RecurringTransaction[];
  budgets: Budget[];
  exportJobs: ExportJob[];
};

export type ListMeta = {
  page: number;
  totalPages: number;
};

export type ListState<T> = {
  items: T[];
  meta: ListMeta;
};

export type RunAction = (action: string, work: () => Promise<string | void>, refresh?: boolean) => Promise<void>;

export const emptyWorkspaceData: WorkspaceData = {
  wallets: [],
  categories: [],
  paymentMethods: [],
  tags: [],
  transactions: [],
  recurring: [],
  budgets: [],
  exportJobs: []
};
