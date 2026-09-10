"use client";

import { ProfileProvider } from "@/lib/profile-store";
import { AuthProvider } from "@/lib/auth-store";

export function AppProviders({ children }: { children: React.ReactNode }) {
  return <AuthProvider><ProfileProvider>{children}</ProfileProvider></AuthProvider>;
}
