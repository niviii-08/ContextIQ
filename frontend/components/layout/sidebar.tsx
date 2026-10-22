"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { navItems } from "@/lib/nav";
import { Activity, Sparkles, Flame, UserCheck, Settings2 } from "lucide-react";
import { USE_MOCK } from "@/lib/api";
import { useUserProfile } from "@/context/user-profile-context";

export function Sidebar() {
  const pathname = usePathname();
  const { profile, personaMeta, openOnboarding } = useUserProfile();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-border/80 bg-card/85 lg:flex lg:flex-col select-none backdrop-blur-xl">
      {/* Brand Header */}
      <div className="flex h-16 items-center gap-3 px-5 border-b border-border/70">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 text-white shadow-md shadow-indigo-500/30">
          <Activity className="h-5 w-5" aria-hidden="true" />
        </div>
        <div>
          <span className="text-base font-extrabold tracking-tight text-foreground flex items-center gap-1.5">
            ContextIQ
            <span className="inline-flex items-center rounded-full bg-indigo-500/10 px-1.5 py-0.5 text-[9px] font-bold font-mono text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
              PRO
            </span>
          </span>
          <span className="block text-[10px] text-muted-foreground font-semibold leading-none">
            Cognitive Flow Co-Pilot
          </span>
        </div>
      </div>

      {/* Nav items */}
      <nav aria-label="Primary" className="flex flex-1 flex-col gap-1.5 p-3 overflow-y-auto">
        <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70 flex items-center justify-between">
          <span>Platform Workspace</span>
          <button
            type="button"
            onClick={openOnboarding}
            className="text-[9px] font-mono text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1"
            title="Configure profile"
          >
            <Settings2 className="h-2.5 w-2.5" />
            Persona
          </button>
        </div>
        {navItems.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-semibold transition-all duration-200",
                active
                  ? "bg-indigo-50/90 text-indigo-700 shadow-xs border-r-2 border-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-300 dark:border-indigo-500"
                  : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
              )}
            >
              <Icon
                className={cn(
                  "h-4 w-4 shrink-0 transition-transform duration-200 group-hover:scale-110",
                  active
                    ? "text-indigo-600 dark:text-indigo-400"
                    : "text-muted-foreground group-hover:text-foreground"
                )}
                aria-hidden="true"
              />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* Role-Calibrated Cognitive Streak Widget */}
      <div className="p-3 pt-0">
        <div className="p-3 rounded-2xl bg-gradient-to-br from-indigo-50/90 via-background to-violet-50/70 dark:from-indigo-950/40 dark:to-violet-950/30 border border-indigo-200/80 dark:border-indigo-900/60 shadow-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-indigo-700 dark:text-indigo-300 flex items-center gap-1.5">
              <span>🔥</span> {profile.name}&apos;s Streak
            </span>
            <span className="text-[9px] font-mono font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-full border border-emerald-500/20">
              {profile.role.toUpperCase()}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-snug">
            Avg resumption lag trimmed from <span className="font-semibold text-foreground">3.8m</span> down to <span className="font-bold text-indigo-600 dark:text-indigo-400">2.1m</span>.
          </p>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div className="h-full bg-gradient-to-r from-indigo-500 to-violet-600 rounded-full w-[78%] transition-all duration-700" />
          </div>
        </div>
      </div>

      {/* Engine Status Footer */}
      <div className="border-t border-border/70 p-3">
        <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-muted/50 text-[11px] text-muted-foreground border border-border/60">
          <span className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            <span className="font-semibold text-foreground/80">
              {USE_MOCK ? "Local Sandbox" : "Live Telemetry"}
            </span>
          </span>
          <span className="font-mono text-[9px] px-2 py-0.5 rounded-full bg-background border border-border/60 text-foreground font-bold shadow-2xs">
            {profile.language.toUpperCase()}
          </span>
        </div>
      </div>
    </aside>
  );
}
