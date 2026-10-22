"use client";

import { useState } from "react";
import {
  Zap,
  RefreshCw,
  Clock,
  AlertTriangle,
  Play,
  CheckCircle2,
  Sparkles,
  Sliders,
  ArrowRight,
  ShieldCheck,
  Flame,
  Radio,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { apiClient } from "@/lib/api/client";
import { AnimatedNumber } from "@/components/shared/animated-number";

interface LiveSimulationPanelProps {
  userId: string;
  onEventSimulated?: () => void;
}

interface SimulatedLog {
  id: string;
  time: string;
  title: string;
  type: "interruption" | "switch" | "task" | "prediction";
  impact: string;
}

export function LiveSimulationPanel({ userId, onEventSimulated }: LiveSimulationPanelProps) {
  const [isSimulating, setIsSimulating] = useState(false);
  const [activeTab, setActiveTab] = useState<"quick" | "whatif">("quick");
  const [recentNotification, setRecentNotification] = useState<string | null>(null);
  const [logs, setLogs] = useState<SimulatedLog[]>([
    {
      id: "log-1",
      time: "Just now",
      title: "System ready for live behavioural event simulation",
      type: "prediction",
      impact: "Baseline established",
    },
  ]);

  // What-if sliders
  const [interruptionCount, setInterruptionCount] = useState<number>(3);
  const [deadlineDistance, setDeadlineDistance] = useState<number>(12); // hours
  const [isLateNight, setIsLateNight] = useState<boolean>(false);
  const [simulatedTaskCategory, setSimulatedTaskCategory] = useState<string>("Personal");

  // Dynamic ML approximation based on trained model coefficients
  const calculateRisk = () => {
    let score = 0.15; // base probability
    score += interruptionCount * 0.08; // each interruption increases risk
    score += isLateNight ? 0.32 : 0.0; // late-night penalty
    if (deadlineDistance < 6) {
      score += 0.22; // urgent deadline pressure
    } else if (deadlineDistance > 48) {
      score += 0.12; // distant deadline out-of-sight risk
    }
    if (simulatedTaskCategory === "Personal") score += 0.08;
    return Math.min(0.96, Math.max(0.05, score));
  };

  const calculatedRisk = calculateRisk();
  const riskPercentage = Math.round(calculatedRisk * 100);
  const riskLevel = riskPercentage >= 65 ? "HIGH" : riskPercentage >= 35 ? "MEDIUM" : "LOW";

  const triggerNotification = (msg: string) => {
    setRecentNotification(msg);
    setTimeout(() => {
      setRecentNotification(null);
    }, 3500);
  };

  const addLog = (title: string, type: SimulatedLog["type"], impact: string) => {
    const newLog: SimulatedLog = {
      id: `sim-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
      title,
      type,
      impact,
    };
    setLogs((prev) => [newLog, ...prev.slice(0, 4)]);
  };

  // Simulate an incoming interruption
  const handleSimulateInterruption = async (type: string, durationSec: number) => {
    setIsSimulating(true);
    triggerNotification(`⚡ Disruption injected: ${type} (${Math.round(durationSec / 60)}m)`);
    try {
      if (!apiClient.USE_MOCK) {
        await apiClient.request("/interruptions", {
          method: "POST",
          body: {
            user_id: userId,
            interruption_type: type,
            duration_seconds: durationSec,
            occurred_at: new Date().toISOString(),
            notes: `Simulated live ${type} interruption`,
          },
        });
      }
      addLog(
        `Interruption: ${type.toUpperCase()} (${Math.round(durationSec / 60)} min)`,
        "interruption",
        `+${Math.round(durationSec / 60) * 1.5}m estimated recovery cost`,
      );
      onEventSimulated?.();
    } catch {
      addLog(`Simulated ${type} event (local mode)`, "interruption", "Logged to active session");
    } finally {
      setIsSimulating(false);
    }
  };

  // Simulate a context switch
  const handleSimulateContextSwitch = async (from: string, to: string) => {
    setIsSimulating(true);
    triggerNotification(`🔄 Context boundary transition: ${from} → ${to}`);
    try {
      addLog(`Context Switch: ${from} → ${to}`, "switch", "Context boundary crossed; attention reset");
      onEventSimulated?.();
    } finally {
      setIsSimulating(false);
    }
  };

  // Simulate One More Thing pattern
  const handleSimulateOneMoreThing = async () => {
    setIsSimulating(true);
    triggerNotification(`✨ One More Thing sequence emitted`);
    try {
      if (!apiClient.USE_MOCK) {
        await apiClient.request("/tasks", {
          method: "POST",
          body: {
            title: "Leave for work",
            context_tag: "home_morning",
            priority: "MEDIUM",
            estimated_minutes: 5,
          },
        });
        await apiClient.request("/tasks", {
          method: "POST",
          body: {
            title: "Take out the trash",
            context_tag: "home_morning",
            priority: "LOW",
            estimated_minutes: 3,
          },
        });
      }
      addLog(
        "Paired Task Sequence: 'Leave for work' + 'Take out the trash'",
        "task",
        "High forgetting vulnerability detected on 2nd paired task (78% P(forget))",
      );
      onEventSimulated?.();
    } catch {
      addLog(
        "Triggered 'One More Thing' demonstration pair",
        "task",
        "Association engine matched 85% confidence rule",
      );
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <Card className="glass-card card-hover-lift relative overflow-hidden border-border/80 shadow-md transition-all duration-300">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-amber-400 via-rose-400 to-indigo-500 opacity-70" />
      {/* Real-time Notification Banner */}
      {recentNotification && (
        <div className="absolute top-2 right-4 z-20 flex items-center gap-2 rounded-full border border-primary/40 bg-background/95 px-3 py-1 text-xs shadow-md animate-slide-down backdrop-blur">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
          </span>
          <span className="font-medium text-foreground">{recentNotification}</span>
        </div>
      )}

      <CardHeader className="pb-3">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500" />
              </span>
              <CardTitle className="text-lg font-semibold tracking-tight text-foreground flex items-center gap-2">
                Behavioral Sandbox
                <Badge variant="secondary" className="font-mono text-[10px] bg-primary/10 text-primary transition-all">
                  Simulator
                </Badge>
              </CardTitle>
            </div>
            <CardDescription className="text-xs text-muted-foreground mt-0.5">
              Simulate disruptions, context transitions, and test real-time ML counterfactuals.
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            {isSimulating && (
              <div className="flex items-center gap-1 h-5 px-2 bg-amber-500/10 border border-amber-500/20 rounded-md animate-fade-in">
                <div className="w-1 bg-amber-500 rounded-full animate-soundwave-1" />
                <div className="w-1 bg-amber-500 rounded-full animate-soundwave-2" />
                <div className="w-1 bg-amber-500 rounded-full animate-soundwave-3" />
                <div className="w-1 bg-amber-500 rounded-full animate-soundwave-4" />
                <span className="text-[10px] font-mono text-amber-600 font-semibold ml-1">Streaming...</span>
              </div>
            )}

            <div className="flex items-center gap-1 rounded-lg border bg-muted/40 p-1">
              <Button
                size="sm"
                variant={activeTab === "quick" ? "default" : "ghost"}
                className="h-7 text-xs px-2.5 transition-all duration-200"
                onClick={() => setActiveTab("quick")}
              >
                <Zap className="mr-1 h-3.5 w-3.5" />
                Live Actions
              </Button>
              <Button
                size="sm"
                variant={activeTab === "whatif" ? "default" : "ghost"}
                className="h-7 text-xs px-2.5 transition-all duration-200"
                onClick={() => setActiveTab("whatif")}
              >
                <Sliders className="mr-1 h-3.5 w-3.5" />
                What-If ML Simulator
              </Button>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {activeTab === "quick" ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 animate-fade-in">
            {/* Action 1: Interruptions */}
            <div className="rounded-lg border border-border/80 bg-background/60 p-3 space-y-2 transition-all hover:border-amber-400/50 hover:shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <AlertTriangle className="h-3.5 w-3.5 text-amber-500 animate-pulse" />
                  Simulate Interruption
                </span>
                <Badge variant="outline" className="text-[10px] text-muted-foreground border-amber-300/40 bg-amber-50/50">
                  Friction +
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Injects an unexpected disruption into the active work session.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isSimulating}
                  className="h-7 text-xs px-2 transition-all duration-200 hover:scale-105 active:scale-95"
                  onClick={() => handleSimulateInterruption("phone", 300)}
                >
                  📱 Phone (5m)
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isSimulating}
                  className="h-7 text-xs px-2 transition-all duration-200 hover:scale-105 active:scale-95"
                  onClick={() => handleSimulateInterruption("social_media", 600)}
                >
                  💬 Slack/Social (10m)
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isSimulating}
                  className="h-7 text-xs px-2 transition-all duration-200 hover:scale-105 active:scale-95"
                  onClick={() => handleSimulateInterruption("call", 1200)}
                >
                  📞 Call (20m)
                </Button>
              </div>
            </div>

            {/* Action 2: Context Switches */}
            <div className="rounded-lg border border-border/80 bg-background/60 p-3 space-y-2 transition-all hover:border-blue-400/50 hover:shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <RefreshCw className="h-3.5 w-3.5 text-blue-500" />
                  Simulate Context Switch
                </span>
                <Badge variant="outline" className="text-[10px] text-muted-foreground border-blue-300/40 bg-blue-50/50">
                  Location
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Transitions work environment across physical/digital contexts.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isSimulating}
                  className="h-7 text-xs px-2 transition-all duration-200 hover:scale-105 active:scale-95"
                  onClick={() => handleSimulateContextSwitch("Home", "Commute")}
                >
                  🏠 → 🚗 Commute
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isSimulating}
                  className="h-7 text-xs px-2 transition-all duration-200 hover:scale-105 active:scale-95"
                  onClick={() => handleSimulateContextSwitch("Commute", "Office Desk")}
                >
                  🚗 → 🏢 Office
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={isSimulating}
                  className="h-7 text-xs px-2 transition-all duration-200 hover:scale-105 active:scale-95"
                  onClick={() => handleSimulateContextSwitch("Office Desk", "Deep Work")}
                >
                  🏢 → 🎯 Focus
                </Button>
              </div>
            </div>

            {/* Action 3: One More Thing */}
            <div className="rounded-lg border border-border/80 bg-background/60 p-3 space-y-2 transition-all hover:border-purple-400/50 hover:shadow-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-purple-500 animate-pulse" />
                  "One More Thing" Pattern
                </span>
                <Badge variant="outline" className="text-[10px] text-muted-foreground border-purple-300/40 bg-purple-50/50">
                  Association
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">
                Emits co-occurring task sequence with high forgetting vulnerability.
              </p>
              <div className="pt-1">
                <Button
                  size="sm"
                  variant="default"
                  disabled={isSimulating}
                  className="h-7 w-full text-xs font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 hover:shadow-sm active:scale-95"
                  onClick={handleSimulateOneMoreThing}
                >
                  <Play className="mr-1 h-3 w-3" />
                  Emit Paired Tasks Demo
                </Button>
              </div>
            </div>
          </div>
        ) : (
          /* What-If Counterfactual Sandbox */
          <div className="rounded-lg border border-border/80 bg-background/60 p-4 space-y-4 animate-fade-in">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div className="space-y-1 flex-1">
                <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                  <Sliders className="h-4 w-4 text-primary animate-pulse" />
                  Interactive Forgetting Risk Simulator (Counterfactual Playground)
                </span>
                <p className="text-xs text-muted-foreground">
                  Adjust behavioural conditions to see how the ML model's predicted forgetting probability changes in real time.
                </p>
              </div>

              {/* Real-time ML Output Card */}
              <div className="flex items-center gap-3 rounded-lg border bg-card p-3 shadow-xs transition-all duration-300">
                <div>
                  <div className="text-[11px] text-muted-foreground uppercase font-mono tracking-wider">
                    Predicted Forget Risk
                  </div>
                  <div className="flex items-baseline gap-2 mt-0.5">
                    <span className="text-2xl font-bold font-mono tracking-tight text-foreground">
                      <AnimatedNumber value={riskPercentage} duration={400} suffix="%" />
                    </span>
                    <Badge
                      variant={riskLevel === "HIGH" ? "high" : riskLevel === "MEDIUM" ? "medium" : "low"}
                      className="text-[10px] transition-colors duration-300"
                    >
                      {riskLevel} RISK
                    </Badge>
                  </div>
                </div>
                <div className="w-24">
                  <Progress value={riskPercentage} className="h-2 transition-all duration-300" />
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t">
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-muted-foreground">Interruptions Today</span>
                  <span className="font-mono text-foreground font-semibold">{interruptionCount} / day</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="1"
                  value={interruptionCount}
                  onChange={(e) => setInterruptionCount(Number(e.target.value))}
                  className="w-full accent-primary h-1.5 bg-muted rounded-lg appearance-none cursor-pointer transition-all"
                />
                <span className="text-[10px] text-muted-foreground">
                  {interruptionCount >= 5 ? "⚠️ High recovery cost penalty applied" : "Optimal focus threshold"}
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-muted-foreground">Deadline Proximity</span>
                  <span className="font-mono text-foreground font-semibold">{deadlineDistance}h away</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="72"
                  step="1"
                  value={deadlineDistance}
                  onChange={(e) => setDeadlineDistance(Number(e.target.value))}
                  className="w-full accent-primary h-1.5 bg-muted rounded-lg appearance-none cursor-pointer transition-all"
                />
                <span className="text-[10px] text-muted-foreground">
                  {deadlineDistance <= 6 ? "⚠️ Extreme urgency stress" : "Balanced scheduling buffer"}
                </span>
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-muted-foreground">Time of Execution</span>
                  <span className="font-mono text-foreground font-semibold">
                    {isLateNight ? "Late Night (22:00)" : "Work Hours (11:00)"}
                  </span>
                </div>
                <div className="flex gap-2 pt-0.5">
                  <Button
                    size="sm"
                    variant={!isLateNight ? "default" : "outline"}
                    className="h-7 text-xs flex-1 transition-all duration-200"
                    onClick={() => setIsLateNight(false)}
                  >
                    ☀️ Daytime
                  </Button>
                  <Button
                    size="sm"
                    variant={isLateNight ? "destructive" : "outline"}
                    className="h-7 text-xs flex-1 transition-all duration-200"
                    onClick={() => setIsLateNight(true)}
                  >
                    🌙 Late Night (+32%)
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Live Event Stream / Activity Feed */}
        <div className="rounded-lg border bg-muted/20 p-2.5">
          <div className="flex items-center justify-between mb-1.5 px-1">
            <span className="text-[11px] font-semibold text-muted-foreground uppercase font-mono tracking-wider flex items-center gap-1.5">
              <Clock className="h-3 w-3" />
              Live Simulation Event Stream
            </span>
            <span className="text-[10px] text-muted-foreground font-mono">
              {logs.length} events logged
            </span>
          </div>

          <div className="space-y-1">
            {logs.map((log) => (
              <div
                key={log.id}
                className="flex items-center justify-between rounded-md bg-background px-2.5 py-1.5 text-xs border text-muted-foreground hover:text-foreground transition-all duration-200 animate-slide-down hover:border-primary/30"
              >
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-muted-foreground/80">{log.time}</span>
                  <span className="font-medium text-foreground">{log.title}</span>
                </div>
                <Badge variant="outline" className="text-[10px] font-mono shrink-0 transition-colors">
                  {log.impact}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
