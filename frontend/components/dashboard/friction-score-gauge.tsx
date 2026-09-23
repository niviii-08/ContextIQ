"use client";

import { RadialBar, RadialBarChart, PolarAngleAxis } from "recharts";
import { cn } from "@/lib/utils";

function scoreColor(score: number): string {
  if (score >= 70) return "var(--risk-high)";
  if (score >= 40) return "var(--risk-medium)";
  return "var(--risk-low)";
}

function scoreLabel(score: number): string {
  if (score >= 70) return "High friction";
  if (score >= 40) return "Moderate friction";
  return "Low friction";
}

export function FrictionScoreGauge({ score }: { score: number }) {
  const color = scoreColor(score);
  const data = [{ name: "friction", value: score, fill: color }];

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-40 w-40">
        <RadialBarChart
          width={160}
          height={160}
          cx="50%"
          cy="50%"
          innerRadius={58}
          outerRadius={76}
          barSize={12}
          data={data}
          startAngle={90}
          endAngle={-270}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background={{ fill: "var(--muted)" }}
            dataKey="value"
            cornerRadius={8}
            angleAxisId={0}
            isAnimationActive={false}
          />
        </RadialBarChart>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-mono text-3xl font-semibold tabular-nums"
            style={{ color }}
          >
            {score}
          </span>
          <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
            / 100
          </span>
        </div>
      </div>
      <p className={cn("mt-2 text-sm font-medium")} style={{ color }}>
        {scoreLabel(score)}
      </p>
    </div>
  );
}
