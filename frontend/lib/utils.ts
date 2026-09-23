import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format minutes as "1h 24m" / "45m" for compact display. */
export function formatMinutes(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours <= 0) return `${minutes}m`;
  if (minutes === 0) return `${hours}h`;
  return `${hours}h ${minutes}m`;
}

/** Format a delta with an explicit sign, e.g. +6 / -3 / 0. */
export function formatDelta(value: number): string {
  if (value > 0) return `+${value}`;
  return `${value}`;
}

export function riskLevelFromScore(score: number): "LOW" | "MEDIUM" | "HIGH" {
  if (score >= 70) return "HIGH";
  if (score >= 40) return "MEDIUM";
  return "LOW";
}
