import { clearSession, getAccessToken, getApiBaseUrl, getRefreshToken, persistTokens } from "@/lib/auth";

type ApiOptions = RequestInit & {
  auth?: boolean;
};

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(extractErrorMessage(detail));
    this.status = status;
    this.detail = detail;
  }
}

export async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const response = await request(path, options);

  if (response.status === 401 && options.auth !== false) {
    if (await refreshAccessToken()) {
      return handleResponse<T>(await request(path, options));
    }
  }

  return handleResponse<T>(response);
}

export async function apiBlobRequest(path: string, options: ApiOptions = {}): Promise<Blob> {
  const response = await request(path, options);

  if (response.status === 401 && options.auth !== false) {
    if (await refreshAccessToken()) {
      return handleBlobResponse(await request(path, options));
    }
  }

  return handleBlobResponse(response);
}

async function request(path: string, options: ApiOptions = {}) {
  const headers = new Headers(options.headers);
  const hasBody = options.body !== undefined;
  const isFormData = typeof FormData !== "undefined" && options.body instanceof FormData;

  if (hasBody && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (options.auth !== false) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return fetch(`${getApiBaseUrl()}${path}`, {
    ...options,
    credentials: options.credentials ?? "same-origin",
    headers
  });
}

async function refreshAccessToken() {
  try {
    const refreshToken = getRefreshToken();
    const refreshResponse = await request("/auth/refresh", {
      method: "POST",
      auth: false,
      body: JSON.stringify(refreshToken ? { refresh: refreshToken } : {})
    });
    const refreshData = await parseResponse(refreshResponse);
    if (refreshResponse.ok && refreshData && typeof refreshData === "object" && "tokens" in refreshData) {
      persistTokens(refreshData.tokens as { access: string; refresh?: string });
      return true;
    }
  } catch {
    clearSession();
  }
  return false;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const data = await parseResponse(response);

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}

async function handleBlobResponse(response: Response): Promise<Blob> {
  if (!response.ok) {
    throw new ApiError(response.status, await parseResponse(response));
  }
  return response.blob();
}

async function parseResponse(response: Response) {
  if (response.status === 204) {
    return undefined;
  }
  const contentType = response.headers.get("content-type") ?? "";
  return contentType.includes("application/json") ? response.json() : response.text();
}

function extractErrorMessage(detail: unknown) {
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object") {
    if ("detail" in detail && typeof detail.detail === "string") {
      return detail.detail;
    }
    if ("message" in detail && typeof detail.message === "string") {
      return detail.message;
    }
  }
  return "Something went wrong. Please try again.";
}
