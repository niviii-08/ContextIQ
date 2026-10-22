"use client";

import {
  Trophy,
  Flame,
  Shield,
  Zap,
  RotateCcw,
  Star,
  Award,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useUserProfile } from "@/context/user-profile-context";
import type { RolePersona } from "@/types/profile";

interface CognitiveBadge {
  id: string;
  title: string;
  tagline: string;
  icon: typeof Trophy;
  progress: number;
  level: string;
  unlocked: boolean;
  color: string;
}

const ROLE_BADGES: Record<RolePersona, CognitiveBadge[]> = {
  developer: [
    {
      id: "badge-quick-resumer",
      title: "Terminal Velocity",
      tagline: "Resumed code syntax & logic in under 90s after an interruption",
      icon: RotateCcw,
      progress: 85,
      level: "Gold Tier",
      unlocked: true,
      color: "text-chart-4 bg-chart-4/10 border-chart-4/30",
    },
    {
      id: "badge-deep-diver",
      title: "PR Architecture Flow",
      tagline: "45 continuous minutes without an external context switch",
      icon: Flame,
      progress: 70,
      level: "Silver Tier",
      unlocked: true,
      color: "text-risk-low bg-risk-low/10 border-risk-low/30",
    },
    {
      id: "badge-context-shield",
      title: "Git Diff Context Shield",
      tagline: "Prevented 5 uncommitted logic drops before context switches",
      icon: Shield,
      progress: 100,
      level: "Master Tier",
      unlocked: true,
      color: "text-primary bg-primary/10 border-primary/30",
    },
    {
      id: "badge-friction-crusher",
      title: "Syntax Friction Crusher",
      tagline: "Lowered developer cognitive friction from 72 down to 48",
      icon: Zap,
      progress: 60,
      level: "Bronze Tier",
      unlocked: false,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    },
  ],
  student: [
    {
      id: "badge-quick-resumer",
      title: "Study Flow Zenith",
      tagline: "Resumed chapter study notes in under 90s after a phone ping",
      icon: RotateCcw,
      progress: 88,
      level: "Gold Tier",
      unlocked: true,
      color: "text-chart-4 bg-chart-4/10 border-chart-4/30",
    },
    {
      id: "badge-deep-diver",
      title: "Dean's Focus Sprint",
      tagline: "45 continuous minutes of uninterrupted academic reading",
      icon: Flame,
      progress: 75,
      level: "Silver Tier",
      unlocked: true,
      color: "text-risk-low bg-risk-low/10 border-risk-low/30",
    },
    {
      id: "badge-context-shield",
      title: "Exam Recall Shield",
      tagline: "Retained 5 spaced repetition targets before the deadline",
      icon: Shield,
      progress: 100,
      level: "Master Tier",
      unlocked: true,
      color: "text-primary bg-primary/10 border-primary/30",
    },
    {
      id: "badge-friction-crusher",
      title: "Procrastination Crusher",
      tagline: "Trimmed assignment abandonment rate by 42% this semester",
      icon: Zap,
      progress: 65,
      level: "Bronze Tier",
      unlocked: false,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    },
  ],
  manager: [
    {
      id: "badge-quick-resumer",
      title: "Rapid Re-Entry Maestro",
      tagline: "Recovered agenda priorities in <60s post-meeting",
      icon: RotateCcw,
      progress: 92,
      level: "Gold Tier",
      unlocked: true,
      color: "text-chart-4 bg-chart-4/10 border-chart-4/30",
    },
    {
      id: "badge-deep-diver",
      title: "Async Strategy Corridor",
      tagline: "45 unbroken minutes drafting quarterly strategy document",
      icon: Flame,
      progress: 68,
      level: "Silver Tier",
      unlocked: true,
      color: "text-risk-low bg-risk-low/10 border-risk-low/30",
    },
    {
      id: "badge-context-shield",
      title: "Delegation Shield",
      tagline: "Zero dropped action items across 14 cross-functional meetings",
      icon: Shield,
      progress: 100,
      level: "Master Tier",
      unlocked: true,
      color: "text-primary bg-primary/10 border-primary/30",
    },
    {
      id: "badge-friction-crusher",
      title: "Calendar Fragment Crusher",
      tagline: "Consolidated 6 fragmented micro-blocks into deep work",
      icon: Zap,
      progress: 58,
      level: "Bronze Tier",
      unlocked: false,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    },
  ],
  researcher: [
    {
      id: "badge-quick-resumer",
      title: "Proof Velocity",
      tagline: "Resumed mathematical derivation in <90s after interruption",
      icon: RotateCcw,
      progress: 86,
      level: "Gold Tier",
      unlocked: true,
      color: "text-chart-4 bg-chart-4/10 border-chart-4/30",
    },
    {
      id: "badge-deep-diver",
      title: "Monograph Deep Dive",
      tagline: "45 unbroken minutes analyzing literature in arXiv papers",
      icon: Flame,
      progress: 72,
      level: "Silver Tier",
      unlocked: true,
      color: "text-risk-low bg-risk-low/10 border-risk-low/30",
    },
    {
      id: "badge-context-shield",
      title: "Hypothesis Shield",
      tagline: "Logged lab hyperparameters & seeds before context loss",
      icon: Shield,
      progress: 100,
      level: "Master Tier",
      unlocked: true,
      color: "text-primary bg-primary/10 border-primary/30",
    },
    {
      id: "badge-friction-crusher",
      title: "Analytical Drift Crusher",
      tagline: "Standardized reproducibility metrics across 4 experiments",
      icon: Zap,
      progress: 62,
      level: "Bronze Tier",
      unlocked: false,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    },
  ],
  creator: [
    {
      id: "badge-quick-resumer",
      title: "Prose Voice Velocity",
      tagline: "Resumed writing rhythm in <90s after notification break",
      icon: RotateCcw,
      progress: 84,
      level: "Gold Tier",
      unlocked: true,
      color: "text-chart-4 bg-chart-4/10 border-chart-4/30",
    },
    {
      id: "badge-deep-diver",
      title: "Immersion Draft Streak",
      tagline: "45 continuous minutes uninterrupted in creative editor",
      icon: Flame,
      progress: 74,
      level: "Silver Tier",
      unlocked: true,
      color: "text-risk-low bg-risk-low/10 border-risk-low/30",
    },
    {
      id: "badge-context-shield",
      title: "Narrative Arc Shield",
      tagline: "Captured spontaneous scene ideas with zero cognitive drop",
      icon: Shield,
      progress: 100,
      level: "Master Tier",
      unlocked: true,
      color: "text-primary bg-primary/10 border-primary/30",
    },
    {
      id: "badge-friction-crusher",
      title: "Creative Block Crusher",
      tagline: "Reduced creative task hesitation and lag by 50%",
      icon: Zap,
      progress: 68,
      level: "Bronze Tier",
      unlocked: false,
      color: "text-amber-500 bg-amber-500/10 border-amber-500/30",
    },
  ],
};

