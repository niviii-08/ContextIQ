export type RolePersona =
  | "developer"
  | "student"
  | "manager"
  | "researcher"
  | "creator";

export type LanguageCode = "en" | "es" | "hi" | "de" | "fr" | "ta";

export type DistractionType =
  | "phone"
  | "slack"
  | "meetings"
  | "in_person"
  | "tab_overload"
  | "noise";

export type FocusRhythm = "morning" | "afternoon" | "night" | "flexible";

export interface ContextualTaskSuggestion {
  title: string;
  confidence: number;
  category: string;
}

export interface ContextualLocationRule {
  location: string;
  primaryAction: string;
  associatedTasks: ContextualTaskSuggestion[];
}

export interface UserCognitiveProfile {
  name: string;
  email?: string;
  customTitle?: string;
  organization?: string;
  role: RolePersona;
  language: LanguageCode;
  distractions: DistractionType[];
  focusRhythm: FocusRhythm;
  dailyGoalMinutes: number;
  onboardingCompleted: boolean;
  isAuthenticated: boolean;
  dailyRoutine?: string;
  dailyChores?: string[];
  weekendChores?: string[];
  frequentForgetItems?: string[];
  timeDelayTriggers?: string[];
  primaryOccupation?: string;
}

export interface PersonaMetadata {
  id: RolePersona;
  title: string;
  tagline: string;
  iconName: string;
  defaultPresets: { title: string; duration: string; type: string }[];
  reentryAnchorTemplate: string;
  baselineFrictionTolerance: string;
  locationRules: ContextualLocationRule[];
}

export interface LanguageMetadata {
  code: LanguageCode;
  name: string;
  nativeName: string;
  flag: string;
}
