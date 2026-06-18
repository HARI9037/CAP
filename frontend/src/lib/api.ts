'use client';

import { useAuth } from "@clerk/nextjs";

import { apiBaseUrl } from "@/lib/clerk-env";

const API_BASE_URL = apiBaseUrl || "http://127.0.0.1:8000";

let cachedGetToken: (() => Promise<string | null>) | null = null;

function getGetTokenFunction() {
  if (cachedGetToken) return cachedGetToken;

  // This will only work in React components, not in standalone functions
  // For now, we'll use a workaround with useAuth in the component
  return null;
}

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
  requiresAuth: boolean = true,
  getTokenFn?: () => Promise<string | null>
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  // Merge custom headers
  if (init?.headers) {
    const customHeaders = init.headers instanceof Headers
      ? Object.fromEntries(init.headers.entries())
      : init.headers as Record<string, string>;
    Object.assign(headers, customHeaders);
  }

  if (requiresAuth && getTokenFn) {
    try {
      const token = await getTokenFn();
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    } catch (error) {
      console.error("Failed to fetch Clerk token:", error);
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

// Hook for use in React components
export function useClerkApiRequest() {
  const { getToken } = useAuth();

  return async function apiRequestWithAuth<T>(
    path: string,
    init?: RequestInit,
    requiresAuth: boolean = true
  ): Promise<T> {
    return apiRequest(path, init, requiresAuth, getToken);
  };
}
