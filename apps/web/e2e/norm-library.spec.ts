import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

import LibraryPage from "../src/app/projects/[projectId]/library/page";

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
