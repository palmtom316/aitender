export const ACCESS_TOKEN_COOKIE_NAME = "aitender_access_token";

export function readAccessTokenFromDocumentCookie(): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookiePrefix = `${ACCESS_TOKEN_COOKIE_NAME}=`;
  const value = document.cookie
    .split("; ")
    .find((entry) => entry.startsWith(cookiePrefix));

  return value ? decodeURIComponent(value.slice(cookiePrefix.length)) : null;
}
