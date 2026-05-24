import { apiRequest } from "@/lib/api";
import type { AuthResponse, AuthTokens, AuthUser } from "@/lib/auth";

export type RegisterPayload = {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export function login(payload: LoginPayload) {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload)
  });
}

export function register(payload: RegisterPayload) {
  return apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    auth: false,
    body: JSON.stringify(payload)
  });
}

export function fetchMe() {
  return apiRequest<{ user: AuthUser }>("/auth/me");
}

export function updateMe(payload: {
  first_name?: string;
  last_name?: string;
  profile?: {
    phone?: string;
    avatar_url?: string;
    country?: string;
    currency_code?: string;
    timezone?: string;
    date_of_birth?: string | null;
  };
}) {
  return apiRequest<{ user: AuthUser }>("/auth/me", {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function refreshSession(refresh?: string | null) {
  return apiRequest<{ tokens: AuthTokens }>("/auth/refresh", {
    method: "POST",
    auth: false,
    body: JSON.stringify(refresh ? { refresh } : {})
  });
}

export function logout(refresh?: string | null) {
  return apiRequest<void>("/auth/logout", {
    method: "POST",
    auth: false,
    body: JSON.stringify(refresh ? { refresh } : {})
  });
}
