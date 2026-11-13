"use client";

import React, { useState, useEffect } from "react";
import {
  Laptop,
  GraduationCap,
  Briefcase,
  Brain,
  Sparkles,
  Check,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  Zap,
  Globe,
  Clock,
  X,
  User,
  Target,
  Utensils,
  Shirt,
  AlertCircle,
  Calendar,
  Flame,
  Plus,
  Trash2,
  CheckCircle2,
  Database,
} from "lucide-react";
import {
  useUserProfile,
  PERSONA_DEFINITIONS,
  AVAILABLE_LANGUAGES,
} from "@/context/user-profile-context";
import type { RolePersona, LanguageCode, DistractionType, FocusRhythm } from "@/types/profile";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const DISTRACTION_OPTIONS: { id: DistractionType; label: string; icon: string; impact: string }[] = [
  { id: "phone", label: "Phone Pings & Socials", icon: "📱", impact: "+4.2m avg lag" },
  { id: "slack", label: "Slack, Teams & Work DMs", icon: "💬", impact: "+6.8m avg lag" },
  { id: "meetings", label: "Meeting-Hopping Spillover", icon: "📅", impact: "+8.5m avg lag" },
  { id: "in_person", label: "In-Person Taps & Noise", icon: "👥", impact: "+5.4m avg lag" },
  { id: "tab_overload", label: "Browser Tab Rabbit Holes", icon: "🌐", impact: "+7.1m avg lag" },
  { id: "noise", label: "Environmental Disruptions", icon: "🎧", impact: "+3.9m avg lag" },
];

const FOCUS_RHYTHMS: { id: FocusRhythm; title: string; window: string; icon: string }[] = [
  { id: "morning", title: "Morning Deep Focus", window: "8:00 AM – 12:00 PM", icon: "🌅" },
  { id: "afternoon", title: "Afternoon Steady", window: "1:00 PM – 5:00 PM", icon: "☀️" },
  { id: "night", title: "Night Hacker Mode", window: "8:00 PM – 1:00 AM", icon: "🌙" },
  { id: "flexible", title: "Dynamic / Flexible", window: "Adaptive throughout day", icon: "⚡" },
];

const GOAL_OPTIONS = [60, 90, 120, 180, 240];

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

