"use client";

import { useEffect, useState } from "react";
import { cloneMockProfile } from "@/lib/mock-data";
import { loadProfileForUsername } from "@/lib/profile-store";
import type { ProfileConfig } from "@/lib/types";
import { ProfileRenderer } from "./ProfileRenderer";

export function PublicProfileView({ username }: { username: string }) {
  const [config, setConfig] = useState<ProfileConfig>(() => {
    const initial = cloneMockProfile();
    initial.profile.username = username;
    initial.profile.displayName = username;
    return initial;
  });

  useEffect(() => {
    let cancelled = false;
    void loadProfileForUsername(username).then((profile) => {
      if (!cancelled) setConfig(profile);
    });
    return () => { cancelled = true; };
  }, [username]);

  return <ProfileRenderer config={config} />;
}
