"use client";

import { AtSign, BadgeCheck, Check, ChevronRight, CircleUserRound, Cloud, Eye, Globe2, Pencil, ShieldCheck, Sparkles, UsersRound } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/lib/auth-store";
import { useProfile } from "@/lib/profile-store";
import { Button, MiniBar, PageHeader, SectionTitle, StatusDot } from "@/components/ui";

export function Overview() {
  const { config } = useProfile();
  const { user } = useAuth();
  const { profile, assets, socials } = config;
  const tasks = [
    ["Upload an Avatar", "/customize", Boolean(assets.avatar.url)],
    ["Add a Description", "/customize", Boolean(profile.description.trim())],
    ["Add Socials", "/links", socials.some((social) => social.enabled)],
    ["Customize Background", "/customize", Boolean(assets.background.url || assets.backgroundVideo.url)],
    ["Add Music", "/customize", Boolean(assets.audio.url)],
  ] as const;
  const completedTasks = tasks.filter(([, , done]) => done).length;
  const completionPercent = Math.round((completedTasks / tasks.length) * 100);
  const stats = [
    { label: "Username", value: profile.username, icon: AtSign, color: "#9b87f5" },
    { label: "Aliases", value: "0 aliases used", icon: UsersRound, color: "#65c7b9" },
    { label: "UID", value: profile.uid, icon: ShieldCheck, color: "#e0a1ef" },
    { label: "Profile Views", value: String(profile.views), icon: Eye, color: "#e2b46d" },
  ];
  return <main className="mx-auto min-h-screen max-w-[1360px] px-5 py-8 sm:px-8 sm:py-11 xl:px-12">
    <PageHeader eyebrow="Account" title="Account overview" description="Manage your Misa.lol profile and account." action={<a href={`/${profile.username}`} target="_blank"><Button variant="subtle"><Globe2 size={15} />View live profile</Button></a>} />
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">{stats.map(({ label, value, icon: Icon, color }, index) => <div key={label} className="surface surface-subtle surface-hover animate-fade-up rounded-[16px] p-5" style={{ animationDelay: `${index * 50}ms` }}><div className="mb-6 flex items-center justify-between"><span className="text-xs font-medium text-zinc-500">{label}</span><span className="icon-glass flex h-8 w-8 items-center justify-center rounded-[10px]" style={{ color, background: `${color}16` }}><Icon size={16} /></span></div><div className="text-xl font-semibold tracking-[-.03em] text-white">{value}</div><div className="mt-2 text-[11px] text-zinc-600">{label === "Profile Views" ? "+0% from last week" : label === "Username" ? "Your permanent public handle" : label === "UID" ? "Account identifier" : "Available to claim"}</div></div>)}</div>
    <div className="mt-8 grid gap-8 xl:grid-cols-[1.3fr_.7fr]"><div className="space-y-8"><section><SectionTitle icon={Sparkles} title="Account statistics" description="A quick look at your profile progress." action={<span className="text-sm font-medium text-[#b6aaff]">{completionPercent}%</span>} /><div className="surface rounded-2xl p-5 sm:p-6"><div className="mb-5 flex items-center justify-between"><div><p className="text-sm font-medium">Profile completion</p><p className="mt-1 text-xs text-zinc-500">Complete these steps to make your page shine.</p></div><span className="rounded-lg bg-[#9b87f5]/10 px-2.5 py-1 text-xs font-medium text-[#b6aaff]">{completedTasks} / {tasks.length}</span></div><MiniBar value={completionPercent} /><div className="mt-6 grid gap-2 sm:grid-cols-2">{tasks.map(([task, href, done]) => <Link key={task} href={href} className="flex items-center gap-3 rounded-xl px-2 py-2.5 text-sm hover:bg-white/[.03]"><span className={`flex h-7 w-7 items-center justify-center rounded-lg ${done ? "bg-emerald-400/10 text-emerald-400" : "bg-white/[.06] text-zinc-600"}`}>{done ? <Check size={14} /> : <CircleUserRound size={14} />}</span><span className={done ? "text-zinc-300" : "text-zinc-500"}>{task}</span>{!done && <span className="ml-auto text-[10px] text-zinc-600">Open</span>}</Link>)}</div></div></section><section><SectionTitle icon={UsersRound} title="Manage your account" description="Keep your identity and account details up to date." /><div className="grid gap-3 sm:grid-cols-2"><div className="surface flex items-center gap-4 rounded-2xl p-4"><span className="icon-glass flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-zinc-400"><AtSign size={17} /></span><span className="min-w-0 flex-1"><span className="block text-sm font-medium text-zinc-200">Permanent username</span><span className="mt-1 block truncate text-xs text-zinc-600">@{profile.username} Ãƒâ€šÃ‚Â· cannot be changed</span></span></div>{[{ title: "Change Display Name", desc: "How you appear on Misa.lol", icon: Pencil }, { title: "Manage Aliases", desc: "Claim extra names for your profile", icon: UsersRound }, { title: "Account Settings", desc: "Preferences and account details", icon: ShieldCheck }].map(({ title, desc, icon: Icon }) => <Link href="/settings" key={title} className="surface surface-hover flex items-center gap-4 rounded-2xl p-4 text-left"><span className="icon-glass flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-zinc-400"><Icon size={17} /></span><span className="min-w-0 flex-1"><span className="block text-sm font-medium text-zinc-200">{title}</span><span className="mt-1 block truncate text-xs text-zinc-600">{desc}</span></span><ChevronRight size={16} className="text-zinc-700" /></Link>)}</div></section></div><div className="space-y-8"><section><SectionTitle icon={Cloud} title="Connections" description="Connected services for your Misa.lol account." /><div className="surface divide-y divide-white/[.06] rounded-2xl">{[{ title: "Discord", subtitle: "Connect to show your current activity", icon: "D", active: false, color: "#7289da" }, { title: "Google", subtitle: user?.email || "Not connected", icon: "G", active: Boolean(user?.email), color: "#f1a37c" }].map((item) => <div key={item.title} className="flex items-center gap-3 p-4"><span className="icon-glass flex h-10 w-10 items-center justify-center rounded-xl text-sm font-semibold" style={{ color: item.color, background: `${item.color}16` }}>{item.icon}</span><span className="min-w-0 flex-1"><span className="block text-sm font-medium text-zinc-200">{item.title}</span><span className="mt-1 block truncate text-xs text-zinc-600">{item.subtitle}</span></span>{item.active ? <span className="flex items-center gap-1.5 text-xs text-emerald-400"><StatusDot />Connected</span> : <Button variant="ghost" className="h-8 min-h-0 px-2.5 text-xs">Connect</Button>}</div>)}</div></section><section className="relative overflow-hidden rounded-2xl border border-[#9b87f5]/20 bg-gradient-to-br from-[#211c3b] to-[#111117] p-5"><div className="absolute -right-8 -top-8 h-32 w-32 rounded-full bg-[#9b87f5]/20 blur-3xl" /><div className="relative"><div className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl bg-[#9b87f5]/20 text-[#bdb2ff]"><BadgeCheck size={18} /></div><h3 className="font-medium">Make your page yours</h3><p className="mt-2 max-w-xs text-xs leading-5 text-zinc-400">Explore customization tools to create a profile that feels unmistakably you.</p><Link href="/customize"><Button variant="accent" className="mt-5 h-9 min-h-0 px-3 text-xs">Customize profile <ChevronRight size={14} /></Button></Link></div></section></div></div>
  </main>;
}






