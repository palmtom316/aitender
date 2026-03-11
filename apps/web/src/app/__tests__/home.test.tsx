import React from "react";
import { render, screen } from "@testing-library/react";
import HomePage from "../page";

describe("HomePage", () => {
  it("renders the Phase 1 title", () => {
    render(<HomePage />);

    expect(
      screen.getByRole("heading", {
        name: "aitender Tender Library Phase 1"
      })
    ).toBeInTheDocument();
  });
});
