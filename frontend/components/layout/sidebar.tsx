"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { navItems } from "@/lib/nav";
import { Activity } from "lucide-react";
import { USE_MOCK } from "@/lib/api";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-64 shrink-0 border-r border-border bg-card lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-3 border-b border-border px-5">
        <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-sm">
          <Activity className="h-4 w-4" aria-hidden="true" />
        </span>
        <div className="leading-tight">
          <p className="text-sm font-semibold tracking-tight">ContextIQ</p>
          <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground">Behavioural intelligence</p>
        </div>
      </div>

      <nav
        aria-label="Primary"
        className="flex flex-1 flex-col gap-1 overflow-y-auto p-3"
      >
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
                "group flex items-start gap-3 rounded-md px-3 py-2.5 text-sm transition-colors",
                active
                  ? "bg-accent text-accent-foreground"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground",
              )}
            >
              <Icon
                className={cn(
                  "mt-0.5 h-4 w-4 shrink-0",
                  active ? "text-primary" : "text-muted-foreground",
                )}
                aria-hidden="true"
              />
              <span className="flex flex-col">
                <span className="font-medium">{item.label}</span>
                <span className="text-[11px] text-muted-foreground group-hover:text-muted-foreground">
                  {item.description}
                </span>
              </span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-4 text-[11px] text-muted-foreground">
        <span className="inline-flex items-center gap-1.5"> <span className={cn("h-1.5 w-1.5 rounded-full", USE_MOCK ? "bg-risk-medium" : "bg-risk-low")} aria-hidden="true" /> {USE_MOCK ? "Mock data mode" : "Live analytics mode"}</span> — see{" "}
        <span className="font-mono text-foreground">.env.example</span>
      </div>
    </aside>
  );
}