export function GamificationBadges() {
  const { profile, personaMeta } = useUserProfile();
  const badges = ROLE_BADGES[profile.role] || ROLE_BADGES.developer;
  const unlockedCount = badges.filter((b) => b.unlocked).length;

  return (
    <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-amber-400 via-emerald-400 to-indigo-500 opacity-60" />
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-risk-low border-risk-low/30">
                Achievements
              </Badge>
              <Badge variant="outline" className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 border-indigo-500/30">
                {personaMeta.title.split("/")[0].trim()}
              </Badge>
            </div>
            <CardTitle className="text-xl font-semibold tracking-tight mt-1 flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-500" />
              Flow Retention &amp; Milestones
            </CardTitle>
            <CardDescription className="text-xs">
              Progress milestones earned by {profile.name} by minimizing resumption lag and sustaining focus.
            </CardDescription>
          </div>
          <Badge className="bg-amber-500/20 text-amber-600 border-amber-500/30 font-mono text-xs">
            {unlockedCount} / {badges.length} Unlocked
          </Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {badges.map((b) => {
            const Icon = b.icon;
            return (
              <div
                key={b.id}
                className={`p-3.5 rounded-2xl border flex flex-col justify-between transition-all duration-200 hover:scale-[1.02] ${
                  b.unlocked
                    ? "bg-card/90 border-border/80 shadow-xs"
                    : "bg-muted/30 border-dashed border-border/70 opacity-70"
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className={`h-8 w-8 rounded-xl flex items-center justify-center border ${b.color}`}>
                      <Icon className="h-4 w-4" />
                    </span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {b.level}
                    </Badge>
                  </div>

                  <div>
                    <h4 className="text-xs font-bold text-foreground flex items-center gap-1.5">
                      {b.title}
                      {b.unlocked && <CheckCircle2 className="h-3 w-3 text-risk-low shrink-0" />}
                    </h4>
                    <p className="text-[11px] text-muted-foreground mt-0.5 leading-snug">
                      {b.tagline}
                    </p>
                  </div>
                </div>

                <div className="space-y-1 pt-3">
                  <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
                    <span>Progress</span>
                    <span>{b.progress}%</span>
                  </div>
                  <Progress value={b.progress} className="h-1.5" />
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
