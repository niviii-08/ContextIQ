"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import type {
  UserCognitiveProfile,
  RolePersona,
  LanguageCode,
  DistractionType,
  FocusRhythm,
  PersonaMetadata,
  LanguageMetadata,
  ContextualLocationRule,
} from "@/types/profile";

export const PERSONA_DEFINITIONS: Record<RolePersona, PersonaMetadata> = {
  developer: {
    id: "developer",
    title: "Software Engineer / Tech",
    tagline: "Minimizing logic-flush and syntax interruption lag",
    iconName: "Laptop",
    defaultPresets: [
      { title: "ML Code Implementation", duration: "45m", type: "Code" },
      { title: "System Architecture Refactor", duration: "30m", type: "Architecture" },
      { title: "Bug Triage & PR Review", duration: "20m", type: "Review" },
    ],
    reentryAnchorTemplate: "Inspect the last modified function signature or uncommitted Git diff.",
    baselineFrictionTolerance: "Sensitive (High penalty for logic interruptions)",
    locationRules: [
      {
        location: "Tech Campus Desk",
        primaryAction: "Pushing Code & Deployment Check",
        associatedTasks: [
          { title: "Push uncommitted Git feature branch to origin", confidence: 0.94, category: "Code" },
          { title: "Verify Docker container teardown & staging test results", confidence: 0.88, category: "DevOps" },
          { title: "Mute Slack #dev-alerts until tomorrow morning", confidence: 0.72, category: "Focus" },
        ],
      },
      {
        location: "Coworking Space / Cafe",
        primaryAction: "Transitioning to Public Network",
        associatedTasks: [
          { title: "Disconnect corporate staging VPN tunnel", confidence: 0.91, category: "Security" },
          { title: "Sync offline local notes and architecture scratchpad", confidence: 0.79, category: "Docs" },
        ],
      },
      {
        location: "Home Dev Setup",
        primaryAction: "Deep Evening Flow & Wrap-Up",
        associatedTasks: [
          { title: "Post standup async summary in Slack #engineering", confidence: 0.86, category: "Async" },
          { title: "Review assigned PR #412 before code freeze", confidence: 0.75, category: "Review" },
        ],
      },
      {
        location: "Conference Pod",
        primaryAction: "System Architecture Review",
        associatedTasks: [
          { title: "Export Miro architecture diagram to PDF", confidence: 0.89, category: "Design" },
          { title: "Log sprint retrospective blockers", confidence: 0.71, category: "Agile" },
        ],
      },
    ],
  },
  student: {
    id: "student",
    title: "Student & Academic",
    tagline: "Preventing concept decay and exam task abandonment",
    iconName: "GraduationCap",
    defaultPresets: [
      { title: "Exam Prep Sprint", duration: "45m", type: "Study" },
      { title: "Lab Manual Record", duration: "30m", type: "Lab" },
      { title: "Problem Set Solution", duration: "25m", type: "Practice" },
    ],
    reentryAnchorTemplate: "Re-read the previous heading and summary bullet point.",
    baselineFrictionTolerance: "Moderate (Recovers through structured notes)",
    locationRules: [
      {
        location: "CS Department",
        primaryAction: "Visiting Professor / Faculty Review",
        associatedTasks: [
          { title: "Submit Machine Learning Lab Record #4", confidence: 0.92, category: "Academic" },
          { title: "Collect Department Clearance & Advisor Signature", confidence: 0.84, category: "Admin" },
        ],
      },
      {
        location: "Central Library",
        primaryAction: "Study Sprint & Book Checkout",
        associatedTasks: [
          { title: "Renew IEEE Digital Library Access Card", confidence: 0.89, category: "Academic" },
          { title: "Return Distributed Systems Reference Handbook", confidence: 0.78, category: "Errand" },
        ],
      },
      {
        location: "Hardware / IoT Lab",
        primaryAction: "Component Checkout & Soldering",
        associatedTasks: [
          { title: "Log Component Requisition in Inventory Sheet", confidence: 0.93, category: "Lab" },
          { title: "Return Oscilloscope Probe Kit to Rack 4", confidence: 0.82, category: "Lab" },
        ],
      },
      {
        location: "Hostel / Dorm Desk",
        primaryAction: "Evening Study & Revision",
        associatedTasks: [
          { title: "Complete Anki spaced repetition flashcard deck", confidence: 0.87, category: "Revision" },
          { title: "Submit Distributed Systems Homework on Canvas", confidence: 0.91, category: "Deadline" },
        ],
      },
    ],
  },
  manager: {
    id: "manager",
    title: "Product & Operations Lead",
    tagline: "Managing high context-switching and rapid decision recovery",
    iconName: "Briefcase",
    defaultPresets: [
      { title: "Roadmap Strategy Doc", duration: "35m", type: "Strategy" },
      { title: "1-on-1 Feedback Sync Prep", duration: "20m", type: "Sync" },
      { title: "Cross-Functional Spec Review", duration: "25m", type: "Review" },
    ],
    reentryAnchorTemplate: "Review the last Slack thread reply or action-item bullet.",
    baselineFrictionTolerance: "Adaptive (High tolerance for meeting fragmentation)",
    locationRules: [
      {
        location: "Executive Boardroom",
        primaryAction: "Strategic Leadership Review",
        associatedTasks: [
          { title: "Circulate meeting action items to engineering leads", confidence: 0.95, category: "Strategy" },
          { title: "Unblock Q4 headcount budget authorization", confidence: 0.81, category: "Ops" },
        ],
      },
      {
        location: "Client HQ / Coffee Sync",
        primaryAction: "Partner Engagement Wrap-Up",
        associatedTasks: [
          { title: "Log client feedback takeaways into CRM notes", confidence: 0.89, category: "Client" },
          { title: "Trigger follow-up NDA & legal review email", confidence: 0.76, category: "Legal" },
        ],
      },
      {
        location: "Open Office Floor",
        primaryAction: "Team Sync & Triaging",
        associatedTasks: [
          { title: "Triage high-priority Slack unread threads", confidence: 0.88, category: "Communication" },
          { title: "Schedule 1-on-1 performance chats for tomorrow", confidence: 0.79, category: "People" },
        ],
      },
      {
        location: "Home Office",
        primaryAction: "End of Day Planning",
        associatedTasks: [
          { title: "Review tomorrow's calendar conflicts & focus blocks", confidence: 0.91, category: "Planning" },
          { title: "Approve expense reports & timeoff requests", confidence: 0.73, category: "Admin" },
        ],
      },
    ],
  },
  researcher: {
    id: "researcher",
    title: "Researcher & Data Scientist",
    tagline: "Deep literature retention and unbroken analytical modeling",
    iconName: "Brain",
    defaultPresets: [
      { title: "Paper Literature Review", duration: "40m", type: "Research" },
      { title: "Model Hyperparameter Tuning", duration: "35m", type: "Experiment" },
      { title: "Statistical Proof & Charts", duration: "30m", type: "Analysis" },
    ],
    reentryAnchorTemplate: "Examine the latest plotted distribution chart or Jupyter cell.",
    baselineFrictionTolerance: "High Precision (Context loss impacts experimental rigor)",
    locationRules: [
      {
        location: "HPC Cluster / DL Lab",
        primaryAction: "Model Training Checkpoint",
        associatedTasks: [
          { title: "Inspect GPU cluster loss curve & checkpoint weights", confidence: 0.96, category: "MLOps" },
          { title: "Log experiment hyperparameters in WandB dashboard", confidence: 0.89, category: "Experiment" },
        ],
      },
      {
        location: "Faculty Archives & Library",
        primaryAction: "Literature Review & Citations",
        associatedTasks: [
          { title: "Export Zotero BibTeX bibliography entries", confidence: 0.92, category: "Research" },
          { title: "Annotate peer review rebuttal comments for NeurIPS", confidence: 0.85, category: "Writing" },
        ],
      },
      {
        location: "Seminar Amphitheater",
        primaryAction: "Colloquium & Presentation",
        associatedTasks: [
          { title: "Export presentation slides to high-res PDF", confidence: 0.90, category: "Presentation" },
          { title: "Upload seminar recording to lab internal wiki", confidence: 0.74, category: "Knowledge" },
        ],
      },
      {
        location: "Home Workstation",
        primaryAction: "Async Paper Writing",
        associatedTasks: [
          { title: "Review arXiv daily digest submissions", confidence: 0.86, category: "Literature" },
          { title: "Format LaTeX table of statistical p-values", confidence: 0.81, category: "Drafting" },
        ],
      },
    ],
  },
  creator: {
    id: "creator",
    title: "Writer, Designer & Creator",
    tagline: "Protecting deep creative flow and narrative momentum",
    iconName: "Sparkles",
    defaultPresets: [
      { title: "Deep Writing Flow", duration: "45m", type: "Writing" },
      { title: "Design System Tokens", duration: "30m", type: "Design" },
      { title: "Editorial Polish & Revision", duration: "25m", type: "Editing" },
    ],
    reentryAnchorTemplate: "Read the last two written paragraphs aloud to catch the rhythm.",
    baselineFrictionTolerance: "Fragile (Creative flow breaks take longer to rekindle)",
    locationRules: [
      {
        location: "Creative Studio / Sound Booth",
        primaryAction: "Audio/Visual Asset Production",
        associatedTasks: [
          { title: "Backup raw multi-track audio to redundant SSD", confidence: 0.94, category: "Audio" },
          { title: "Export 4K master ProRes video cut to review drive", confidence: 0.88, category: "Video" },
        ],
      },
      {
        location: "Inspiration Cafe",
        primaryAction: "Brainstorming & Scripting",
        associatedTasks: [
          { title: "Sync Notion narrative outline & storyboard notes", confidence: 0.91, category: "Draft" },
          { title: "Curate moodboard visual references in Figma", confidence: 0.79, category: "Design" },
        ],
      },
      {
        location: "Editing Suite",
        primaryAction: "Post-Production Color & Audio",
        associatedTasks: [
          { title: "Render Davinci Resolve color grading timeline", confidence: 0.90, category: "Edit" },
          { title: "Clear scratch cache temp files to free disk space", confidence: 0.77, category: "Maintenance" },
        ],
      },
      {
        location: "Home Desk",
        primaryAction: "Community & Publishing",
        associatedTasks: [
          { title: "Schedule newsletter dispatch & YouTube premiere", confidence: 0.93, category: "Publishing" },
          { title: "Respond to community comments & Twitter thread", confidence: 0.82, category: "Community" },
        ],
      },
    ],
  },
};

