"use client";

import { useEffect, useState } from "react";
import {
  MapPin,
  Sparkles,
  CheckCircle2,
  Clock,
  Compass,
  ArrowRight,
  ShieldAlert,
  Building2,
  BookOpen,
  Home,
  Laptop,
  Check,
  Settings2,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useUserProfile } from "@/context/user-profile-context";
import type { ContextualLocationRule } from "@/types/profile";

export function LocationGeofenceSimulator() {
  const { personaMeta, profile, openOnboarding } = useUserProfile();
  const rules = personaMeta.locationRules || [];

  const [selectedLocation, setSelectedLocation] = useState<ContextualLocationRule>(rules[0] || {
    location: "Tech Campus Desk",
    primaryAction: "Work session",
    associatedTasks: [],
  });
  const [activeAlert, setActiveAlert] = useState<boolean>(false);
  const [completedTasks, setCompletedTasks] = useState<Record<string, boolean>>({});
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Automatically update selected location when persona changes
  useEffect(() => {
    if (rules.length > 0) {
      setSelectedLocation(rules[0]);
      setActiveAlert(false);
      setStatusMessage(null);
    }
  }, [personaMeta.id]);

  const handleSimulateMovement = (action: "arriving" | "departing") => {
    setActiveAlert(true);
    const verb = action === "departing" ? "Leaving" : "Arriving at";
    setStatusMessage(`📍 Location Trigger: ${verb} ${selectedLocation.location}. Evaluating contextual association rules for ${profile.name}...`);
  };

  const toggleTask = (taskTitle: string) => {
    setCompletedTasks((prev) => ({
      ...prev,
      [taskTitle]: !prev[taskTitle],
    }));
  };

  return (
    <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-sky-400 via-teal-400 to-indigo-500 opacity-60" />
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase text-chart-1 border-chart-1/30">
                Proactive Context
              </Badge>
              <Badge variant="outline" className="text-[10px] font-mono text-indigo-600 dark:text-indigo-400 border-indigo-500/30">
                Calibrated: {personaMeta.title.split("/")[0].trim()}
              </Badge>
            </div>
            <CardTitle className="text-xl font-semibold tracking-tight mt-1 flex items-center gap-2">
              <Compass className="h-5 w-5 text-chart-1" />
              Contextual Task Suggestions
            </CardTitle>
            <CardDescription className="text-xs">
              Anticipates forgotten tasks and errands when transitioning between physical or digital environments for {profile.name}.
            </CardDescription>
          </div>

          <button
            type="button"
            onClick={openOnboarding}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-border/70 hover:bg-muted text-[11px] font-semibold text-muted-foreground hover:text-foreground transition-colors self-start sm:self-auto"
            title="Switch persona to see role-specific location rules"
          >
            <Settings2 className="h-3 w-3 text-indigo-500" />
            <span>Customize</span>
          </button>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Environment selector */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
            <MapPin className="h-3.5 w-3.5 text-primary" />
            Select Current Simulated Environment:
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {rules.map((rule) => {
              const active = selectedLocation.location === rule.location;
              return (
                <button
                  key={rule.location}
                  type="button"
                  onClick={() => {
                    setSelectedLocation(rule);
                    setActiveAlert(false);
                    setStatusMessage(null);
                  }}
                  className={`p-3 text-left rounded-xl border text-xs transition-all duration-200 ${
                    active
                      ? "border-primary bg-primary/10 font-semibold shadow-xs text-foreground"
                      : "border-border/80 bg-muted/40 hover:bg-muted text-muted-foreground"
                  }`}
                >
                  <div className="flex items-center gap-1.5">
                    <Building2 className={`h-3.5 w-3.5 ${active ? "text-primary" : "text-muted-foreground"}`} />
                    <span className="truncate">{rule.location}</span>
                  </div>
                  <p className="text-[10px] font-normal text-muted-foreground mt-1 truncate">
                    {rule.primaryAction}
                  </p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Triggers */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <Button
            size="sm"
            variant="outline"
            className="text-xs gap-1.5 border-chart-1/30 hover:bg-chart-1/10 hover:text-chart-1 rounded-xl"
            onClick={() => handleSimulateMovement("arriving")}
          >
            <Compass className="h-3.5 w-3.5 text-chart-1" />
            Simulate Arriving Here
          </Button>
          <Button
            size="sm"
            className="text-xs gap-1.5 bg-chart-1 hover:bg-chart-1/90 text-white rounded-xl shadow-xs"
            onClick={() => handleSimulateMovement("departing")}
          >
            <Sparkles className="h-3.5 w-3.5 fill-current" />
            Simulate Departing (Trigger &quot;One More Thing&quot;)
          </Button>
        </div>

        {/* Active Geofence Alert Banner */}
        {activeAlert && (
          <div className="p-4 rounded-2xl border border-chart-1/40 bg-gradient-to-r from-chart-1/10 via-card to-card space-y-3 animate-slide-up shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <Badge className="bg-chart-1 text-white text-[10px] uppercase font-mono tracking-wider">
                  📍 Context Alert: Departure Imminent
                </Badge>
                <h4 className="text-sm font-semibold text-foreground">
                  Before you leave {selectedLocation.location}... Did you forget these, {profile.name}?
                </h4>
                <p className="text-xs text-muted-foreground">
                  ContextIQ association engine detected high task abandonment risk for your active role ({personaMeta.title.split("/")[0].trim()}).
                </p>
              </div>

              <Button
                variant="ghost"
                size="sm"
                className="text-xs h-7 text-muted-foreground"
                onClick={() => setActiveAlert(false)}
              >
                Dismiss
              </Button>
            </div>

            <div className="space-y-2 pt-1">
              {selectedLocation.associatedTasks.map((task) => {
                const isDone = completedTasks[task.title];
                return (
                  <div
                    key={task.title}
                    className={`flex items-center justify-between p-2.5 rounded-xl border text-xs transition-all ${
                      isDone
                        ? "bg-risk-low/10 border-risk-low/30 text-muted-foreground line-through"
                        : "bg-background/80 border-border/80 text-foreground hover:border-chart-1/40"
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate">
                      <Button
                        size="sm"
                        variant={isDone ? "default" : "outline"}
                        className={`h-6 w-6 p-0 rounded-full shrink-0 ${
                          isDone ? "bg-risk-low text-white" : ""
                        }`}
                        onClick={() => toggleTask(task.title)}
                      >
                        {isDone ? <Check className="h-3 w-3" /> : <div className="h-2 w-2 rounded-full border border-muted-foreground" />}
                      </Button>
                      <span className="font-medium truncate">{task.title}</span>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant="outline" className="text-[10px] font-mono">
                        {task.category}
                      </Badge>
                      <Badge className="bg-chart-1/20 text-chart-1 border-chart-1/30 text-[10px] font-mono">
                        {Math.round(task.confidence * 100)}% match
                      </Badge>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
