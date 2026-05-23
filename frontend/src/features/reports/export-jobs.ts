import { financeApi, type ExportJob } from "@/lib/finance-api";

export async function completeVisibleExportJobs(jobs: ExportJob[]) {
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
