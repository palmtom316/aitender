import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";

import LibraryPage from "../page";

describe("NormLibraryPage", () => {
  it("shows documents, searches norms, and syncs detail panels from the selected result", async () => {
    render(
      await LibraryPage({
        params: Promise.resolve({ projectId: "project-alpha" })
      })
    );

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
});
