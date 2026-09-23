"use client";

import { usePathname } from "next/navigation";
import { navItems } from "@/lib/nav";
import { Badge } from "@/components/ui/badge";
import { USE_MOCK } from "@/lib/api";

export function Topbar() {
  const pathname = usePathname();
  const current =
    navItems.find((item) =>
      item.href === "/" ? pathname === "/" : pathname.startsWith(item.href),
    ) ?? navItems[0];

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
  });

  return (
    <header className="sticky top-0 z-30 flex min-h-16 items-center justify-between gap-4 border-b border-border bg-background/90 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/75 sm:px-6 lg:px-8">
      <div>
        <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">Workspace / {USE_MOCK ? "simulation" : "live"}</p>
        <h1 className="mt-0.5 text-base font-semibold tracking-tight text-foreground">
          {current.label}
        </h1>
        <p className="hidden text-xs text-muted-foreground sm:block">
          {current.description}
        </p>
      </div>
      <div className="flex items-center gap-3">
        <span className="hidden font-mono text-xs text-muted-foreground sm:inline">
          {today}
        </span>
        {USE_MOCK && (
          <Badge variant="outline" className="font-mono normal-case">
            Mock data
          </Badge>
        )}
      </div>
    </header>
  );
}
