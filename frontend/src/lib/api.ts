/**
 * src/lib/api.ts — Generic API client with Bearer auth
 *
 * Tự động gắn Authorization header từ auth.ts.
 * Hỗ trợ CRUD modules + menu + settings.
 */

import type { ApiRecord, PaginatedResponse, MenuModule, ModuleSchema, SystemSetting } from "@/types/module";
import { getAccessToken } from "@/lib/auth";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Core request helper ────────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getAccessToken();
  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });

  if (res.status === 401) {
    // Token expired or missing — redirect to login (client-side only)
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
    throw new Error("Chưa đăng nhập");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Standard backend response wrapper ─────────────────────────────────────────

interface BackendResponse<T> {
  success: boolean;
  data: T;
  message: string | null;
}

async function apiGet<T>(path: string): Promise<T> {
  const resp = await request<BackendResponse<T>>(path);
  return resp.data;
}

// ── Auth API ───────────────────────────────────────────────────────────────────

export const authApi = {
  login: async (email: string, password: string) => {
    const resp = await request<BackendResponse<{
      access_token: string;
      refresh_token: string;
      user: { id: number; email: string; full_name: string; is_superuser: boolean };
    }>>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    return resp.data;
  },

  me: () => apiGet<{ id: number; email: string; full_name: string; is_superuser: boolean }>("/auth/me"),

  logout: () => request("/auth/logout", { method: "POST" }).catch(() => {}),
};

// ── Menu API ───────────────────────────────────────────────────────────────────

export const menuApi = {
  getModules: () => apiGet<MenuModule[]>("/modules/menu"),
};

// ── Schema API ─────────────────────────────────────────────────────────────────

export const schemaApi = {
  get: (moduleName: string) => apiGet<ModuleSchema>(`/${moduleName}/meta/schema`),
};

// ── List params ────────────────────────────────────────────────────────────────

export interface ListParams {
  skip?: number;
  limit?: number;
  search?: string;
  with_archived?: boolean;
  [key: string]: unknown; // filter params (e.g. category_id=2, is_available=true)
}

// ── Generic CRUD API factory ───────────────────────────────────────────────────

export function createApiModule<T extends ApiRecord = ApiRecord>(name: string) {
  const base = `/${name}`;

  return {
    list: async (params: ListParams = {}): Promise<{ items: T[]; total: number; skip: number; limit: number }> => {
      const q = new URLSearchParams();
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") {
          q.set(k, String(v));
        }
      }
      // Backend may return paginated {items,total} OR plain array — normalise both
      const resp = await request<BackendResponse<{ items: T[]; total: number; skip: number; limit: number } | T[]>>(`${base}/?${q}`);
      const raw = resp.data;
      if (Array.isArray(raw)) {
        return { items: raw, total: raw.length, skip: 0, limit: raw.length };
      }
      return raw;
    },

    get: async (id: number): Promise<T> => {
      const resp = await request<BackendResponse<T>>(`${base}/${id}`);
      return resp.data;
    },

    create: async (data: Partial<T>): Promise<T> => {
      const resp = await request<BackendResponse<T>>(`${base}/`, {
        method: "POST",
        body: JSON.stringify(data),
      });
      return resp.data;
    },

    update: async (id: number, data: Partial<T>): Promise<T> => {
      const resp = await request<BackendResponse<T>>(`${base}/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return resp.data;
    },

    delete: async (id: number): Promise<void> => {
      await request(`${base}/${id}`, { method: "DELETE" });
    },

    archive: async (id: number): Promise<void> => {
      await request(`${base}/${id}/archive`, { method: "POST" });
    },

    restore: async (id: number): Promise<void> => {
      await request(`${base}/${id}/restore`, { method: "POST" });
    },

    // Fetch options for FK select
    listAll: async (params: ListParams = {}): Promise<T[]> => {
      const q = new URLSearchParams();
      q.set("limit", "500"); // Use max allowed limit for options fetching
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null && v !== "") {
          q.set(k, String(v));
        }
      }
      const resp = await request<BackendResponse<{ items: T[] } | T[]>>(`${base}/?${q}`);
      const raw = resp.data;
      if (Array.isArray(raw)) return raw;
      return raw.items;
    },
  };
}

// ── Settings API ───────────────────────────────────────────────────────────────

export const settingsApi = {
  getAll: () => apiGet<SystemSetting[]>("/system-settings/"),

  update: (moduleName: string, key: string, value: string) =>
    request(`/system-settings/${moduleName}/${key}`, {
      method: "PUT",
      body: JSON.stringify({ value }),
    }),
};

// ── Backward compat ────────────────────────────────────────────────────────────

export interface PaginatedResponseLegacy<T = ApiRecord> extends PaginatedResponse<T> {}

export const api = {
  items: createApiModule("items"),
};
