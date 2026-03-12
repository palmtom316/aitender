import React from "react";
import { vi, describe, expect, it } from "vitest";
import HomePage from "../page";

const redirectMock = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

describe("HomePage", () => {
  it("redirects to the protected projects console", () => {
    HomePage();

    expect(redirectMock).toHaveBeenCalledWith("/projects");
  });
});
