"use client";

import { AlertTriangle, Check, ChevronRight, Languages, LockKeyhole, Mail, Shield, Smartphone, Trash2, UserRound } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/lib/auth-store";
import { useProfile } from "@/lib/profile-store";
import { Button, FieldLabel, PageHeader, SectionTitle, StatusDot, TextInput, Toggle } from "@/components/ui";

export function SettingsView() {
  const { user, updateUsername } = useAuth();
  const { config, updateConfig, saveProfile, saveState } = useProfile();
  const [saved, setSaved] = useState(false);
  const [displayName, setDisplayName] = useState(config.profile.displayName);
  const [username, setUsername] = useState(user?.username || "");
  const [usernameMessage, setUsernameMessage] = useState("");

  const claimUsername = async () => {
    try {
      await updateUsername(username);
      setUsernameMessage("Username claimed.");
    } catch (error) {
      setUsernameMessage(error instanceof Error ? error.message : "Could not claim that username.");
    }
  };

  const save = () => {
    const next = { ...config, profile: { ...config.profile, displayName: displayName.trim() || config.profile.displayName } };
    updateConfig(() => next);
    void saveProfile(next).then(() => { setSaved(true); window.setTimeout(() => setSaved(false), 1800); });
  };

  return <main className="mx-auto min-h-screen max-w-[1050px] px-5 py-8 sm:px-8 sm:py-11 xl:px-12">
    <PageHeader eyebrow="Account" title="Settings" description="Your account, your preferences, your control." action={<Button variant="accent" onClick={save} disabled={saveState === "saving"}>{saved ? <><Check size={15} />Saved</> : saveState === "saving" ? "Saving…" : "Save changes"}</Button>} />
    <div className="space-y-8">
      <section>
        <SectionTitle icon={UserRound} title="General information" description="How your account appears across Misa.lol." />
        <div className="surface grid gap-5 rounded-2xl p-5 sm:grid-cols-2 sm:p-6">
          <div><FieldLabel>Username · permanent</FieldLabel>{user?.username ? <div className="flex h-11 items-center rounded-xl border border-white/[.08] bg-white/[.025] px-3.5 text-sm text-zinc-200">@{user.username}</div> : <><div className="flex gap-2"><TextInput value={username} onChange={setUsername} placeholder="yourname" /><Button variant="subtle" className="shrink-0" onClick={() => void claimUsername()}>Claim</Button></div>{usernameMessage && <p className="mt-2 text-xs text-zinc-500">{usernameMessage}</p>}</>}</div>
          <div><FieldLabel>Display name</FieldLabel><TextInput value={displayName} onChange={setDisplayName} /></div>
          <div><FieldLabel>Primary email</FieldLabel><div className="relative"><Mail size={15} className="absolute left-3 top-3.5 text-zinc-600" /><TextInput value={user?.email || ""} onChange={() => undefined} className="pl-9" disabled /></div></div>
          <div><FieldLabel>Language</FieldLabel><button type="button" className="flex h-11 w-full items-center gap-3 rounded-xl border border-white/[.08] bg-black/20 px-3.5 text-left text-sm text-zinc-300"><Languages size={15} className="text-zinc-600" />English <ChevronRight size={14} className="ml-auto text-zinc-700" /></button></div>
        </div>
      </section>
      <section>
        <SectionTitle icon={Shield} title="Connected accounts" description="Services linked to your account." />
        <div className="surface divide-y divide-white/[.06] rounded-2xl">
          {(["google", "discord", "telegram"] as const).map((provider) => <div key={provider} className="flex items-center gap-3 p-4"><span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#9b87f5]/10 font-semibold text-[#b8acff]">{provider[0].toUpperCase()}</span><div className="flex-1"><p className="text-sm capitalize text-zinc-200">{provider}</p><p className="mt-1 text-xs text-zinc-600">{user?.providers?.[provider] ? "Connected" : "Not connected"}</p></div>{user?.providers?.[provider] ? <span className="flex items-center gap-1.5 text-xs text-emerald-400"><StatusDot />Connected</span> : <Button variant="subtle" className="h-8 min-h-0 px-3 text-xs" onClick={() => window.location.assign(`/api/v1/auth/${provider}`)}>Connect</Button>}</div>)}
        </div>
      </section>
      <section><SectionTitle icon={LockKeyhole} title="Security" description="Keep your account protected." /><div className="surface divide-y divide-white/[.06] rounded-2xl"><div className="flex w-full items-center gap-3 p-4 text-left"><Smartphone size={17} className="text-zinc-500" /><span className="flex-1"><span className="block text-sm text-zinc-300">Multi-factor authentication</span><span className="mt-1 block text-xs text-zinc-600">Additional security controls are coming soon.</span></span><Toggle label="Enable multi-factor authentication" checked={false} onChange={() => undefined} /></div></div></section>
      <section><SectionTitle icon={AlertTriangle} title="Danger zone" description="Irreversible account actions." /><div className="rounded-2xl border border-red-400/15 bg-red-400/[.025] p-4"><div className="flex items-start gap-3"><Trash2 size={17} className="mt-0.5 text-red-300" /><div><p className="text-sm text-zinc-300">Delete your account</p><p className="mt-1 text-xs leading-5 text-zinc-600">Account deletion requires support approval.</p></div></div></div></section>
    </div>
  </main>;
}

