"use client";

import { useEffect, useState } from "react";
import { Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const isDarkMode = document.documentElement.classList.contains("dark");
    setIsDark(isDarkMode);
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDark;
    setIsDark(nextDark);

    if (nextDark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme_preference", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme_preference", "light");
    }
  };

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={toggleTheme}
      className="h-8 w-8 p-0 rounded-full border-border/80 bg-card/80 backdrop-blur-md hover:border-primary/50 hover:bg-accent/40 transition-all duration-300 shadow-xs"
      aria-label="Toggle theme"
      title={isDark ? "Switch to signature light theme" : "Switch to midnight slate theme"}
    >
      {isDark ? (
        <Sun className="h-4 w-4 text-amber-500 rotate-0 scale-100 transition-transform duration-300 hover:rotate-45" />
      ) : (
        <Moon className="h-4 w-4 text-indigo-600 rotate-0 scale-100 transition-transform duration-300 hover:-rotate-12" />
      )}
    </Button>
  );
}
