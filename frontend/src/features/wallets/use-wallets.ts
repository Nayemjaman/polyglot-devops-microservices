"use client";

import { useQuery } from "@tanstack/react-query";
import { financeApi, type QueryValue } from "@/lib/finance-api";

export const walletsQueryKey = (params: Record<string, QueryValue> = {}) => ["wallets", params] as const;

export function useWallets(params: Record<string, QueryValue> = {}) {
  return useQuery({
    queryKey: walletsQueryKey(params),
    queryFn: () => financeApi.wallets.list(params)
  });
}
