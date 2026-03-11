export type NormDocument = {
  id: string;
  fileName: string;
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

const MOCK_DOCUMENTS: NormDocument[] = [
  {
    id: "doc-1",
    fileName: "grid-standard.pdf",
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

export async function listNormDocuments(_projectId: string): Promise<NormDocument[]> {
  return MOCK_DOCUMENTS;
}

export async function getNormDocumentBundle(
  _projectId: string,
  documentId: string
): Promise<NormDocumentBundle> {
  const document = MOCK_DOCUMENTS.find((item) => item.id === documentId) ?? MOCK_DOCUMENTS[0];

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
