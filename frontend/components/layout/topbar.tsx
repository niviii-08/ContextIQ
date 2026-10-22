"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { navItems } from "@/lib/nav";
import {
  Clock,
  ShieldCheck,
  Globe,
  Settings2,
  Laptop,
  GraduationCap,
  Briefcase,
  Brain,
  Sparkles,
  LogOut,
  UserCircle2,
} from "lucide-react";
import { ThemeToggle } from "@/components/shared/theme-toggle";
import { useUserProfile, AVAILABLE_LANGUAGES } from "@/context/user-profile-context";
import type { LanguageCode, RolePersona } from "@/types/profile";
import { Badge } from "@/components/ui/badge";

export function Topbar() {
  const router = useRouter();
  const pathname = usePathname();
  const current =
    navItems.find((item) =>
      item.href === "/" ? pathname === "/" : pathname.startsWith(item.href)
    ) ?? navItems[0];

  const { profile, personaMeta, setLanguage, openOnboarding, logout, t } = useUserProfile();
  const [currentTime, setCurrentTime] = useState<string>("");
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour12: false,
          hour: "2-digit",
          minute: "2-digit",
        })
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const today = new Date().toLocaleDateString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

  const getPersonaIcon = (roleId: RolePersona) => {
    switch (roleId) {
      case "developer":
        return Laptop;
      case "student":
        return GraduationCap;
      case "manager":
        return Briefcase;
      case "researcher":
        return Brain;
      case "creator":
        return Sparkles;
      default:
        return Laptop;
    }
  };

  const PersonaIcon = getPersonaIcon(profile.role);
  const currentLang =
    AVAILABLE_LANGUAGES.find((l) => l.code === profile.language) || AVAILABLE_LANGUAGES[0];

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border/70 bg-card/75 px-5 backdrop-blur-xl sm:px-8 transition-colors shadow-[0_2px_12px_-2px_rgba(15,23,42,0.03)]">
      {/* Left Breadcrumb */}
      <div className="flex items-center gap-2.5 text-xs">
        <span className="text-muted-foreground font-semibold">ContextIQ</span>
        <span className="text-muted-foreground/40 font-mono">/</span>
        <span className="font-bold text-foreground bg-muted/60 px-2 py-0.5 rounded-lg border border-border/50">
          {current.label}
        </span>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2.5">
        {/* Interactive Persona Button (Opens Setup Wizard) */}
        <button
          type="button"
          onClick={openOnboarding}
          className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-indigo-200/80 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/40 hover:bg-indigo-100/80 dark:hover:bg-indigo-900/50 transition-all text-xs group shadow-2xs"
          title="Click to customize your professional persona and distraction sensitivity"
        >
          <PersonaIcon className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" />
          <span className="font-bold text-indigo-700 dark:text-indigo-300 hidden sm:inline">
            {profile.name} · {personaMeta.title.split("/")[0].trim()}
          </span>
          <Settings2 className="h-3 w-3 text-indigo-500/70" />
        </button>

        {/* Multilingual Selector Dropdown */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsLangMenuOpen((prev) => !prev)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border border-border/70 bg-background/80 hover:bg-muted/70 transition-all text-xs font-semibold shadow-2xs"
            title="Switch Language"
          >
            <span>{currentLang.flag}</span>
            <span className="font-mono text-muted-foreground">{currentLang.code.toUpperCase()}</span>
          </button>

          {isLangMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-44 rounded-2xl glass-card border border-border/80 shadow-lg p-1.5 z-50 animate-fade-in space-y-0.5">
              <span className="text-[10px] font-mono text-muted-foreground uppercase px-2.5 py-1 block font-semibold">
                Select Language
              </span>
              {AVAILABLE_LANGUAGES.map((lang) => (
                <button
                  key={lang.code}
                  type="button"
                  onClick={() => {
                    setLanguage(lang.code);
                    setIsLangMenuOpen(false);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                    profile.language === lang.code
                      ? "bg-indigo-50 dark:bg-indigo-950/60 font-bold text-indigo-600 dark:text-indigo-400"
                      : "text-foreground hover:bg-muted/70"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <span>{lang.flag}</span>
                    <span>{lang.nativeName}</span>
                  </span>
                  <span className="text-[10px] font-mono text-muted-foreground uppercase">
                    {lang.code}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Live System Time */}
        <div className="hidden lg:flex items-center gap-2 text-xs text-muted-foreground font-mono bg-muted/50 px-3 py-1 rounded-full border border-border/60 shadow-2xs">
          <Clock className="h-3.5 w-3.5 text-indigo-500" />
          <span>{today}</span>
          <span className="text-foreground font-bold">{currentTime}</span>
        </div>

        {/* Cognitive Shield Status */}
        <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
          <ShieldCheck className="h-3.5 w-3.5" />
          <span>Flow Shield</span>
        </div>

        <ThemeToggle />

        {/* User Account & Auth Menu */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setIsUserMenuOpen((prev) => !prev)}
            className="flex items-center gap-2 p-1 pl-1.5 pr-2 rounded-full border border-border/80 bg-background/80 hover:bg-muted text-xs font-semibold shadow-2xs transition-all"
            title="User Account & Auth"
          >
            <span className="flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-violet-600 text-[11px] font-bold text-white shadow-xs">
              {(profile.name || "N").charAt(0).toUpperCase()}
            </span>
            <span className="hidden md:inline font-bold text-foreground text-xs">
              {profile.name}
            </span>
          </button>

          {isUserMenuOpen && (
            <div className="absolute right-0 mt-1.5 w-52 rounded-2xl glass-card border border-border/80 shadow-lg p-2 z-50 animate-fade-in space-y-1">
              <div className="px-2.5 py-1.5 border-b border-border/60">
                <p className="text-xs font-bold text-foreground truncate">{profile.name}</p>
                <p className="text-[10px] text-muted-foreground truncate">
                  {profile.email || "neevetha@contextiq.io"}
                </p>
                <Badge
                  variant="outline"
                  className="mt-1 text-[9px] font-mono border-indigo-400/40 text-indigo-600 dark:text-indigo-400 uppercase"
                >
                  {profile.role}
                </Badge>
              </div>

              <button
                type="button"
                onClick={() => {
                  setIsUserMenuOpen(false);
                  openOnboarding();
                }}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-foreground hover:bg-muted/70 transition-colors"
              >
                <Settings2 className="h-3.5 w-3.5 text-indigo-500" />
                <span>Cognitive Setup</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setIsUserMenuOpen(false);
                  router.push("/login");
                }}
                className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-foreground hover:bg-muted/70 transition-colors"
              >
                <UserCircle2 className="h-3.5 w-3.5 text-sky-500" />
                <span>Switch / Demo Account</span>
              </button>

              <div className="pt-1 border-t border-border/60">
                <button
                  type="button"
                  onClick={() => {
                    setIsUserMenuOpen(false);
                    logout();
                    router.push("/login");
                  }}
                  className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors font-semibold"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
