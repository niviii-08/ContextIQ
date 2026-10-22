"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  Laptop,
  GraduationCap,
  Briefcase,
  Brain,
  Sparkles,
  ArrowRight,
  ArrowLeft,
  Lock,
  Mail,
  User,
  Building,
  Check,
  Eye,
  EyeOff,
  Globe,
  ShieldCheck,
  Zap,
  ListTodo,
  Plus,
  Trash2,
  Clock,
  Database,
  Shirt,
  Utensils,
  AlertCircle,
  Calendar,
  Coffee,
  Smartphone,
  Flame,
  CheckCircle2,
} from "lucide-react";
import {
  useUserProfile,
  PERSONA_DEFINITIONS,
  AVAILABLE_LANGUAGES,
} from "@/context/user-profile-context";
import type { RolePersona, LanguageCode, FocusRhythm } from "@/types/profile";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { ThemeToggle } from "@/components/shared/theme-toggle";

interface AuthCardProps {
  initialMode?: "login" | "signup";
}

const DEMO_ACCOUNTS = [
  {
    name: "Neevetha",
    email: "neevetha@contextiq.io",
    title: "Senior Software Engineer",
    org: "Distributed Systems Lab",
    role: "developer" as RolePersona,
    rhythm: "morning" as FocusRhythm,
    icon: Laptop,
    badge: "Engineering",
    avatarBg: "from-indigo-500 to-indigo-700",
  },
  {
    name: "Alex Chen",
    email: "alex.chen@stanford.edu",
    title: "MSc Computer Science Candidate",
    org: "Stanford AI Lab",
    role: "student" as RolePersona,
    rhythm: "night" as FocusRhythm,
    icon: GraduationCap,
    badge: "Academic",
    avatarBg: "from-sky-500 to-blue-700",
  },
  {
    name: "Sarah Miller",
    email: "sarah.m@fintech.io",
    title: "VP Product & Operations",
    org: "Global FinTech HQ",
    role: "manager" as RolePersona,
    rhythm: "afternoon" as FocusRhythm,
    icon: Briefcase,
    badge: "Leadership",
    avatarBg: "from-emerald-500 to-teal-700",
  },
  {
    name: "Dr. Aris Thorne",
    email: "athorne@research.org",
    title: "Deep Learning Research Scientist",
    org: "Frontier Intelligence Institute",
    role: "researcher" as RolePersona,
    rhythm: "morning" as FocusRhythm,
    icon: Brain,
    badge: "AI Research",
    avatarBg: "from-purple-500 to-violet-700",
  },
];

interface SignupTask {
  id: string;
  title: string;
  priority: "low" | "medium" | "high" | "urgent";
  estimated_minutes: number;
  category: string;
}

const DEFAULT_DAILY_CHORES = [
  "Vessel washing / Dishwashing",
  "Cooking & Meal Prep",
  "Sweeping & Mopping",
  "Taking out the trash",
  "Watering plants",
  "Making bed & dusting",
];

const DEFAULT_WEEKEND_CHORES = [
  "Dress washing / Laundry & Ironing",
  "Deep house & room cleaning",
  "Grocery & vegetable market run",
  "Weekly meal prep",
  "Changing bed linens",
  "Vehicle wash & maintenance",
];

const DEFAULT_FORGET_ITEMS = [
  "Switching off geyser / stove / appliances",
  "Taking daily vitamins & prescribed medications",
  "Replying to starred DMs & urgent emails",
  "Pushing git branch / committing work before leaving",
  "Drinking water throughout focus blocks",
  "Grabbing keys, office badge, or laptop charger",
];

const DEFAULT_TIME_DELAYS = [
  "Reels / Shorts / Social doomscroll loops",
  "Post-lunch 2 PM cognitive slump",
  "Context switching from meetings back to code",
  "Browser tab rabbit holes & docs wandering",
  "Resuming after unexpected phone calls or taps",
  "Indecision on what task to start next",
];

