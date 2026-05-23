"use client";

import { useCallback, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { financeApi } from "@/lib/finance-api";
import { completeVisibleExportJobs } from "@/features/reports/export-jobs";
import { emptyWorkspaceData, type WorkspaceData } from "@/features/dashboard/types";

const workspaceQueryKey = ["workspace-data"] as const;

async function fetchWorkspaceData(): Promise<WorkspaceData> {
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
  return {
    wallets: wallets.data,
    categories: categories.data,
    paymentMethods: paymentMethods.data,
    tags: tags.data,
    transactions: transactions.data,
    recurring: recurring.data,
    budgets: budgets.data,
    exportJobs: completedExportJobs
  };
}

export function useWorkspaceData() {
  const queryClient = useQueryClient();
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const workspaceQuery = useQuery({
    queryKey: workspaceQueryKey,
    queryFn: fetchWorkspaceData
  });

  const loadCoreData = useCallback(async (showLoader = true) => {
    setActionError(null);
    try {
      if (showLoader) {
        await workspaceQuery.refetch();
      } else {
        await queryClient.invalidateQueries({ queryKey: workspaceQueryKey });
      }
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Unable to load workspace data");
    }
  }, [queryClient, workspaceQuery]);

  const runAction = useCallback(
    async (action: string, work: () => Promise<string | void>, refresh = true) => {
      setBusyAction(action);
      setActionError(null);
      setMessage(null);
      try {
        const result = await work();
        setMessage(result || "Done");
        if (refresh) {
          await queryClient.invalidateQueries({ queryKey: workspaceQueryKey });
        }
      } catch (err) {
        setActionError(err instanceof Error ? err.message : "Request failed");
      } finally {
        setBusyAction(null);
      }
    },
    [queryClient]
  );

  return {
    data: workspaceQuery.data ?? emptyWorkspaceData,
    isLoading: workspaceQuery.isLoading,
    busyAction,
    message,
    error: actionError ?? (workspaceQuery.error instanceof Error ? workspaceQuery.error.message : null),
    setMessage,
    loadCoreData,
    runAction
  };
}
