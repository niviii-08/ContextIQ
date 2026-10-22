"use client";

import { useCallback, useEffect, useState } from "react";
import {
    Activity,
    AlertTriangle,
    ArrowDownRight,
    ArrowUpRight,
    BarChart3,
    Calendar,
    CheckCircle2,
    Clock3,
    Info,
    Layers3,
    RefreshCw,
    RotateCcw,
    Settings2,
    Shuffle,
    TimerReset,
    Zap,
} from "lucide-react";
import {
    Area,
    AreaChart,
    CartesianGrid,
    Label,
    ReferenceLine,
    ResponsiveContainer,
    Tooltip as RechartsTooltip,
    XAxis,
    YAxis,
} from "recharts";
import { analyticsApi } from "@/lib/api/services/analytics";
import type { AllInsights, DerivedMetrics, HeatmapData, Insight, StoryAnalytics, TimelineEntry, TrendAnalysis } from "@/lib/api/services/analytics";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState, ErrorState } from "@/components/shared/async-states";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { LiveSimulationPanel } from "@/components/dashboard/live-simulation-panel";
import { LiveFocusTracker } from "@/components/dashboard/live-focus-tracker";
import { LocationGeofenceSimulator } from "@/components/dashboard/location-geofence-simulator";
import { AskContextIQDrawer } from "@/components/dashboard/ask-contextiq-drawer";
import { GamificationBadges } from "@/components/dashboard/gamification-badges";
import { useUserProfile } from "@/context/user-profile-context";

interface EnhancedDashboardProps { userId: string; periodDays?: number; }
const integerFormat = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const format = (value: number, digits = 1) => new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value);

