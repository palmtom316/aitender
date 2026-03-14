import { afterEach, describe, expect, it, vi } from "vitest";

import {
  getNormDocumentBundle,
  getProcessingJobStatus,
  listNormDocuments,
  searchNorms,
  uploadNormDocument
} from "../norms";

describe("norms API client", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_BEARER_TOKEN;
    vi.unstubAllGlobals();
  });

  it("maps the document list response into frontend document rows", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    process.env.NEXT_PUBLIC_API_BEARER_TOKEN = "auth-token-pm";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          {
            id: "doc-1",
            file_name: "grid-standard.pdf",
            latest_job_id: "norm-job-1",
            status: "indexed",
            library_type: "norm_library"
          }
        ]
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await listNormDocuments("project-alpha");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/projects/project-alpha/norm-library/documents",
      {
        headers: { Authorization: "Bearer auth-token-pm" }
      }
    );
    expect(result).toEqual([
      {
        id: "doc-1",
        fileName: "grid-standard.pdf",
        latestJobId: "norm-job-1",
        status: "indexed",
        libraryType: "norm_library"
      }
    ]);
  });

  it("maps the document bundle response into frontend bundle state", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        document: {
          id: "doc-1",
          file_name: "grid-standard.pdf",
          latest_job_id: "norm-job-1",
          status: "indexed",
          library_type: "norm_library"
        },
        tree: [
          {
            label: "1",
            title: "General",
            children: [{ label: "1.1.1", title: "Clause text" }]
          }
        ],
        results: [
          {
            label: "1.1.1",
            title: "Clause text",
            page_start: 2,
            page_end: 2,
            summary_text: "Clause text",
            commentary_summary: "",
            path_labels: ["1", "1.1.1"],
            tags: ["mandatory"]
          }
        ]
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getNormDocumentBundle("project-alpha", "doc-1");

    expect(result).toEqual({
      document: {
        id: "doc-1",
        fileName: "grid-standard.pdf",
        latestJobId: "norm-job-1",
        status: "indexed",
        libraryType: "norm_library"
      },
      tree: [
        {
          label: "1",
          title: "General",
          children: [{ label: "1.1.1", title: "Clause text", children: undefined }]
        }
      ],
      results: [
        {
          label: "1.1.1",
          title: "Clause text",
          pageStart: 2,
          pageEnd: 2,
          summaryText: "Clause text",
          commentarySummary: "",
          contentPreview: "",
          pathLabels: ["1", "1.1.1"],
          tags: ["mandatory"]
        }
      ]
    });
  });

  it("maps the search response into frontend search results", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        items: [
          {
            label: "1.1.1",
            title: "Clause text",
            page_start: 2,
            page_end: 2,
            summary_text: "Clause text",
            commentary_summary: "",
            path_labels: ["1", "1.1.1"],
            tags: ["mandatory"]
          }
        ]
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await searchNorms({
      projectId: "project-alpha",
      documentId: "doc-1",
      query: "scope"
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.test/projects/project-alpha/norm-library/documents/doc-1/search?query=scope",
      {
        headers: {}
      }
    );
    expect(result).toEqual({
      items: [
        {
          label: "1.1.1",
          title: "Clause text",
          pageStart: 2,
          pageEnd: 2,
          summaryText: "Clause text",
          commentarySummary: "",
          contentPreview: "",
          pathLabels: ["1", "1.1.1"],
          tags: ["mandatory"]
        }
      ]
    });
  });

  it("uploads a PDF document with project and provider fields", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    process.env.NEXT_PUBLIC_API_BEARER_TOKEN = "auth-token-pm";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        document: {
          id: "doc-1",
          file_name: "grid-standard.pdf",
          latest_job_id: "norm-job-1",
          status: "indexed",
          library_type: "norm_library"
        }
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await uploadNormDocument({
      projectId: "project-alpha",
      file: new File(["pdf"], "grid-standard.pdf", {
        type: "application/pdf"
      })
    });

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/documents/upload", {
      method: "POST",
      headers: { Authorization: "Bearer auth-token-pm" },
      body: expect.any(FormData)
    });
    expect(result).toEqual({
      id: "doc-1",
      fileName: "grid-standard.pdf",
      latestJobId: "norm-job-1",
      status: "indexed",
      libraryType: "norm_library"
    });
  });
});

describe("getProcessingJobStatus", () => {
  afterEach(() => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_BEARER_TOKEN;
    vi.unstubAllGlobals();
  });

  it("maps the jobs API response into the frontend processing job view", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    process.env.NEXT_PUBLIC_API_BEARER_TOKEN = "auth-token-pm";
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        job: {
          id: "norm-job-1",
          provider_name: "mineru",
          status: "completed",
          error_message: null
        },
        audit_logs: [{ step: "job_started" }, { step: "ocr_completed" }]
      })
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await getProcessingJobStatus("norm-job-1");

    expect(fetchMock).toHaveBeenCalledWith("http://api.test/jobs/norm-job-1", {
      headers: { Authorization: "Bearer auth-token-pm" }
    });
    expect(result).toEqual({
      id: "norm-job-1",
      status: "completed",
      providerName: "mineru",
      errorMessage: null,
      auditSteps: ["job_started", "ocr_completed"]
    });
  });
});
