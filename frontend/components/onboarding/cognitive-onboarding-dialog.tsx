"use client";

import React, { useState } from "react";
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
  Building,
  Target,
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
  { id: "in_person", label: "In-Person Taps & Office Noise", icon: "👥", impact: "+5.4m avg lag" },
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

export function CognitiveOnboardingDialog() {
  const {
    profile,
    updateProfile,
    personaMeta,
    isOnboardingOpen,
    closeOnboarding,
    t,
  } = useUserProfile();

  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [name, setName] = useState<string>(profile.name || "Neevetha");
  const [customTitle, setCustomTitle] = useState<string>(profile.customTitle || "Senior Software Engineer");
  const [organization, setOrganization] = useState<string>(profile.organization || "Distributed Systems Lab");
  const [selectedRole, setSelectedRole] = useState<RolePersona>(profile.role);
  const [selectedLanguage, setSelectedLanguage] = useState<LanguageCode>(profile.language);
  const [selectedDistractions, setSelectedDistractions] = useState<DistractionType[]>(
    profile.distractions
  );
  const [selectedRhythm, setSelectedRhythm] = useState<FocusRhythm>(profile.focusRhythm);
  const [dailyGoal, setDailyGoal] = useState<number>(profile.dailyGoalMinutes || 120);

  if (!isOnboardingOpen) return null;

  const toggleDistraction = (id: DistractionType) => {
    setSelectedDistractions((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const handleFinish = () => {
    const updated = {
      name: name.trim() || "Neevetha",
      customTitle: customTitle.trim() || PERSONA_DEFINITIONS[selectedRole]?.title,
      organization: organization.trim() || "Focus Mode",
      role: selectedRole,
      language: selectedLanguage,
      distractions: selectedDistractions,
      focusRhythm: selectedRhythm,
      dailyGoalMinutes: dailyGoal,
      onboardingCompleted: true,
    };
    updateProfile(updated);

    // Persist all user details directly to PostgreSQL database
    try {
      fetch("http://localhost:8000/api/v1/users/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: profile.email || "neevetha@contextiq.io",
          password: "password123",
          display_name: updated.name,
          role_persona: updated.role,
          custom_title: updated.customTitle,
          organization: updated.organization,
          focus_rhythm: updated.focusRhythm,
          daily_goal_minutes: updated.dailyGoalMinutes,
          language: updated.language,
          distractions: updated.distractions,
          daily_routine: profile.dailyRoutine,
          daily_chores: profile.dailyChores,
          weekend_chores: profile.weekendChores,
          frequent_forget_items: profile.frequentForgetItems,
          time_delay_triggers: profile.timeDelayTriggers,
          primary_occupation: updated.customTitle,
          initial_tasks: [],
        }),
      }).catch(() => {});
    } catch {
      // offline fallback
    }

    closeOnboarding();
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
            <div className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-sm shadow-indigo-500/25">
                <Brain className="h-4 w-4" />
              </span>
              <div>
                <h2 className="text-base font-bold text-foreground tracking-tight">
                  {t("profileTitle")}
                </h2>
                <p className="text-xs text-muted-foreground">
                  {t("profileSubtitle")}
                </p>
              </div>
            </div>

            {/* Stepper Dots */}
            <div className="flex items-center gap-1.5 font-mono text-xs">
              {[1, 2, 3, 4].map((num) => (
                <div
                  key={num}
                  className={cn(
                    "h-2 rounded-full transition-all duration-300",
                    step === num
                      ? "w-6 bg-indigo-600 dark:bg-indigo-400"
                      : step > num
                      ? "w-2 bg-emerald-500"
                      : "w-2 bg-muted-foreground/30"
                  )}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Body Content by Step */}
        <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto">
          {/* ================= STEP 1: IDENTITY & ROLE PERSONA ================= */}
          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-indigo-600 dark:text-indigo-400 border-indigo-500/30">
                  Step 1 of 4: Identity &amp; Cognitive Persona
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  Tell us who you are and what you do
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Calibrates the cold-start Machine Learning baseline and task distraction sensitivity.
                </p>
              </div>

              {/* Name & Title Inputs */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 rounded-2xl bg-muted/40 border border-border/70">
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 mb-1">
                    <User className="h-3 w-3 text-indigo-500" />
                    Your Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Neevetha"
                    className="w-full px-3 py-1.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 mb-1">
                    <Briefcase className="h-3 w-3 text-indigo-500" />
                    Professional Title
                  </label>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={(e) => setCustomTitle(e.target.value)}
                    placeholder="e.g. Software Engineer"
                    className="w-full px-3 py-1.5 rounded-xl border border-border/80 bg-background text-xs font-semibold text-foreground focus:outline-hidden focus:ring-2 focus:ring-indigo-500/40"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1 mb-1">
                    <Building className="h-3 w-3 text-indigo-500" />
                    Org / Institution
                  </label>
                  <input
                    type="text"
                    value={organization}
                    onChange={(e) => setOrganization(e.target.value)}
                    placeholder="e.g. Stripe / CSAIL"
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
                        if (!customTitle || customTitle === "Senior Software Engineer" || customTitle === "Student & Academic") {
                          setCustomTitle(meta.title.split("/")[0].trim());
                        }
                      }}
                      className={cn(
                        "p-3.5 rounded-2xl border text-left transition-all duration-200 relative group flex flex-col justify-between",
                        isSelected
                          ? "bg-indigo-50/90 border-indigo-600 dark:bg-indigo-950/60 dark:border-indigo-500 shadow-sm ring-1 ring-indigo-500"
                          : "bg-background/70 border-border/80 hover:bg-muted/50 hover:border-indigo-400/40"
                      )}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2.5">
                          <span
                            className={cn(
                              "flex h-8 w-8 items-center justify-center rounded-xl border transition-colors",
                              isSelected
                                ? "bg-indigo-600 text-white border-indigo-700"
                                : "bg-muted text-muted-foreground border-border/80 group-hover:text-indigo-600"
                            )}
                          >
                            <Icon className="h-4 w-4" />
                          </span>
                          <div>
                            <span className="text-xs font-bold text-foreground block">
                              {meta.title}
                            </span>
                          </div>
                        </div>
                        {isSelected && (
                          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-white">
                            <Check className="h-3 w-3" />
                          </span>
                        )}
                      </div>

                      <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">
                        {meta.tagline}
                      </p>

                      <div className="mt-2.5 pt-2 border-t border-border/50 flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                        <span>Tolerance:</span>
                        <span className="text-indigo-700 dark:text-indigo-400 font-semibold truncate max-w-[130px]">
                          {meta.baselineFrictionTolerance.split(" ")[0]}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* ================= STEP 2: DISTRACTION LANDSCAPE ================= */}
          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-amber-600 dark:text-amber-400 border-amber-500/30">
                  Step 2 of 4: Distraction Landscape
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  What causes your longest mental resumption delays?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Select all that pull you away from deep work. We weight these heavier in friction calculations.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {DISTRACTION_OPTIONS.map((opt) => {
                  const isChecked = selectedDistractions.includes(opt.id);

                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => toggleDistraction(opt.id)}
                      className={cn(
                        "p-3 rounded-2xl border text-left transition-all duration-200 flex items-center justify-between",
                        isChecked
                          ? "bg-amber-50/80 border-amber-500 dark:bg-amber-950/40 dark:border-amber-600 shadow-xs"
                          : "bg-background/70 border-border/80 hover:bg-muted/50 hover:border-amber-400/40"
                      )}
                    >
                      <div className="flex items-center gap-2.5 truncate">
                        <span className="text-xl">{opt.icon}</span>
                        <div className="truncate">
                          <span className="text-xs font-semibold text-foreground block truncate">
                            {opt.label}
                          </span>
                          <span className="text-[10px] font-mono text-amber-600 dark:text-amber-400 font-medium">
                            {opt.impact}
                          </span>
                        </div>
                      </div>

                      <div
                        className={cn(
                          "h-5 w-5 rounded-md border flex items-center justify-center shrink-0 ml-2 transition-colors",
                          isChecked
                            ? "bg-amber-500 border-amber-600 text-white"
                            : "border-border bg-background"
                        )}
                      >
                        {isChecked && <Check className="h-3 w-3" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* ================= STEP 3: LANGUAGE & RHYTHM & GOAL ================= */}
          {step === 3 && (
            <div className="space-y-5 animate-fade-in">
              <div>
                <Badge variant="outline" className="text-[10px] uppercase font-mono text-sky-600 dark:text-sky-400 border-sky-500/30">
                  Step 3 of 4: Language, Rhythm &amp; Daily Goal
                </Badge>
                <h3 className="text-sm font-bold text-foreground mt-1">
                  How and when do you operate best?
                </h3>
                <p className="text-xs text-muted-foreground mt-0.5">
                  AI re-entry briefings and NLP task processing will speak your language.
                </p>
              </div>

              {/* Language Selector Grid */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Globe className="h-3.5 w-3.5 text-indigo-500" />
                  Primary Interface &amp; AI Language:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {AVAILABLE_LANGUAGES.map((lang) => {
                    const isLangSelected = selectedLanguage === lang.code;

                    return (
                      <button
                        key={lang.code}
                        type="button"
                        onClick={() => setSelectedLanguage(lang.code)}
                        className={cn(
                          "p-2.5 rounded-xl border text-left transition-all duration-200 flex items-center justify-between",
                          isLangSelected
                            ? "bg-indigo-50/90 border-indigo-600 dark:bg-indigo-950/60 dark:border-indigo-500 shadow-2xs font-bold"
                            : "bg-background/70 border-border/80 hover:bg-muted/60"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <span className="text-base">{lang.flag}</span>
                          <div>
                            <span className="text-xs text-foreground block">
                              {lang.nativeName}
                            </span>
                            <span className="text-[10px] text-muted-foreground font-mono">
                              {lang.name}
                            </span>
                          </div>
                        </div>
                        {isLangSelected && <Check className="h-3 w-3 text-indigo-600" />}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Peak Focus Rhythm */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Clock className="h-3.5 w-3.5 text-amber-500" />
                  Peak Focus Hours:
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
                          "p-2.5 rounded-xl border text-left transition-all duration-200",
                          isRhythmSelected
                            ? "bg-amber-50/80 border-amber-500 dark:bg-amber-950/40 dark:border-amber-600 shadow-2xs"
                            : "bg-background/70 border-border/80 hover:bg-muted/60"
                        )}
                      >
                        <div className="flex items-center gap-1.5">
                          <span>{r.icon}</span>
                          <span className="text-xs font-semibold text-foreground truncate">
                            {r.title}
                          </span>
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-1 truncate">
                          {r.window}
                        </p>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Daily Target Goal */}
              <div className="space-y-2">
                <label className="text-xs font-semibold text-foreground flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Target className="h-3.5 w-3.5 text-emerald-500" />
                    Daily Deep Focus Target:
                  </span>
                  <span className="font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                    {dailyGoal} minutes ({Math.round(dailyGoal / 60 * 10) / 10} hrs)
                  </span>
                </label>
                <div className="flex items-center gap-2">
                  {GOAL_OPTIONS.map((mins) => (
                    <button
                      key={mins}
                      type="button"
                      onClick={() => setDailyGoal(mins)}
                      className={cn(
                        "flex-1 py-1.5 rounded-xl text-xs font-semibold border transition-all",
                        dailyGoal === mins
                          ? "bg-emerald-500 text-white border-emerald-600 shadow-2xs"
                          : "bg-background/70 border-border/80 hover:bg-muted text-muted-foreground hover:text-foreground"
                      )}
                    >
                      {mins}m
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ================= STEP 4: SUMMARY & CELEBRATION ================= */}
          {step === 4 && (
            <div className="space-y-4 animate-fade-in text-center py-2">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 shadow-sm">
                <ShieldCheck className="h-8 w-8" />
              </div>

              <div>
                <h3 className="text-base font-bold text-foreground">
                  Personalized Baseline Calibrated for {name}!
                </h3>
                <p className="text-xs text-muted-foreground mt-1 max-w-md mx-auto">
                  ContextIQ has tuned its machine learning forgetting risk models and telemetry anchors to your role as <span className="font-semibold text-foreground">{customTitle}</span>.
                </p>
              </div>

              {/* Summary Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-2xl bg-muted/40 border border-border/60 text-left text-xs">
                <div>
                  <span className="text-[10px] font-mono text-muted-foreground uppercase">Role Persona</span>
                  <p className="font-bold text-foreground mt-0.5 truncate">
                    {PERSONA_DEFINITIONS[selectedRole]?.title.split("/")[0].trim()}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-muted-foreground uppercase">Daily Target</span>
                  <p className="font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
                    {dailyGoal} min / day
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-muted-foreground uppercase">Language</span>
                  <p className="font-bold text-indigo-600 dark:text-indigo-400 mt-0.5">
                    {AVAILABLE_LANGUAGES.find((l) => l.code === selectedLanguage)?.nativeName}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] font-mono text-muted-foreground uppercase">Shielded Triggers</span>
                  <p className="font-bold text-amber-600 dark:text-amber-400 mt-0.5">
                    {selectedDistractions.length} Distractors
                  </p>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200/80 dark:border-indigo-900/60 text-left text-xs">
                <span className="text-[10px] font-mono text-indigo-700 dark:text-indigo-300 font-bold uppercase block">
                  Tailored Cognitive Re-Entry Anchor:
                </span>
                <p className="text-foreground mt-1 font-medium">
                  &quot;{PERSONA_DEFINITIONS[selectedRole]?.reentryAnchorTemplate}&quot;
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-5 border-t border-border/60 bg-muted/30 flex items-center justify-between">
          {step > 1 && step < 4 ? (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setStep((prev) => (prev - 1) as any)}
              className="h-9 gap-1.5 text-xs rounded-xl"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back
            </Button>
          ) : (
            <div />
          )}

          {step < 3 ? (
            <Button
              size="sm"
              onClick={() => setStep((prev) => (prev + 1) as any)}
              className="h-9 px-4 gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-sm shadow-indigo-500/25"
            >
              Continue
              <ArrowRight className="h-3.5 w-3.5" />
            </Button>
          ) : step === 3 ? (
            <Button
              size="sm"
              onClick={() => setStep(4)}
              className="h-9 px-5 gap-1.5 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-sm shadow-emerald-500/25"
            >
              Save Profile &amp; Calibrate
              <Check className="h-3.5 w-3.5" />
            </Button>
          ) : (
            <Button
              size="sm"
              onClick={handleFinish}
              className="w-full h-10 gap-1.5 text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl shadow-md shadow-indigo-500/25"
            >
              Launch Personalized Flow Dashboard
              <Zap className="h-4 w-4 fill-current" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
