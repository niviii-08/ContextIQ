import { NextResponse } from "next/server";
import { polishAndBulletizeRoutineLocally } from "@/lib/routine-formatter";

export async function POST(req: Request) {
  let body: any = {};
  try {
    const raw = await req.text();
    body = JSON.parse(raw);
  } catch {
    body = {};
  }

  const { text = "" } = body;
  if (!text || !text.trim()) {
    return NextResponse.json({ polished: "" });
  }

  const apiKey = process.env.OPENROUTER_API_KEY || "";
  const model = process.env.OPENROUTER_MODEL || "nvidia/nemotron-3.5-lightning:free";

  if (apiKey) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const res = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        signal: controller.signal,
        headers: {
          "Authorization": `Bearer ${apiKey}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "http://localhost:3001",
          "X-Title": "ContextIQ Routine Polisher",
        },
        body: JSON.stringify({
          model,
          messages: [
            {
              role: "system",
              content:
                "You are an expert executive schedule assistant. The user will provide a rough, conversational or broken-English daily routine. Transform it into a clean, concise, grammatically correct bulleted daily schedule. Each bullet must start with '• ' followed by the time (e.g. '• 7:00 AM – Wake up & morning routine') or general phase if no time was given. Fix all spelling, typos, and syntax. Return ONLY the bulleted list without preamble, code blocks, or explanations.",
            },
            {
              role: "user",
              content: text.trim(),
            },
          ],
          max_tokens: 600,
          temperature: 0.2,
        }),
      });

      clearTimeout(timeoutId);

      if (res.ok) {
        const data = await res.json();
        const content = data.choices?.[0]?.message?.content;
        if (content && typeof content === "string") {
          // Normalize any - or * bullets to • bullets
          const cleaned = content
            .replace(/```[a-z]*\n?/g, "")
            .replace(/```/g, "")
            .split("\n")
            .map((l: string) => l.trim())
            .filter(Boolean)
            .map((l: string) => {
              const stripped = l.replace(/^[•\-\*\d\.\)\s]+/, "").trim();
              return stripped ? `• ${stripped}` : "";
            })
            .filter(Boolean)
            .join("\n");

          if (cleaned) {
            return NextResponse.json({ polished: cleaned, source: "ai" });
          }
        }
      }
    } catch {
      // Fall through to local fallback
    }
  }

  // Local rule-based fallback
  const localPolished = polishAndBulletizeRoutineLocally(text);
  return NextResponse.json({ polished: localPolished, source: "heuristic" });
}
