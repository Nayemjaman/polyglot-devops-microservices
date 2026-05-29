export type AuthTokens = {
  access: string;
  refresh?: string;
};

export type AuthUser = {
  id: string;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  profile?: {
    phone: string;
    avatar_url: string;
    country: string;
    currency_code: string;
    timezone: string;
    date_of_birth: string | null;
  };
};

export type AuthResponse = {
  user: AuthUser;
  tokens: AuthTokens;
};

const ACCESS_TOKEN_KEY = "polyglot.accessToken";
const REFRESH_TOKEN_KEY = "polyglot.refreshToken";
const USER_KEY = "polyglot.user";

let accessToken: string | null = null;

export function getApiBaseUrl() {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

export function persistSession(response: AuthResponse) {
  persistTokens(response.tokens);
  persistUser(response.user);
}

export function persistTokens(tokens: AuthTokens) {
  if (typeof window === "undefined") {
    return;
  }
  accessToken = tokens.access;
  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access);
  if (tokens.refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh);
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY);
  }
}

export function persistUser(user: AuthUser) {
  if (typeof window === "undefined") {
    return;
  }
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getStoredUser(): AuthUser | null {
  if (typeof window === "undefined") {
    return null;
  }
  const rawUser = localStorage.getItem(USER_KEY);
  if (!rawUser) {
    return null;
  }
  try {
    return JSON.parse(rawUser) as AuthUser;
  } catch {
    return null;
  }
}

export function getAccessToken() {
  if (accessToken) {
    return accessToken;
  }
  if (typeof window === "undefined") {
    return null;
  }
  accessToken = localStorage.getItem(ACCESS_TOKEN_KEY);
  return accessToken;
}

export function getRefreshToken() {
  if (typeof window === "undefined") {
    return null;
  }
  // Legacy fallback for sessions created before refresh moved to HttpOnly cookies.
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function clearSession() {
  if (typeof window === "undefined") {
    return;
  }
  accessToken = null;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
