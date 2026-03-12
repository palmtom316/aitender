// @vitest-environment node

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ACCESS_TOKEN_COOKIE_NAME } from "../../../lib/auth/session";
import { loginAction } from "../actions";

const redirectMock = vi.hoisted(() => vi.fn());
const cookiesMock = vi.hoisted(() => vi.fn());
const cookieSetMock = vi.hoisted(() => vi.fn());

vi.mock("next/navigation", () => ({
  redirect: redirectMock
}));

vi.mock("next/headers", () => ({
  cookies: cookiesMock
}));

function createLoginFormData() {
  const formData = new FormData();
  formData.set("email", "pm@aitender.local");
  formData.set("password", "pm-pass");
  return formData;
}

describe("loginAction", () => {
  beforeEach(() => {
    delete process.env.AITENDER_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_BASE_URL;

    redirectMock.mockReset();
    cookieSetMock.mockReset();
    cookiesMock.mockReset();
    cookiesMock.mockResolvedValue({ set: cookieSetMock });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns a validation error when the API base URL is missing", async () => {
    const result = await loginAction(
      { errorMessage: null },
      createLoginFormData()
    );

    expect(result).toEqual({
      errorMessage:
        "API base URL is not configured. Set AITENDER_API_BASE_URL or NEXT_PUBLIC_API_BASE_URL."
    });
  });

  it("returns a friendly error when the API server is unreachable", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("fetch failed")));

    const result = await loginAction(
      { errorMessage: null },
      createLoginFormData()
    );

    expect(result).toEqual({
      errorMessage:
        "Unable to reach the API server. Check the API URL and make sure the backend is running."
    });
    expect(redirectMock).not.toHaveBeenCalled();
  });

  it("returns an auth error for invalid credentials", async () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.test";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    );

    const result = await loginAction(
      { errorMessage: null },
      createLoginFormData()
    );

    expect(result).toEqual({
      errorMessage: "Invalid credentials."
    });
  });

  it("uses the server API base URL, stores the token, and redirects", async () => {
    process.env.AITENDER_API_BASE_URL = "http://api.internal";
    process.env.NEXT_PUBLIC_API_BASE_URL = "http://api.public";
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ access_token: "auth-token-pm" }), {
          status: 200,
          headers: {
            "Content-Type": "application/json"
          }
        })
      );
    vi.stubGlobal("fetch", fetchMock);

    await loginAction({ errorMessage: null }, createLoginFormData());

    expect(fetchMock).toHaveBeenCalledWith(
      "http://api.internal/auth/login",
      expect.objectContaining({
        method: "POST",
        cache: "no-store"
      })
    );
    expect(cookies).toBeDefined();
    expect(cookiesMock).toHaveBeenCalled();
    expect(cookieSetMock).toHaveBeenCalledWith(
      ACCESS_TOKEN_COOKIE_NAME,
      "auth-token-pm",
      {
        path: "/",
        sameSite: "lax"
      }
    );
    expect(redirect).toBeDefined();
    expect(redirectMock).toHaveBeenCalledWith("/projects");
  });
});
