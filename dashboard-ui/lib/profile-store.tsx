"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useAuth, type AuthUser } from "./auth-store";
import { cloneMockProfile } from "./mock-data";
import type { ProfileAsset, ProfileConfig } from "./types";

type SaveState = "idle" | "saving" | "saved" | "error";
interface ProfileContextValue {
  config: ProfileConfig;
  updateConfig: (updater: (config: ProfileConfig) => ProfileConfig) => void;
  resetConfig: () => void;
  saveProfile: (nextConfig?: ProfileConfig) => Promise<void>;
  saveState: SaveState;
  saveError: string;
}

const ProfileContext = createContext<ProfileContextValue | null>(null);

export function ProfileProvider({ children }: { children: React.ReactNode }) {
  const { user, isReady: authReady } = useAuth();
  const [config, setConfig] = useState<ProfileConfig>(() => cloneMockProfile());
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    if (!authReady) return;
    let cancelled = false;
    const load = async () => {
      const next = user ? await loadProfileForUser(user) : cloneMockProfile();
      if (!cancelled) { setConfig(next); setSaveState("idle"); setSaveError(""); }
    };
    void load();
    return () => { cancelled = true; };
  }, [authReady, user]);

  const value = useMemo<ProfileContextValue>(() => ({
    config,
    updateConfig: (updater) => { setConfig((current) => updater(current)); setSaveState("idle"); setSaveError(""); },
    resetConfig: () => { setConfig(user ? profileForUser(user) : cloneMockProfile()); setSaveState("idle"); setSaveError(""); },
    saveProfile: async (nextConfig) => {
      if (!user) { setSaveState("error"); setSaveError("You are not signed in."); return; }
      if (!user.username) { setSaveState("error"); setSaveError("Choose a username in Account settings before saving your profile."); return; }
      setSaveState("saving");
      setSaveError("");
      try {
        const profileToSave = nextConfig || config;
        const response = await fetch("/api/v1/profile/me", { method: "PUT", headers: { "Content-Type": "application/json" }, credentials: "include", body: JSON.stringify(profileToSave) });
        const raw = await response.text();
        let result: { profile?: ProfileConfig; detail?: string; error?: string } = {};
        try { result = raw ? JSON.parse(raw) as typeof result : {}; } catch { /* The proxy may return an HTML error page. */ }
        if (!response.ok && !result.detail && !result.error) result.detail = `Profile save failed (server returned ${response.status}).`;
        if (!response.ok || !result.profile) throw new Error(result.detail || result.error || "Profile save failed. Please try again.");
        setConfig(result.profile);
        setSaveState("saved");
      } catch (error) { setSaveState("error"); setSaveError(error instanceof Error ? error.message : "Profile save failed. Please try again."); }
    },
    saveState,
    saveError,
  }), [config, saveState, saveError, user]);
  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfile() {
  const value = useContext(ProfileContext);
  if (!value) throw new Error("useProfile must be used inside ProfileProvider");
  return value;
}

export async function loadProfileForUsername(username: string): Promise<ProfileConfig> {
  const normalized = username.trim().toLowerCase();
  try {
    const response = await fetch(`/api/v1/profile?username=${encodeURIComponent(normalized)}`, { cache: "no-store" });
    if (response.ok) {
      const result = await response.json() as { profile: ProfileConfig };
      return result.profile;
    }
  } catch { /* Keep public profiles resilient while the API recovers. */ }
  const base = cloneMockProfile();
  base.profile.username = normalized;
  base.profile.displayName = normalized;
  return base;
}

export function assetFromFile(file: File): Promise<ProfileAsset> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve({ url: typeof reader.result === "string" ? reader.result : null, name: file.name, type: file.type });
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function profileForUser(user: AuthUser) {
  const profile = cloneMockProfile();
  profile.profile.username = user.username || "choose-username";
  profile.profile.displayName = user.displayName;
  profile.profile.uid = user.id;
  profile.socials = profile.socials.map((social) => ({ ...social, value: social.value.replaceAll("demo", user.username || "user") }));
  return profile;
}

async function loadProfileForUser(user: AuthUser) {
  const response = await fetch("/api/v1/profile/me", { credentials: "include", cache: "no-store" });
  if (response.ok) {
    const result = await response.json() as { profile?: ProfileConfig };
    if (result.profile) return result.profile;
  }
  return profileForUser(user);
}