export const AVAILABLE_LANGUAGES: LanguageMetadata[] = [
  { code: "en", name: "English", nativeName: "English", flag: "🇺🇸" },
  { code: "es", name: "Spanish", nativeName: "Español", flag: "🇪🇸" },
  { code: "hi", name: "Hindi", nativeName: "हिन्दी", flag: "🇮🇳" },
  { code: "de", name: "German", nativeName: "Deutsch", flag: "🇩🇪" },
  { code: "fr", name: "French", nativeName: "Français", flag: "🇫🇷" },
  { code: "ta", name: "Tamil", nativeName: "தமிழ்", flag: "🇮🇳" },
];

export const TRANSLATIONS: Record<LanguageCode, Record<string, string>> = {
  en: {
    overview: "Overview",
    liveTelemetry: "Live Telemetry",
    flowChronometer: "Cognitive Flow Chronometer",
    flowSubtitle: "Real-time attention tracking & mental resumption lag quantifier.",
    startFlow: "Start Flow",
    ready: "Ready",
    deepFlowActive: "Deep Flow Active",
    disruptionLogged: "Disruption Logged",
    lagStopwatchRunning: "Lag Stopwatch Running",
    measuringLag: "Measuring Mental Resumption Lag",
    disruptionInProgress: "Disruption in Progress",
    disruptionEnded: "Disruption Ended (Begin Lag Measurement)",
    backInFlow: "I Am Back in Flow (Record Micro-Delay)",
    markSessionDone: "Mark Session Done ✓",
    reentryAnchorTitle: "Cognitive Re-Entry Anchor:",
    taskAbandonmentRisk: "Task Abandonment Risk:",
    frictionBreakdown: "Cognitive Friction Breakdown",
    frictionSubtitle: "Relative weights contributing to current focus disruption.",
    askCopilot: "Ask ContextIQ",
    askSubtitle: "Ask questions about your focus patterns, micro-delays, and productivity bottlenecks.",
    profileTitle: "Cognitive Profile & Workflow Setup",
    profileSubtitle: "Personalize ContextIQ for your profession, language, and distraction triggers.",
    dailyGoal: "Daily Focus Goal",
    personalizeBtn: "Personalize Profile",
    goodMorning: "Good morning",
    goodAfternoon: "Good afternoon",
    goodEvening: "Good evening",
  },
  es: {
    overview: "Visión General",
    liveTelemetry: "Telemetría en Vivo",
    flowChronometer: "Cronómetro de Flujo Cognitivo",
    flowSubtitle: "Seguimiento de atención en tiempo real y cálculo de micro-retrasos.",
    startFlow: "Iniciar Enfoque",
    ready: "Listo",
    deepFlowActive: "Flujo Profundo Activo",
    disruptionLogged: "Interrupción Registrada",
    lagStopwatchRunning: "Cronómetro de Retraso Activo",
    measuringLag: "Midiendo Retraso de Reanudación Mental",
    disruptionInProgress: "Interrupción en Progreso",
    disruptionEnded: "Interrupción Finalizada (Iniciar Medición)",
    backInFlow: "He Vuelto al Flujo (Registrar Micro-Retraso)",
    markSessionDone: "Marcar Sesión Completada ✓",
    reentryAnchorTitle: "Ancla de Reinserción Cognitiva:",
    taskAbandonmentRisk: "Riesgo de Abandono de Tarea:",
    frictionBreakdown: "Desglose de Fricción Cognitiva",
    frictionSubtitle: "Pesos relativos que contribuyen a la dispersión de atención.",
    askCopilot: "Preguntar a ContextIQ",
    askSubtitle: "Haz preguntas sobre tus patrones de concentración y cuellos de botella.",
    profileTitle: "Perfil Cognitivo y Configuración",
    profileSubtitle: "Personaliza ContextIQ según tu profesión, idioma y distracciones.",
    dailyGoal: "Objetivo Diario de Enfoque",
    personalizeBtn: "Personalizar Perfil",
    goodMorning: "Buenos días",
    goodAfternoon: "Buenas tardes",
    goodEvening: "Buenas noches",
  },
  hi: {
    overview: "अवलोकन (Overview)",
    liveTelemetry: "लाइव टेलीमेट्री",
    flowChronometer: "संज्ञानात्मक प्रवाह क्रोनोमीटर (Flow Chronometer)",
    flowSubtitle: "रीयल-टाइम ध्यान ट्रैकिंग और रुकावट के बाद वापसी समय की गणना।",
    startFlow: "फोकस शुरू करें",
    ready: "तैयार",
    deepFlowActive: "गहन प्रवाह सक्रिय (Deep Flow)",
    disruptionLogged: "रुकावट दर्ज की गई",
    lagStopwatchRunning: "वापसी स्टॉपवॉच चालू है",
    measuringLag: "मानसिक वापसी में लगने वाला समय मापा जा रहा है",
    disruptionInProgress: "रुकावट जारी है",
    disruptionEnded: "रुकावट समाप्त (वापसी समय मापना शुरू करें)",
    backInFlow: "मैं वापस काम पर आ गया (माइक्रो-डिले दर्ज करें)",
    markSessionDone: "सत्र पूर्ण चिह्नित करें ✓",
    reentryAnchorTitle: "संज्ञानात्मक पुनःप्रवेश सहारा (Anchor):",
    taskAbandonmentRisk: "कार्य छूटने का जोखिम:",
    frictionBreakdown: "संज्ञानात्मक घर्षण विश्लेषण (Friction)",
    frictionSubtitle: "ध्यान भटकने में योगदान देने वाले प्रमुख कारण।",
    askCopilot: "ContextIQ से पूछें",
    askSubtitle: "अपनी उत्पादकता और ध्यान के पैटर्न के बारे में प्रश्न पूछें।",
    profileTitle: "संज्ञानात्मक प्रोफ़ाइल और कार्य सेटअप",
    profileSubtitle: "अपने कार्य, भाषा और ध्यान भटकाव के अनुसार ContextIQ को अनुकूलित करें।",
    dailyGoal: "दैनिक फोकस लक्ष्य",
    personalizeBtn: "प्रोफ़ाइल अनुकूलित करें",
    goodMorning: "शुभ प्रभात",
    goodAfternoon: "शुभ दोपहर",
    goodEvening: "शुभ संध्या",
  },
  de: {
    overview: "Übersicht",
    liveTelemetry: "Live-Telemetrie",
    flowChronometer: "Kognitiver Flow-Chronometer",
    flowSubtitle: "Echtzeit-Aufmerksamkeitsverfolgung und Messung von Verzögerungen.",
    startFlow: "Fokus Starten",
    ready: "Bereit",
    deepFlowActive: "Tiefer Flow Aktiv",
    disruptionLogged: "Unterbrechung Erfasst",
    lagStopwatchRunning: "Wiederaufnahmestoppuhr Läuft",
    measuringLag: "Wiederaufnahmeverzögerung Wird Gemessen",
    disruptionInProgress: "Unterbrechung Läuft",
    disruptionEnded: "Unterbrechung Beendet (Verzögerung Messen)",
    backInFlow: "Wieder im Flow (Mikroverzögerung Speichern)",
    markSessionDone: "Sitzung Beenden ✓",
    reentryAnchorTitle: "Kognitiver Wiedereinstiegsanker:",
    taskAbandonmentRisk: "Aufgabenabbruchsrisiko:",
    frictionBreakdown: "Kognitive Reibungsanalyse",
    frictionSubtitle: "Faktoren, die zur Aufmerksamkeitsstreuung beitragen.",
    askCopilot: "ContextIQ Fragen",
    askSubtitle: "Stellen Sie Fragen zu Ihren Fokusmustern und Verzögerungen.",
    profileTitle: "Kognitives Profil & Arbeits-Setup",
    profileSubtitle: "Personalisieren Sie ContextIQ für Ihren Beruf und Ihre Sprache.",
    dailyGoal: "Tägliches Fokus-Ziel",
    personalizeBtn: "Profil Anpassen",
    goodMorning: "Guten Morgen",
    goodAfternoon: "Guten Tag",
    goodEvening: "Guten Abend",
  },
  fr: {
    overview: "Aperçu",
    liveTelemetry: "Télémétrie en Direct",
    flowChronometer: "Chronomètre de Flux Cognitif",
    flowSubtitle: "Suivi de l'attention en temps réel et quantification du délai de reprise.",
    startFlow: "Démarrer le Focus",
    ready: "Prêt",
    deepFlowActive: "Flux Profond Actif",
    disruptionLogged: "Interruption Enregistrée",
    lagStopwatchRunning: "Chronomètre de Reprise en Cours",
    measuringLag: "Mesure du Délai de Réorientation Mentale",
    disruptionInProgress: "Interruption en Cours",
    disruptionEnded: "Interruption Terminée (Lancer la Mesure)",
    backInFlow: "De Retour dans le Flux (Enregistrer le Micro-Délai)",
    markSessionDone: "Session Terminée ✓",
    reentryAnchorTitle: "Ancre de Réinsertion Cognitive :",
    taskAbandonmentRisk: "Risque d'Abandon de Tâche :",
    frictionBreakdown: "Répartition des Frictions Cognitives",
    frictionSubtitle: "Poids relatifs contribuant à la dispersion de l'attention.",
    askCopilot: "Demander à ContextIQ",
    askSubtitle: "Posez des questions sur vos habitudes de concentration.",
    profileTitle: "Profil Cognitif & Configuration",
    profileSubtitle: "Personnalisez ContextIQ selon votre profession et votre langue.",
    dailyGoal: "Objectif de Focus Quotidien",
    personalizeBtn: "Personnaliser le Profil",
    goodMorning: "Bonjour",
    goodAfternoon: "Bon après-midi",
    goodEvening: "Bonsoir",
  },
  ta: {
    overview: "கண்ணோட்டம் (Overview)",
    liveTelemetry: "நேரலை டெலிமெட்ரி",
    flowChronometer: "கவனப் பாய்வு கடிகாரம் (Flow Chronometer)",
    flowSubtitle: "நிகழ்நேர கவன கண்காணிப்பு மற்றும் தடங்கலுக்குப் பின் தொடங்கும் நேர கணக்கீடு.",
    startFlow: "கவனத்தைத் தொடங்கு",
    ready: "தயார்",
    deepFlowActive: "ஆழ்ந்த கவனம் செயல்பாட்டில் உள்ளது",
    disruptionLogged: "தடங்கல் பதிவாகியது",
    lagStopwatchRunning: "மீண்டும் தொடங்கும் நேரம் கணக்கிடப்படுகிறது",
    measuringLag: "மனதில் கவனம் மீண்டும் குவியும் நேரம் அளவிடப்படுகிறது",
    disruptionInProgress: "தடங்கல் தொடர்கிறது",
    disruptionEnded: "தடங்கல் முடிந்தது (நேரத்தை அளவிடவும்)",
    backInFlow: "நான் மீண்டும் வேலையைத் தொடங்கினேன்",
    markSessionDone: "அமர்வை முடிக்கவும் ✓",
    reentryAnchorTitle: "மீண்டும் வேலை தொடங்குவதற்கான குறிப்பு:",
    taskAbandonmentRisk: "வேலை கைவிடப்படும் அபாயம்:",
    frictionBreakdown: "கவன இழப்பு பகுப்பாய்வு",
    frictionSubtitle: "கவனச்சிதறலுக்குக் காரணமான முக்கிய காரணிகள்.",
    askCopilot: "ContextIQ-விடம் கேளுங்கள்",
    askSubtitle: "உங்கள் உற்பத்தித்திறன் மற்றும் கவன முறைகள் பற்றி கேளுங்கள்.",
    profileTitle: "சுயவிவரம் & பணி அமைப்பு",
    profileSubtitle: "உங்கள் பணி, மொழி மற்றும் கவனச்சிதறல்களுக்கு ஏற்ப அமைத்திடுங்கள்.",
    dailyGoal: "தினசரி கவன இலக்கு",
    personalizeBtn: "சுயவிவரத்தை மாற்று",
    goodMorning: "காலை வணக்கம்",
    goodAfternoon: "மதிய வணக்கம்",
    goodEvening: "மாலை வணக்கம்",
  },
};

