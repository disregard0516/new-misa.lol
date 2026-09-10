"use client";

import { BadgeCheck, Crown, Gem, Lock, Sparkles, Trophy, UserRound } from "lucide-react";
import { useProfile } from "@/lib/profile-store";
import type { ProfileBadge } from "@/lib/types";
import { Button, PageHeader, SectionTitle, Toggle } from "@/components/ui";

const iconFor = (name: string) => name === "Premium" ? Crown : ["Winner", "Second Place", "Third Place"].includes(name) ? Trophy : name === "Donor" || name === "Gifter" ? Gem : name === "OG" ? Sparkles : BadgeCheck;

export function BadgesManager() {
  const { config, updateConfig } = useProfile();
  const owned = config.badges.filter((badge) => badge.owned);
  const locked = config.badges.filter((badge) => !badge.owned);
  const toggle = (id: string, enabled: boolean) => updateConfig((current) => ({ ...current, badges: current.badges.map((badge) => badge.id === id ? { ...badge, enabled } : badge) }));
  return <main className="mx-auto min-h-screen max-w-[1200px] px-5 py-8 sm:px-8 sm:py-11 xl:px-12"><PageHeader eyebrow="Identity" title="Badges" description="Collect and display the moments that make your profile yours." action={<Button variant="subtle"><BadgeCheck size={15} />{owned.length} earned</Button>} /><section><SectionTitle icon={Sparkles} title="Your badges" description="Choose which badges appear on your public profile." /><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{owned.map((badge) => <BadgeCard key={badge.id} badge={badge} onToggle={toggle} />)}</div></section><section className="mt-10"><SectionTitle icon={Lock} title="Other badges" description="Keep building your presence to unlock more." /><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{locked.map((badge) => <BadgeCard key={badge.id} badge={badge} onToggle={toggle} />)}</div></section></main>;
}

function BadgeCard({ badge, onToggle }: { badge: ProfileBadge; onToggle: (id: string, enabled: boolean) => void }) {
  const Icon = iconFor(badge.name);
  return <div className={`surface rounded-2xl p-4 transition ${badge.owned ? "" : "opacity-55"}`}><div className="flex items-start gap-3"><span className="flex h-11 w-11 items-center justify-center rounded-xl" style={{ color: badge.color, background: `${badge.color}16`, boxShadow: badge.enabled ? `0 0 24px ${badge.color}16` : undefined }}><Icon size={20} /></span><div className="min-w-0 flex-1"><div className="flex items-center gap-2"><p className="text-sm font-medium text-zinc-200">{badge.name}</p>{badge.owned && <span className="rounded-full bg-emerald-400/10 px-1.5 py-0.5 text-[9px] text-emerald-400">Owned</span>}</div><p className="mt-1 text-xs text-zinc-600">{badge.description}</p></div>{badge.owned && <Toggle label={`Show ${badge.name} badge`} checked={badge.enabled} onChange={(value) => onToggle(badge.id, value)} />}</div>{!badge.owned && <div className="mt-4 flex items-center gap-1.5 text-[10px] text-zinc-600"><Lock size={11} />Earn this badge to display it</div>}</div>;
}
