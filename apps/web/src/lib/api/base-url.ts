export function getApiBaseUrl(): string | undefined {
  if (typeof window === "undefined") {
    return (
      process.env.AITENDER_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL
    );
  }

  return process.env.NEXT_PUBLIC_API_BASE_URL;
}