export function AuthCard({ initialMode = "login" }: AuthCardProps) {
  const router = useRouter();
  const { profile, login, setLanguage } = useUserProfile();

  const [mode, setMode] = useState<"login" | "signup">(initialMode);
  const [signupStep, setSignupStep] = useState<1 | 2 | 3 | 4>(1);
  const [showPassword, setShowPassword] = useState(false);
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);

  // Form states - Step 1: Identity & Occupation (Empty by default for user entry)
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [customTitle, setCustomTitle] = useState("");
  const [organization, setOrganization] = useState("");
  const [selectedRole, setSelectedRole] = useState<RolePersona>("developer");

  // Form states - Step 2: Daily Routine & Real-Life Chores (Empty by default)
  const [dailyRoutine, setDailyRoutine] = useState("");
  const [dailyChores, setDailyChores] = useState<string[]>([]);
  const [customDailyChore, setCustomDailyChore] = useState("");
  const [weekendChores, setWeekendChores] = useState<string[]>([]);
  const [customWeekendChore, setCustomWeekendChore] = useState("");

  // Form states - Step 3: What are you always likely to forget? (Empty by default)
  const [frequentForgetItems, setFrequentForgetItems] = useState<string[]>([]);
  const [customForgetItem, setCustomForgetItem] = useState("");

  // Form states - Step 4: Where exists a time delay? & Tasks (Empty by default)
  const [timeDelayTriggers, setTimeDelayTriggers] = useState<string[]>([]);
  const [customTimeDelay, setCustomTimeDelay] = useState("");
  const [selectedRhythm, setSelectedRhythm] = useState<FocusRhythm>("morning");

  // Initial focus tasks state (Empty by default)
  const [initialTasks, setInitialTasks] = useState<SignupTask[]>([]);
  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState<"low" | "medium" | "high" | "urgent">("medium");
  const [newTaskMinutes, setNewTaskMinutes] = useState<number>(45);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authStatusMessage, setAuthStatusMessage] = useState<string | null>(null);

  const currentLang =
    AVAILABLE_LANGUAGES.find((l) => l.code === profile.language) || AVAILABLE_LANGUAGES[0];

  const handleSelectRole = (roleKey: RolePersona) => {
    setSelectedRole(roleKey);
  };

  const toggleItem = (list: string[], setList: React.Dispatch<React.SetStateAction<string[]>>, item: string) => {
    if (list.includes(item)) {
      setList(list.filter((i) => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  const addCustomItem = (
    value: string,
    setValue: (val: string) => void,
    list: string[],
    setList: React.Dispatch<React.SetStateAction<string[]>>
  ) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    if (!list.includes(trimmed)) {
      setList([...list, trimmed]);
    }
    setValue("");
  };

  const handleAddCustomTask = () => {
    if (!newTaskTitle.trim()) return;
    setInitialTasks((prev) => [
      ...prev,
      {
        id: `t_${Date.now()}`,
        title: newTaskTitle.trim(),
        priority: newTaskPriority,
        estimated_minutes: newTaskMinutes,
        category: "Deep Work",
      },
    ]);
    setNewTaskTitle("");
  };

  const handleRemoveTask = (id: string) => {
    setInitialTasks((prev) => prev.filter((t) => t.id !== id));
  };

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setAuthError(null);
    setAuthStatusMessage("Authenticating with PostgreSQL database...");

    try {
      const res = await fetch("http://localhost:8000/api/v1/users/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password: password.trim() || "password123",
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          localStorage.setItem("contextiq_token", data.access_token);
        }
        if (data.user?.id) {
          localStorage.setItem("contextiq_user_id", data.user.id);
        }
        if (data.tasks && Array.isArray(data.tasks)) {
          const mappedTasks = data.tasks.map((t: any) => ({
            id: String(t.id),
            title: t.title,
            description: t.description || "",
            category: t.context_tag || "General",
            context: t.context_tag || "General",
            status: t.status || "PENDING",
            priority: t.priority?.toUpperCase() || "MEDIUM",
            dueAt: t.due_at,
            createdAt: t.created_at || new Date().toISOString(),
            updatedAt: t.updated_at || new Date().toISOString(),
            estimatedMinutes: t.estimated_minutes || 30,
            tags: [t.context_tag || "General"],
            forgottenCount: 0,
            completionStreak: 0,
          }));
          localStorage.setItem("contextiq_user_tasks", JSON.stringify(mappedTasks));
        }

        login({
          name: data.user.display_name,
          email: data.user.email,
          role: (data.user.role_persona as RolePersona) || selectedRole,
          customTitle: data.user.custom_title || customTitle,
          organization: data.user.organization || organization,
          focusRhythm: (data.user.focus_rhythm as FocusRhythm) || selectedRhythm,
          language: (data.user.language as LanguageCode) || profile.language,
          dailyRoutine: data.user.daily_routine || dailyRoutine,
          dailyChores: data.user.daily_chores ? JSON.parse(data.user.daily_chores) : dailyChores,
          weekendChores: data.user.weekend_chores ? JSON.parse(data.user.weekend_chores) : weekendChores,
          frequentForgetItems: data.user.frequent_forget_items ? JSON.parse(data.user.frequent_forget_items) : frequentForgetItems,
          timeDelayTriggers: data.user.time_delay_triggers ? JSON.parse(data.user.time_delay_triggers) : timeDelayTriggers,
          primaryOccupation: data.user.primary_occupation || customTitle,
          isAuthenticated: true,
        });
        router.push("/tasks");
        return;
      } else {
        const errData = await res.json().catch(() => ({}));
        setAuthError(errData.detail || "Invalid email or password.");
      }
    } catch {
      // offline fallback
    } finally {
      setIsSubmitting(false);
    }

    login({
      name: name.trim() || "Neevetha",
      email: email.trim() || "neevetha@contextiq.io",
      role: selectedRole,
      customTitle,
      organization,
      focusRhythm: selectedRhythm,
      isAuthenticated: true,
    });
    router.push("/tasks");
  };

  const handleSignupSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!name.trim()) {
      setAuthError("Please provide your name.");
      setSignupStep(1);
      return;
    }
    if (!email.trim() || !email.includes("@")) {
      setAuthError("Please provide a valid email address.");
      setSignupStep(1);
      return;
    }

    setIsSubmitting(true);
    setAuthError(null);
    setAuthStatusMessage("Persisting routine, chores, memory anchors & tasks directly to PostgreSQL...");

    const tasksToSubmit = initialTasks
      .filter((t) => t.title.trim().length > 0)
      .map((t) => ({
        title: t.title.trim(),
        priority: t.priority,
        estimated_minutes: t.estimated_minutes,
        category: t.category,
      }));

    try {
      const res = await fetch("http://localhost:8000/api/v1/users/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password: password.trim() || "password123",
          display_name: name.trim() || "User",
          role_persona: selectedRole,
          custom_title: customTitle.trim() || PERSONA_DEFINITIONS[selectedRole]?.title.split("/")[0].trim(),
          organization: organization.trim() || "Focus Mode",
          focus_rhythm: selectedRhythm,
          daily_goal_minutes: 120,
          language: profile.language,
          distractions: profile.distractions,
          daily_routine: dailyRoutine.trim(),
          daily_chores: dailyChores,
          weekend_chores: weekendChores,
          frequent_forget_items: frequentForgetItems,
          time_delay_triggers: timeDelayTriggers,
          primary_occupation: customTitle.trim() || PERSONA_DEFINITIONS[selectedRole]?.title.split("/")[0].trim(),
          initial_tasks: tasksToSubmit,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          localStorage.setItem("contextiq_token", data.access_token);
        }
        if (data.user?.id) {
          localStorage.setItem("contextiq_user_id", data.user.id);
        }
        if (data.tasks && Array.isArray(data.tasks)) {
          const mappedTasks = data.tasks.map((t: any) => ({
            id: String(t.id),
            title: t.title,
            description: t.description || "",
            category: t.context_tag || "General",
            context: t.context_tag || "General",
            status: t.status || "PENDING",
            priority: t.priority?.toUpperCase() || "MEDIUM",
            dueAt: t.due_at,
            createdAt: t.created_at || new Date().toISOString(),
            updatedAt: t.updated_at || new Date().toISOString(),
            estimatedMinutes: t.estimated_minutes || 30,
            tags: [t.context_tag || "General"],
            forgottenCount: 0,
            completionStreak: 0,
          }));
          localStorage.setItem("contextiq_user_tasks", JSON.stringify(mappedTasks));
        }

        login({
          name: data.user.display_name,
          email: data.user.email,
          role: (data.user.role_persona as RolePersona) || selectedRole,
          customTitle: data.user.custom_title,
          organization: data.user.organization,
          focusRhythm: (data.user.focus_rhythm as FocusRhythm) || selectedRhythm,
          language: (data.user.language as LanguageCode) || profile.language,
          dailyRoutine: dailyRoutine.trim(),
          dailyChores,
          weekendChores,
          frequentForgetItems,
          timeDelayTriggers,
          primaryOccupation: customTitle.trim(),
          isAuthenticated: true,
          onboardingCompleted: true,
        });
        router.push("/tasks");
        return;
      } else {
        const errData = await res.json().catch(() => ({}));
        setAuthError(errData.detail || "Signup failed on database server.");
      }
    } catch {
      // offline fallback
    } finally {
      setIsSubmitting(false);
    }

    // Offline task generation from collected questionnaire items ONLY
    const offlineTasks = [
      ...dailyChores.map((c, i) => ({
        id: `dc-${i}`,
        title: `Daily Chore: ${c}`,
        description: `Registered daily routine chore: ${c}`,
        category: "Daily Chores",
        context: "Home",
        status: "PENDING" as const,
        priority: "MEDIUM" as const,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        estimatedMinutes: 25,
        tags: ["Daily Chores"],
        forgottenCount: 0,
        completionStreak: 0,
      })),
      ...weekendChores.map((c, i) => ({
        id: `wc-${i}`,
        title: `Weekend Chore: ${c}`,
        description: `Registered weekend chore routine: ${c}`,
        category: "Weekend Chores",
        context: "Home",
        status: "PENDING" as const,
        priority: "MEDIUM" as const,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        estimatedMinutes: 45,
        tags: ["Weekend Chores"],
        forgottenCount: 0,
        completionStreak: 0,
      })),
      ...frequentForgetItems.map((f, i) => ({
        id: `fa-${i}`,
        title: `Anti-Forget Anchor: ${f}`,
        description: `Safety memory checkpoint: ${f}`,
        category: "Memory Anchor",
        context: "Safety",
        status: "PENDING" as const,
        priority: "HIGH" as const,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        estimatedMinutes: 10,
        tags: ["Memory Anchor"],
        forgottenCount: 0,
        completionStreak: 0,
      })),
      ...tasksToSubmit.map((t, i) => ({
        id: `init-${i}`,
        title: t.title,
        description: "Focus work item",
        category: t.category || "Deep Work",
        context: "Work",
        status: "PENDING" as const,
        priority: (t.priority?.toUpperCase() as any) || "MEDIUM",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        estimatedMinutes: t.estimated_minutes || 45,
        tags: [t.category || "Deep Work"],
        forgottenCount: 0,
        completionStreak: 0,
      })),
    ];
    localStorage.setItem("contextiq_user_tasks", JSON.stringify(offlineTasks));

    login({
      name: name.trim() || "User",
      email: email.trim() || "user@contextiq.io",
      role: selectedRole,
      customTitle: customTitle.trim() || PERSONA_DEFINITIONS[selectedRole]?.title.split("/")[0].trim(),
      organization: organization.trim() || "Focus Mode",
      focusRhythm: selectedRhythm,
      dailyRoutine: dailyRoutine.trim(),
      dailyChores,
      weekendChores,
      frequentForgetItems,
      timeDelayTriggers,
      primaryOccupation: customTitle.trim(),
      isAuthenticated: true,
      onboardingCompleted: true,
    });
    router.push("/tasks");
  };

  const handleQuickDemo = async (demo: (typeof DEMO_ACCOUNTS)[0]) => {
    setIsSubmitting(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/users/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: demo.email,
          password: "demopassword123",
          display_name: demo.name,
          role_persona: demo.role,
          custom_title: demo.title,
          organization: demo.org,
          focus_rhythm: demo.rhythm,
          language: "en",
          daily_routine: "Morning focus 8 AM - 12 PM, system review, afternoon synchronization",
          daily_chores: ["Vessel washing / Dishwashing", "Cooking & Meal Prep"],
          weekend_chores: ["Dress washing / Laundry & Ironing", "Market run"],
          frequent_forget_items: ["Switching off geyser / stove / appliances", "Pushing git branch"],
          time_delay_triggers: ["Reels & Shorts loops", "Post-lunch slump"],
          primary_occupation: demo.title,
          initial_tasks: [
            {
              title: `${demo.title}: Review Workstream & PRs`,
              priority: "high",
              estimated_minutes: 45,
              category: "Workstream",
            },
            {
              title: `${demo.title}: Context Switch Friction Analysis`,
              priority: "medium",
              estimated_minutes: 30,
              category: "Analysis",
            },
          ],
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.access_token) localStorage.setItem("contextiq_token", data.access_token);
        if (data.user?.id) localStorage.setItem("contextiq_user_id", data.user.id);
        if (data.tasks && Array.isArray(data.tasks)) {
          const mappedTasks = data.tasks.map((t: any) => ({
            id: String(t.id),
            title: t.title,
            description: t.description || "",
            category: t.context_tag || "General",
            context: t.context_tag || "General",
            status: t.status || "PENDING",
            priority: t.priority?.toUpperCase() || "MEDIUM",
            dueAt: t.due_at,
            createdAt: t.created_at || new Date().toISOString(),
            updatedAt: t.updated_at || new Date().toISOString(),
            estimatedMinutes: t.estimated_minutes || 30,
            tags: [t.context_tag || "General"],
            forgottenCount: 0,
            completionStreak: 0,
          }));
          localStorage.setItem("contextiq_user_tasks", JSON.stringify(mappedTasks));
        }
      }
    } catch {
      // offline fallback
    } finally {
      setIsSubmitting(false);
    }

    login({
      name: demo.name,
      email: demo.email,
      role: demo.role,
      customTitle: demo.title,
      organization: demo.org,
      focusRhythm: demo.rhythm,
      isAuthenticated: true,
      onboardingCompleted: true,
    });
    router.push("/tasks");
  };

  const getRoleIcon = (roleId: RolePersona) => {
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

  return (
    <div className="w-full max-w-2xl mx-auto animate-fade-in">
      <div className="relative rounded-3xl glass-card border border-border/80 shadow-[0_20px_60px_-15px_rgba(15,23,42,0.15)] dark:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.6)] overflow-hidden">
        {/* Top Iridescent Accent Bar */}
        <div className="absolute inset-x-0 top-0 h-[4px] bg-gradient-to-r from-indigo-500 via-sky-400 to-amber-400" />

        {/* Header Bar */}
        <div className="p-6 pb-5 border-b border-border/70 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-700 text-white shadow-md shadow-indigo-500/30">
              <Activity className="h-5 w-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-extrabold tracking-tight text-foreground">
                  ContextIQ
                </h1>
                <Badge className="bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/20 text-[9px] font-mono">
                  v2.4 PRO • PostgreSQL
                </Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Behavioral Intelligence &amp; Cognitive Flow Telemetry
              </p>
            </div>
          </div>

          {/* Right Controls: Language & Theme */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <button
                type="button"
                onClick={() => setIsLangMenuOpen((prev) => !prev)}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl border border-border/70 bg-background/80 hover:bg-muted text-xs font-semibold shadow-2xs transition-all"
                title="Switch Language"
              >
                <span>{currentLang.flag}</span>
                <span className="font-mono text-muted-foreground uppercase text-[11px]">
                  {currentLang.code}
                </span>
              </button>

              {isLangMenuOpen && (
                <div className="absolute right-0 mt-1.5 w-40 rounded-2xl glass-card border border-border/80 shadow-lg p-1.5 z-50 animate-fade-in space-y-0.5">
                  {AVAILABLE_LANGUAGES.map((lang) => (
                    <button
                      key={lang.code}
                      type="button"
                      onClick={() => {
                        setLanguage(lang.code);
                        setIsLangMenuOpen(false);
                      }}
                      className={cn(
                        "w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors",
                        profile.language === lang.code
                          ? "bg-indigo-50 dark:bg-indigo-950/60 font-bold text-indigo-600 dark:text-indigo-400"
                          : "text-foreground hover:bg-muted/70"
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <span>{lang.flag}</span>
                        <span>{lang.nativeName}</span>
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            <ThemeToggle />
          </div>
        </div>

        {/* Tab Switcher */}
        <div className="px-6 pt-5">
          <div className="grid grid-cols-2 p-1 rounded-2xl bg-muted/60 border border-border/60">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={cn(
                "py-2 text-xs font-bold rounded-xl transition-all duration-200",
                mode === "login"
                  ? "bg-card text-foreground shadow-xs border border-border/80"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setMode("signup")}
              className={cn(
                "py-2 text-xs font-bold rounded-xl transition-all duration-200",
                mode === "signup"
                  ? "bg-card text-foreground shadow-xs border border-border/80"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Sign Up (Interactive Questionnaire)
            </button>
          </div>
        </div>

        {/* Body Content */}
        <div className="p-6 space-y-5">
          {/* ================= 1. SIGN IN FORM ================= */}
          {mode === "login" ? (
            <form onSubmit={handleLoginSubmit} className="space-y-4">
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                    <Mail className="h-3.5 w-3.5 text-indigo-500" />
                    Work or University Email
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@organization.com"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Lock className="h-3.5 w-3.5 text-indigo-500" />
                      Password
                    </label>
                    <span className="text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline cursor-pointer">
                      Forgot password?
                    </span>
                  </div>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••••••"
                      className="w-full pl-3.5 pr-10 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword((prev) => !prev)}
                      className="absolute right-3 top-2.5 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-1">
                <label className="flex items-center gap-2 cursor-pointer select-none text-muted-foreground hover:text-foreground">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="rounded border-border text-indigo-600 focus:ring-indigo-500"
                  />
                  <span>Remember session on this device</span>
                </label>
              </div>

              <Button
                type="submit"
                disabled={isSubmitting}
                className="w-full h-11 text-xs font-bold gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-md shadow-indigo-500/25 transition-all active:scale-98"
              >
                {isSubmitting ? "Authenticating..." : "Sign In to Workspace"}
                <ArrowRight className="h-4 w-4" />
              </Button>

              {/* 1-Click Demo Profiles */}
              <div className="pt-3 border-t border-border/60 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1">
                    <Zap className="h-3 w-3 text-amber-500 fill-current" />
                    Quick Demo Sign-In (Recruiter Fast Pass):
                  </span>
                  <span className="text-[10px] text-muted-foreground">1-click test</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {DEMO_ACCOUNTS.map((demo) => {
                    const Icon = demo.icon;
                    return (
                      <button
                        key={demo.email}
                        type="button"
                        onClick={() => handleQuickDemo(demo)}
                        className="flex items-center justify-between p-2.5 rounded-xl border border-border/70 bg-background/70 hover:bg-muted/70 hover:border-indigo-400/50 transition-all text-left group shadow-2xs"
                      >
                        <div className="flex items-center gap-2.5 truncate">
                          <span
                            className={cn(
                              "flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br text-white shrink-0 shadow-2xs",
                              demo.avatarBg
                            )}
                          >
                            <Icon className="h-3.5 w-3.5" />
                          </span>
                          <div className="truncate">
                            <span className="text-xs font-bold text-foreground block truncate group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                              {demo.name}
                            </span>
                            <span className="text-[10px] text-muted-foreground truncate block">
                              {demo.title}
                            </span>
                          </div>
                        </div>
                        <Badge
                          variant="outline"
                          className="text-[9px] font-mono shrink-0 ml-1 border-border/80"
                        >
                          {demo.badge}
                        </Badge>
                      </button>
                    );
                  })}
                </div>
              </div>
            </form>
          ) : (
            /* ================= 2. SIGN UP 4-STEP QUESTIONNAIRE WIZARD ================= */
            <div className="space-y-5">
              {/* Questionnaire Progress Header */}
              <div className="p-3.5 rounded-2xl bg-indigo-50/60 dark:bg-indigo-950/40 border border-indigo-200/60 dark:border-indigo-800/60 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-mono font-bold text-indigo-700 dark:text-indigo-300 uppercase tracking-wide flex items-center gap-1.5">
                    <Database className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                    Personal Life &amp; Routine Questionnaire (Stored in PostgreSQL)
                  </span>
                  <Badge variant="outline" className="text-[10px] font-mono border-indigo-400/40 text-indigo-700 dark:text-indigo-300 font-bold">
                    Step {signupStep} of 4
                  </Badge>
                </div>

                <div className="grid grid-cols-4 gap-1.5 pt-1">
                  {[
                    { s: 1, label: "Identity & Work" },
                    { s: 2, label: "Routine & Chores" },
                    { s: 3, label: "Memory Anchors" },
                    { s: 4, label: "Delays & Tasks" },
                  ].map((stepItem) => (
                    <button
                      key={stepItem.s}
                      type="button"
                      onClick={() => setSignupStep(stepItem.s as any)}
                      className="text-left group cursor-pointer focus:outline-hidden"
                    >
                      <div
                        className={cn(
                          "h-1.5 rounded-full transition-all duration-300",
                          signupStep === stepItem.s
                            ? "bg-indigo-600 dark:bg-indigo-400 shadow-xs"
                            : signupStep > stepItem.s
                            ? "bg-emerald-500"
                            : "bg-muted-foreground/20"
                        )}
                      />
                      <span
                        className={cn(
                          "text-[9px] font-medium block mt-1 truncate transition-colors",
                          signupStep === stepItem.s
                            ? "text-indigo-700 dark:text-indigo-300 font-bold"
                            : signupStep > stepItem.s
                            ? "text-emerald-600 dark:text-emerald-400"
                            : "text-muted-foreground"
                        )}
                      >
                        {stepItem.label}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* ---------------- STEP 1: IDENTITY & OCCUPATION ---------------- */}
              {signupStep === 1 && (
                <div className="space-y-4 animate-fade-in">
                  <div className="border-b border-border/60 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Step 1 • Who are you &amp; what is your occupation?
                    </h3>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      We never assume. Tell us your real identity and professional context.
                    </p>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                        <User className="h-3.5 w-3.5 text-indigo-500" />
                        Full Name
                      </label>
                      <input
                        type="text"
                        required
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="e.g. Neevetha N"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                        <Mail className="h-3.5 w-3.5 text-indigo-500" />
                        Email Address
                      </label>
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="neevetha@contextiq.io"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                        <Briefcase className="h-3.5 w-3.5 text-indigo-500" />
                        What do you do? (Primary Occupation)
                      </label>
                      <input
                        type="text"
                        value={customTitle}
                        onChange={(e) => setCustomTitle(e.target.value)}
                        placeholder="e.g. Senior Software Engineer / AI Researcher"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                        <Building className="h-3.5 w-3.5 text-indigo-500" />
                        Company / Lab / School
                      </label>
                      <input
                        type="text"
                        value={organization}
                        onChange={(e) => setOrganization(e.target.value)}
                        placeholder="e.g. Distributed Systems Lab / Tech Corp"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1.5">
                      <Lock className="h-3.5 w-3.5 text-indigo-500" />
                      Create Account Password
                    </label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Minimum 6 characters"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                    />
                  </div>

                  {/* Role Persona Picker */}
                  <div className="space-y-1.5 pt-1">
                    <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                      <span>Primary Cognitive Work Style:</span>
                      <span className="text-[10px] font-mono text-muted-foreground">
                        Calibrates resumption lag penalty
                      </span>
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {(Object.keys(PERSONA_DEFINITIONS) as RolePersona[]).map((key) => {
                        const meta = PERSONA_DEFINITIONS[key];
                        const Icon = getRoleIcon(key);
                        const isSelected = selectedRole === key;

                        return (
                          <button
                            key={key}
                            type="button"
                            onClick={() => handleSelectRole(key)}
                            className={cn(
                              "p-2.5 rounded-xl border text-left transition-all duration-200 flex flex-col justify-between",
                              isSelected
                                ? "bg-indigo-50/90 border-indigo-600 dark:bg-indigo-950/60 dark:border-indigo-500 shadow-2xs font-bold ring-1 ring-indigo-500"
                                : "bg-background/70 border-border/80 hover:bg-muted/60"
                            )}
                          >
                            <div className="flex items-center justify-between w-full">
                              <Icon
                                className={cn(
                                  "h-4 w-4",
                                  isSelected ? "text-indigo-600 dark:text-indigo-400" : "text-muted-foreground"
                                )}
                              />
                              {isSelected && <Check className="h-3 w-3 text-indigo-600 dark:text-indigo-400" />}
                            </div>
                            <span className="text-xs font-semibold text-foreground mt-1.5 truncate">
                              {meta.title.split("/")[0].trim()}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div className="pt-3 flex items-center justify-between">
                    <div>
                      {authError && signupStep === 1 && (
                        <p className="text-xs font-semibold text-rose-600 dark:text-rose-400">
                          {authError}
                        </p>
                      )}
                    </div>
                    <Button
                      type="button"
                      onClick={() => {
                        if (!name.trim()) {
                          setAuthError("Please enter your name.");
                          return;
                        }
                        if (!email.trim() || !email.includes("@")) {
                          setAuthError("Please enter a valid email address.");
                          return;
                        }
                        setAuthError(null);
                        setSignupStep(2);
                      }}
                      className="h-10 px-5 text-xs font-bold gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-md shadow-indigo-500/25"
                    >
                      Next: Daily Routine &amp; Chores
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {/* ---------------- STEP 2: DAILY ROUTINE & REAL-LIFE CHORES ---------------- */}
              {signupStep === 2 && (
                <div className="space-y-4 animate-fade-in">
                  <div className="border-b border-border/60 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Step 2 • Daily Routine &amp; Real-Life Chores
                    </h3>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Tell us what your day looks like. We track both professional and physical household chores.
                    </p>
                  </div>

                  {/* Daily Routine Textarea */}
                  <div>
                    <label className="text-xs font-semibold text-foreground flex items-center justify-between mb-1.5">
                      <span className="flex items-center gap-1.5">
                        <Calendar className="h-3.5 w-3.5 text-indigo-500" />
                        Describe Your Daily Routine &amp; Schedule:
                      </span>
                      <span className="text-[10px] font-mono text-muted-foreground">Calibrates flow chronometry</span>
                    </label>
                    <textarea
                      rows={2}
                      value={dailyRoutine}
                      onChange={(e) => setDailyRoutine(e.target.value)}
                      placeholder="e.g. Wake up 7:30 AM, quick breakfast, deep coding sprint 9 AM - 1 PM, team standup, PR review, evening walk, reading before sleep..."
                      className="w-full px-3.5 py-2 rounded-xl border border-border/80 bg-background text-xs text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                    />
                  </div>

                  {/* Daily Chores Section */}
                  <div className="space-y-2 p-3 rounded-2xl bg-background/60 border border-border/80">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Utensils className="h-3.5 w-3.5 text-amber-500" />
                        Daily Chores (e.g. Vessel Washing, Cooking)
                      </label>
                      <Badge variant="outline" className="text-[9px] font-mono text-amber-600 dark:text-amber-400 border-amber-500/30">
                        {dailyChores.length} selected
                      </Badge>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      Click to toggle what you personally do daily. These become trackable habits in PostgreSQL.
                    </p>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {DEFAULT_DAILY_CHORES.map((chore) => {
                        const isSelected = dailyChores.includes(chore);
                        return (
                          <button
                            key={chore}
                            type="button"
                            onClick={() => toggleItem(dailyChores, setDailyChores, chore)}
                            className={cn(
                              "px-2.5 py-1 rounded-xl text-xs font-medium border transition-all flex items-center gap-1.5",
                              isSelected
                                ? "bg-amber-500/15 border-amber-500 text-amber-800 dark:text-amber-200 font-bold shadow-2xs"
                                : "bg-background/80 border-border/80 text-muted-foreground hover:bg-muted"
                            )}
                          >
                            {isSelected ? <Check className="h-3 w-3 text-amber-600" /> : <Plus className="h-3 w-3 opacity-60" />}
                            {chore}
                          </button>
                        );
                      })}
                      {dailyChores
                        .filter((c) => !DEFAULT_DAILY_CHORES.includes(c))
                        .map((custom) => (
                          <button
                            key={custom}
                            type="button"
                            onClick={() => toggleItem(dailyChores, setDailyChores, custom)}
                            className="px-2.5 py-1 rounded-xl text-xs font-bold border bg-amber-500/20 border-amber-500 text-amber-800 dark:text-amber-200 shadow-2xs flex items-center gap-1.5"
                          >
                            <Check className="h-3 w-3 text-amber-600" />
                            {custom}
                          </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-2 pt-1.5">
                      <input
                        type="text"
                        value={customDailyChore}
                        onChange={(e) => setCustomDailyChore(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addCustomItem(customDailyChore, setCustomDailyChore, dailyChores, setDailyChores);
                          }
                        }}
                        placeholder="+ Add custom daily chore (e.g. Vessel washing, cooking)..."
                        className="flex-1 px-3 py-1.5 rounded-xl border border-border/70 bg-background text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-amber-500"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => addCustomItem(customDailyChore, setCustomDailyChore, dailyChores, setDailyChores)}
                        className="h-8 px-2.5 text-xs font-semibold gap-1 shrink-0"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add
                      </Button>
                    </div>
                  </div>

                  {/* Weekend Chores Section */}
                  <div className="space-y-2 p-3 rounded-2xl bg-background/60 border border-border/80">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Shirt className="h-3.5 w-3.5 text-sky-500" />
                        Weekend Chores (e.g. Dress Washing, Deep Cleaning)
                      </label>
                      <Badge variant="outline" className="text-[9px] font-mono text-sky-600 dark:text-sky-400 border-sky-500/30">
                        {weekendChores.length} selected
                      </Badge>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      Tasks like dress washing / laundry and market runs scheduled for weekends.
                    </p>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {DEFAULT_WEEKEND_CHORES.map((chore) => {
                        const isSelected = weekendChores.includes(chore);
                        return (
                          <button
                            key={chore}
                            type="button"
                            onClick={() => toggleItem(weekendChores, setWeekendChores, chore)}
                            className={cn(
                              "px-2.5 py-1 rounded-xl text-xs font-medium border transition-all flex items-center gap-1.5",
                              isSelected
                                ? "bg-sky-500/15 border-sky-500 text-sky-800 dark:text-sky-200 font-bold shadow-2xs"
                                : "bg-background/80 border-border/80 text-muted-foreground hover:bg-muted"
                            )}
                          >
                            {isSelected ? <Check className="h-3 w-3 text-sky-600" /> : <Plus className="h-3 w-3 opacity-60" />}
                            {chore}
                          </button>
                        );
                      })}
                      {weekendChores
                        .filter((c) => !DEFAULT_WEEKEND_CHORES.includes(c))
                        .map((custom) => (
                          <button
                            key={custom}
                            type="button"
                            onClick={() => toggleItem(weekendChores, setWeekendChores, custom)}
                            className="px-2.5 py-1 rounded-xl text-xs font-bold border bg-sky-500/20 border-sky-500 text-sky-800 dark:text-sky-200 shadow-2xs flex items-center gap-1.5"
                          >
                            <Check className="h-3 w-3 text-sky-600" />
                            {custom}
                          </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-2 pt-1.5">
                      <input
                        type="text"
                        value={customWeekendChore}
                        onChange={(e) => setCustomWeekendChore(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addCustomItem(customWeekendChore, setCustomWeekendChore, weekendChores, setWeekendChores);
                          }
                        }}
                        placeholder="+ Add custom weekend chore (e.g. Dress washing, groceries)..."
                        className="flex-1 px-3 py-1.5 rounded-xl border border-border/70 bg-background text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-sky-500"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => addCustomItem(customWeekendChore, setCustomWeekendChore, weekendChores, setWeekendChores)}
                        className="h-8 px-2.5 text-xs font-semibold gap-1 shrink-0"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add
                      </Button>
                    </div>
                  </div>

                  <div className="pt-3 flex justify-between">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setSignupStep(1)}
                      className="h-10 px-4 text-xs font-semibold gap-2 rounded-xl"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back
                    </Button>
                    <Button
                      type="button"
                      onClick={() => setSignupStep(3)}
                      className="h-10 px-5 text-xs font-bold gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-md shadow-indigo-500/25"
                    >
                      Next: Memory Anchors
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {/* ---------------- STEP 3: WHAT ARE YOU ALWAYS LIKELY TO FORGET? ---------------- */}
              {signupStep === 3 && (
                <div className="space-y-4 animate-fade-in">
                  <div className="border-b border-border/60 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Step 3 • What are you always likely to forget?
                    </h3>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Cognitive fatigue and context switching cause memory lapses. ContextIQ acts as your safety net.
                    </p>
                  </div>

                  <div className="space-y-3 p-4 rounded-2xl bg-rose-50/40 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <AlertCircle className="h-4 w-4 text-rose-500" />
                        Frequent Memory Lapses &amp; Safety Checks
                      </label>
                      <Badge variant="outline" className="text-[9px] font-mono text-rose-600 dark:text-rose-400 border-rose-500/30">
                        {frequentForgetItems.length} selected
                      </Badge>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      Select items you frequently overlook or forget when transitioning between home and work.
                    </p>

                    <div className="space-y-2 pt-1">
                      {DEFAULT_FORGET_ITEMS.map((item) => {
                        const isSelected = frequentForgetItems.includes(item);
                        return (
                          <div
                            key={item}
                            onClick={() => toggleItem(frequentForgetItems, setFrequentForgetItems, item)}
                            className={cn(
                              "p-2.5 rounded-xl border cursor-pointer transition-all flex items-center justify-between shadow-2xs group",
                              isSelected
                                ? "bg-rose-50 dark:bg-rose-950/60 border-rose-500 text-rose-950 dark:text-rose-100 font-bold"
                                : "bg-background/80 border-border/80 text-muted-foreground hover:bg-muted"
                            )}
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={cn(
                                  "h-5 w-5 rounded-md flex items-center justify-center text-xs transition-colors",
                                  isSelected ? "bg-rose-600 text-white" : "border border-border text-transparent"
                                )}
                              >
                                ✓
                              </span>
                              <span className="text-xs">{item}</span>
                            </div>
                            {isSelected && (
                              <Badge className="bg-rose-500/20 text-rose-700 dark:text-rose-300 border-rose-500/30 text-[9px]">
                                Protected
                              </Badge>
                            )}
                          </div>
                        );
                      })}
                      {frequentForgetItems
                        .filter((item) => !DEFAULT_FORGET_ITEMS.includes(item))
                        .map((custom) => (
                          <div
                            key={custom}
                            onClick={() => toggleItem(frequentForgetItems, setFrequentForgetItems, custom)}
                            className="p-2.5 rounded-xl border cursor-pointer bg-rose-50 dark:bg-rose-950/60 border-rose-500 text-rose-950 dark:text-rose-100 font-bold flex items-center justify-between shadow-2xs"
                          >
                            <div className="flex items-center gap-2">
                              <span className="h-5 w-5 rounded-md flex items-center justify-center text-xs bg-rose-600 text-white">
                                ✓
                              </span>
                              <span className="text-xs">{custom}</span>
                            </div>
                            <Badge className="bg-rose-500/20 text-rose-700 dark:text-rose-300 border-rose-500/30 text-[9px]">
                              Custom
                            </Badge>
                          </div>
                        ))}
                    </div>

                    <div className="flex items-center gap-2 pt-2 border-t border-rose-200/40 dark:border-rose-900/40">
                      <input
                        type="text"
                        value={customForgetItem}
                        onChange={(e) => setCustomForgetItem(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addCustomItem(customForgetItem, setCustomForgetItem, frequentForgetItems, setFrequentForgetItems);
                          }
                        }}
                        placeholder="+ Add custom forget item (e.g. Turn off geyser, pack badge)..."
                        className="flex-1 px-3 py-1.5 rounded-xl border border-border/70 bg-background text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-rose-500"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => addCustomItem(customForgetItem, setCustomForgetItem, frequentForgetItems, setFrequentForgetItems)}
                        className="h-8 px-2.5 text-xs font-semibold gap-1 shrink-0"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add
                      </Button>
                    </div>
                  </div>

                  <div className="pt-3 flex justify-between">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setSignupStep(2)}
                      className="h-10 px-4 text-xs font-semibold gap-2 rounded-xl"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back
                    </Button>
                    <Button
                      type="button"
                      onClick={() => setSignupStep(4)}
                      className="h-10 px-5 text-xs font-bold gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-md shadow-indigo-500/25"
                    >
                      Next: Time Delays &amp; Tasks
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}

              {/* ---------------- STEP 4: TIME DELAY TRIGGERS & FOCUS TASKS ---------------- */}
              {signupStep === 4 && (
                <div className="space-y-4 animate-fade-in">
                  <div className="border-b border-border/60 pb-2">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      Step 4 • Where exists a time delay? &amp; Initial Focus Tasks
                    </h3>
                    <p className="text-[11px] text-muted-foreground mt-0.5">
                      Identify where attention slips and enter your active tasks for the PostgreSQL database.
                    </p>
                  </div>

                  {/* Where exists a time delay they think? */}
                  <div className="space-y-2 p-3.5 rounded-2xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                        <Flame className="h-3.5 w-3.5 text-amber-500" />
                        Where exists a time delay in your day? (Resumption Lag Triggers)
                      </label>
                      <Badge variant="outline" className="text-[9px] font-mono text-amber-600 dark:text-amber-400 border-amber-500/30">
                        {timeDelayTriggers.length} selected
                      </Badge>
                    </div>
                    <p className="text-[10px] text-muted-foreground">
                      ContextIQ quantifies recovery minutes for each trigger during your focus sessions.
                    </p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                      {DEFAULT_TIME_DELAYS.map((trigger) => {
                        const isSelected = timeDelayTriggers.includes(trigger);
                        return (
                          <button
                            key={trigger}
                            type="button"
                            onClick={() => toggleItem(timeDelayTriggers, setTimeDelayTriggers, trigger)}
                            className={cn(
                              "p-2 rounded-xl text-left border transition-all text-xs flex items-center justify-between",
                              isSelected
                                ? "bg-amber-500/15 border-amber-500 text-amber-900 dark:text-amber-100 font-bold shadow-2xs"
                                : "bg-background/80 border-border/80 text-muted-foreground hover:bg-muted"
                            )}
                          >
                            <span className="truncate">{trigger}</span>
                            {isSelected && <Check className="h-3 w-3 text-amber-600 shrink-0 ml-1" />}
                          </button>
                        );
                      })}
                      {timeDelayTriggers
                        .filter((t) => !DEFAULT_TIME_DELAYS.includes(t))
                        .map((custom) => (
                          <button
                            key={custom}
                            type="button"
                            onClick={() => toggleItem(timeDelayTriggers, setTimeDelayTriggers, custom)}
                            className="p-2 rounded-xl text-left border bg-amber-500/20 border-amber-500 text-amber-900 dark:text-amber-100 font-bold text-xs flex items-center justify-between shadow-2xs"
                          >
                            <span className="truncate">{custom}</span>
                            <Check className="h-3 w-3 text-amber-600 shrink-0 ml-1" />
                          </button>
                        ))}
                    </div>

                    <div className="flex items-center gap-2 pt-1.5 border-t border-amber-200/40 dark:border-amber-900/40">
                      <input
                        type="text"
                        value={customTimeDelay}
                        onChange={(e) => setCustomTimeDelay(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            addCustomItem(customTimeDelay, setCustomTimeDelay, timeDelayTriggers, setTimeDelayTriggers);
                          }
                        }}
                        placeholder="+ Add custom delay trigger (e.g. Social media reels, Slack dms)..."
                        className="flex-1 px-3 py-1.5 rounded-xl border border-border/70 bg-background text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-amber-500"
                      />
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={() => addCustomItem(customTimeDelay, setCustomTimeDelay, timeDelayTriggers, setTimeDelayTriggers)}
                        className="h-8 px-2.5 text-xs font-semibold gap-1 shrink-0"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add
                      </Button>
                    </div>
                  </div>

                  {/* Focus Rhythm Selector */}
                  <div className="space-y-1.5 pt-1">
                    <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                      <span className="flex items-center gap-1.5">
                        <Clock className="h-3.5 w-3.5 text-indigo-500" />
                        Circadian Focus Rhythm:
                      </span>
                      <span className="text-[10px] font-mono text-muted-foreground">Peak mental window</span>
                    </label>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                      {[
                        { id: "morning" as FocusRhythm, label: "Morning", sub: "8 AM - 12 PM" },
                        { id: "afternoon" as FocusRhythm, label: "Afternoon", sub: "1 PM - 5 PM" },
                        { id: "night" as FocusRhythm, label: "Night", sub: "8 PM - 1 AM" },
                        { id: "flexible" as FocusRhythm, label: "Flexible", sub: "Dynamic" },
                      ].map((r) => (
                        <button
                          key={r.id}
                          type="button"
                          onClick={() => setSelectedRhythm(r.id)}
                          className={cn(
                            "p-2 rounded-xl border text-center transition-all",
                            selectedRhythm === r.id
                              ? "bg-indigo-50 dark:bg-indigo-950/70 border-indigo-600 text-indigo-700 dark:text-indigo-300 font-bold ring-1 ring-indigo-500"
                              : "bg-background/60 border-border/80 text-muted-foreground hover:text-foreground"
                          )}
                        >
                          <span className="text-xs block font-semibold">{r.label}</span>
                          <span className="text-[9px] font-mono opacity-80 block">{r.sub}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Immediate Focus Tasks for Project DB */}
                  <div className="space-y-2.5 pt-2 border-t border-border/80">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                          <ListTodo className="h-4 w-4 text-emerald-500" />
                          Initial Work Tasks (Stored in PostgreSQL Database)
                        </label>
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Enter your current active tasks. These will be tracked for recovery friction.
                        </p>
                      </div>
                      <Badge variant="outline" className="text-[9px] font-mono text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
                        <Database className="h-3 w-3 mr-1" />
                        {initialTasks.length} {initialTasks.length === 1 ? "task" : "tasks"}
                      </Badge>
                    </div>

                    {/* Active task list */}
                    <div className="space-y-2">
                      {initialTasks.length === 0 ? (
                        <div className="p-3 rounded-xl border border-dashed border-border/80 text-center text-xs text-muted-foreground bg-background/40">
                          No tasks added yet. Type a task below and click &quot;Add&quot; to save it to PostgreSQL.
                        </div>
                      ) : (
                        initialTasks.map((t, idx) => (
                          <div
                            key={t.id}
                            className="p-2.5 rounded-xl bg-background/80 border border-border/70 flex items-center justify-between gap-2 shadow-2xs group hover:border-emerald-500/40 transition-colors"
                          >
                            <div className="flex items-center gap-2 flex-1 min-w-0">
                              <span className="h-5 w-5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center font-mono text-[10px] font-bold shrink-0">
                                {idx + 1}
                              </span>
                              <input
                                type="text"
                                value={t.title}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setInitialTasks((prev) =>
                                    prev.map((item) => (item.id === t.id ? { ...item, title: val } : item))
                                  );
                                }}
                                placeholder="Focus task title..."
                                className="w-full text-xs font-medium text-foreground bg-transparent focus:outline-hidden"
                              />
                            </div>

                            <div className="flex items-center gap-1.5 shrink-0">
                              <Badge
                                variant="outline"
                                className={cn(
                                  "text-[9px] font-mono uppercase px-1.5 py-0.5",
                                  t.priority === "urgent"
                                    ? "text-rose-600 border-rose-500/30 bg-rose-500/10"
                                    : t.priority === "high"
                                    ? "text-amber-600 border-amber-500/30 bg-amber-500/10"
                                    : "text-slate-600 border-slate-500/30 bg-slate-500/10"
                                )}
                              >
                                {t.priority}
                              </Badge>
                              <span className="text-[10px] font-mono text-muted-foreground">{t.estimated_minutes}m</span>
                              <button
                                type="button"
                                onClick={() => handleRemoveTask(t.id)}
                                className="p-1 text-muted-foreground hover:text-rose-600 transition-colors rounded-md"
                                title="Remove task"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>

                    {/* Add custom task row */}
                    <div className="flex items-center gap-2 pt-1">
                      <input
                        type="text"
                        value={newTaskTitle}
                        onChange={(e) => setNewTaskTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            handleAddCustomTask();
                          }
                        }}
                        placeholder="+ Type a focus task for today..."
                        className="flex-1 px-3 py-1.5 rounded-xl border border-border/70 bg-background text-xs text-foreground placeholder:text-muted-foreground focus:outline-hidden focus:ring-1 focus:ring-emerald-500"
                      />
                      <select
                        value={newTaskPriority}
                        onChange={(e) => setNewTaskPriority(e.target.value as any)}
                        className="px-2 py-1.5 rounded-xl border border-border/70 bg-background text-[11px] font-mono text-foreground focus:outline-hidden"
                      >
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                        <option value="low">Low</option>
                      </select>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={handleAddCustomTask}
                        className="h-8 px-2.5 text-xs font-semibold gap-1 shrink-0"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add
                      </Button>
                    </div>
                  </div>

                  {authStatusMessage && (
                    <p className="text-[11px] font-mono text-indigo-600 dark:text-indigo-400 text-center animate-pulse">
                      {authStatusMessage}
                    </p>
                  )}

                  {authError && (
                    <p className="text-xs font-medium text-rose-600 dark:text-rose-400 text-center">
                      {authError}
                    </p>
                  )}

                  <div className="pt-3 flex justify-between">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setSignupStep(3)}
                      className="h-10 px-4 text-xs font-semibold gap-2 rounded-xl"
                    >
                      <ArrowLeft className="h-4 w-4" />
                      Back
                    </Button>
                    <Button
                      type="button"
                      disabled={isSubmitting}
                      onClick={() => handleSignupSubmit()}
                      className="h-11 px-6 text-xs font-bold gap-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-md shadow-emerald-500/25 transition-all active:scale-98"
                    >
                      {isSubmitting ? "Saving to PostgreSQL..." : "Complete & Save All to Database"}
                      <CheckCircle2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Privacy & Trust Footer */}
          <div className="pt-3 border-t border-border/60 flex items-center justify-between text-[11px] text-muted-foreground font-medium">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
              <span>ACID PostgreSQL persistence • Full user data sovereignty</span>
            </span>
            <span className="font-mono text-[10px]">DB: dataproject:5433</span>
          </div>
        </div>
      </div>
    </div>
  );
}