const DEFAULT_PROFILE: UserCognitiveProfile = {
  name: "Neevetha",
  email: "neevetha@contextiq.io",
  customTitle: "Senior Software Engineer",
  organization: "Distributed Systems & AI",
  role: "developer",
  language: "en",
  distractions: ["phone", "slack", "tab_overload"],
  focusRhythm: "morning",
  dailyGoalMinutes: 120,
  onboardingCompleted: true,
  isAuthenticated: true,
  dailyRoutine: "Morning deep work sprint 8 AM - 12 PM, review PRs, evening code sync",
  dailyChores: ["Vessel washing / Dishwashing", "Cooking & Meal Prep", "Sweeping & Mopping"],
  weekendChores: ["Dress washing / Laundry", "Deep room & workstation clean", "Grocery market run"],
  frequentForgetItems: ["Switching off geyser/stove", "Taking daily vitamins", "Pushing git branch before leaving"],
  timeDelayTriggers: ["Reels & Shorts doomscroll loops", "Post-lunch 2 PM slump", "Meeting-to-code context switches"],
  primaryOccupation: "Software Engineering & Distributed Systems",
};

interface UserProfileContextType {
  profile: UserCognitiveProfile;
  updateProfile: (updates: Partial<UserCognitiveProfile>) => void;
  setRole: (role: RolePersona) => void;
  setLanguage: (lang: LanguageCode) => void;
  login: (userData?: Partial<UserCognitiveProfile>) => void;
  logout: () => void;
  personaMeta: PersonaMetadata;
  t: (key: string) => string;
  isOnboardingOpen: boolean;
  setIsOnboardingOpen: (open: boolean) => void;
  openOnboarding: () => void;
  closeOnboarding: () => void;
}

