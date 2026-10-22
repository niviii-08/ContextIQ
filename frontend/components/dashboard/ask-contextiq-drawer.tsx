"use client";

import { useState, useEffect } from "react";
import {
  MessageSquare,
  Bot,
  Send,
  Sparkles,
  HelpCircle,
  Brain,
  Lightbulb,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { useUserProfile } from "@/context/user-profile-context";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  timestamp: string;
}

export function AskContextIQDrawer() {
  const { profile, personaMeta, t } = useUserProfile();

  const [isOpen, setIsOpen] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);

  const getGreeting = () => {
    const userName = profile.name || "there";
    const userRole = profile.customTitle || personaMeta.title;
    switch (profile.language) {
      case "es":
        return `¡Hola, ${userName}! Soy tu Copiloto Cognitivo ContextIQ calibrado para tu rol de ${userRole}. Analizo tus micro-retrasos y dispersión de atención. ¡Pregúntame lo que necesites!`;
      case "hi":
        return `नमस्ते ${userName}! मैं आपका ContextIQ संज्ञानात्मक सह-पायलट हूँ, जो आपके ${userRole} कार्यशैली के लिए अनुकूलित है। आज अपने ध्यान और वापसी समय के बारे में कुछ भी पूछें!`;
      case "de":
        return `Hallo ${userName}! Ich bin Ihr ContextIQ Kognitiver Copilot, kalibriert für Ihre Rolle als ${userRole}. Fragen Sie mich alles über Ihre Fokusmuster und Verzögerungen!`;
      case "fr":
        return `Bonjour ${userName} ! Je suis votre Copilote Cognitif ContextIQ configuré pour votre rôle de ${userRole}. Posez-moi des questions sur vos micro-délais et votre concentration !`;
      case "ta":
        return `வணக்கம் ${userName}! நான் உங்கள் ContextIQ கவனப் பாய்வு உதவியாளர் (${userRole}). உங்கள் பணி, தடங்கல்கள் மற்றும் உற்பத்தித்திறன் பற்றி என்னிடம் கேளுங்கள்!`;
      default:
        return `Hello ${userName}! I am your ContextIQ Behavioral Co-Pilot calibrated for your ${userRole} workflow. I observe your micro-delays, context switches, and task patterns. Ask me anything about where your focus went today!`;
    }
  };

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-init",
      sender: "assistant",
      text: getGreeting(),
      timestamp: "Just now",
    },
  ]);

  // Update greeting if language or role changes
  useEffect(() => {
    setMessages((prev) => [
      {
        id: "msg-init",
        sender: "assistant",
        text: getGreeting(),
        timestamp: "Just now",
      },
      ...prev.slice(1),
    ]);
  }, [profile.language, profile.role]);

  const quickPrompts = [
    profile.language === "es"
      ? "¿Por qué mi puntuación de fricción es 64 hoy?"
      : profile.language === "hi"
      ? "आज मेरा घर्षण स्कोर 64 क्यों है?"
      : "Why is my friction score 64 today?",
    profile.language === "es"
      ? "¿Qué interrupción causó mi mayor micro-retraso?"
      : profile.language === "hi"
      ? "किस रुकावट से सबसे लंबा माइक्रो-डिले हुआ?"
      : "Which interruption caused my longest micro-delay?",
    profile.language === "es"
      ? "¿Cómo reduzco el riesgo de olvidar tareas?"
      : profile.language === "hi"
      ? "कार्य भूलने के जोखिम को कैसे कम करें?"
      : "How can I cut my forgetting risk tomorrow?",
    profile.language === "es"
      ? "¿Cuál es mi peor hora de cambio de contexto?"
      : profile.language === "hi"
      ? "मेरा सबसे ज्यादा ध्यान भटकने वाला समय कौन सा है?"
      : "What is my peak context-switching hour?",
  ];

  const handleSendPrompt = async (promptText: string) => {
    if (!promptText.trim()) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue("");
    setIsTyping(true);

    try {
      const res = await fetch("/api/copilot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: promptText,
          language: profile.language,
          profile,
          personaTitle: personaMeta.title,
        }),
      });

      if (!res.ok) throw new Error("API response error");
      const data = await res.json();

      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: "assistant",
        text: data.reply || "I am analyzing your cognitive telemetry...",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      // Local fallback on connection hitch
      const botMsg: ChatMessage = {
        id: `bot-${Date.now()}`,
        sender: "assistant",
        text: `Based on your active ${personaMeta.title} telemetry for ${profile.name}: Resumption lag efficiency is 72%. Keep your re-entry anchor active: "${personaMeta.reentryAnchorTemplate}".`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Card className="glass-card card-hover-lift group relative overflow-hidden border-border/80">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-violet-500 via-indigo-500 to-sky-400 opacity-60" />
      <CardHeader
        className="pb-3 cursor-pointer select-none"
        onClick={() => setIsOpen((prev) => !prev)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-md bg-chart-4/20 text-chart-4 border border-chart-4/30">
              <Bot className="h-4 w-4" />
            </span>
            <div>
              <CardTitle className="text-base font-semibold tracking-tight flex items-center gap-2">
                {t("askCopilot")}
                <Badge variant="outline" className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 border-emerald-500/30 bg-emerald-500/10">
                  ⚡ OpenRouter AI · {profile.language.toUpperCase()}
                </Badge>
              </CardTitle>
              <CardDescription className="text-xs">
                {t("askSubtitle")}
              </CardDescription>
            </div>
          </div>

          <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-muted-foreground">
            {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </Button>
        </div>
      </CardHeader>

      {isOpen && (
        <CardContent className="space-y-4 pt-0 animate-slide-up">
          {/* Quick chips */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {quickPrompts.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => handleSendPrompt(q)}
                className="text-xs px-2.5 py-1 rounded-full border border-border bg-muted/40 hover:bg-muted text-muted-foreground hover:text-foreground transition-all duration-200 hover:scale-105 active:scale-95"
              >
                {q}
              </button>
            ))}
          </div>

          {/* Chat Messages scroll area */}
          <div className="max-h-60 overflow-y-auto space-y-2.5 pr-1 text-xs">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-2 ${m.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                {m.sender === "assistant" && (
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-chart-4/20 text-chart-4 mt-0.5">
                    <Bot className="h-3.5 w-3.5" />
                  </span>
                )}
                <div
                  className={`p-2.5 rounded-lg max-w-[85%] leading-relaxed ${
                    m.sender === "user"
                      ? "bg-primary text-primary-foreground font-medium rounded-br-xs"
                      : "bg-muted/70 text-foreground border border-border rounded-bl-xs"
                  }`}
                >
                  <p>{m.text}</p>
                  <span className="text-[10px] opacity-70 mt-1 block text-right font-mono">
                    {m.timestamp}
                  </span>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex gap-2 items-center text-xs text-muted-foreground">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-chart-4/20 text-chart-4">
                  <Bot className="h-3.5 w-3.5" />
                </span>
                <span className="animate-pulse font-mono text-[11px]">
                  ContextIQ is analyzing your behavioral timeline...
                </span>
              </div>
            )}
          </div>

          {/* Input box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendPrompt(inputValue);
            }}
            className="flex gap-2"
          >
            <Input
              placeholder={
                profile.language === "es"
                  ? "Pregunta a ContextIQ sobre tus patrones de concentración..."
                  : profile.language === "hi"
                  ? "अपने ध्यान और वापसी समय के बारे में ContextIQ से पूछें..."
                  : "Ask ContextIQ about where your attention went today..."
              }
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="text-xs h-9 bg-background/80"
            />
            <Button type="submit" size="sm" className="h-9 px-3 gap-1.5 text-xs">
              <Send className="h-3.5 w-3.5" />
              Send
            </Button>
          </form>
        </CardContent>
      )}
    </Card>
  );
}
