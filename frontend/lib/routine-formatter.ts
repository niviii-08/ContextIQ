/**
 * Intelligent Daily Routine Polisher & Bulletizer
 * Converts raw, broken or informal English schedule text into clean, structured bullet points.
 */

export function polishAndBulletizeRoutineLocally(rawText: string): string {
  if (!rawText || !rawText.trim()) return "";

  const text = rawText.trim();

  // If already formatted as multi-line bullets, normalize spacing & capitalization
  const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
  const bulletCount = lines.filter((l) => /^[•\-\*\d\.\)]/.test(l)).length;
  if (lines.length > 1 && bulletCount >= lines.length * 0.7) {
    return lines
      .map((l) => {
        const clean = l.replace(/^[•\-\*\d\.\)\s]+/, "").trim();
        if (!clean) return "";
        return `• ${clean.charAt(0).toUpperCase() + clean.slice(1)}`;
      })
      .filter(Boolean)
      .join("\n");
  }

  // 1. Common spelling & slang normalizations
  let cleaned = text
    .replace(/\bbreak\s*fast\b|\bbrakefast\b|\bbrekfast\b|\bbf\b/gi, "breakfast")
    .replace(/\bfresh\s*up\b|\bbrush\s*up\b/gi, "freshen up")
    .replace(/\bclg\b|\bcollge\b|\bcolleg\b/gi, "college")
    .replace(/\bstuding\b|\bstudying\b/gi, "study")
    .replace(/\bgoin\b|\bgoing\s+to\b|\bgo\s+to\b/gi, "go to")
    .replace(/\bwrk\b|\bwoking\b/gi, "work")
    .replace(/\bsleping\b|\bsleeping\b|\bgoto\s*bed\b/gi, "sleep")
    .replace(/\bcoding\b|\bprgming\b/gi, "coding")
    .replace(/\bhavng\b|\bhving\b/gi, "having");

  // 2. Split on punctuation, transitions, or clauses
  const splitRegex = /[\r\n]+|[;\.]+|\b(?:and\s+then|then|after\s+that|afterwards|followed\s+by|next|later)\b|,/gi;
  const rawSegments = cleaned.split(splitRegex);

  const bullets: string[] = [];

  for (const seg of rawSegments) {
    let s = seg.trim().replace(/^[•\-\*\d\.\)\s]+/, "").trim();
    if (!s) continue;

    // Detect explicit time range or timestamp: e.g. "9 AM - 1 PM", "7:30 AM", "7am"
    const timeRangeMatch = s.match(/(\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:-|to)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)\b)/i);
    const timeSingleMatch = s.match(/(\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b)/i);

    let timeTag = "";
    let actionText = s;

    if (timeRangeMatch) {
      timeTag = timeRangeMatch[1].toUpperCase();
      actionText = (s.slice(0, timeRangeMatch.index) + " " + s.slice(timeRangeMatch.index! + timeRangeMatch[0].length)).trim();
    } else if (timeSingleMatch) {
      timeTag = timeSingleMatch[1].toUpperCase();
      actionText = (s.slice(0, timeSingleMatch.index) + " " + s.slice(timeSingleMatch.index! + timeSingleMatch[0].length)).trim();
    } else {
      // Check for shorthand numbers like "sleep 10" or "wake 7" or "at 8"
      const clockNumMatch = s.match(/\b(?:at|around|sleep|wake(?:\s*up)?)\s+(\d{1,2})\b/i);
      if (clockNumMatch) {
        const num = parseInt(clockNumMatch[1], 10);
        if (num >= 1 && num <= 12) {
          if ([5, 6, 7, 8, 9, 10, 11].includes(num) && /wake|morning|breakfast|start/i.test(s)) {
            timeTag = `${num}:00 AM`;
          } else if (/sleep|night|dinner|evening|bed/i.test(s)) {
            timeTag = num === 12 ? "12:00 AM" : `${num}:00 PM`;
          } else {
            timeTag = `${num}:00`;
          }
          actionText = (s.slice(0, clockNumMatch.index) + " " + s.slice(clockNumMatch.index! + clockNumMatch[0].length)).trim();
        }
      }
    }

    // Clean filler words
    actionText = actionText.replace(/^(?:at|around|during|in\s+the|for|and|then)\s+/i, "").trim().replace(/\s+/g, " ");

    const low = actionText.toLowerCase();
    let refinedAction = actionText;

    if (/wake|get up|waking/i.test(low)) {
      refinedAction = "Wake up & morning routine";
    } else if (/breakfast|morning tea|coffee/i.test(low)) {
      refinedAction = "Healthy breakfast & morning beverage";
    } else if (/freshen|bath|shower|brush/i.test(low)) {
      refinedAction = "Freshen up & personal care";
    } else if (/college|classes|lecture|campus/i.test(low)) {
      refinedAction = "Attend college classes & academic coursework";
    } else if (/office|standup|sprint/i.test(low)) {
      refinedAction = "Office focus & team synchronization";
    } else if (/coding|code|dev|programming/i.test(low)) {
      refinedAction = "Deep coding sprint & project development";
    } else if (/study|revision|exam|homework|assignment/i.test(low)) {
      const dur = low.match(/(\d+\s*(?:hr|hour|hours|mins?))/i);
      refinedAction = dur ? `Focused study session (${dur[1]})` : "Dedicated study session & assignments";
    } else if (/lunch/i.test(low)) {
      refinedAction = "Nutritious lunch & midday mental pause";
    } else if (/walk|jog|jogging|walking/i.test(low)) {
      refinedAction = "Outdoor walk & physical recharge";
    } else if (/gym|workout|exercise/i.test(low)) {
      refinedAction = "Gym workout & physical fitness";
    } else if (/dinner/i.test(low)) {
      refinedAction = "Dinner & relaxation";
    } else if (/sleep|bed/i.test(low)) {
      refinedAction = "Wind down, reflection & sleep";
    } else if (/reading|book|read/i.test(low)) {
      refinedAction = "Reading & cognitive wind-down";
    } else if (refinedAction) {
      refinedAction = refinedAction.charAt(0).toUpperCase() + refinedAction.slice(1);
    }

    // Format time if present
    if (timeTag) {
      let formattedTime = timeTag.replace(/(\d+)(AM|PM)/, "$1 $2");
      if (!formattedTime.includes(":") && (formattedTime.includes(" AM") || formattedTime.includes(" PM"))) {
        formattedTime = formattedTime.replace(" AM", ":00 AM").replace(" PM", ":00 PM");
      }
      const item = `• ${formattedTime} – ${refinedAction}`;
      if (!bullets.includes(item)) bullets.push(item);
    } else if (refinedAction) {
      const item = `• ${refinedAction}`;
      if (!bullets.includes(item)) bullets.push(item);
    }
  }

  if (bullets.length === 0) return text;
  return bullets.join("\n");
}

/**
 * Attempts to polish routine using OpenRouter AI server-side;
 * automatically falls back to local heuristic formatting if unavailable.
 */
export async function polishRoutineWithAI(rawText: string): Promise<string> {
  if (!rawText || !rawText.trim()) return "";

  try {
    const res = await fetch("/api/routine/polish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: rawText }),
    });

    if (res.ok) {
      const data = await res.json();
      if (data.polished && typeof data.polished === "string") {
        return data.polished.trim();
      }
    }
  } catch {
    // offline fallback
  }

  return polishAndBulletizeRoutineLocally(rawText);
}
