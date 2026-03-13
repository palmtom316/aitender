import { readAccessTokenFromDocumentCookie } from "../auth/session";
import { getApiBaseUrl } from "./base-url";

export type ProviderApiConfig = {
  baseUrl: string;
  apiKey: string;
  model: string;
};

export type ProjectAiSettings = {
  projectId: string;
  ocr: ProviderApiConfig;
  analysis: ProviderApiConfig;
};

type ProjectAiSettingsApiResponse = {
  project_id: string;
  ocr: {
    base_url: string;
    api_key: string;
    model: string;
  };
  analysis: {
    base_url: string;
    api_key: string;
    model: string;
  };
};

function getAuthHeaders(accessToken?: string): HeadersInit {
  const token =
    accessToken ??
    process.env.AITENDER_API_BEARER_TOKEN ??
    process.env.NEXT_PUBLIC_API_BEARER_TOKEN ??
    readAccessTokenFromDocumentCookie();

  return token ? { Authorization: `Bearer ${token}` } : {};
}

function mapSettings(payload: ProjectAiSettingsApiResponse): ProjectAiSettings {
  return {
    projectId: payload.project_id,
    ocr: {
      baseUrl: payload.ocr.base_url,
      apiKey: payload.ocr.api_key,
      model: payload.ocr.model
    },
    analysis: {
      baseUrl: payload.analysis.base_url,
      apiKey: payload.analysis.api_key,
      model: payload.analysis.model
    }
  };
}

function toApiPayload(settings: ProjectAiSettings): ProjectAiSettingsApiResponse {
  return {
    project_id: settings.projectId,
    ocr: {
      base_url: settings.ocr.baseUrl,
      api_key: settings.ocr.apiKey,
      model: settings.ocr.model
    },
    analysis: {
      base_url: settings.analysis.baseUrl,
      api_key: settings.analysis.apiKey,
      model: settings.analysis.model
    }
  };
}

export async function getProjectAiSettings(
  projectId: string,
  options?: { accessToken?: string }
): Promise<ProjectAiSettings> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    return {
      projectId,
      ocr: { baseUrl: "", apiKey: "", model: "" },
      analysis: { baseUrl: "", apiKey: "", model: "" }
    };
  }

  const response = await fetch(`${baseUrl}/projects/${projectId}/settings/ai`, {
    headers: getAuthHeaders(options?.accessToken)
  });
  if (response.status === 401) {
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    throw new Error("Failed to load project AI settings");
  }

  return mapSettings((await response.json()) as ProjectAiSettingsApiResponse);
}

export async function saveProjectAiSettings(
  settings: ProjectAiSettings,
  options?: { accessToken?: string }
): Promise<ProjectAiSettings> {
  const baseUrl = getApiBaseUrl();
  if (!baseUrl) {
    throw new Error("Project AI settings require NEXT_PUBLIC_API_BASE_URL");
  }

  const response = await fetch(
    `${baseUrl}/projects/${settings.projectId}/settings/ai`,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(options?.accessToken)
      },
      body: JSON.stringify(toApiPayload(settings))
    }
  );
  if (response.status === 401) {
    throw new Error("Unauthorized");
  }
  if (!response.ok) {
    throw new Error("Failed to save project AI settings");
  }

  return mapSettings((await response.json()) as ProjectAiSettingsApiResponse);
}
