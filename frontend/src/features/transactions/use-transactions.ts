"use client";

import { useQuery } from "@tanstack/react-query";
import { financeApi, type QueryValue } from "@/lib/finance-api";

export const transactionsQueryKey = (params: Record<string, QueryValue> = {}) => ["transactions", params] as const;

export function useTransactions(params: Record<string, QueryValue> = {}) {
  return useQuery({
    queryKey: transactionsQueryKey(params),
    queryFn: () => financeApi.transactions.list(params)
  });
}

export const recurringTransactionsQueryKey = (params: Record<string, QueryValue> = {}) => ["recurring-transactions", params] as const;

export function useRecurringTransactions(params: Record<string, QueryValue> = {}) {
  return useQuery({
    queryKey: recurringTransactionsQueryKey(params),
    queryFn: () => financeApi.recurring.list(params)
  });
}
