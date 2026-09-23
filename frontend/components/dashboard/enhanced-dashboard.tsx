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
    Shuffle,
    TimerReset,
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
            <div className="space-y-7">
                <section className="flex flex-col justify-between gap-4 border-b border-border pb-5 sm:flex-row sm:items-end" aria-labelledby="dashboard-heading">
                    <div>
                        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-primary">30-day operating view</p>
                        <h2 id="dashboard-heading" className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">Behavioural signal, in context</h2>
                        <p className="mt-2 max-w-2xl text-sm text-muted-foreground">A decision-support view of friction, memory risk, and the cost of interrupted work.</p>
                    </div>
                    <Badge variant="outline" className="w-fit gap-1.5 px-3 py-1 font-mono normal-case"><span className="h-1.5 w-1.5 rounded-full bg-risk-low" aria-hidden="true" />{periodDays}-day window</Badge>
                </section>
                <TopMetrics metrics={metrics} />
                <section aria-labelledby="signals-heading">
                    <SectionHeading id="signals-heading" eyebrow="Signal layer" title="What is moving" description="Direction and confidence are shown only where the analytics service provides them." />
                    <div className="mt-4 grid gap-4 lg:grid-cols-2"><TrendSignalCard title="Behavioural friction trend" metric={metrics.behavioral_friction_score.friction_score} unit="score" trend={frictionTrend} tone="orange" /><TrendSignalCard title="Forgetting risk trend" metric={metrics.forget_risk.forget_risk * 100} unit="% probability" trend={forgettingTrend} tone="red" /></div>
                </section>
                <section aria-labelledby="diagnostics-heading">
                    <SectionHeading id="diagnostics-heading" eyebrow="Diagnostic layer" title="Where attention is being lost" description="Current-period measurements, component breakdowns, and data availability." />
                    <div className="mt-4 grid gap-4 lg:grid-cols-2"><FrictionSourcesCard metrics={metrics} /><ForgettingRiskCard metrics={metrics} /><InterruptionAnalysisCard metrics={metrics} /><RiskDistributionCard insights={insights?.insights ?? []} /><ContextSwitchTimelineCard timeline={timeline} /><TaskContextHeatmapCard heatmap={heatmap} /></div>
                </section>
                {story ? <InsightArea story={story} insights={insights?.insights ?? []} /> : <EmptyState title="No narrative insights yet" description="The analytics service did not return a story for this period." />}
            </div>
        </TooltipProvider>
    );
}

