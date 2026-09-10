"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

export interface AuthUser {
  id: string;
  username: string | null;
  displayName: string;
  email: string | null;
  uid: string;
  isAdmin: boolean;
  providers?: { email: boolean; google: boolean; discord: boolean; telegram: boolean };
}

type AuthResult = { ok: true; user: AuthUser } | { ok: false; error: string };
interface AuthContextValue {
  user: AuthUser | null;
  isReady: boolean;
  signUp: (input: { username: string; displayName: string; email: string; password: string }) => Promise<AuthResult>;
  login: (identifier: string, password: string) => Promise<AuthResult>;
  logout: () => Promise<void>;
  updateDisplayName: (displayName: string) => Promise<void>;
  updateUsername: (username: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function normalizeUser(value: Record<string, unknown>): AuthUser {
  return {
    id: String(value.id || ""),
    username: value.username ? String(value.username) : null,
    displayName: String(value.display_name || value.displayName || value.username || "Misa user"),
    email: value.email ? String(value.email) : null,
    uid: String(value.id || value.uid || ""),
    isAdmin: Boolean(value.is_admin || value.isAdmin),
    providers: value.providers as AuthUser["providers"],
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    void fetch("/api/v1/me", { credentials: "include", cache: "no-store" })
      .then(async (response) => response.ok ? normalizeUser(await response.json() as Record<string, unknown>) : null)
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setIsReady(true));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isReady,
    signUp: async () => ({ ok: false, error: "Create your account from the main signup page." }),
    login: async () => ({ ok: false, error: "Log in from the main login page." }),
    logout: async () => {
      await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
      setUser(null);
      window.location.assign("/login");
    },
    updateDisplayName: async (displayName) => {
      const response = await fetch("/api/v1/me", { method: "PATCH", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ display_name: displayName }) });
      const result = await response.json() as Record<string, unknown>;
      if (!response.ok) throw new Error(String(result.detail || result.error || "Could not update your display name."));
      setUser(normalizeUser(result));
    },
    updateUsername: async (username) => {
      const response = await fetch("/api/v1/me/username", { method: "PATCH", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify({ username }) });
      const result = await response.json() as Record<string, unknown>;
      if (!response.ok) throw new Error(String(result.detail || result.error || "Could not claim that username."));
      setUser(normalizeUser(result));
    },
  }), [isReady, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}