export function EnhancedDashboard({ userId, periodDays = 30 }: EnhancedDashboardProps) {
    const [metrics, setMetrics] = useState<DerivedMetrics | null>(null);
    const [insights, setInsights] = useState<AllInsights | null>(null);
    const [story, setStory] = useState<StoryAnalytics | null>(null);
    const [frictionTrend, setFrictionTrend] = useState<TrendAnalysis | null>(null);
    const [forgettingTrend, setForgettingTrend] = useState<TrendAnalysis | null>(null);
    const [timeline, setTimeline] = useState<TimelineEntry[] | null>(null);
    const [heatmap, setHeatmap] = useState<HeatmapData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { profile, personaMeta, openOnboarding, t } = useUserProfile();
    const [currentHour, setCurrentHour] = useState(12);

    useEffect(() => {
        setCurrentHour(new Date().getHours());
    }, []);

    const greetingTime = currentHour < 12 ? t("goodMorning") : currentHour < 17 ? t("goodAfternoon") : t("goodEvening");

    const loadAnalytics = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [metricResult, insightResult, storyResult, frictionResult, forgettingResult, timelineResult, heatmapResult] = await Promise.all([
                analyticsApi.getDerivedMetrics(userId, periodDays),
                analyticsApi.getAllInsights(userId, periodDays),
                analyticsApi.getStoryAnalytics(userId, periodDays),
                analyticsApi.getTrendAnalysis(userId, "behavioral_friction_score", periodDays),
                analyticsApi.getTrendAnalysis(userId, "forgetting_rate", periodDays),
                analyticsApi.getContextSwitchTimeline(userId, periodDays),
                analyticsApi.getTaskContextHeatmap(userId, periodDays),
            ]);
            if (metricResult.error || !metricResult.data) throw new Error(metricResult.error?.message ?? "Metrics are unavailable.");
            setMetrics(metricResult.data);
            setInsights(insightResult.data);
            setStory(storyResult.data);
            setFrictionTrend(frictionResult.data);
            setForgettingTrend(forgettingResult.data);
            setTimeline(timelineResult.data);
            setHeatmap(heatmapResult.data);
        } catch (cause) {
            setError(cause instanceof Error ? cause.message : "Failed to load analytics data.");
        } finally {
            setLoading(false);
        }
    }, [periodDays, userId]);

    useEffect(() => {
        const timerId = window.setTimeout(() => { void loadAnalytics(); }, 0);
        return () => window.clearTimeout(timerId);
    }, [loadAnalytics]);
    if (loading) return <DashboardSkeleton />;
    if (error || !metrics) return <ErrorState message={error ?? "No behavioural metrics were returned."} onRetry={() => void loadAnalytics()} />;

    return (
        <TooltipProvider>
            <div className="space-y-6">
                {/* Executive Personalized Header */}
                <header className="flex flex-col justify-between gap-4 border-b border-border/70 pb-5 sm:flex-row sm:items-center">
                    <div>
                        <div className="flex items-center gap-2.5 flex-wrap">
                            <h1 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
                                {greetingTime}, {profile.name} 👋
                            </h1>
                            <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2.5 py-0.5 text-[11px] font-semibold text-indigo-700 border border-indigo-200/80 dark:bg-indigo-950/60 dark:text-indigo-300 dark:border-indigo-850">
                                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                                {personaMeta.title.split("/")[0].trim()} Mode
                            </span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 flex items-center gap-2 flex-wrap">
                            <span className="font-semibold text-foreground/80">{profile.customTitle || personaMeta.title}</span>
                            <span>•</span>
                            <span>{profile.organization || "Focus Mode"}</span>
                            <span>•</span>
                            <span className="text-indigo-600 dark:text-indigo-400 font-mono text-[11px] font-bold">
                                {profile.focusRhythm.toUpperCase()} PEAK
                            </span>
                        </p>
                    </div>

                    {/* Daily Target Progress & Quick Personalize */}
                    <div className="flex items-center gap-2.5 flex-wrap">
                        <div className="p-2.5 px-3.5 rounded-2xl glass-card border border-border/80 shadow-2xs space-y-1.5 min-w-[190px]">
                            <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold text-muted-foreground text-[11px] flex items-center gap-1.5">
                                    <span>🎯</span> {t("dailyGoal")}
                                </span>
                                <span className="font-mono font-bold text-foreground text-[11px]">
                                    45m / {profile.dailyGoalMinutes}m
                                </span>
                            </div>
                            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                                <div
                                    className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-sky-400 to-emerald-500 transition-all duration-700"
                                    style={{ width: `${Math.min(100, Math.round((45 / (profile.dailyGoalMinutes || 120)) * 100))}%` }}
                                />
                            </div>
                        </div>

                        <button
                            type="button"
                            onClick={openOnboarding}
                            className="flex items-center gap-1.5 px-3 py-2 rounded-xl border border-indigo-200/80 dark:border-indigo-900/60 bg-indigo-50/70 dark:bg-indigo-950/40 hover:bg-indigo-100/80 dark:hover:bg-indigo-900/50 transition-all text-xs font-semibold text-indigo-700 dark:text-indigo-300 shadow-2xs"
                            title="Customize your persona, daily focus goal, and language"
                        >
                            <Settings2 className="h-3.5 w-3.5 text-indigo-600 dark:text-indigo-400" />
                            <span className="hidden sm:inline">{t("personalizeBtn")}</span>
                        </button>

                        <Badge variant="outline" className="font-mono text-xs normal-case py-1.5 px-2.5 bg-card border-border/80 shadow-2xs">
                            Last {periodDays} Days
                        </Badge>
                    </div>
                </header>

                {/* 1. Core KPIs Strip (Immediate Above-the-Fold Vital Signs) */}
                <TopMetrics metrics={metrics} />

                {/* 2. Core Interactive Row: Focus & Lag Tracker + Top Friction Breakdown */}
                <div className="grid gap-4 lg:grid-cols-2">
                    <LiveFocusTracker onSessionRecorded={loadAnalytics} />
                    <FrictionSourcesCard metrics={metrics} />
                </div>

                {/* 3. Forgetting Risk Profile + Location Context Discovery */}
                <div className="grid gap-4 lg:grid-cols-2">
                    <ForgettingRiskCard metrics={metrics} />
                    <LocationGeofenceSimulator />
                </div>

                {/* 4. Trends Section */}
                <div className="space-y-3">
                    <div>
                        <h3 className="text-sm font-semibold text-foreground">Behavioral Trajectories</h3>
                        <p className="text-xs text-muted-foreground">Observed friction and risk direction across sample days.</p>
                    </div>
                    <div className="grid gap-4 lg:grid-cols-2">
                        <TrendSignalCard title="Cognitive Friction Trend" metric={metrics.behavioral_friction_score.friction_score} unit="score" trend={frictionTrend} tone="orange" />
                        <TrendSignalCard title="Forgetting Probability Trend" metric={metrics.forget_risk.forget_risk * 100} unit="% probability" trend={forgettingTrend} tone="red" />
                    </div>
                </div>

                {/* 5. Diagnostics: Timeline, Interruptions & Heatmap */}
                <div className="grid gap-4 lg:grid-cols-2">
                    <InterruptionAnalysisCard metrics={metrics} />
                    <RiskDistributionCard insights={insights?.insights ?? []} />
                    <ContextSwitchTimelineCard timeline={timeline} />
                    <TaskContextHeatmapCard heatmap={heatmap} />
                </div>

                {/* 6. What-If Scenario Sandbox & Cognitive Badges */}
                <div className="grid gap-4 lg:grid-cols-2">
                    <LiveSimulationPanel userId={userId} onEventSimulated={loadAnalytics} />
                    <GamificationBadges />
                </div>

                {/* 7. Conversational AI Assistant & Narrative Story */}
                <AskContextIQDrawer />
                {story ? <InsightArea story={story} insights={insights?.insights ?? []} /> : null}
            </div>
        </TooltipProvider>
    );
}

