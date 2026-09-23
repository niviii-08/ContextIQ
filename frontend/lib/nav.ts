import type { LucideIcon } from "lucide-react";
import {
  LayoutDashboard,
  ListChecks,
  Radar,
  Lightbulb,
  Sparkles,
  BrainCircuit,
} from "lucide-react";

export interface NavItem {
  href: string;
  label: string;
  icon: LucideIcon;
  description: string;
}

export const navItems: NavItem[] = [
  {
    href: "/",
    label: "Dashboard",
    icon: LayoutDashboard,
    description: "Today's behaviour overview",
  },
  {
    href: "/tasks",
    label: "Tasks",
    icon: ListChecks,
    description: "Create, track, and resolve tasks",
  },
  {
    href: "/context",
    label: "Context Intelligence",
    icon: Radar,
    description: "Focus, interruptions, and switching",
  },
  {
    href: "/predictions",
    label: "Predictions",
    icon: BrainCircuit,
    description: "Forgetting risk, explained",
  },
  {
    href: "/recommendations",
    label: "Recommendations",
    icon: Sparkles,
    description: "Contextual suggestions",
  },
  {
    href: "/insights",
    label: "Behaviour Insights",
    icon: Lightbulb,
    description: "Patterns in how you work",
  },
];
