"use client";

import { useQuery } from "@tanstack/react-query";
import { financeApi, type QueryValue } from "@/lib/finance-api";

export const categoriesQueryKey = (params: Record<string, QueryValue> = {}) => ["categories", params] as const;

export function useCategories(params: Record<string, QueryValue> = {}) {
  return useQuery({
    queryKey: categoriesQueryKey(params),
    queryFn: () => financeApi.categories.list(params)
  });
}
