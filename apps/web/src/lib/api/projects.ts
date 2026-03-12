import { getApiBaseUrl } from "./base-url";

export type ProjectSummary = {
  id: string;
  name: string;
  memberRole: string;
};

type ProjectApiResponse = {
  id: string;
  name: string;
  member_role: string;
};

export async function listProjects(options?: {
  accessToken?: string;
}): Promise<ProjectSummary[]> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    return [
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
    ];
  }

  const response = await fetch(`${baseUrl}/projects`, {
    headers: options?.accessToken
      ? { Authorization: `Bearer ${options.accessToken}` }
      : {}
  });
  if (response.status === 401) {
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    throw new Error("Failed to load projects");
  }

  const payload = (await response.json()) as { items: ProjectApiResponse[] };
  return payload.items.map((item) => ({
    id: item.id,
    name: item.name,
    memberRole: item.member_role
  }));
}
