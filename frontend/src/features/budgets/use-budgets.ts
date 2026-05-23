"use client";

import { useQuery } from "@tanstack/react-query";
import { financeApi, type QueryValue } from "@/lib/finance-api";

export const budgetsQueryKey = (params: Record<string, QueryValue> = {}) => ["budgets", params] as const;

export function useBudgets(params: Record<string, QueryValue> = {}) {
  return useQuery({
    queryKey: budgetsQueryKey(params),
    queryFn: () => financeApi.budgets.list(params)
  });
}

export function useBudgetChildren(budgetId: string | undefined) {
  return useQuery({
    queryKey: ["budget-children", budgetId],
    enabled: Boolean(budgetId),
    queryFn: async () => {
      const id = budgetId || "";
      const [categories, alertRules] = await Promise.all([
        financeApi.budgets.categories.list(id),
        financeApi.budgets.alertRules.list(id)
      ]);
      return {
        categories: categories.data,
        alertRules: alertRules.data
      };
    }
  });
}
