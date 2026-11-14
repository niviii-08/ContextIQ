import re


def polish_and_bulletize_routine(raw_text: str | None) -> str | None:
    """
    Intelligently corrects informal/broken English and formats raw daily routine
    descriptions into clean, consistent, bulleted schedule items for PostgreSQL persistence.
    """
    if not raw_text or not raw_text.strip():
        return raw_text

    text = raw_text.strip()

    # If the user already provided clean bulleted lines, normalize spacing and return
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    bullet_count = sum(1 for l in lines if l.startswith(("•", "-", "*", "1.", "2.", "3.", "4.", "5.")))
    if len(lines) > 1 and bullet_count >= len(lines) * 0.7:
        normalized = []
        for l in lines:
            clean = re.sub(r"^[•\-\*\d\.\)\s]+", "", l).strip()
            if clean:
                normalized.append(f"• {clean[0].upper() + clean[1:] if len(clean) > 1 else clean.upper()}")
        return "\n".join(normalized)

    # Common spelling/informal corrections
    substitutions = [
        (r"\bbreak\s*fast\b|\bbrakefast\b|\bbrekfast\b|\bbf\b", "breakfast"),
        (r"\bfresh\s*up\b|\bbrush\s*up\b", "freshen up"),
        (r"\bclg\b|\bcollge\b|\bcolleg\b", "college"),
        (r"\bstuding\b|\bstudying\b", "study"),
        (r"\bgoin\b|\bgoing\s+to\b|\bgo\s+to\b", "go to"),
        (r"\bwrk\b|\bwoking\b", "work"),
        (r"\bsleping\b|\bsleeping\b|\bgoto\s*bed\b", "sleep"),
        (r"\bcoding\b|\bprgming\b", "coding"),
        (r"\bhavng\b|\bhving\b", "having"),
    ]
    for pattern, repl in substitutions:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # Delimiters: newlines, semicolons, transition phrases, or commas separating activities
    split_pattern = r"[\r\n]+|[;\.]+|\b(?:and\s+then|then|after\s+that|afterwards|followed\s+by|next|later)\b|,"
    raw_segments = re.split(split_pattern, text, flags=re.IGNORECASE)

    bullets: list[str] = []

    for seg in raw_segments:
        s = seg.strip()
        if not s:
            continue

        # Strip bullet symbols if present
        s = re.sub(r"^[•\-\*\d\.\)\s]+", "", s).strip()
        if not s:
            continue

        # Extract explicit time range or timestamp: e.g. "9 AM - 1 PM", "7:30 AM", "7am"
        time_range = re.search(r"(\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:-|to)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)\b)", s, flags=re.IGNORECASE)
        time_single = re.search(r"(\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b)", s, flags=re.IGNORECASE)

        time_tag = ""
        action_text = s

        if time_range:
            time_tag = time_range.group(1).upper()
            action_text = (s[:time_range.start()] + " " + s[time_range.end():]).strip()
        elif time_single:
            time_tag = time_single.group(1).upper()
            action_text = (s[:time_single.start()] + " " + s[time_single.end():]).strip()
        else:
            # Check for numbers like "sleep 10" or "wake 7" or "at 8"
            clock_num = re.search(r"\b(?:at|around|sleep|wake(?:\s*up)?)\s+(\d{1,2})\b", s, flags=re.IGNORECASE)
            if clock_num:
                num = int(clock_num.group(1))
                if 1 <= num <= 12:
                    if num in [5, 6, 7, 8, 9, 10, 11] and any(w in s.lower() for w in ["wake", "morning", "breakfast", "start"]):
                        time_tag = f"{num}:00 AM"
                    elif any(w in s.lower() for w in ["sleep", "night", "dinner", "evening", "bed"]):
                        time_tag = f"{num}:00 PM" if num != 12 else "12:00 AM"
                    else:
                        time_tag = f"{num}:00"
                    action_text = (s[:clock_num.start()] + " " + s[clock_num.end():]).strip()

        # Clean filler words
        action_text = re.sub(r"^(?:at|around|during|in\s+the|for|and|then)\s+", "", action_text, flags=re.IGNORECASE).strip()
        action_text = re.sub(r"\s+", " ", action_text)

        # Canonical activity mappings for clarity and correct English
        low = action_text.lower()
        refined_action = action_text

        if any(w in low for w in ["wake", "get up", "waking"]):
            refined_action = "Wake up & morning routine"
        elif any(w in low for w in ["breakfast", "eating breakfast", "morning tea", "coffee"]):
            refined_action = "Healthy breakfast & morning beverage"
        elif any(w in low for w in ["freshen", "bath", "shower", "brush"]):
            refined_action = "Freshen up & personal care"
        elif any(w in low for w in ["college", "classes", "lecture", "campus"]):
            refined_action = "Attend college classes & academic coursework"
        elif any(w in low for w in ["office", "standup", "sprint"]):
            refined_action = "Office focus & team synchronization"
        elif any(w in low for w in ["coding", "code", "dev", "programming"]):
            refined_action = "Deep coding sprint & project development"
        elif any(w in low for w in ["study", "revision", "exam", "homework", "assignment"]):
            dur = re.search(r"(\d+\s*(?:hr|hour|hours|mins?))", low)
            if dur:
                refined_action = f"Focused study session ({dur.group(1)})"
            else:
                refined_action = "Dedicated study session & assignments"
        elif any(w in low for w in ["lunch", "eating lunch"]):
            refined_action = "Nutritious lunch & midday mental pause"
        elif any(w in low for w in ["walk", "jog", "jogging", "walking"]):
            refined_action = "Outdoor walk & physical recharge"
        elif any(w in low for w in ["gym", "workout", "exercise"]):
            refined_action = "Gym workout & physical fitness"
        elif any(w in low for w in ["dinner", "eating dinner"]):
            refined_action = "Dinner & relaxation"
        elif any(w in low for w in ["sleep", "sleeping", "bed"]):
            refined_action = "Wind down, reflection & sleep"
        elif any(w in low for w in ["reading", "book", "read"]):
            refined_action = "Reading & cognitive wind-down"
        else:
            if refined_action:
                refined_action = refined_action[0].upper() + refined_action[1:]

        # Format time if present
        if time_tag:
            formatted_time = re.sub(r"(\d+)(AM|PM)", r"\1 \2", time_tag)
            if ":" not in formatted_time and (" AM" in formatted_time or " PM" in formatted_time):
                formatted_time = formatted_time.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
            item = f"• {formatted_time} – {refined_action}"
        elif refined_action:
            item = f"• {refined_action}"
        else:
            item = ""

        if item and item not in bullets:
            bullets.append(item)

    if not bullets:
        return text

    return "\n".join(bullets)
