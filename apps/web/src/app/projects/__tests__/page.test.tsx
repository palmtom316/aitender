import React from "react";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import ProjectsPage from "../page";
import { listProjects } from "../../../lib/api/projects";

const redirectMock = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

vi.mock("../../../lib/auth/server-session", () => ({
  requireAccessToken: vi.fn().mockResolvedValue("auth-token-pm")
}));

vi.mock("../../../lib/api/projects", () => ({
  listProjects: vi.fn()
}));

const listProjectsMock = vi.mocked(listProjects);

describe("ProjectsPage", () => {
  beforeEach(() => {
    listProjectsMock.mockResolvedValue([
      {
        id: "project-alpha",
        name: "Alpha Substation Bid",
        memberRole: "writer"
      },
      {
        id: "project-beta",
        name: "Beta Transmission Line Bid",
        memberRole: "project_manager"
      }
    ]);
  });

  it("renders the dashboard shell and accessible project links", async () => {
    render(await ProjectsPage());

    expect(
      screen.getByRole("heading", {
        name: "从这里进入每个项目工作面"
      })
    ).toBeInTheDocument();
    expect(screen.getByText("项目 2")).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: "Alpha Substation Bid 编写人"
      })
    ).toBeInTheDocument();
    const libraryLinks = screen.getAllByRole("link", {
      name: "打开资料库"
    });
    expect(libraryLinks[0]).toHaveAttribute("href", "/projects/project-alpha/library");
  });
});
