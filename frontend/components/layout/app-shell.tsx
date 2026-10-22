"use client";

import { usePathname } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { Topbar } from "@/components/layout/topbar";
import { MobileNav } from "@/components/layout/mobile-nav";
import { UserProfileProvider } from "@/context/user-profile-context";
import { CognitiveOnboardingDialog } from "@/components/onboarding/cognitive-onboarding-dialog";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname === "/signup";

  return (
    <UserProfileProvider>
      <div className="relative flex min-h-screen w-full bg-background text-foreground antialiased selection:bg-indigo-500/20 selection:text-indigo-600">
        {/* Trademark Ethereal Ambient Mesh Orbs */}
        <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
          {/* Top-Left Electric Iris Orb */}
          <div className="absolute -top-[12%] left-[8%] h-[580px] w-[580px] rounded-full bg-gradient-to-br from-indigo-500/12 via-violet-500/8 to-transparent blur-[120px] dark:from-indigo-600/15 dark:via-violet-600/10" />
          {/* Top-Right Sky Cyan Orb */}
          <div className="absolute top-[8%] -right-[8%] h-[620px] w-[620px] rounded-full bg-gradient-to-bl from-sky-400/14 via-teal-400/8 to-transparent blur-[130px] dark:from-sky-500/12 dark:via-cyan-600/10" />
          {/* Bottom-Center Warm Amber/Rose Orb */}
          <div className="absolute -bottom-[15%] left-[25%] h-[600px] w-[600px] rounded-full bg-gradient-to-tr from-amber-400/10 via-rose-400/8 to-transparent blur-[140px] dark:from-amber-600/10 dark:via-rose-600/8" />
        </div>

        {isAuthPage ? (
          <main className="relative z-10 flex min-h-screen w-full items-center justify-center p-4">
            {children}
          </main>
        ) : (
          <>
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
            >
              Skip to main content
            </a>

            {/* Global Onboarding & Workflow Wizard */}
            <CognitiveOnboardingDialog />

            {/* Main App Layout */}
            <div className="relative z-10 flex min-h-screen w-full">
              <Sidebar />
              <div className="flex min-h-screen w-full flex-1 flex-col">
                <Topbar />
                <main
                  id="main-content"
                  className="flex-1 px-4 pb-24 pt-6 sm:px-6 lg:px-8 lg:pb-8"
                >
                  <div className="mx-auto w-full max-w-7xl">{children}</div>
                </main>
                <MobileNav />
              </div>
            </div>
          </>
        )}
      </div>
    </UserProfileProvider>
  );
}
