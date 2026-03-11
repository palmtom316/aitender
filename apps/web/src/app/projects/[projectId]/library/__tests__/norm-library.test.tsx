import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import LibraryPage from "../page";
import NormDocumentPage from "../norms/[documentId]/page";
import {
  getNormDocumentBundle,
  getProcessingJobStatus,
  listNormDocuments,
  searchNorms
} from "../../../../../lib/api/norms";

vi.mock("../../../../../lib/api/norms", () => ({
  getNormDocumentBundle: vi.fn(),
  getProcessingJobStatus: vi.fn(),
  listNormDocuments: vi.fn(),
  searchNorms: vi.fn()
}));

const listNormDocumentsMock = vi.mocked(listNormDocuments);
const getNormDocumentBundleMock = vi.mocked(getNormDocumentBundle);
const getProcessingJobStatusMock = vi.mocked(getProcessingJobStatus);
const searchNormsMock = vi.mocked(searchNorms);

const defaultDocuments = [
  {
    id: "doc-1",
    fileName: "grid-standard.pdf",
    latestJobId: "norm-job-1",
    status: "indexed",
    libraryType: "norm_library"
  }
];

const defaultBundle = {
  document: defaultDocuments[0],
  tree: [
    {
      label: "1",
      title: "General",
      children: [
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
    }
  ],
  results: [
    {
      label: "1.1.1",
      title: "Scope clause text that explains the implementation scope.",
      pageStart: 2,
      pageEnd: 2,
      summaryText: "Scope clause text that explains the implementation scope.",
      commentarySummary: "Commentary for the scope clause.",
      pathLabels: ["1", "1.1", "1.1.1"]
    }
  ]
};

describe("NormLibraryPage", () => {
  beforeEach(() => {
    listNormDocumentsMock.mockResolvedValue(defaultDocuments);
    getNormDocumentBundleMock.mockResolvedValue(defaultBundle);
    getProcessingJobStatusMock.mockResolvedValue({
      id: "norm-job-1",
      status: "completed",
      providerName: "mineru",
      errorMessage: null,
      auditSteps: ["job_started", "ocr_completed"]
    });
    searchNormsMock.mockResolvedValue({ items: defaultBundle.results });
  });

  it("shows documents, searches norms, and syncs detail panels from the selected result", async () => {
    render(
      await LibraryPage({
        params: Promise.resolve({ projectId: "project-alpha" })
      })
    );

    expect(getProcessingJobStatusMock).toHaveBeenCalledWith("norm-job-1");
    expect(screen.getByText("grid-standard.pdf")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search norms"), {
      target: { value: "scope" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    const resultButton = await screen.findByRole("button", {
      name: "1.1.1 Scope clause text that explains the implementation scope."
    });
    fireEvent.click(resultButton);

    expect(
      screen.getByRole("heading", {
        name: "1.1.1 Scope clause text that explains the implementation scope."
      })
    ).toBeInTheDocument();
    expect(screen.getByText("Commentary for the scope clause.")).toBeInTheDocument();
    expect(screen.getByText("Pages 2-2")).toBeInTheDocument();
    expect(screen.getByRole("treeitem", { name: "1.1.1" })).toHaveAttribute(
      "aria-current",
      "true"
    );
  });

  it("shows an empty state when the project has no norm documents yet", async () => {
    listNormDocumentsMock.mockResolvedValueOnce([]);

    render(
      await LibraryPage({
        params: Promise.resolve({ projectId: "project-empty" })
      })
    );

    expect(screen.getByText("No norm documents uploaded yet.")).toBeInTheDocument();
  });

  it("shows a not-found state when the requested document bundle is missing", async () => {
    getNormDocumentBundleMock.mockResolvedValueOnce(null);

    render(
      await NormDocumentPage({
        params: Promise.resolve({
          documentId: "missing-doc",
          projectId: "project-alpha"
        })
      })
    );

    expect(screen.getByText("Document not found.")).toBeInTheDocument();
  });

  it("shows a recoverable error when norm search fails", async () => {
    searchNormsMock.mockRejectedValueOnce(new Error("network down"));

    render(
      await LibraryPage({
        params: Promise.resolve({ projectId: "project-alpha" })
      })
    );

    fireEvent.change(screen.getByLabelText("Search norms"), {
      target: { value: "scope" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    expect(
      await screen.findByText("Failed to load search results.")
    ).toBeInTheDocument();
  });
});