function SectionHeading({ id, eyebrow, title, description }: { id: string; eyebrow: string; title: string; description: string }) { return <div><p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p><h3 id={id} className="mt-1 text-lg font-semibold tracking-tight">{title}</h3><p className="mt-1 text-xs text-muted-foreground">{description}</p></div>; }
function MetricHelp({ label, description }: { label: string; description: string }) { return <Tooltip><TooltipTrigger asChild><button type="button" aria-label={`About ${label}`} className="rounded-full text-muted-foreground hover:text-foreground"><Info className="h-3.5 w-3.5" aria-hidden="true" /></button></TooltipTrigger><TooltipContent className="max-w-xs text-xs">{description}</TooltipContent></Tooltip>; }

function TopMetrics({ metrics }: { metrics: DerivedMetrics }) {
    const { profile, personaMeta } = useUserProfile();
    const friction = metrics.behavioral_friction_score.friction_score;
    const recoveryMin = metrics.recovery_time?.recovery_time_minutes ?? 7.4;
    const switches = metrics.context_switch_rate.context_switch_rate;
    const lostHours = metrics.time_lost_to_interruptions.time_lost_hours;
    const forgetRisk = metrics.forget_risk.forget_risk * 100;
    const roleShort = personaMeta.title.split("/")[0].trim();

    return (
        <div className="grid gap-3.5 sm:grid-cols-2 xl:grid-cols-5">
            {/* 1. Cognitive Friction */}
            <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
                <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-indigo-500 to-indigo-600 opacity-80 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-4.5">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                            Cognitive Friction
                        </span>
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border border-indigo-500/20">
                            <Activity className="h-3.5 w-3.5" />
                        </span>
                    </div>

                    <div className="mt-2.5 flex items-baseline gap-1.5">
                        <span className="font-mono text-3xl font-extrabold tracking-tight text-foreground tabular-nums">
                            {format(friction, 0)}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">/100</span>
                    </div>

                    {/* Mini SVG Sparkline Curve */}
                    <div className="mt-3 flex items-center justify-between">
                        <svg className="w-20 h-6 overflow-visible" viewBox="0 0 80 24">
                            <defs>
                                <linearGradient id="frictionGrad" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="0%" stopColor="#6366f1" stopOpacity="0.35" />
                                    <stop offset="100%" stopColor="#6366f1" stopOpacity="0.0" />
                                </linearGradient>
                            </defs>
                            <path d="M0,18 Q15,8 30,14 T60,6 T80,10 L80,24 L0,24 Z" fill="url(#frictionGrad)" />
                            <path d="M0,18 Q15,8 30,14 T60,6 T80,10" fill="none" stroke="#6366f1" strokeWidth="2" strokeLinecap="round" />
                            <circle cx="80" cy="10" r="3" fill="#6366f1" className="animate-pulse" />
                        </svg>
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold font-mono text-emerald-600 dark:text-emerald-400 border border-emerald-500/20" title={`Tolerance: ${personaMeta.baselineFrictionTolerance}`}>
                            ● {personaMeta.baselineFrictionTolerance.split(" ")[0]} Baseline
                        </span>
                    </div>
                </CardContent>
            </Card>

            {/* 2. Avg Micro-Delay */}
            <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
                <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-amber-500 to-amber-600 opacity-80 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-4.5">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                            Avg Micro-Delay
                        </span>
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                            <RotateCcw className="h-3.5 w-3.5" />
                        </span>
                    </div>

                    <div className="mt-2.5 flex items-baseline gap-1.5">
                        <span className="font-mono text-3xl font-extrabold tracking-tight text-amber-600 dark:text-amber-400 tabular-nums">
                            {format(recoveryMin, 1)}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">min</span>
                    </div>

                    {/* Resumption Lag Track */}
                    <div className="mt-3 space-y-1.5">
                        <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
                            <span>Resumption Lag</span>
                            <span className="text-amber-600 dark:text-amber-400 font-semibold">-42s vs {roleShort}</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                            <div className="h-full rounded-full bg-gradient-to-r from-amber-400 to-amber-600 transition-all duration-700" style={{ width: `${Math.min(100, (recoveryMin / 10) * 100)}%` }} />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* 3. Switch Frequency */}
            <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
                <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-sky-500 to-blue-600 opacity-80 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-4.5">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                            Switch Frequency
                        </span>
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20">
                            <Shuffle className="h-3.5 w-3.5" />
                        </span>
                    </div>

                    <div className="mt-2.5 flex items-baseline gap-1.5">
                        <span className="font-mono text-3xl font-extrabold tracking-tight text-sky-600 dark:text-sky-400 tabular-nums">
                            {format(switches, 1)}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">/hr</span>
                    </div>

                    {/* 5-Hour Rhythm Histogram */}
                    <div className="mt-3 flex items-end justify-between gap-1 h-6 pt-1">
                        {[40, 75, 55, 90, 60].map((h, i) => (
                            <div key={i} className="flex-1 bg-sky-100 dark:bg-sky-950/50 rounded-t h-full flex items-end overflow-hidden">
                                <div className="w-full bg-gradient-to-t from-sky-500 to-blue-600 rounded-t transition-all duration-500" style={{ height: `${h}%` }} />
                            </div>
                        ))}
                    </div>
                    <div className="mt-1 flex justify-between text-[10px] font-mono text-muted-foreground">
                        <span>Rhythm</span>
                        <span className="text-sky-600 dark:text-sky-400 font-semibold">{profile.focusRhythm.toUpperCase()} peak</span>
                    </div>
                </CardContent>
            </Card>

            {/* 4. Time Lost to Breaks */}
            <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
                <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-purple-500 to-indigo-600 opacity-80 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-4.5">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                            Time Lost to Breaks
                        </span>
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                            <Clock3 className="h-3.5 w-3.5" />
                        </span>
                    </div>

                    <div className="mt-2.5 flex items-baseline gap-1.5">
                        <span className="font-mono text-3xl font-extrabold tracking-tight text-purple-600 dark:text-purple-400 tabular-nums">
                            {format(lostHours, 1)}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">hrs</span>
                    </div>

                    <div className="mt-3 space-y-1.5">
                        <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
                            <span>Primary Shield</span>
                            <span className="text-purple-600 dark:text-purple-400 font-semibold truncate max-w-[120px]" title={profile.distractions.join(", ")}>
                                {profile.distractions[0]?.replace('_', ' ') || "Focus shield"}
                            </span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden flex">
                            <div className="bg-purple-500 h-full" style={{ width: "60%" }} title="Direct Interruption" />
                            <div className="bg-indigo-400 h-full" style={{ width: "40%" }} title="Switch Overhead" />
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* 5. Forgetting Probability */}
            <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
                <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-rose-500 to-red-600 opacity-80 group-hover:opacity-100 transition-opacity" />
                <CardContent className="p-4.5">
                    <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-muted-foreground group-hover:text-foreground transition-colors">
                            Forgetting Probability
                        </span>
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                            <AlertTriangle className="h-3.5 w-3.5" />
                        </span>
                    </div>

                    <div className="mt-2.5 flex items-baseline gap-1.5">
                        <span className="font-mono text-3xl font-extrabold tracking-tight text-rose-600 dark:text-rose-400 tabular-nums">
                            {format(forgetRisk, 0)}
                        </span>
                        <span className="text-xs font-medium text-muted-foreground">%</span>
                    </div>

                    {/* Gradient Risk Meter */}
                    <div className="mt-3 space-y-1.5">
                        <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
                            <span>Risk Prior</span>
                            <span className="text-rose-600 dark:text-rose-400 font-semibold">{roleShort} ML Model</span>
                        </div>
                        <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                            <div className="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-rose-500 transition-all duration-700" style={{ width: `${Math.min(100, Math.max(10, forgetRisk))}%` }} />
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