export function CognitiveOnboardingDialog() {
  const {
    profile,
    updateProfile,
    saveProfileToDb,
    personaMeta,
    isOnboardingOpen,
    closeOnboarding,
    t,
  } = useUserProfile();

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);

  // Step 1: Identity & Occupation
  const [name, setName] = useState<string>(profile.name || "");
  const [customTitle, setCustomTitle] = useState<string>(profile.customTitle || "");
  const [selectedRole, setSelectedRole] = useState<RolePersona>(profile.role || "developer");

  // Step 2: Routine & Chores
  const [dailyRoutine, setDailyRoutine] = useState<string>(profile.dailyRoutine || "");
  const [dailyChores, setDailyChores] = useState<string[]>(profile.dailyChores || []);
  const [customDailyChore, setCustomDailyChore] = useState("");
  const [weekendChores, setWeekendChores] = useState<string[]>(profile.weekendChores || []);
  const [customWeekendChore, setCustomWeekendChore] = useState("");

  // Step 3: Forget Anchors & Distractions
  const [frequentForgetItems, setFrequentForgetItems] = useState<string[]>(
    profile.frequentForgetItems || []
  );
  const [customForgetItem, setCustomForgetItem] = useState("");
  const [selectedDistractions, setSelectedDistractions] = useState<DistractionType[]>(
    profile.distractions || ["phone", "slack", "tab_overload"]
  );

  // Step 4: Delay Triggers, Language, Rhythm & Goal
  const [timeDelayTriggers, setTimeDelayTriggers] = useState<string[]>(
    profile.timeDelayTriggers || []
  );
  const [customTimeDelay, setCustomTimeDelay] = useState("");
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>(profile.language || "en");
  const [selectedRhythm, setSelectedRhythm] = useState<FocusRhythm>(profile.focusRhythm || "morning");
  const [dailyGoal, setDailyGoal] = useState<number>(profile.dailyGoalMinutes || 120);

  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Hydrate states when dialog opens with latest profile values
  useEffect(() => {
    if (isOnboardingOpen) {
      setName(profile.name || "");
      setCustomTitle(profile.customTitle || "");
      setSelectedRole(profile.role || "developer");
      setDailyRoutine(profile.dailyRoutine || "");
      setDailyChores(profile.dailyChores || []);
      setWeekendChores(profile.weekendChores || []);
      setFrequentForgetItems(profile.frequentForgetItems || []);
      setSelectedDistractions(profile.distractions || ["phone", "slack", "tab_overload"]);
      setTimeDelayTriggers(profile.timeDelayTriggers || []);
      setSelectedLanguage(profile.language || "en");
      setSelectedRhythm(profile.focusRhythm || "morning");
      setDailyGoal(profile.dailyGoalMinutes || 120);
      setSaveSuccess(false);
    }
  }, [isOnboardingOpen, profile]);

  if (!isOnboardingOpen) return null;

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

  const toggleDistraction = (id: DistractionType) => {
    setSelectedDistractions((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const handleFinish = async () => {
    setIsSaving(true);
    const updated = {
      name: name.trim() || profile.name || "User",
      customTitle: customTitle.trim() || PERSONA_DEFINITIONS[selectedRole]?.title.split("/")[0].trim(),
      role: selectedRole,
      language: selectedLanguage,
      distractions: selectedDistractions,
      focusRhythm: selectedRhythm,
      dailyGoalMinutes: dailyGoal,
      dailyRoutine: dailyRoutine.trim(),
      dailyChores,
      weekendChores,
      frequentForgetItems,
      timeDelayTriggers,
      primaryOccupation: customTitle.trim() || PERSONA_DEFINITIONS[selectedRole]?.title.split("/")[0].trim(),
      onboardingCompleted: true,
    };

    try {
      await saveProfileToDb(updated);
      setSaveSuccess(true);
      setTimeout(() => {
        closeOnboarding();
      }, 900);
    } catch {
      updateProfile(updated);
      closeOnboarding();
    } finally {
      setIsSaving(false);
    }
  };

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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-xl animate-fade-in">
      <div className="relative w-full max-w-2xl rounded-3xl glass-card border border-border/80 shadow-[0_20px_60px_-15px_rgba(15,23,42,0.18)] dark:shadow-[0_20px_60px_-15px_rgba(0,0,0,0.6)] overflow-hidden">
        {/* Top Iridescent Ambient Accent */}
        <div className="absolute inset-x-0 top-0 h-[4px] bg-gradient-to-r from-indigo-500 via-sky-400 to-amber-400" />

        {/* Close Button */}
        <button
          onClick={closeOnboarding}
          className="absolute top-4 right-4 p-2 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/70 transition-colors"
          aria-label="Close setup"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Header & Step Tracker */}
        <div className="p-6 pb-4 border-b border-border/60">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-sm shadow-indigo-500/25">
                <Brain className="h-4.5 w-4.5" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-foreground tracking-tight">
                    Personalized Routine &amp; Cognitive Setup
                  </h2>
                  <Badge variant="outline" className="text-[10px] font-mono border-indigo-400/40 text-indigo-700 dark:text-indigo-300 font-bold">
                    PostgreSQL ACID Sync
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Update your daily life routine, chores, forget anchors, and friction triggers.
                </p>
              </div>
            </div>

            {/* Stepper Dots */}
            <div className="flex items-center gap-1.5 font-mono text-xs">
              {[1, 2, 3, 4].map((num) => (
                <button
                  key={num}
                  type="button"
                  onClick={() => setStep(num as any)}
                  className={cn(
                    "h-2 rounded-full transition-all duration-300 cursor-pointer",
                    step === num
                      ? "w-6 bg-indigo-600 dark:bg-indigo-400"
                      : step > num
                      ? "w-2.5 bg-emerald-500"
                      : "w-2 bg-muted-foreground/30 hover:bg-muted-foreground/50"
                  )}
                  title={`Go to Step ${num}`}
                />
              ))}
            </div>
          </div>

          {/* Step Labels Bar */}
          <div className="grid grid-cols-4 gap-2 pt-3 text-[11px] font-semibold text-center border-t border-border/50 mt-3">
            {[
              { s: 1, label: "1. Work & Identity" },
              { s: 2, label: "2. Routine & Chores" },
              { s: 3, label: "3. Forget Anchors" },
              { s: 4, label: "4. Delays & Goals" },
            ].map((st) => (
              <button
                key={st.s}
                type="button"
                onClick={() => setStep(st.s as any)}
                className={cn(
                  "py-1 rounded-lg transition-colors truncate",
                  step === st.s
                    ? "text-indigo-600 dark:text-indigo-400 font-bold bg-indigo-50 dark:bg-indigo-950/50"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {st.label}
              </button>
            ))}
          </div>
        </div>

        {/* Body Content by Step */}
        <div className="p-6 space-y-5 max-h-[65vh] overflow-y-auto">
          {/* ================= STEP 1: IDENTITY & ROLE PERSONA ================= */}
          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-indigo-600 dark:text-indigo-400 border-indigo-500/30">
                  Step 1 • Identity &amp; Cognitive Work Style
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  Who are you and what do you do?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Calibrates the baseline resumption cost penalty and focus chronometer.
                </p>
              </div>

              {/* Name & Title Inputs */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3.5 rounded-2xl bg-muted/40 border border-border/70">
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 mb-1">
                    <User className="h-3 w-3 text-indigo-500" />
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Neevetha N"
                    className="w-full px-3 py-1.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 mb-1">
                    <Briefcase className="h-3 w-3 text-indigo-500" />
                    What do you do? (Title)
                  </label>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    placeholder="e.g. Senior Software Engineer"
                    className="w-full px-3 py-1.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>
              </div>

              {/* Persona Selection */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {(Object.keys(PERSONA_DEFINITIONS) as RolePersona[]).map((key) => {
                  const meta = PERSONA_DEFINITIONS[key];
                  const Icon = getPersonaIcon(key);
                  const isSelected = selectedRole === key;

                  return (
                    <button
                      key={key}
                      type="button"
                      onClick={() => {
                        setSelectedRole(key);
                        if (!customTitle) {
                          setCustomTitle(meta.title.split("/")[0].trim());
                        }
                      }}
                      className={cn(
                        "p-3 rounded-2xl border text-left transition-all duration-200 relative group flex flex-col justify-between",
                        isSelected
                          ? "bg-indigo-50/90 border-indigo-600 dark:bg-indigo-950/60 dark:border-indigo-500 shadow-sm ring-1 ring-indigo-500"
                          : "bg-background/70 border-border/80 hover:bg-muted/50 hover:border-indigo-400/40"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2.5">
                          <span
                            className={cn(
                              "flex h-7 w-7 items-center justify-center rounded-xl border transition-colors",
                              isSelected
                                ? "bg-indigo-600 text-white border-indigo-700"
                                : "bg-muted text-muted-foreground border-border/80 group-hover:text-indigo-600"
                            )}
                          >
                            <Icon className="h-3.5 w-3.5" />
                          </span>
                          <div>
                            <span className="text-xs font-bold text-foreground block">
                              {meta.title}
                            </span>
                          </div>
                        </div>
                        {isSelected && (
                          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-indigo-600 text-white text-[10px]">
                            ✓
                          </span>
                        )}
                      </div>

                      <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">
                        {meta.tagline}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* ================= STEP 2: ROUTINE & REAL-LIFE CHORES ================= */}
          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-amber-600 dark:text-amber-400 border-amber-500/30">
                  Step 2 • Daily Routine &amp; Household Chores
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  What does your actual day look like?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  ContextIQ tracks physical routines alongside cognitive work blocks so nothing slips.
                </p>
              </div>

              {/* Daily Routine Textarea */}
              <div>
                <label className="text-xs font-semibold text-foreground flex items-center justify-between mb-1.5">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="h-3.5 w-3.5 text-indigo-500" />
                    Daily Routine &amp; Schedule Flow:
                  </span>
                  <span className="text-[10px] font-mono text-muted-foreground">Calibrates flow chronometry</span>
                </label>
                <textarea
                  rows={2}
                  value={dailyRoutine}
                  onChange={(e) => setDailyRoutine(e.target.value)}
                  placeholder="e.g. Wake up 7:30 AM, filter coffee, deep coding sprint 9 AM - 1 PM, team standup, PR review, evening walk..."
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
                    placeholder="+ Add custom daily chore..."
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
                    placeholder="+ Add custom weekend chore..."
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
            </div>
          )}

          {/* ================= STEP 3: FORGET ANCHORS & DISTRACTIONS ================= */}
          {step === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-rose-600 dark:text-rose-400 border-rose-500/30">
                  Step 3 • Anti-Forget Anchors &amp; Cognitive Safety
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  What are you always likely to forget?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  High-friction transitions cause memory lapses. ContextIQ acts as your safety net.
                </p>
              </div>

              {/* Frequent Forget Items */}
              <div className="space-y-2 p-3.5 rounded-2xl bg-rose-50/40 dark:bg-rose-950/20 border border-rose-200/60 dark:border-rose-900/40">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <AlertCircle className="h-3.5 w-3.5 text-rose-500" />
                    Frequent Memory Lapses &amp; Safety Checks
                  </label>
                  <Badge variant="outline" className="text-[9px] font-mono text-rose-600 dark:text-rose-400 border-rose-500/30">
                    {frequentForgetItems.length} selected
                  </Badge>
                </div>

                <div className="space-y-1.5 pt-1">
                  {DEFAULT_FORGET_ITEMS.map((item) => {
                    const isSelected = frequentForgetItems.includes(item);
                    return (
                      <div
                        key={item}
                        onClick={() => toggleItem(frequentForgetItems, setFrequentForgetItems, item)}
                        className={cn(
                          "p-2 rounded-xl border cursor-pointer transition-all flex items-center justify-between shadow-2xs group text-xs",
                          isSelected
                            ? "bg-rose-50 dark:bg-rose-950/60 border-rose-500 text-rose-950 dark:text-rose-100 font-bold"
                            : "bg-background/80 border-border/80 text-muted-foreground hover:bg-muted"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              "h-4 w-4 rounded-md flex items-center justify-center text-[10px] transition-colors",
                              isSelected ? "bg-rose-600 text-white" : "border border-border text-transparent"
                            )}
                          >
                            ✓
                          </span>
                          <span>{item}</span>
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
                        className="p-2 rounded-xl border cursor-pointer bg-rose-50 dark:bg-rose-950/60 border-rose-500 text-rose-950 dark:text-rose-100 font-bold flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          <span className="h-4 w-4 rounded-md flex items-center justify-center text-[10px] bg-rose-600 text-white">
                            ✓
                          </span>
                          <span>{custom}</span>
                        </div>
                        <Badge className="bg-rose-500/20 text-rose-700 dark:text-rose-300 border-rose-500/30 text-[9px]">
                          Custom
                        </Badge>
                      </div>
                    ))}
                </div>

                <div className="flex items-center gap-2 pt-1.5 border-t border-rose-200/40 dark:border-rose-900/40">
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
                    placeholder="+ Add custom forget item (e.g. Turn off stove, pack keys)..."
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

              {/* Distraction Selection */}
              <div className="space-y-2">
                <label className="text-xs font-bold text-foreground">
                  Primary Distractions (Weighted in Friction Score):
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {DISTRACTION_OPTIONS.map((opt) => {
                    const isChecked = selectedDistractions.includes(opt.id);
                    return (
                      <button
                        key={opt.id}
                        type="button"
                        onClick={() => toggleDistraction(opt.id)}
                        className={cn(
                          "p-2.5 rounded-xl border text-left transition-all duration-200 flex items-center justify-between text-xs",
                          isChecked
                            ? "bg-amber-50/80 border-amber-500 dark:bg-amber-950/40 dark:border-amber-600 shadow-2xs font-semibold"
                            : "bg-background/70 border-border/80 hover:bg-muted/50"
                        )}
                      >
                        <div className="flex items-center gap-2 truncate">
                          <span className="text-base">{opt.icon}</span>
                          <span className="truncate">{opt.label}</span>
                        </div>
                        {isChecked && <Check className="h-3.5 w-3.5 text-amber-600 shrink-0" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* ================= STEP 4: DELAYS, RHYTHMS & GOALS ================= */}
          {step === 4 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-emerald-600 dark:text-emerald-400 border-emerald-500/30">
                  Step 4 • Micro-Delays, Circadian Rhythm &amp; Target Goal
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  Where exists a time delay &amp; how do you operate?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Calibrate your daily focus target and resumption lag triggers.
                </p>
              </div>

              {/* Time Delay Triggers */}
              <div className="space-y-2 p-3 rounded-2xl bg-amber-50/40 dark:bg-amber-950/20 border border-amber-200/60 dark:border-amber-900/40">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-bold text-foreground flex items-center gap-1.5">
                    <Flame className="h-3.5 w-3.5 text-amber-500" />
                    Where exists a time delay in your day?
                  </label>
                  <Badge variant="outline" className="text-[9px] font-mono text-amber-600 dark:text-amber-400 border-amber-500/30">
                    {timeDelayTriggers.length} selected
                  </Badge>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
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
                    placeholder="+ Add custom delay trigger..."
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

              {/* Peak Focus Rhythm */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-indigo-500" />
                  Circadian Peak Focus Window:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {FOCUS_RHYTHMS.map((r) => {
                    const isRhythmSelected = selectedRhythm === r.id;
                    return (
                      <button
                        key={r.id}
                        type="button"
                        onClick={() => setSelectedRhythm(r.id)}
                        className={cn(
                          "p-2 rounded-xl border text-center transition-all text-xs",
                          isRhythmSelected
                            ? "bg-indigo-50 dark:bg-indigo-950/70 border-indigo-600 text-indigo-700 dark:text-indigo-300 font-bold ring-1 ring-indigo-500"
                            : "bg-background/60 border-border/80 text-muted-foreground hover:text-foreground"
                        )}
                      >
                        <span className="block font-semibold">{r.title.split(" ")[0]}</span>
                        <span className="text-[9px] font-mono opacity-80 block">{r.window.split("–")[0].trim()}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Daily Target Goal & Language */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="text-xs font-semibold text-foreground flex items-center justify-between mb-1">
                    <span className="flex items-center gap-1.5">
                      <Target className="h-3.5 w-3.5 text-emerald-500" />
                      Daily Target Goal:
                    </span>
                    <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                      {dailyGoal}m
                    </span>
                  </label>
                  <div className="flex items-center gap-1.5">
                    {GOAL_OPTIONS.map((mins) => (
                      <button
                        key={mins}
                        type="button"
                        onClick={() => setDailyGoal(mins)}
                        className={cn(
                          "flex-1 py-1 rounded-lg text-xs font-semibold border transition-all",
                          dailyGoal === mins
                            ? "bg-emerald-500 text-white border-emerald-600 shadow-2xs"
                            : "bg-background/70 border-border/80 hover:bg-muted text-muted-foreground"
                        )}
                      >
                        {mins}m
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-foreground flex items-center gap-1.5 mb-1">
                    <Globe className="h-3.5 w-3.5 text-indigo-500" />
                    Language:
                  </label>
                  <select
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value as any)}
                    className="w-full px-3 py-1.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden"
                  >
                    {AVAILABLE_LANGUAGES.map((l) => (
                      <option key={l.code} value={l.code}>
                        {l.flag} {l.nativeName} ({l.name})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-border/60 bg-muted/30 flex items-center justify-between">
          <div>
            {saveSuccess && (
              <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 animate-pulse">
                <CheckCircle2 className="h-4 w-4" />
                All inputs saved directly to PostgreSQL!
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {step > 1 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setStep((prev) => (prev - 1) as any)}
                className="h-9 px-3.5 gap-1.5 text-xs rounded-xl"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
                Back
              </Button>
            )}

            {step < 4 ? (
              <Button
                type="button"
                size="sm"
                onClick={() => setStep((prev) => (prev + 1) as any)}
                className="h-9 px-4 gap-1.5 text-xs font-bold rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white shadow-xs"
              >
                Next Step
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            ) : (
              <Button
                type="button"
                size="sm"
                disabled={isSaving}
                onClick={handleFinish}
                className="h-9 px-5 gap-1.5 text-xs font-bold rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm shadow-emerald-500/25"
              >
                {isSaving ? "Saving to PostgreSQL..." : "Save All to Database"}
                <CheckCircle2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