const UserProfileContext = createContext<UserProfileContextType | null>(null);

export function UserProfileProvider({ children }: { children: React.ReactNode }) {
  const [profile, setProfile] = useState<UserCognitiveProfile>(DEFAULT_PROFILE);
  const [isOnboardingOpen, setIsOnboardingOpen] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    try {
      const saved = localStorage.getItem("contextiq_user_profile");
      if (saved) {
        const parsed = JSON.parse(saved);
        const resolved = { ...DEFAULT_PROFILE, ...parsed };
        setProfile(resolved);
      } else {
        localStorage.setItem("contextiq_user_profile", JSON.stringify(DEFAULT_PROFILE));
      }
    } catch {
      // fallback to default
    }
    setIsLoaded(true);
  }, []);

  const updateProfile = (updates: Partial<UserCognitiveProfile>) => {
    setProfile((prev) => {
      const next = { ...prev, ...updates };
      try {
        localStorage.setItem("contextiq_user_profile", JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
  };

  const setRole = (role: RolePersona) => updateProfile({ role });
  const setLanguage = (language: LanguageCode) => updateProfile({ language });

  const login = (userData?: Partial<UserCognitiveProfile>) => {
    updateProfile({
      ...userData,
      isAuthenticated: true,
    });
  };

  const logout = () => {
    updateProfile({
      isAuthenticated: false,
    });
  };

  const personaMeta = PERSONA_DEFINITIONS[profile.role] || PERSONA_DEFINITIONS.developer;

  const t = (key: string): string => {
    const langDict = TRANSLATIONS[profile.language] || TRANSLATIONS.en;
    return langDict[key] || TRANSLATIONS.en[key] || key;
  };

  const openOnboarding = () => setIsOnboardingOpen(true);
  const closeOnboarding = () => setIsOnboardingOpen(false);

  return (
    <UserProfileContext.Provider
      value={{
        profile,
        updateProfile,
        setRole,
        setLanguage,
        login,
        logout,
        personaMeta,
        t,
        isOnboardingOpen,
        setIsOnboardingOpen,
        openOnboarding,
        closeOnboarding,
      }}
    >
      {children}
    </UserProfileContext.Provider>
  );
}

export function useUserProfile() {
  const context = useContext(UserProfileContext);
  if (!context) {
    throw new Error("useUserProfile must be used within a UserProfileProvider");
  }
  return context;
}
