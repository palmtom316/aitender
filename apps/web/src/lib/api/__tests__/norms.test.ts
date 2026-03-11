import { afterEach, describe, expect, it, vi } from "vitest";

import { getProcessingJobStatus } from "../norms";

describe("getProcessingJobStatus", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    vi.unstubAllGlobals();
  });

  it("maps the jobs API response into the frontend processing job view", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        job: {
          id: "norm-job-1",
          provider_name: "mineru",
          status: "completed",
          error_message: null,
        },
        audit_logs: [
          { step: "job_started" },
          { step: "ocr_completed" },
        ],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getProcessingJobStatus("norm-job-1");

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/jobs/norm-job-1");
    expect(result).toEqual({
      id: "norm-job-1",
      status: "completed",
      providerName: "mineru",
      errorMessage: null,
      auditSteps: ["job_started", "ocr_completed"],
    });
  });
});
