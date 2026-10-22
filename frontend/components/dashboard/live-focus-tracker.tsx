"use client";

import { useState, useEffect } from "react";
import {
  Play,
  RotateCcw,
  Zap,
  CheckCircle2,
  Clock,
  Coffee,
  PhoneCall,
  Mail,
  MessageCircle,
  UserCheck,
  Brain,
  Sparkles,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useUserProfile } from "@/context/user-profile-context";

type SessionState = "idle" | "focused" | "interrupted" | "resuming_delay";

interface RecordedEvent {
  id: string;
  taskTitle: string;
  focusSeconds: number;
  interruptionType?: string;
  interruptionSeconds: number;
  microDelaySeconds: number;
  timestamp: string;
}

export function LiveFocusTracker({ onSessionRecorded }: { onSessionRecorded?: () => void }) {
  const { profile, personaMeta, t } = useUserProfile();

  const [sessionState, setSessionState] = useState<SessionState>("idle");
  const [taskTitle, setTaskTitle] = useState<string>("Deep Focus Sprint");
  const [customTask, setCustomTask] = useState<string>("");

  const [focusSeconds, setFocusSeconds] = useState(0);
  const [interruptionSeconds, setInterruptionSeconds] = useState(0);
  const [microDelaySeconds, setMicroDelaySeconds] = useState(0);
  const [selectedInterruptionType, setSelectedInterruptionType] = useState<string>("Notification");

  // Keep taskTitle aligned with persona preset when first loading
  useEffect(() => {
    if (sessionState === "idle" && personaMeta.defaultPresets.length > 0) {
      setTaskTitle(personaMeta.defaultPresets[0].title);
    }
  }, [personaMeta, sessionState]);

  const [history, setHistory] = useState<RecordedEvent[]>([
    {
      id: "ev-01",
      taskTitle: "Literature Review on Resumption Lag",
      focusSeconds: 1540,
      interruptionType: "Phone Call",
      interruptionSeconds: 240,
      microDelaySeconds: 185,
      timestamp: "11:20 AM",
    },
  ]);

  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (sessionState === "focused") {
      interval = setInterval(() => setFocusSeconds((prev) => prev + 1), 1000);
    } else if (sessionState === "interrupted") {
      interval = setInterval(() => setInterruptionSeconds((prev) => prev + 1), 1000);
    } else if (sessionState === "resuming_delay") {
      interval = setInterval(() => setMicroDelaySeconds((prev) => prev + 1), 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [sessionState]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  const handleStartSession = (presetTitle?: string) => {
    const active = presetTitle || (customTask.trim() ? customTask : taskTitle);
    setTaskTitle(active);
    setFocusSeconds(0);
    setInterruptionSeconds(0);
    setMicroDelaySeconds(0);
    setSessionState("focused");
  };

  const handleTriggerInterruption = (type: string) => {
    setSelectedInterruptionType(type);
    setInterruptionSeconds(0);
    setSessionState("interrupted");
  };

  const handleDisruptionEnded = () => {
    setMicroDelaySeconds(0);
    setSessionState("resuming_delay");
  };

  const handleRestoreFlow = () => {
    const newEvent: RecordedEvent = {
      id: `ev-${Date.now()}`,
      taskTitle,
      focusSeconds,
      interruptionType: selectedInterruptionType,
      interruptionSeconds,
      microDelaySeconds,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setHistory((prev) => [newEvent, ...prev.slice(0, 2)]);
    setSessionState("focused");
    onSessionRecorded?.();
  };

  const handleCompleteSession = () => {
    setSessionState("idle");
    onSessionRecorded?.();
  };

  return (
    <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
      {/* Top Ambient Glow Line */}
      <div
        className={cn(
          "absolute inset-x-0 top-0 h-[3px] transition-all duration-500",
          sessionState === "idle" && "bg-gradient-to-r from-indigo-500 via-sky-400 to-indigo-500 opacity-60",
          sessionState === "focused" && "bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-500 opacity-100",
          sessionState === "interrupted" && "bg-gradient-to-r from-rose-500 via-amber-400 to-rose-500 opacity-100",
          sessionState === "resuming_delay" && "bg-gradient-to-r from-amber-400 via-orange-400 to-amber-500 opacity-100 animate-pulse"
        )}
      />

      <CardHeader className="p-5 pb-3 flex flex-row items-center justify-between space-y-0 border-b border-border/50">
        <div>
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
            <span
              className={cn(
                "flex h-2.5 w-2.5 rounded-full transition-colors duration-300",
                sessionState === "idle" && "bg-indigo-500",
                sessionState === "focused" && "bg-emerald-500 animate-ping",
                sessionState === "interrupted" && "bg-rose-500 animate-pulse",
                sessionState === "resuming_delay" && "bg-amber-500 animate-pulse"
              )}
            />
            {t("flowChronometer")}
          </CardTitle>
          <CardDescription className="text-xs text-muted-foreground mt-0.5">
            {t("flowSubtitle")}
          </CardDescription>
        </div>

        {sessionState === "idle" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border border-indigo-500/20">
            <Sparkles className="h-3 w-3" />
            {t("ready")}
          </span>
        )}
        {sessionState === "focused" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            {t("deepFlowActive")}
          </span>
        )}
        {sessionState === "interrupted" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
            <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse" />
            {t("disruptionLogged")}
          </span>
        )}
        {sessionState === "resuming_delay" && (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
            <span className="h-2 w-2 rounded-full bg-amber-500 animate-pulse" />
            {t("lagStopwatchRunning")}
          </span>
        )}
      </CardHeader>

      <CardContent className="p-5 space-y-4">
        {/* ================= 1. IDLE STATE ================= */}
        {sessionState === "idle" && (
          <div className="space-y-4">
            {/* Command-style Input */}
            <div className="relative flex items-center">
              <Input
                placeholder="What high-leverage task are you tackling right now?"
                value={customTask}
                onChange={(e) => setCustomTask(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleStartSession()}
                className="h-11 pl-3.5 pr-28 text-xs bg-background/80 border-border/80 rounded-xl shadow-xs focus-visible:ring-indigo-500/50"
              />
              <Button
                size="sm"
                onClick={() => handleStartSession()}
                className="absolute right-1.5 h-8 px-3.5 gap-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-sm shadow-indigo-500/25 transition-all active:scale-95"
              >
                <Play className="h-3 w-3 fill-current" />
                {t("startFlow")}
              </Button>
            </div>

            {/* Role-Personalized Presets */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  {personaMeta.title.split("/")[0]} Sprint Presets:
                </span>
                <span className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400">
                  Calibrated for {profile.role}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {personaMeta.defaultPresets.map((preset) => (
                  <button
                    key={preset.title}
                    type="button"
                    onClick={() => handleStartSession(preset.title)}
                    className="flex flex-col items-start p-2.5 rounded-xl border border-border/70 bg-background/60 text-left transition-all duration-200 group/btn hover:border-indigo-500/40 hover:bg-indigo-50/50 dark:hover:bg-indigo-950/30"
                  >
                    <div className="flex items-center justify-between w-full">
                      <Zap className="h-3.5 w-3.5 text-indigo-500 transition-transform group-hover/btn:scale-110" />
                      <span className="text-[10px] font-mono text-muted-foreground">{preset.duration}</span>
                    </div>
                    <span className="text-xs font-semibold text-foreground mt-1.5 truncate w-full">
                      {preset.title}
                    </span>
                    <span className="text-[9px] font-mono text-muted-foreground/80 mt-0.5">
                      {preset.type}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= 2. FOCUSED STATE (CIRCULAR RADIAL CHRONOMETER) ================= */}
        {sessionState === "focused" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-gradient-to-r from-indigo-50/80 via-background to-background dark:from-indigo-950/30 border border-indigo-200/60 dark:border-indigo-900/60 shadow-xs">
              <div className="flex items-center gap-3">
                {/* Mini Pulsing Circular SVG Dial */}
                <div className="relative flex items-center justify-center shrink-0">
                  <svg className="w-16 h-16 -rotate-90 transform" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="40" className="stroke-muted" strokeWidth="8" fill="transparent" />
                    <circle
                      cx="50"
                      cy="50"
                      r="40"
                      className="stroke-emerald-500 dark:stroke-emerald-400 transition-all duration-1000"
                      strokeWidth="8"
                      strokeDasharray={251}
                      strokeDashoffset={251 - (251 * (focusSeconds % 60)) / 60}
                      strokeLinecap="round"
                      fill="transparent"
                    />
                  </svg>
                  <span className="absolute font-mono text-xs font-bold text-emerald-600 dark:text-emerald-400">
                    {focusSeconds % 60}s
                  </span>
                </div>

                <div>
                  <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                    {t("deepFlowActive")}
                  </span>
                  <p className="text-sm font-bold text-foreground mt-0.5">{taskTitle}</p>
                </div>
              </div>

              <div className="text-right">
                <span className="font-mono text-3xl font-extrabold tracking-tight text-foreground tabular-nums">
                  {formatTimer(focusSeconds)}
                </span>
                <button
                  type="button"
                  onClick={handleCompleteSession}
                  className="block text-[11px] text-emerald-600 hover:text-emerald-700 font-semibold underline underline-offset-2 mt-1"
                >
                  {t("markSessionDone")}
                </button>
              </div>
            </div>

            {/* Interruption Trigger Grid */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-foreground flex items-center gap-1.5">
                  <Zap className="h-3.5 w-3.5 text-amber-500" />
                  Did you get interrupted? Log disruption:
                </span>
                <span className="text-[10px] text-muted-foreground font-mono">Switches to lag mode</span>
              </div>

              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: "Phone", icon: PhoneCall, type: "Phone Call", lag: "+4m avg" },
                  { label: "Slack/Chat", icon: MessageCircle, type: "Social Media", lag: "+6m avg" },
                  { label: "Colleague", icon: UserCheck, type: "Colleague", lag: "+8m avg" },
                  { label: "Email", icon: Mail, type: "Notification", lag: "+3m avg" },
                ].map(({ label, icon: Icon, type, lag }) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => handleTriggerInterruption(type)}
                    className="flex flex-col items-center p-2 rounded-xl border border-border/80 bg-background/70 hover:bg-amber-50/70 hover:border-amber-400/50 dark:hover:bg-amber-950/30 transition-all duration-200 group/btn"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground group-hover/btn:text-amber-500 transition-colors" />
                    <span className="text-xs font-semibold text-foreground mt-1">{label}</span>
                    <span className="text-[9px] font-mono text-muted-foreground group-hover/btn:text-amber-600">{lag}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= 3. INTERRUPTED STATE ================= */}
        {sessionState === "interrupted" && (
          <div className="p-4 rounded-xl bg-rose-50/80 dark:bg-rose-950/25 border border-rose-200/80 dark:border-rose-900/60 space-y-3 animate-fade-in shadow-xs">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-rose-600 dark:text-rose-400">
                  {t("disruptionInProgress")}
                </span>
                <p className="text-sm font-bold text-foreground">
                  Interrupted by: {selectedInterruptionType}
                </p>
              </div>
              <span className="font-mono text-3xl font-extrabold text-rose-600 dark:text-rose-400 tabular-nums">
                {formatTimer(interruptionSeconds)}
              </span>
            </div>

            <Button
              size="sm"
              className="w-full h-10 text-xs font-semibold gap-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white shadow-sm shadow-amber-500/25"
              onClick={handleDisruptionEnded}
            >
              <RotateCcw className="h-4 w-4" />
              {t("disruptionEnded")}
            </Button>
          </div>
        )}

        {/* ================= 4. RESUMING LAG STATE (THE ROLE RE-ENTRY BRIEFING) ================= */}
        {sessionState === "resuming_delay" && (
          <div className="p-4 rounded-xl bg-amber-50/90 dark:bg-amber-950/30 border border-amber-300/80 dark:border-amber-800/80 space-y-3.5 animate-fade-in shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-mono font-bold tracking-wider text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping" />
                  {t("measuringLag")}
                </span>
                <p className="text-sm font-bold text-foreground">
                  Refocusing onto: &quot;{taskTitle}&quot;
                </p>
              </div>
              <span className="font-mono text-3xl font-extrabold text-amber-600 dark:text-amber-400 tabular-nums animate-pulse">
                {formatTimer(microDelaySeconds)}
              </span>
            </div>

            {/* Smart Role-Calibrated Cognitive Re-Entry Briefing */}
            <div className="p-3 rounded-lg bg-background/90 border border-amber-200/80 dark:border-amber-900/60 text-xs space-y-1.5">
              <div className="flex items-center justify-between font-semibold text-amber-700 dark:text-amber-400 text-[11px]">
                <div className="flex items-center gap-1.5">
                  <Brain className="h-3.5 w-3.5 text-amber-500 shrink-0" />
                  <span>{t("reentryAnchorTitle")}</span>
                </div>
                <Badge variant="outline" className="text-[9px] font-mono border-amber-400/50 uppercase">
                  {profile.role}
                </Badge>
              </div>
              <p className="text-foreground text-[11px] font-medium leading-relaxed">
                &quot;{personaMeta.reentryAnchorTemplate}&quot;
              </p>
              <div className="flex items-center justify-between pt-1 text-[10px] font-mono text-amber-600 dark:text-amber-400">
                <span>{t("taskAbandonmentRisk")}</span>
                <span className="font-bold">+{Math.min(48, Math.round(microDelaySeconds * 0.15))}%</span>
              </div>
            </div>

            <Button
              size="sm"
              className="w-full h-10 text-xs font-semibold gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white shadow-sm shadow-emerald-600/25 active:scale-98"
              onClick={handleRestoreFlow}
            >
              <Zap className="h-4 w-4 fill-current" />
              {t("backInFlow")}
            </Button>
          </div>
        )}

        {/* Recent Resumption Lags History */}
        {history.length > 0 && (
          <div className="pt-2 border-t border-border/60 space-y-1.5">
            <span className="text-[10px] font-mono uppercase font-bold tracking-wider text-muted-foreground">
              Recent Micro-Delay Telemetry:
            </span>
            {history.slice(0, 2).map((ev) => (
              <div key={ev.id} className="flex items-center justify-between text-xs py-1 text-muted-foreground">
                <span className="truncate max-w-[220px] text-foreground font-medium">{ev.taskTitle}</span>
                <span className="font-mono text-xs text-amber-600 dark:text-amber-400 font-bold bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20">
                  +{Math.round(ev.microDelaySeconds / 60)}m {ev.microDelaySeconds % 60}s lag
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
