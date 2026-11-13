"use client";

import React, { useState } from "react";
import {
  Clock,
  Utensils,
  Shirt,
  AlertCircle,
  Zap,
  CheckCircle2,
  Settings2,
  Sparkles,
  Calendar,
  ShieldAlert,
  ArrowRight,
  Database,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useUserProfile } from "@/context/user-profile-context";
import { cn } from "@/lib/utils";

export function DailyRoutineChoresPanel() {
  const { profile, openOnboarding } = useUserProfile();
  const [completedChores, setCompletedChores] = useState<Record<string, boolean>>({});

  const toggleChore = (chore: string) => {
    setCompletedChores((prev) => ({
      ...prev,
      [chore]: !prev[chore],
    }));
  };

  const hasChores =
    (profile.dailyChores && profile.dailyChores.length > 0) ||
    (profile.weekendChores && profile.weekendChores.length > 0);
  const hasAnchors = profile.frequentForgetItems && profile.frequentForgetItems.length > 0;
  const hasDelays = profile.timeDelayTriggers && profile.timeDelayTriggers.length > 0;
  const hasRoutine = profile.dailyRoutine && profile.dailyRoutine.trim().length > 0;

  return (
    <Card className="glass-card border-border/80 overflow-hidden relative shadow-sm">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500 opacity-90" />

      <CardHeader className="pb-3 pt-5 px-5 sm:px-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                <Clock className="h-3.5 w-3.5" />
              </span>
              <CardTitle className="text-base font-bold text-foreground">
                My Daily Rhythm, Chores & Anti-Forget Anchors
              </CardTitle>
              <Badge variant="outline" className="text-[10px] font-mono border-emerald-500/30 text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 flex items-center gap-1">
                <Database className="h-3 w-3" />
                Live PostgreSQL
              </Badge>
            </div>
            <CardDescription className="text-xs mt-1">
              Real-world routine and chores captured during onboarding to prevent cognitive friction and task forgetting.
            </CardDescription>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={openOnboarding}
            className="self-start sm:self-auto h-8 px-3 text-xs font-semibold gap-1.5 border-indigo-200/80 dark:border-indigo-900/60 bg-indigo-50/50 dark:bg-indigo-950/30 hover:bg-indigo-100/70 text-indigo-700 dark:text-indigo-300 rounded-xl"
          >
            <Settings2 className="h-3.5 w-3.5" />
            <span>Edit Routine & Chores</span>
          </Button>
        </div>
      </CardHeader>

      <CardContent className="px-5 sm:px-6 pb-5 space-y-4">
        {/* 1. Daily Routine Narrative */}
        <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/60 space-y-1.5">
          <div className="flex items-center justify-between text-xs font-semibold text-foreground">
            <span className="flex items-center gap-1.5 text-indigo-600 dark:text-indigo-400">
              <Calendar className="h-3.5 w-3.5" />
              <span>Daily Routine & Circadian Schedule</span>
            </span>
            <span className="text-[10px] font-mono text-muted-foreground uppercase">
              {profile.focusRhythm} Rhythm
            </span>
          </div>
          {hasRoutine ? (
            <p className="text-xs text-foreground/90 leading-relaxed font-normal bg-background/60 p-2.5 rounded-xl border border-border/40">
              &ldquo;{profile.dailyRoutine}&rdquo;
            </p>
          ) : (
            <p className="text-xs text-muted-foreground italic">
              No daily routine schedule added yet. Click &ldquo;Edit Routine & Chores&rdquo; to input your waking, commute, study/work, and resting hours.
            </p>
          )}
        </div>

        {/* 2. Grid of Chores, Anti-Forget Anchors & Delays */}
        <div className="grid gap-3.5 md:grid-cols-3">
          {/* Daily Chores Card */}
          <div className="p-3 rounded-2xl bg-amber-500/5 border border-amber-500/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-amber-700 dark:text-amber-300 flex items-center gap-1.5">
                <Utensils className="h-3.5 w-3.5 text-amber-600" />
                <span>Daily Chores</span>
              </span>
              <Badge variant="outline" className="text-[9px] font-mono border-amber-400/40 text-amber-700 dark:text-amber-300">
                {profile.dailyChores?.length || 0} active
              </Badge>
            </div>

            {profile.dailyChores && profile.dailyChores.length > 0 ? (
              <ul className="space-y-1.5">
                {profile.dailyChores.map((chore, idx) => {
                  const isDone = completedChores[chore];
                  return (
                    <li
                      key={idx}
                      onClick={() => toggleChore(chore)}
                      className={cn(
                        "flex items-center gap-2 p-1.5 px-2 rounded-xl text-xs cursor-pointer transition-all border",
                        isDone
                          ? "bg-amber-100/60 dark:bg-amber-950/40 border-amber-300/40 text-muted-foreground line-through"
                          : "bg-background/80 border-border/50 hover:border-amber-400/50 text-foreground font-medium",
                      )}
                    >
                      <CheckCircle2
                        className={cn(
                          "h-3.5 w-3.5 flex-shrink-0 transition-colors",
                          isDone ? "text-emerald-500 fill-emerald-500/20" : "text-muted-foreground/50",
                        )}
                      />
                      <span className="truncate">{chore}</span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-[11px] text-muted-foreground italic">
                No daily chores specified (e.g. vessel washing, meal prep).
              </p>
            )}
          </div>

          {/* Weekend Chores Card */}
          <div className="p-3 rounded-2xl bg-sky-500/5 border border-sky-500/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-sky-700 dark:text-sky-300 flex items-center gap-1.5">
                <Shirt className="h-3.5 w-3.5 text-sky-600" />
                <span>Weekend Chores</span>
              </span>
              <Badge variant="outline" className="text-[9px] font-mono border-sky-400/40 text-sky-700 dark:text-sky-300">
                {profile.weekendChores?.length || 0} active
              </Badge>
            </div>

            {profile.weekendChores && profile.weekendChores.length > 0 ? (
              <ul className="space-y-1.5">
                {profile.weekendChores.map((chore, idx) => {
                  const isDone = completedChores[chore];
                  return (
                    <li
                      key={idx}
                      onClick={() => toggleChore(chore)}
                      className={cn(
                        "flex items-center gap-2 p-1.5 px-2 rounded-xl text-xs cursor-pointer transition-all border",
                        isDone
                          ? "bg-sky-100/60 dark:bg-sky-950/40 border-sky-300/40 text-muted-foreground line-through"
                          : "bg-background/80 border-border/50 hover:border-sky-400/50 text-foreground font-medium",
                      )}
                    >
                      <CheckCircle2
                        className={cn(
                          "h-3.5 w-3.5 flex-shrink-0 transition-colors",
                          isDone ? "text-emerald-500 fill-emerald-500/20" : "text-muted-foreground/50",
                        )}
                      />
                      <span className="truncate">{chore}</span>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <p className="text-[11px] text-muted-foreground italic">
                No weekend chores entered (e.g. dress washing / laundry).
              </p>
            )}
          </div>

          {/* Anti-Forget Anchors Card */}
          <div className="p-3 rounded-2xl bg-rose-500/5 border border-rose-500/20 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-rose-700 dark:text-rose-300 flex items-center gap-1.5">
                <AlertCircle className="h-3.5 w-3.5 text-rose-600" />
                <span>Anti-Forget Safety Anchors</span>
              </span>
              <Badge variant="outline" className="text-[9px] font-mono border-rose-400/40 text-rose-700 dark:text-rose-300">
                High Risk
              </Badge>
            </div>

            {profile.frequentForgetItems && profile.frequentForgetItems.length > 0 ? (
              <ul className="space-y-1.5">
                {profile.frequentForgetItems.map((anchor, idx) => (
                  <li
                    key={idx}
                    className="flex items-center gap-2 p-1.5 px-2 rounded-xl text-xs bg-background/80 border border-border/50 text-foreground font-medium"
                  >
                    <ShieldAlert className="h-3.5 w-3.5 text-rose-500 flex-shrink-0" />
                    <span className="truncate" title={anchor}>{anchor}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-[11px] text-muted-foreground italic">
                No forget triggers logged (e.g. geyser, keys, vitamins, git push).
              </p>
            )}
          </div>
        </div>

        {/* 3. Time Delay Triggers Hotspot Strip */}
        {hasDelays && (
          <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-border/50">
            <span className="text-[11px] font-bold text-muted-foreground flex items-center gap-1">
              <Zap className="h-3 w-3 text-amber-500" />
              <span>Identified Delay Traps:</span>
            </span>
            {profile.timeDelayTriggers?.map((delay, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 text-[11px] font-medium bg-muted/60 text-foreground px-2 py-0.5 rounded-lg border border-border/60"
              >
                <span>âš ï¸ </span> {delay}
              </span>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
