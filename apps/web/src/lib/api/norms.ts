import { readAccessTokenFromDocumentCookie } from "../auth/session";
import { getApiBaseUrl } from "./base-url";

export type NormDocument = {
  id: string;
  fileName: string;
  latestJobId: string | null;
  status: string;
  libraryType: string;
};

export type NormTreeNode = {
  label: string;
  title: string;
  children?: NormTreeNode[];
};

export type NormSearchResult = {
  label: string;
  title: string;
  pageStart: number;
  pageEnd: number;
  summaryText: string;
  commentarySummary: string;
  pathLabels: string[];
  tags: string[];
};

export type NormDocumentBundle = {
  document: NormDocument;
  tree: NormTreeNode[];
  results: NormSearchResult[];
};

export type ProcessingJobView = {
  id: string;
  status: "completed" | "failed" | "running";
  providerName: string;
  errorMessage: string | null;
  auditSteps: string[];
};

type ProcessingJobApiResponse = {
  job: {
    id: string;
    provider_name: string;
    status: "completed" | "failed" | "running";
    error_message: string | null;
  };
  audit_logs: Array<{
    step: string;
  }>;
};

type NormDocumentApiResponse = {
  id: string;
  file_name: string;
  latest_job_id: string | null;
  status: string;
  library_type: string;
};

type NormTreeApiNode = {
  label: string;
  title: string;
  children?: NormTreeApiNode[];
};

type NormSearchResultApiResponse = {
  label: string;
  title: string;
  page_start: number;
  page_end: number;
  summary_text: string;
  commentary_summary: string;
  path_labels: string[];
  tags?: string[];
};

type NormDocumentBundleApiResponse = {
  document: NormDocumentApiResponse;
  tree: NormTreeApiNode[];
  results: NormSearchResultApiResponse[];
};

type UploadNormDocumentApiResponse = {
  document: NormDocumentApiResponse;
};

const MOCK_DOCUMENTS: NormDocument[] = [
  {
    id: "doc-1",
    fileName: "grid-standard.pdf",
    latestJobId: "norm-job-1",
    status: "indexed",
    libraryType: "norm_library"
  }
];

const MOCK_TREE: NormTreeNode[] = [
  {
    label: "1",
    title: "General",
    children: [
      {
        label: "1.0.1",
        title: "General clause text for the project."
      },
      {
        label: "1.1",
        title: "Scope",
        children: [
          {
            label: "1.1.1",
            title: "Scope clause text that explains the implementation scope."
          }
        ]
      }
    ]
  },
  {
    label: "2",
    title: "Safety",
    children: [
      {
        label: "2.0.1",
        title: "Safety clause text for on-site execution."
      }
    ]
  }
];

const MOCK_RESULTS: NormSearchResult[] = [
  {
    label: "1.0.1",
    title: "General clause text for the project.",
    pageStart: 1,
    pageEnd: 1,
    summaryText: "General clause text for the project.",
    commentarySummary: "Commentary for the general clause.",
    pathLabels: ["1", "1.0.1"],
    tags: []
  },
  {
    label: "1.1.1",
    title: "Scope clause text that explains the implementation scope.",
    pageStart: 2,
    pageEnd: 2,
    summaryText: "Scope clause text that explains the implementation scope.",
    commentarySummary: "Commentary for the scope clause.",
    pathLabels: ["1", "1.1", "1.1.1"],
    tags: ["mandatory"]
  },
  {
    label: "2.0.1",
    title: "Safety clause text for on-site execution.",
    pageStart: 3,
    pageEnd: 3,
    summaryText: "Safety clause text for on-site execution.",
    commentarySummary: "Commentary for the safety clause.",
    pathLabels: ["2", "2.0.1"],
    tags: []
  }
];

const MOCK_JOB_RESPONSES: Record<string, ProcessingJobApiResponse> = {
  "norm-job-1": {
    job: {
      id: "norm-job-1",
      provider_name: "mineru",
      status: "completed",
      error_message: null
    },
    audit_logs: [{ step: "job_started" }, { step: "ocr_completed" }]
  }
};

function getAuthHeaders(accessToken?: string): HeadersInit {
  const token =
    accessToken ??
    process.env.AITENDER_API_BEARER_TOKEN ??
    process.env.NEXT_PUBLIC_API_BEARER_TOKEN ??
    readAccessTokenFromDocumentCookie();

  return token ? { Authorization: `Bearer ${token}` } : {};
}

function mapDocument(payload: NormDocumentApiResponse): NormDocument {
  return {
    id: payload.id,
    fileName: payload.file_name,
    latestJobId: payload.latest_job_id,
    status: payload.status,
    libraryType: payload.library_type
  };
}

function mapTree(payload: NormTreeApiNode[]): NormTreeNode[] {
  return payload.map((node) => ({
    label: node.label,
    title: node.title,
    children: node.children ? mapTree(node.children) : undefined
  }));
}

function mapSearchResult(
  payload: NormSearchResultApiResponse
): NormSearchResult {
  return {
    label: payload.label,
    title: payload.title,
    pageStart: payload.page_start,
    pageEnd: payload.page_end,
    summaryText: payload.summary_text,
    commentarySummary: payload.commentary_summary,
    pathLabels: payload.path_labels,
    tags: payload.tags ?? []
  };
}

