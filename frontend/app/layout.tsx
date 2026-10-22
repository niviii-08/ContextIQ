import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/app-shell";

export const metadata: Metadata = {
  title: "ContextIQ — Behavioral Intelligence & Micro-Delay Analytics",
  description:
    "ContextIQ quantifies micro-delays, context switching, and task forgetting to eliminate invisible friction from your daily workflow.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `try { if (localStorage.getItem('theme_preference') === 'dark') { document.documentElement.classList.add('dark'); } else { document.documentElement.classList.remove('dark'); } } catch (_) {}`,
          }}
        />
      </head>
      <body className="min-h-full bg-background text-foreground font-sans antialiased selection:bg-primary/20 selection:text-primary">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
