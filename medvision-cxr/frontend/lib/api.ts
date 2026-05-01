import axios, { type AxiosRequestConfig } from "axios";

import { AnalyzeResponse, AnalysisResult, GradCAMResponse, HistoryItem, UploadResponse } from "@/types";
import { mockHistory } from "@/lib/mock-data";

const runtimeBaseUrl =
  typeof window === "undefined"
    ? process.env.INTERNAL_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
    : process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: runtimeBaseUrl,
  timeout: 10000
});

const LONG_RUNNING_REQUEST_TIMEOUT_MS = 120000;

const DEMO_SESSION_STORAGE_KEY = "medvision-cxr.demo-session";
const DEMO_ROLE_CODE = "clinician";
const DEMO_PASSWORD_PREFIX = "StrongPass123!";

type DemoSession = {
  email: string;
  password: string;
  accessToken: string;
  expiresAt: number;
};

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function createDemoSuffix(): string {
  if (typeof globalThis !== "undefined" && "crypto" in globalThis && typeof globalThis.crypto.randomUUID === "function") {
    return globalThis.crypto.randomUUID().replace(/-/g, "");
  }
  return `${Date.now()}${Math.random().toString(36).slice(2, 10)}`;
}

function readDemoSession(): DemoSession | null {
  if (!isBrowser()) {
    return null;
  }

  const raw = window.localStorage.getItem(DEMO_SESSION_STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as DemoSession;
  } catch {
    window.localStorage.removeItem(DEMO_SESSION_STORAGE_KEY);
    return null;
  }
}

function writeDemoSession(session: DemoSession): DemoSession {
  if (isBrowser()) {
    window.localStorage.setItem(DEMO_SESSION_STORAGE_KEY, JSON.stringify(session));
  }
  return session;
}

async function loginDemoSession(email: string, password: string): Promise<DemoSession> {
  const response = await api.post("/auth/login", { email, password });
  return writeDemoSession({
    email,
    password,
    accessToken: response.data.access_token,
    expiresAt: Date.now() + response.data.expires_in * 1000
  });
}

async function ensureDemoSession(): Promise<DemoSession> {
  if (!isBrowser()) {
    throw new Error("This action requires a browser session.");
  }

  const current = readDemoSession();
  if (current && current.expiresAt > Date.now() + 30_000) {
    return current;
  }

  if (current?.email && current?.password) {
    try {
      return await loginDemoSession(current.email, current.password);
    } catch {
    }
  }

  const suffix = createDemoSuffix();
  const email = current?.email ?? `frontend-clinician-${suffix}@example.com`;
  const password = current?.password ?? `${DEMO_PASSWORD_PREFIX}${suffix.slice(0, 8)}`;

  try {
    await api.post("/auth/register", { email, password, role_code: DEMO_ROLE_CODE });
  } catch (error) {
    if (!(axios.isAxiosError(error) && error.response?.status === 400 && error.response?.data?.detail === "Email already registered")) {
      throw error;
    }
  }

  return loginDemoSession(email, password);
}

async function authorizedConfig(config: AxiosRequestConfig = {}): Promise<AxiosRequestConfig> {
  const session = await ensureDemoSession();
  return {
    ...config,
    headers: {
      ...config.headers,
      Authorization: `Bearer ${session.accessToken}`
    }
  };
}

function encodeStoragePath(storageKey: string): string {
  return storageKey
    .split("/")
    .filter(Boolean)
    .map((segment) => encodeURIComponent(segment))
    .join("/");
}

function backendOrigin(): string {
  try {
    return new URL(runtimeBaseUrl).origin;
  } catch {
    return "";
  }
}

function resolveBackendAssetUrl(url: string | null | undefined): string | undefined {
  if (!url) {
    return undefined;
  }

  if (/^https?:\/\//i.test(url)) {
    return url;
  }

  if (url.startsWith("/")) {
    const origin = backendOrigin();
    return origin ? `${origin}${url}` : url;
  }

  return url;
}

export function buildRawImageUrl(storageKey: string): string {
  return `${backendOrigin()}/storage/cxr-raw/${encodeStoragePath(storageKey)}`;
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
    if (typeof error.message === "string" && error.message.trim()) {
      return error.message;
    }
  }
  return fallback;
}

export const frontendApi = {
  async uploadCxr(formData: FormData): Promise<UploadResponse> {
    const response = await api.post(
      "/cxr/upload",
      formData,
      await authorizedConfig({
        headers: { "Content-Type": "multipart/form-data" }
      })
    );
    return response.data as UploadResponse;
  },

  async analyzeCxr(imageId: string, requestedHeatmaps: string[] = []): Promise<AnalyzeResponse> {
    const response = await api.post(
      `/cxr/${imageId}/analyze`,
      {
        priority: "normal",
        requested_heatmaps: requestedHeatmaps
      },
      await authorizedConfig({
        timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS
      })
    );
    return response.data as AnalyzeResponse;
  },

  async fetchAnalysisResult(predictionId: string): Promise<AnalysisResult> {
    const response = await api.get(`/cxr/results/${predictionId}`, await authorizedConfig());
    return {
      ...response.data,
      image_url: resolveBackendAssetUrl(response.data.image_url),
      overlay_url: resolveBackendAssetUrl(response.data.overlay_url)
    } as AnalysisResult;
  },

  async fetchHistory(): Promise<HistoryItem[]> {
    try {
      if (!isBrowser()) {
        return mockHistory;
      }

      const response = await api.get("/cxr/history", await authorizedConfig());
      return response.data.items as HistoryItem[];
    } catch {
      return mockHistory;
    }
  },

  async fetchHeatmap(imageId: string, label: string): Promise<GradCAMResponse> {
    const response = await api.get(
      `/cxr/${imageId}/heatmap`,
      await authorizedConfig({
        params: { label }
      })
    );

    return {
      image_id: response.data.image_id,
      target_label: response.data.label,
      heatmap_url: resolveBackendAssetUrl(response.data.heatmap_url),
      overlay_url: resolveBackendAssetUrl(response.data.overlay_url),
      notice: response.data.notice,
      disclaimer: response.data.disclaimer
    } as GradCAMResponse;
  },

  async generateGradcam(imageId: string, targetLabel: string): Promise<GradCAMResponse> {
    const response = await api.post(
      `/cxr/${imageId}/gradcam`,
      {
        image_id: imageId,
        target_label: targetLabel
      },
      await authorizedConfig({
        timeout: LONG_RUNNING_REQUEST_TIMEOUT_MS
      })
    );
    return {
      ...response.data,
      heatmap_url: resolveBackendAssetUrl(response.data.heatmap_url),
      overlay_url: resolveBackendAssetUrl(response.data.overlay_url)
    } as GradCAMResponse;
  }
};

export default api;
