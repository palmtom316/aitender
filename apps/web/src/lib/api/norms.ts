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
    pathLabels: ["1", "1.0.1"]
  },
  {
    label: "1.1.1",
    title: "Scope clause text that explains the implementation scope.",
    pageStart: 2,
    pageEnd: 2,
    summaryText: "Scope clause text that explains the implementation scope.",
    commentarySummary: "Commentary for the scope clause.",
    pathLabels: ["1", "1.1", "1.1.1"]
  },
  {
    label: "2.0.1",
    title: "Safety clause text for on-site execution.",
    pageStart: 3,
    pageEnd: 3,
    summaryText: "Safety clause text for on-site execution.",
    commentarySummary: "Commentary for the safety clause.",
    pathLabels: ["2", "2.0.1"]
  }
];

const MOCK_JOB_RESPONSES: Record<string, ProcessingJobApiResponse> = {
  "norm-job-1": {
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
  },
};

export async function listNormDocuments(_projectId: string): Promise<NormDocument[]> {
  return MOCK_DOCUMENTS;
}

export async function getNormDocumentBundle(
  _projectId: string,
  documentId: string
): Promise<NormDocumentBundle | null> {
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
  query: string;
}): Promise<{ items: NormSearchResult[] }> {
  const normalizedQuery = options.query.trim().toLowerCase();
  if (!normalizedQuery) {
    return { items: [] };
  }

  return {
    items: MOCK_RESULTS.filter((item) => {
      const haystack = [
        item.label,
        item.title,
        item.summaryText,
        item.commentarySummary,
        item.pathLabels.join(" ")
      ]
        .join(" ")
        .toLowerCase();

      return normalizedQuery.split(/\s+/).every((token) => haystack.includes(token));
    })
  };
}

export async function getProcessingJobStatus(
  jobId: string
): Promise<ProcessingJobView> {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (baseUrl) {
    const response = await fetch(`${baseUrl}/jobs/${jobId}`);
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
    auditSteps: payload.audit_logs.map((item) => item.step),
  };
}
