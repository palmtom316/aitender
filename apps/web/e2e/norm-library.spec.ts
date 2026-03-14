import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import LibraryPage from "../src/app/projects/[projectId]/library/page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    refresh: vi.fn()
  })
}));

vi.mock("../src/lib/auth/server-session", () => ({
  requireAccessToken: vi.fn().mockResolvedValue("auth-token-pm")
}));

vi.mock("../src/lib/api/norms", () => ({
  listNormDocuments: vi.fn().mockResolvedValue([
    {
      id: "doc-1",
      fileName: "grid-standard.pdf",
      latestJobId: "norm-job-1",
      status: "indexed",
      libraryType: "norm_library"
    }
  ]),
  getNormDocumentBundle: vi.fn().mockResolvedValue({
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
        contentPreview: "1.1.1 Scope clause text that explains the implementation scope.",
        pathLabels: ["1", "1.1", "1.1.1"],
        tags: ["mandatory"]
      }
    ],
    commentaryResults: []
  }),
  getProcessingJobStatus: vi.fn().mockResolvedValue({
    id: "norm-job-1",
    status: "completed",
    providerName: "mineru",
    errorMessage: null,
    auditSteps: ["job_started", "ocr_completed"]
  }),
  searchNorms: vi.fn().mockResolvedValue({
    items: [
      {
        label: "1.1.1",
        title: "Scope clause text that explains the implementation scope.",
        pageStart: 2,
        pageEnd: 2,
        summaryText: "Scope clause text that explains the implementation scope.",
        commentarySummary: "Commentary for the scope clause.",
        contentPreview: "1.1.1 Scope clause text that explains the implementation scope.",
        pathLabels: ["1", "1.1", "1.1.1"],
        tags: ["mandatory"]
      }
    ],
    commentaryItems: []
  }),
  uploadNormDocument: vi.fn()
}));

describe("NormLibraryE2E", () => {
  it("renders processing status and completes the search workflow", async () => {
    render(
      await LibraryPage({
        params: Promise.resolve({ projectId: "project-alpha" })
      })
    );

    expect(screen.getByText("Status: completed")).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search norms"), {
      target: { value: "scope" }
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    fireEvent.click(
      await screen.findByRole("button", {
        name: "1.1.1 Scope clause text that explains the implementation scope."
      })
    );

    expect(screen.getByText("Commentary for the scope clause.")).toBeInTheDocument();
    expect(screen.getByText("Pages 2-2")).toBeInTheDocument();
  });
});
