/**
 * src/lib/auth.ts — JWT token management
 *
 * Access token: memory (module-level variable) — không persist qua refresh tab
 * Refresh token: localStorage — persist 30 ngày
 */

const ACCESS_TOKEN_KEY = "ct_access";
const REFRESH_TOKEN_KEY = "ct_refresh";

let _accessToken: string | null = null;

/**
 * Lấy access token từ memory.
 * Khi user reload tab → token mất → cần refresh tự động.
 */
export function getAccessToken(): string | null {
  // Ưu tiên memory, fallback localStorage (hot-reload / SSR guard)
  if (_accessToken) return _accessToken;
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken: string): void {
  _accessToken = accessToken;
  if (typeof window !== "undefined") {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    // Also set cookie so middleware can read it server-side
    document.cookie = `ct_access=${accessToken}; path=/; max-age=1800; SameSite=Lax`;
  }
}

export function clearTokens(): void {
  _accessToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    // Clear cookie
    document.cookie = "ct_access=; path=/; max-age=0";
  }
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

/** User info stored in localStorage after login */
export interface StoredUser {
  id: number;
  email: string;
  full_name: string;
  is_superuser: boolean;
}

export function getStoredUser(): StoredUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("ct_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredUser;
  } catch {
    return null;
  }
}

export function setStoredUser(user: StoredUser): void {
  if (typeof window !== "undefined") {
    localStorage.setItem("ct_user", JSON.stringify(user));
  }
}

export function clearStoredUser(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem("ct_user");
  }
}

export function logout(): void {
  clearTokens();
  clearStoredUser();
}