function SectionHeading({ id, eyebrow, title, description }: { id: string; eyebrow: string; title: string; description: string }) { return <div><p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">{eyebrow}</p><h3 id={id} className="mt-1 text-lg font-semibold tracking-tight">{title}</h3><p className="mt-1 text-xs text-muted-foreground">{description}</p></div>; }
function MetricHelp({ label, description }: { label: string; description: string }) { return <Tooltip><TooltipTrigger asChild><button type="button" aria-label={`About ${label}`} className="rounded-full text-muted-foreground hover:text-foreground"><Info className="h-3.5 w-3.5" aria-hidden="true" /></button></TooltipTrigger><TooltipContent className="max-w-xs text-xs">{description}</TooltipContent></Tooltip>; }

function TopMetrics({ metrics }: { metrics: DerivedMetrics }) {
    const items = [
        { label: "Behavioural friction", value: format(metrics.behavioral_friction_score.friction_score, 0), suffix: "/100", icon: Activity, tone: "text-risk-medium", help: "Composite score of forgetting, interruptions, context switching, and recovery cost." },
        { label: "Forgetting risk", value: format(metrics.forget_risk.forget_risk * 100, 0), suffix: "%", icon: AlertTriangle, tone: "text-risk-high", help: "Estimated probability of forgetting based on observed patterns in this period." },
        { label: "Context switch rate", value: format(metrics.context_switch_rate.context_switch_rate), suffix: "/hr", icon: Shuffle, tone: "text-chart-4", help: "Average number of context changes per active hour." },
        { label: "Interruption cost", value: `${format(metrics.time_lost_to_interruptions.time_lost_hours)}h`, suffix: "", icon: Clock3, tone: "text-chart-1", help: "Direct interruption time plus estimated switch-overhead time." },
        { label: "Completion reliability", value: format(metrics.completion_reliability.completion_reliability * 100, 0), suffix: "%", icon: CheckCircle2, tone: "text-risk-low", help: "Consistency of daily completion rate across the sample days." },
    ];
    return <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">{items.map(({ label, value, suffix, icon: Icon, tone, help }) => <Card key={label}><CardContent className="p-4"><div className="flex items-center justify-between gap-2"><span className="text-xs font-medium text-muted-foreground">{label}</span><div className="flex items-center gap-2"><MetricHelp label={label} description={help} /><Icon className={cn("h-4 w-4", tone)} aria-hidden="true" /></div></div><p className={cn("mt-3 font-mono text-2xl font-semibold tabular-nums", tone)}>{value}<span className="ml-1 text-xs font-normal text-muted-foreground">{suffix}</span></p><p className="mt-1 text-[11px] text-muted-foreground">Current period</p></CardContent></Card>)}</div>;
}

function TrendSignalCard({ title, metric, unit, trend, tone }: { title: string; metric: number; unit: string; trend: TrendAnalysis | null; tone: "orange" | "red" }) {
    const increasing = trend?.trend_direction === "INCREASING";
    return <Card><CardHeader className="pb-3"><div className="flex items-start justify-between gap-4"><div><CardTitle>{title}</CardTitle><CardDescription>API-derived direction, not a fabricated time series</CardDescription></div><Badge variant={increasing ? "high" : trend ? "low" : "outline"}>{trend?.trend_direction.toLowerCase() ?? "unavailable"}</Badge></div></CardHeader><CardContent><div className="flex items-end justify-between gap-4"><div><p className={cn("font-mono text-3xl font-semibold tabular-nums", tone === "red" ? "text-risk-high" : "text-risk-medium")}>{format(metric, 0)}<span className="ml-1 text-xs font-normal text-muted-foreground">{unit}</span></p><p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">{trend ? <>{increasing ? <ArrowUpRight className="h-3.5 w-3.5" aria-hidden="true" /> : <ArrowDownRight className="h-3.5 w-3.5" aria-hidden="true" />} {trend.confidence.toLowerCase()} confidence · n={integerFormat.format(trend.sample_size)}</> : "Trend endpoint unavailable"}</p></div><div className="rounded-md bg-muted/60 px-3 py-2 text-right text-[11px] text-muted-foreground"><p className="font-mono uppercase tracking-wide">Signal quality</p><p className="mt-1 font-medium text-foreground">{trend ? trend.confidence.toLowerCase() : "unavailable"}</p></div></div>{trend && <div className="mt-4 flex items-center justify-between border-t border-border pt-3 text-xs"><span className="text-muted-foreground">Slope</span><span className="font-mono tabular-nums">{format(trend.slope)} · R² {format(trend.r_squared)}</span></div>}</CardContent></Card>;
}

function FrictionSourcesCard({ metrics }: { metrics: DerivedMetrics }) { const sources = [["Interruptions", metrics.behavioral_friction_score.components.interruption_component], ["Forgetting", metrics.behavioral_friction_score.components.forgetting_component], ["Context switching", metrics.behavioral_friction_score.components.context_switch_component], ["Recovery", metrics.behavioral_friction_score.components.recovery_component]] as const; return <Card><CardHeader><CardTitle className="flex items-center gap-2"><Layers3 className="h-4 w-4 text-primary" aria-hidden="true" />Top friction sources</CardTitle><CardDescription>Contributors to the current composite score</CardDescription></CardHeader><CardContent className="space-y-4">{[...sources].sort((a, b) => b[1] - a[1]).map(([label, value]) => <div key={label}><div className="mb-1.5 flex justify-between text-xs"><span>{label}</span><span className="font-mono tabular-nums text-muted-foreground">{format(value, 0)}</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, Math.max(0, value))}%` }} /></div></div>)}</CardContent></Card>; }
function ForgettingRiskCard({ metrics }: { metrics: DerivedMetrics }) { const risk = metrics.forget_risk.forget_risk * 100; const rows = [["Recent forgetting rate", `${format(metrics.forget_risk.components.recent_forgetting_rate * 100)}%`], ["Interruption density", `${format(metrics.forget_risk.components.interruption_density)}/hr`], ["Switch frequency", `${format(metrics.forget_risk.components.context_switch_frequency)}/session`], ["Deadline pressure", `${format(metrics.forget_risk.components.deadline_pressure_ratio * 100, 0)}%`]]; return <Card><CardHeader><CardTitle>Forgetting risk profile</CardTitle><CardDescription>Observed factors behind the current probability</CardDescription></CardHeader><CardContent><div className="mb-5 flex items-center justify-between"><div><p className="font-mono text-3xl font-semibold tabular-nums text-risk-high">{format(risk, 0)}%</p><p className="text-xs text-muted-foreground">current probability</p></div><Badge variant={risk >= 50 ? "high" : risk >= 30 ? "medium" : "low"}>{risk >= 50 ? "high" : risk >= 30 ? "moderate" : "low"} risk</Badge></div><div className="space-y-3">{rows.map(([label, value]) => <div key={label} className="flex justify-between gap-3 text-xs"><span className="text-muted-foreground">{label}</span><span className="font-mono tabular-nums">{value}</span></div>)}</div></CardContent></Card>; }
function InterruptionAnalysisCard({ metrics }: { metrics: DerivedMetrics }) { return <Card><CardHeader><CardTitle className="flex items-center gap-2"><TimerReset className="h-4 w-4 text-chart-1" aria-hidden="true" />Interruption analysis</CardTitle><CardDescription>Direct loss, switching overhead, and recovery</CardDescription></CardHeader><CardContent><div className="grid grid-cols-2 gap-3"><MiniMeasure label="Direct time" value={`${format(metrics.time_lost_to_interruptions.interruption_hours)}h`} /><MiniMeasure label="Switch overhead" value={`${format(metrics.time_lost_to_interruptions.switch_overhead_hours)}h`} /></div><div className="mt-5 space-y-3 text-xs"><Row label="Interruption rate" value={`${format(metrics.interruption_rate.interruption_rate)}/hr`} /><Row label="Total interruptions" value={integerFormat.format(metrics.interruption_rate.total_interruptions)} /><Row label="Recovery time" value={`${format(metrics.recovery_time.recovery_time_minutes)} min`} /><Row label="Recovery sample" value={integerFormat.format(metrics.recovery_time.sample_size)} /></div></CardContent></Card>; }
function RiskDistributionCard({ insights }: { insights: Insight[] }) { const counts = ["HIGH", "MEDIUM", "LOW"].map((level) => ({ level, count: insights.filter((insight) => insight.risk_level === level).length })); const total = counts.reduce((sum, item) => sum + item.count, 0); if (!total) return <UnavailableVisual title="Risk distribution" description="No classified insights were returned for this period." />; return <Card><CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-4 w-4 text-chart-4" aria-hidden="true" />Risk distribution</CardTitle><CardDescription>Classification of returned insights</CardDescription></CardHeader><CardContent className="space-y-4">{counts.map(({ level, count }) => <div key={level}><div className="mb-1.5 flex justify-between text-xs"><span>{level.toLowerCase()}</span><span className="font-mono tabular-nums">{count} · {format(count / total * 100, 0)}%</span></div><div className="h-2 overflow-hidden rounded-full bg-muted"><div className={cn("h-full rounded-full", level === "HIGH" ? "bg-risk-high" : level === "MEDIUM" ? "bg-risk-medium" : "bg-risk-low")} style={{ width: `${count / total * 100}%` }} /></div></div>)}</CardContent></Card>; }

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
