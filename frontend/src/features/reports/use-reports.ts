"use client";

import { useQuery } from "@tanstack/react-query";
import { financeApi, type QueryValue } from "@/lib/finance-api";
import { completeVisibleExportJobs } from "@/features/reports/export-jobs";

export const exportJobsQueryKey = (params: Record<string, QueryValue> = {}) => ["export-jobs", params] as const;

export function useExportJobs(params: Record<string, QueryValue> = {}) {
  return useQuery({
    queryKey: exportJobsQueryKey(params),
    queryFn: async () => {
      const response = await financeApi.reports.exportJobs(params);
      return {
        ...response,
        data: await completeVisibleExportJobs(response.data)
      };
    }
  });
}
