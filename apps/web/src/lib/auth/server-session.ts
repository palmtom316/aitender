import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ACCESS_TOKEN_COOKIE_NAME } from "./session";

export async function getAccessToken(): Promise<string | null> {
  const cookieStore = await cookies();
  return cookieStore.get(ACCESS_TOKEN_COOKIE_NAME)?.value ?? null;
}

export async function requireAccessToken(): Promise<string> {
  const accessToken = await getAccessToken();
  if (!accessToken) {
    redirect("/login");
  }

  return accessToken;
}
