"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { getApiBaseUrl } from "../../lib/api/base-url";
import { ACCESS_TOKEN_COOKIE_NAME } from "../../lib/auth/session";

export type LoginActionState = {
  errorMessage: string | null;
};

export async function loginAction(
  _previousState: LoginActionState,
  formData: FormData
): Promise<LoginActionState> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    return {
      errorMessage:
        "API base URL is not configured. Set AITENDER_API_BASE_URL or NEXT_PUBLIC_API_BASE_URL."
    };
  }

  const email = String(formData.get("email") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!email || !password) {
    return {
      errorMessage: "Email and password are required."
    };
  }

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ email, password }),
      cache: "no-store"
    });
  } catch {
    return {
      errorMessage:
        "Unable to reach the API server. Check the API URL and make sure the backend is running."
    };
  }

  if (!response.ok) {
    return {
      errorMessage: response.status === 401 ? "Invalid credentials." : "Login failed."
    };
  }

  const payload = (await response.json()) as {
    access_token: string;
  };
  const cookieStore = await cookies();
  cookieStore.set(ACCESS_TOKEN_COOKIE_NAME, payload.access_token, {
    path: "/",
    sameSite: "lax"
  });

  redirect("/projects");
}
