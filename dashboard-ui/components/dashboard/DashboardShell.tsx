"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { BarChart3, BadgeCheck, BookOpen, ChevronRight, CircleHelp, LayoutDashboard, Link2, LogOut, Menu, Palette, Search, Settings, Share2, ShieldCheck, Sparkles, UploadCloud, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth-store";
import { useProfile } from "@/lib/profile-store";

const groups = [
  { label: "Account", items: [{ label: "Overview", href: "/", icon: LayoutDashboard }, { label: "Analytics", href: "/analytics", icon: BarChart3 }, { label: "Badges", href: "/badges", icon: BadgeCheck }, { label: "Settings", href: "/settings", icon: Settings }] },
  { label: "Customize", items: [{ label: "Customize", href: "/customize", icon: Palette }] },
  { label: "Links", items: [{ label: "Links", href: "/links", icon: Link2 }] },
];

function SidebarContent({ close }: { close: () => void }) {
  const pathname = usePathname();
  const { config } = useProfile();
  const { logout, user } = useAuth();
  const [accountOpen, setAccountOpen] = useState(true);
  const initials = config.profile.displayName.trim().slice(0, 1).toUpperCase() || "U";
  return <div className="flex h-full flex-col">
    <div className="flex h-[76px] items-center justify-between px-5"><Link href="/" onClick={close} className="flex items-center gap-3"><span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#c5b8ff] via-[#8c75eb] to-[#5946b8] text-sm font-bold text-white shadow-[0_0_25px_rgba(155,135,245,.28)]">M</span><span className="text-[15px] font-semibold tracking-[-.02em]">Misa<span className="text-[#a899ff]">.lol</span></span></Link><button type="button" className="rounded-lg p-1.5 text-zinc-500 hover:bg-white/[.06] hover:text-white md:hidden" onClick={close} aria-label="Close navigation"><X size={18} /></button></div>
    <div className="px-4"><button type="button" className="flex h-10 w-full items-center gap-2.5 rounded-xl border border-white/[.06] bg-white/[.025] px-3 text-left text-xs text-zinc-500 transition hover:border-white/[.12] hover:text-zinc-300"><Search size={15} /><span className="flex-1">Search features...</span><kbd className="rounded-md border border-white/[.09] bg-white/[.04] px-1.5 py-0.5 font-mono text-[10px] text-zinc-500">ÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Å¡Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¹ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ K</kbd></button></div>
    <nav className="mt-8 flex-1 space-y-7 overflow-y-auto px-3 pb-5">{groups.map((group) => <div key={group.label}><button type="button" onClick={() => group.label === "Account" && setAccountOpen((open) => !open)} className="mb-2 flex w-full items-center justify-between px-3 text-left text-[10px] font-semibold uppercase tracking-[.2em] text-zinc-600">{group.label}{group.label === "Account" && <ChevronRight size={13} className={`transition-transform ${accountOpen ? "rotate-90" : ""}`} />}</button><div className={`space-y-1 ${group.label === "Account" && !accountOpen ? "hidden" : ""}`}>{group.items.map(({ label, href, icon: Icon }) => { const active = pathname === href; return <Link key={href} href={href} onClick={close} className={`group relative flex h-10 items-center gap-3 rounded-xl px-3 text-sm transition ${active ? "bg-[#9b87f5]/[.12] text-white" : "text-zinc-500 hover:bg-white/[.05] hover:text-zinc-200"}`}><Icon size={17} strokeWidth={active ? 2 : 1.7} className={active ? "text-[#b4a8ff]" : "text-zinc-600 group-hover:text-zinc-300"} />{label}{active && <span className="absolute right-3 h-1.5 w-1.5 rounded-full bg-[#b7aaff] shadow-[0_0_10px_#9b87f5]" />}</Link> })}</div></div>)}<>{user?.isAdmin && <Link href="/admin" onClick={close} className="mb-7 flex h-10 items-center gap-3 rounded-xl px-3 text-sm text-amber-200 hover:bg-white/[.05]"><ShieldCheck size={17} />Admin panel</Link>}</><div><div className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[.2em] text-zinc-600">More</div><div className="space-y-1"><Link href="#" className="flex h-10 items-center gap-3 rounded-xl px-3 text-sm text-zinc-500 hover:bg-white/[.05] hover:text-zinc-200"><Sparkles size={17} className="text-zinc-600" />Premium</Link><Link href="#" className="flex h-10 items-center gap-3 rounded-xl px-3 text-sm text-zinc-500 hover:bg-white/[.05] hover:text-zinc-200"><UploadCloud size={17} className="text-zinc-600" />Image Host</Link><Link href="#" className="flex h-10 items-center gap-3 rounded-xl px-3 text-sm text-zinc-500 hover:bg-white/[.05] hover:text-zinc-200"><BookOpen size={17} className="text-zinc-600" />Templates</Link></div></div></nav>
    <div className="space-y-1 border-t border-white/[.06] p-3"><Link href="#" className="flex h-9 items-center gap-3 rounded-lg px-3 text-xs text-zinc-500 hover:bg-white/[.05] hover:text-zinc-200"><CircleHelp size={15} />Help Center</Link><a href={`/${config.profile.username}`} target="_blank" className="flex h-9 items-center gap-3 rounded-lg px-3 text-xs text-zinc-500 hover:bg-white/[.05] hover:text-zinc-200"><Share2 size={15} />Share Your Profile</a><div className="mt-3 flex items-center gap-3 rounded-xl border border-white/[.06] bg-white/[.025] p-2.5"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-[#5d4ea4] to-[#241d45] text-xs font-semibold">{initials}</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-medium text-zinc-200">@{config.profile.username}</p><p className="font-mono text-[10px] text-zinc-600">UID: {config.profile.uid}</p></div><button type="button" aria-label="Log out" title="Log out" onClick={() => void logout()} className="rounded-lg p-1.5 text-zinc-600 hover:bg-white/[.06] hover:text-white"><LogOut size={15} /></button></div></div>
  </div>;
}

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, isReady } = useAuth();
  const [open, setOpen] = useState(false);
  useEffect(() => { if (isReady && !user) router.replace("/login"); }, [isReady, router, user]);
  if (!isReady || !user) return <div className="min-h-screen bg-[#07070a]" />;
  return <div className="app-shell min-h-screen"><aside className="sidebar-glass fixed inset-y-0 left-0 z-50 hidden w-[248px] border-r md:block"><SidebarContent close={() => undefined} /></aside>{open && <><button type="button" className="animate-fade-in fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden" onClick={() => setOpen(false)} aria-label="Close navigation" /><aside className="sidebar-glass animate-slide-in fixed inset-y-0 left-0 z-50 w-[272px] border-r md:hidden"><SidebarContent close={() => setOpen(false)} /></aside></>}<div className="md:pl-[248px]"><header className="sticky top-0 z-30 flex h-[68px] items-center border-b border-white/[.06] bg-[#07070a]/70 px-4 backdrop-blur-xl sm:px-8 md:hidden"><button type="button" onClick={() => setOpen(true)} className="rounded-[11px] border border-[#9b87f5]/30 bg-[#9b87f5]/10 p-2 text-[#c8beff] hover:bg-[#9b87f5]/20" aria-label="Open navigation"><Menu size={19} /></button><div className="ml-3 flex items-center gap-2 text-sm font-semibold">Misa<span className="text-[#a899ff]">.lol</span></div></header>{children}</div></div>;
}