function TrendSignalCard({ title, metric, unit, trend, tone }: { title: string; metric: number; unit: string; trend: TrendAnalysis | null; tone: "orange" | "red" }) {
    const increasing = trend?.trend_direction === "INCREASING";
    return (
        <Card className="glass-card card-hover-lift group relative overflow-hidden transition-all duration-300 border-border/80">
            <div className={cn("absolute inset-x-0 top-0 h-[3px] opacity-70", tone === "red" ? "bg-gradient-to-r from-rose-500 to-red-600" : "bg-gradient-to-r from-amber-500 to-orange-500")} />
            <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <CardTitle>{title}</CardTitle>
                        <CardDescription>Observed trajectory over the active period</CardDescription>
                    </div>
                    <Badge variant={increasing ? "high" : trend ? "low" : "outline"} className="transition-all duration-200">
                        {trend?.trend_direction.toLowerCase() ?? "unavailable"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <div className="flex items-end justify-between gap-4">
                    <div>
                        <p className={cn("font-mono text-3xl font-semibold tabular-nums transition-transform duration-200 hover:scale-105", tone === "red" ? "text-risk-high" : "text-risk-medium")}>
                            {format(metric, 0)}
                            <span className="ml-1 text-xs font-normal text-muted-foreground">{unit}</span>
                        </p>
                        <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                            {trend ? (
                                <>
                                    {increasing ? (
                                        <ArrowUpRight className="h-3.5 w-3.5 text-risk-high transition-transform duration-200 hover:translate-y-[-2px]" aria-hidden="true" />
                                    ) : (
                                        <ArrowDownRight className="h-3.5 w-3.5 text-risk-low transition-transform duration-200 hover:translate-y-[2px]" aria-hidden="true" />
                                    )}
                                    {trend.confidence.toLowerCase()} confidence · n={integerFormat.format(trend.sample_size)}
                                </>
                            ) : (
                                "Trend endpoint unavailable"
                            )}
                        </p>
                    </div>
                    <div className="rounded-md bg-muted/60 px-3 py-2 text-right text-[11px] text-muted-foreground transition-colors hover:bg-muted">
                        <p className="font-mono uppercase tracking-wide">Signal quality</p>
                        <p className="mt-1 font-medium text-foreground">{trend ? trend.confidence.toLowerCase() : "unavailable"}</p>
                    </div>
                </div>
                {trend && (
                    <div className="mt-4 flex items-center justify-between border-t border-border pt-3 text-xs">
                        <span className="text-muted-foreground">Slope</span>
                        <span className="font-mono tabular-nums">{format(trend.slope)} · R² {format(trend.r_squared)}</span>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

function FrictionSourcesCard({ metrics }: { metrics: DerivedMetrics }) {
    const { profile } = useUserProfile();
    const primaryLabel = profile.distractions.length > 0
        ? profile.distractions.slice(0, 2).map((d: string) => d === 'phone' ? 'Phone Pings' : d === 'slack' ? 'Slack & Teams' : d === 'meetings' ? 'Meetings' : d === 'tab_overload' ? 'Browser Tabs' : d.replace('_', ' ')).join(' & ') + ' Disruptions'
        : "Phone & Slack Disruptions";

    const sources = [
        { label: primaryLabel, value: metrics.behavioral_friction_score.components.interruption_component, icon: Zap, color: "text-amber-500", bar: "from-amber-400 to-orange-500", tag: "Primary Drain" },
        { label: "External Context Switching", value: metrics.behavioral_friction_score.components.context_switch_component, icon: Shuffle, color: "text-sky-500", bar: "from-sky-400 to-blue-600", tag: "Focus Leak" },
        { label: "Working Memory Forgetting", value: metrics.behavioral_friction_score.components.forgetting_component, icon: AlertTriangle, color: "text-rose-500", bar: "from-rose-400 to-red-600", tag: "Task Drop" },
        { label: "Micro-Delay Resumption Lag", value: metrics.behavioral_friction_score.components.recovery_component, icon: RotateCcw, color: "text-indigo-500", bar: "from-indigo-400 to-purple-600", tag: "Mental Lag" },
    ];
    return (
        <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
            <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-indigo-500 via-sky-400 to-indigo-500 opacity-60" />
            <CardHeader className="p-5 pb-3">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="text-sm font-bold flex items-center gap-2 text-foreground">
                            <Layers3 className="h-4 w-4 text-indigo-500" />
                            Cognitive Friction Breakdown
                        </CardTitle>
                        <CardDescription className="text-xs text-muted-foreground mt-0.5">
                            Relative weights contributing to current focus disruption.
                        </CardDescription>
                    </div>
                    <Badge variant="outline" className="font-mono text-[10px] bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border-indigo-500/20">
                        Weighted Impact
                    </Badge>
                </div>
            </CardHeader>
            <CardContent className="p-5 pt-2 space-y-3.5">
                {[...sources].sort((a, b) => b.value - a.value).map((item) => {
                    const Icon = item.icon;
                    return (
                        <div key={item.label} className="group/row space-y-1.5">
                            <div className="flex items-center justify-between text-xs">
                                <span className="font-semibold text-foreground flex items-center gap-2">
                                    <Icon className={cn("h-3.5 w-3.5", item.color)} />
                                    {item.label}
                                </span>
                                <div className="flex items-center gap-2 font-mono">
                                    <span className="text-[10px] font-semibold text-muted-foreground bg-muted px-1.5 py-0.5 rounded border border-border/60">
                                        {item.tag}
                                    </span>
                                    <span className="font-bold text-foreground tabular-nums">
                                        {format(item.value, 0)}%
                                    </span>
                                </div>
                            </div>
                            <div className="h-2 overflow-hidden rounded-full bg-muted/80 border border-border/40">
                                <div
                                    className={cn("h-full rounded-full bg-gradient-to-r transition-all duration-700 ease-out shadow-xs", item.bar)}
                                    style={{ width: `${Math.min(100, Math.max(8, item.value))}%` }}
                                />
                            </div>
                        </div>
                    );
                })}
            </CardContent>
        </Card>
    );
}

function ForgettingRiskCard({ metrics }: { metrics: DerivedMetrics }) {
    const risk = metrics.forget_risk.forget_risk * 100;
    const rows = [
        ["Recent forgetting rate", `${format(metrics.forget_risk.components.recent_forgetting_rate * 100)}%`],
        ["Interruption density", `${format(metrics.forget_risk.components.interruption_density)}/hr`],
        ["Switch frequency", `${format(metrics.forget_risk.components.context_switch_frequency)}/session`],
        ["Deadline pressure", `${format(metrics.forget_risk.components.deadline_pressure_ratio * 100, 0)}%`],
    ];
    return (
        <Card className="card-hover-lift transition-all duration-300 hover:border-primary/40 animate-slide-up">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-risk-high animate-pulse" aria-hidden="true" />
                    Forgetting risk profile
                </CardTitle>
                <CardDescription>Observed factors behind the current probability</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="mb-5 flex items-center justify-between">
                    <div>
                        <p className="font-mono text-3xl font-semibold tabular-nums text-risk-high">
                            {format(risk, 0)}%
                        </p>
                        <p className="text-xs text-muted-foreground">current probability</p>
                    </div>
                    <Badge variant={risk >= 50 ? "high" : risk >= 30 ? "medium" : "low"} className="transition-all duration-200">
                        {risk >= 50 ? "high" : risk >= 30 ? "moderate" : "low"} risk
                    </Badge>
                </div>
                <div className="space-y-3">
                    {rows.map(([label, value]) => (
                        <div key={label} className="flex justify-between gap-3 text-xs transition-colors hover:text-foreground">
                            <span className="text-muted-foreground">{label}</span>
                            <span className="font-mono tabular-nums font-medium">{value}</span>
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

function InterruptionAnalysisCard({ metrics }: { metrics: DerivedMetrics }) {
    return (
        <Card className="card-hover-lift transition-all duration-300 hover:border-primary/40 animate-slide-up">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TimerReset className="h-4 w-4 text-chart-1 animate-spin-slow" aria-hidden="true" />
                    Interruption analysis
                </CardTitle>
                <CardDescription>Direct loss, switching overhead, and recovery</CardDescription>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-2 gap-3">
                    <MiniMeasure label="Direct time" value={`${format(metrics.time_lost_to_interruptions.interruption_hours)}h`} />
                    <MiniMeasure label="Switch overhead" value={`${format(metrics.time_lost_to_interruptions.switch_overhead_hours)}h`} />
                </div>
                <div className="mt-5 space-y-3 text-xs">
                    <Row label="Interruption rate" value={`${format(metrics.interruption_rate.interruption_rate)}/hr`} />
                    <Row label="Total interruptions" value={integerFormat.format(metrics.interruption_rate.total_interruptions)} />
                    <Row label="Resumption lag (Micro-delay)" value={`${format(metrics.recovery_time.recovery_time_minutes)} min`} />
                    <Row label="Recovery sample" value={integerFormat.format(metrics.recovery_time.sample_size)} />
                </div>
            </CardContent>
        </Card>
    );
}

function RiskDistributionCard({ insights }: { insights: Insight[] }) {
    const counts = ["HIGH", "MEDIUM", "LOW"].map((level) => ({
        level,
        count: insights.filter((insight) => insight.risk_level === level).length,
    }));
    const total = counts.reduce((sum, item) => sum + item.count, 0);
    if (!total) return <UnavailableVisual title="Risk distribution" description="No classified insights were returned for this period." />;
    return (
        <Card className="card-hover-lift transition-all duration-300 hover:border-primary/40 animate-slide-up">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-4 w-4 text-chart-4" aria-hidden="true" />
                    Risk distribution
                </CardTitle>
                <CardDescription>Classification of returned insights</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                {counts.map(({ level, count }) => (
                    <div key={level} className="group">
                        <div className="mb-1.5 flex justify-between text-xs">
                            <span className="font-medium text-foreground group-hover:text-primary transition-colors">{level.toLowerCase()}</span>
                            <span className="font-mono tabular-nums text-muted-foreground">{count} · {format((count / total) * 100, 0)}%</span>
                        </div>
                        <div className="h-2 overflow-hidden rounded-full bg-muted">
                            <div
                                className={cn(
                                    "h-full rounded-full transition-all duration-700 ease-out",
                                    level === "HIGH" ? "bg-risk-high" : level === "MEDIUM" ? "bg-risk-medium" : "bg-risk-low",
                                )}
                                style={{ width: `${(count / total) * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </CardContent>
        </Card>
    );
}

function ContextSwitchTimelineCard({ timeline }: { timeline: TimelineEntry[] | null }) {
    if (!timeline || timeline.length < 3) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Shuffle className="h-4 w-4 text-chart-3" aria-hidden="true" />
                        Context-switch timeline
                    </CardTitle>
                    <CardDescription>Timestamped context switches with interruption markers</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-start gap-2 text-xs text-muted-foreground">
                        <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                        <div>Insufficient data for this view — you need ≥ 3 events.</div>
                    </div>
                </CardContent>
            </Card>
        );
    }
    const chartData = timeline.map((entry, index) => {
        const d = new Date(entry.timestamp);
        const hh = d.getHours().toString().padStart(2, "0");
        const mm = d.getMinutes().toString().padStart(2, "0");
        return {
            time: `${hh}:${mm}`,
            value: index,
            locationLabel: entry.locationLabel ?? "—",
            taskTitle: entry.taskTitle,
            isInterruption: entry.isInterruption,
            fullTimestamp: entry.timestamp,
        };
    });
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Shuffle className="h-4 w-4 text-chart-3" aria-hidden="true" />
                    Context-switch timeline
                </CardTitle>
                <CardDescription>Timestamped context switches with interruption markers</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
                <div className="p-4" role="img" aria-label="Context switch timeline with interruption markers">
                    <div style={{ height: 220 }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={chartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="timelineGradient" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="var(--chart-3)" stopOpacity={0.18} />
                                        <stop offset="95%" stopColor="var(--chart-3)" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                                <XAxis
                                    dataKey="time"
                                    tick={{ fontSize: 11, fill: "var(--muted-foreground)" }}
                                    tickLine={false}
                                    axisLine={{ stroke: "var(--border)" }}
                                >
                                    <Label value="Timeline" position="insideBottom" offset={-4} style={{ fontSize: 10, fill: "var(--muted-foreground)" }} />
                                </XAxis>
                                <YAxis hide />
                                <RechartsTooltip
                                    contentStyle={{
                                        background: "var(--popover)",
                                        border: "1px solid var(--border)",
                                        borderRadius: 8,
                                        fontSize: 12,
                                    }}
                                    labelStyle={{ color: "var(--foreground)", fontWeight: 600 }}
                                    content={({ active, payload }) => {
                                        if (!active || !payload?.[0]) return null;
                                        const d = payload[0].payload as typeof chartData[number];
                                        return (
                                            <div
                                                style={{
                                                    background: "var(--popover)",
                                                    border: "1px solid var(--border)",
                                                    borderRadius: 8,
                                                    fontSize: 12,
                                                    padding: 8,
                                                }}
                                            >
                                                <div style={{ color: "var(--foreground)", fontWeight: 600 }}>{d.time}</div>
                                                {d.isInterruption && (
                                                    <div style={{ color: "var(--risk-high)", fontWeight: 700, marginTop: 4 }}>INTERRUPTION</div>
                                                )}
                                                <div style={{ color: "var(--muted-foreground)", marginTop: 4 }}>Task: {d.taskTitle}</div>
                                                <div style={{ color: "var(--muted-foreground)" }}>Location: {d.locationLabel}</div>
                                                <div style={{ color: "var(--muted-foreground)" }}>{d.fullTimestamp}</div>
                                            </div>
                                        );
                                    }}
                                />
                                <Area
                                    dataKey="value"
                                    type="monotone"
                                    stroke="var(--chart-3)"
                                    fill="var(--chart-3)"
                                    fillOpacity={0.18}
                                    isAnimationActive={false}
                                />
                                {chartData.map((entry, idx) =>
                                    entry.isInterruption ? (
                                        <ReferenceLine
                                            key={`ref-${idx}`}
                                            x={entry.time}
                                            stroke="var(--risk-high)"
                                            strokeDasharray="4 2"
                                            label={{ value: "!", fill: "var(--risk-high)", fontSize: 14, fontWeight: 700, position: "top" }}
                                        />
                                    ) : null
                                )}
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
}

function TaskContextHeatmapCard({ heatmap }: { heatmap: HeatmapData | null }) {
    if (!heatmap || !heatmap.rows.length) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-primary" aria-hidden="true" />
                        Task / context heatmap
                    </CardTitle>
                    <CardDescription>Task-by-context intensity grid</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-start gap-2 text-xs text-muted-foreground">
                        <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                        <div>Insufficient data for this view — you need ≥ 3 events.</div>
                    </div>
                </CardContent>
            </Card>
        );
    }
    const { rows, columns, cells, sampleSizes } = heatmap;
    let nonNullCount = 0;
    for (const row of cells) for (const v of row) if (v != null) nonNullCount++;
    if (nonNullCount < 3) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Calendar className="h-4 w-4 text-primary" aria-hidden="true" />
                        Task / context heatmap
                    </CardTitle>
                    <CardDescription>Task-by-context intensity grid</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-start gap-2 text-xs text-muted-foreground">
                        <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                        <div>Insufficient data for this view — you need ≥ 3 events.</div>
                    </div>
                </CardContent>
            </Card>
        );
    }
    const gridStyle = {
        display: "grid",
        gridTemplateColumns: `120px repeat(${columns.length}, minmax(40px, 1fr))`,
        gap: 4,
    } as const;
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-primary" aria-hidden="true" />
                    Task / context heatmap
                </CardTitle>
                <CardDescription>Task-by-context intensity grid</CardDescription>
            </CardHeader>
            <CardContent className="overflow-x-auto">
                <div style={gridStyle}>
                    <div />
                    {columns.map((col, c) => (
                        <div key={`col-${c}`} className="flex items-center justify-center text-[10px] font-mono text-muted-foreground text-center">
                            {col}
                        </div>
                    ))}
                    {rows.map((rowLabel, r) => (
                        <div className="contents" key={`row-${r}`}>
                            <div className="flex items-center justify-end pr-2 text-right text-xs text-muted-foreground">
                                {rowLabel}
                            </div>
                            {columns.map((_, c) => {
                                const v = cells[r][c];
                                const sample = sampleSizes[r][c];
                                const cellStyle: React.CSSProperties =
                                    v == null
                                        ? { background: "var(--muted)", opacity: 0.1 }
                                        : {
                                            background: `color-mix(in srgb, var(--primary) ${(v * 100).toFixed(0)}%, var(--muted) 60%)`,
                                            color: v > 0.55 ? "var(--primary-foreground)" : "var(--foreground)",
                                        };
                                return (
                                    <Tooltip key={`cell-${r}-${c}`}>
                                        <TooltipTrigger asChild>
                                            <div
                                                style={cellStyle}
                                                className="min-h-10 min-w-10 rounded-sm flex items-center justify-center text-xs font-mono tabular-nums"
                                            >
                                                {v == null ? "—" : `${(v * 100).toFixed(0)}%`}
                                            </div>
                                        </TooltipTrigger>
                                        <TooltipContent className="text-xs">
                                            <div>Row: {rows[r]}</div>
                                            <div>Col: {columns[c]}</div>
                                            {v == null ? (
                                                <div>No data</div>
                                            ) : (
                                                <>
                                                    <div>Value: {(v * 100).toFixed(0)}%</div>
                                                    <div>Sample: n={sample}</div>
                                                </>
                                            )}
                                        </TooltipContent>
                                    </Tooltip>
                                );
                            })}
                        </div>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}

function UnavailableVisual({ title, description }: { title: string; description: string }) { return <Card><CardHeader><CardTitle>{title}</CardTitle><CardDescription>Requested visual</CardDescription></CardHeader><CardContent><EmptyState title="Not available yet" description={description} /></CardContent></Card>; }

function InsightArea({ story, insights }: { story: StoryAnalytics; insights: Insight[] }) { const highRiskInsights = insights.filter((insight) => insight.risk_level === "HIGH"); return <section aria-labelledby="insights-heading"><SectionHeading id="insights-heading" eyebrow="Decision layer" title="What to do with the signal" description="Narrative context tied back to the returned evidence." /><div className="mt-4 grid gap-4 lg:grid-cols-3"><InsightBlock title="What changed?" icon={<RefreshCw className="h-4 w-4" />}><p>{story.narrative}</p>{story.key_behaviors.length > 0 && <ul className="mt-3 space-y-2">{story.key_behaviors.slice(0, 3).map((behavior) => <li key={behavior} className="flex gap-2"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" aria-hidden="true" />{behavior}</li>)}</ul>}</InsightBlock><InsightBlock title="Why does this matter?" icon={<AlertTriangle className="h-4 w-4 text-risk-high" />}><p>{highRiskInsights[0]?.message ?? story.risks[0] ?? "No high-risk insight was returned for this period."}</p></InsightBlock><InsightBlock title="What should I do next?" icon={<CheckCircle2 className="h-4 w-4 text-risk-low" />}><ul className="space-y-2">{(story.recommendations.length ? story.recommendations : ["Collect more observations before changing your routine."]).slice(0, 3).map((recommendation) => <li key={recommendation}>{recommendation}</li>)}</ul></InsightBlock></div><p className="mt-3 text-[11px] text-muted-foreground">Based on {integerFormat.format(story.data_traceability.tasks_count)} tasks, {integerFormat.format(story.data_traceability.sessions_count)} sessions, and {integerFormat.format(story.data_traceability.interruptions_count)} interruptions over {story.data_traceability.period_days} days.</p></section>; }
function InsightBlock({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) { return <Card><CardHeader className="pb-3"><CardTitle className="flex items-center gap-2">{icon}{title}</CardTitle></CardHeader><CardContent className="text-sm leading-6 text-muted-foreground">{children}</CardContent></Card>; }
function MiniMeasure({ label, value }: { label: string; value: string }) { return <div className="rounded-md bg-muted/60 p-3"><p className="font-mono text-xl font-semibold tabular-nums">{value}</p><p className="mt-1 text-[11px] text-muted-foreground">{label}</p></div>; }
function Row({ label, value }: { label: string; value: string }) { return <div className="flex items-center justify-between gap-3"><span className="text-muted-foreground">{label}</span><span className="font-medium tabular-nums">{value}</span></div>; }
function DashboardSkeleton() { return <div className="space-y-7" aria-label="Loading dashboard" aria-busy="true"><div className="space-y-2"><Skeleton className="h-3 w-32" /><Skeleton className="h-8 w-72" /><Skeleton className="h-4 w-full max-w-xl" /></div><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">{Array.from({ length: 5 }).map((_, index) => <Skeleton key={index} className="h-32" />)}</div><div className="grid gap-4 lg:grid-cols-2">{Array.from({ length: 6 }).map((_, index) => <Skeleton key={index} className="h-56" />)}</div></div>; }