export async function listNormDocuments(
  projectId: string,
  options?: { accessToken?: string }
): Promise<NormDocument[]> {
  const baseUrl = getApiBaseUrl();
  if (baseUrl) {
    const response = await fetch(
      `${baseUrl}/projects/${projectId}/norm-library/documents`,
      {
        headers: getAuthHeaders(options?.accessToken)
      }
    );
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    if (!response.ok) {
      throw new Error("Failed to load norm documents");
    }

    const payload = (await response.json()) as { items: NormDocumentApiResponse[] };
    return payload.items.map(mapDocument);
  }

  return MOCK_DOCUMENTS;
}

export async function uploadNormDocument(options: {
  projectId: string;
  file: File;
  providerName?: string;
  accessToken?: string;
}): Promise<NormDocument> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("Norm uploads require NEXT_PUBLIC_API_BASE_URL");
  }

  const formData = new FormData();
  formData.set("project_id", options.projectId);
  formData.set("provider_name", options.providerName ?? "mineru");
  formData.set("file", options.file);

  const response = await fetch(`${baseUrl}/documents/upload`, {
    method: "POST",
    headers: getAuthHeaders(options.accessToken),
    body: formData
  });
  if (response.status === 401) {
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    throw new Error("Failed to upload norm document");
  }

  const payload = (await response.json()) as UploadNormDocumentApiResponse;
  return mapDocument(payload.document);
}

export async function getNormDocumentBundle(
  projectId: string,
  documentId: string,
  options?: { accessToken?: string }
): Promise<NormDocumentBundle | null> {
  const baseUrl = getApiBaseUrl();
  if (baseUrl) {
    const response = await fetch(
      `${baseUrl}/projects/${projectId}/norm-library/documents/${documentId}`,
      {
        headers: getAuthHeaders(options?.accessToken)
      }
    );
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    if (response.status === 404) {
      return null;
    }
    if (!response.ok) {
      throw new Error("Failed to load norm document bundle");
    }

    const payload = (await response.json()) as NormDocumentBundleApiResponse;
    return {
      document: mapDocument(payload.document),
      tree: mapTree(payload.tree),
      results: payload.results.map(mapSearchResult)
    };
  }

  const document = MOCK_DOCUMENTS.find((item) => item.id === documentId);
  if (!document) {
    return null;
  }

  return {
    document,
    tree: MOCK_TREE,
    results: MOCK_RESULTS
  };
}

export async function searchNorms(options: {
  projectId: string;
  documentId: string;
  query?: string;
  clauseId?: string;
  pathPrefix?: string;
  accessToken?: string;
}): Promise<{ items: NormSearchResult[] }> {
  const baseUrl = getApiBaseUrl();
  if (baseUrl) {
    const params = new URLSearchParams();
    if (options.query?.trim()) {
      params.set("query", options.query.trim());
    }
    if (options.clauseId?.trim()) {
      params.set("clause_id", options.clauseId.trim());
    }
    if (options.pathPrefix?.trim()) {
      params.set("path_prefix", options.pathPrefix.trim());
    }

    const response = await fetch(
      `${baseUrl}/projects/${options.projectId}/norm-library/documents/${options.documentId}/search?${params.toString()}`,
      {
        headers: getAuthHeaders(options.accessToken)
      }
    );
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    if (!response.ok) {
      throw new Error("Failed to load search results");
    }

    const payload = (await response.json()) as {
      items: NormSearchResultApiResponse[];
    };
    return {
      items: payload.items.map(mapSearchResult)
    };
  }

  const normalizedQuery = options.query?.trim().toLowerCase() ?? "";
  let items = MOCK_RESULTS;
  if (options.clauseId?.trim()) {
    items = items.filter((item) => item.label === options.clauseId);
  }
  if (options.pathPrefix?.trim()) {
    items = items.filter((item) => item.pathLabels.includes(options.pathPrefix!));
  }
  if (!normalizedQuery) {
    return { items };
  }

  return {
    items: items.filter((item) => {
      const haystack = [
        item.label,
        item.title,
        item.summaryText,
        item.commentarySummary,
        item.pathLabels.join(" "),
        item.tags.join(" ")
      ]
        .join(" ")
        .toLowerCase();

      return normalizedQuery.split(/\s+/).every((token) => haystack.includes(token));
    })
  };
}

export async function getProcessingJobStatus(
  jobId: string,
  options?: { accessToken?: string }
): Promise<ProcessingJobView> {
  const baseUrl = getApiBaseUrl();
  if (baseUrl) {
    const response = await fetch(`${baseUrl}/jobs/${jobId}`, {
      headers: getAuthHeaders(options?.accessToken)
    });
    if (response.status === 401) {
      throw new Error("Unauthorized");
    }
    if (!response.ok) {
      throw new Error("Failed to load processing job status");
    }

    return mapProcessingJobResponse(
      (await response.json()) as ProcessingJobApiResponse
    );
  }

  const payload = MOCK_JOB_RESPONSES[jobId];
  if (!payload) {
    throw new Error(`Missing mock processing job: ${jobId}`);
  }

  return mapProcessingJobResponse(payload);
}

function mapProcessingJobResponse(
  payload: ProcessingJobApiResponse
): ProcessingJobView {
  return {
    id: payload.job.id,
    status: payload.job.status,
    providerName: payload.job.provider_name,
    errorMessage: payload.job.error_message,
    auditSteps: payload.audit_logs.map((item) => item.step)
  };
}
