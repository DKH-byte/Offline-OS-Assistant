import random
import time

# WAKE WORD MAP

WAKE_VOICE_MAP = {
    "jarvis":     "david",
    "friday":     "zira",
    "hey jarvis": "david",
    "ok jarvis":  "david",
    "hello jarvis":"david",
    "hey friday": "zira",
    "ok friday":  "zira",
    "hello friday":"zira",
}

# Single source of truth — no second assignment that overwrites this
WAKE_WORDS = list(WAKE_VOICE_MAP.keys())

RESPONSES = {

    # ── Wake ─────────────────────────────────────────────
    "WAKE_JARVIS": [
        "At your service, Sir.",
        "Systems online. What do you need?",
        "Yes, Sir. Ready.",
        "I'm here. What's the move?",
        "Online and operational, Sir.",
        "Ready when you are.",
    ],
    "WAKE_FRIDAY": [
        "Hey. I'm online. What's the move?",
        "Back again? Let's get it.",
        "Ready. Try not to break anything.",
        "Online, Sir.",
        "Alright, what are we doing?",
    ],
    "SLEEP": [
        "Going to sleep. Call me when you need me.",
        "Sleep mode. Don't stay up too late.",
        "Offline for now. Take care.",
        "Resting. You should too.",
        "Going quiet. See you soon.",
    ],

    # ── Thank you ─────────────────────────────────────────
    "THANK YOU": [
        "Always, Sir.",
        "Anytime.",
        "Happy to help.",
        "Of course, Sir.",
        "That's what I'm here for.",
        "Don't mention it.",
        "Glad I could help.",
    ],

    # ── Volume ───────────────────────────────────────────
    "VOLUME UP":      ["Turning it up.", "More volume.", "Louder.", "Cranking it up."],
    "VOLUME DOWN":    ["Turning it down.", "Quieter now.", "Volume down.", "Softening it."],
    "MUTE":           ["Muted.", "Silent mode.", "All quiet."],

    # ── Brightness ───────────────────────────────────────
    "BRIGHTNESS UP":  ["Brighter now.", "Light it up.", "Screen brightened."],
    "BRIGHTNESS DOWN":["Dimming it.", "Softer light.", "Going darker."],

    # ── Navigation ───────────────────────────────────────
    "SCROLL UP":      ["Scrolling up.", "Going up.", "Up we go."],
    "SCROLL DOWN":    ["Scrolling down.", "Going down.", "Down we go."],
    "ZOOM IN":        ["Zooming in.", "Bigger now.", "Closer look."],
    "ZOOM OUT":       ["Zooming out.", "Wider view.", "Stepping back."],
    "NEXT WINDOW":    ["Switching window.", "Next one.", "Window switched."],
    "SNAP LEFT":      ["Snapped left.", "Left side."],
    "SNAP RIGHT":     ["Snapped right.", "Right side."],
    "SNAP UP":        ["Maximized.", "Full screen."],
    "SNAP DOWN":      ["Minimized.", "Snapped down."],

    # ── Tabs ─────────────────────────────────────────────
    "NEW TAB":        ["New tab.", "Opening tab.", "Fresh tab."],
    "CLOSE TAB":      ["Tab closed.", "Closing it.", "Gone."],
    "NEXT TAB":       ["Next tab.", "Moving over.", "Tab switched."],
    "INCOGNITO":      ["Going incognito.", "Private mode on.", "No trace."],
    "REOPEN TAB":     ["Tab reopened.", "Brought it back.", "There you go."],

    # ── Edit ─────────────────────────────────────────────
    "COPY":           ["Copied.", "Got it.", "In clipboard."],
    "PASTE":          ["Pasted.", "Done.", "Applied."],
    "CUT":            ["Cut.", "Removed.", "Done."],
    "UNDO":           ["Undone.", "Going back.", "Reverted."],
    "REDO":           ["Redone.", "Forward again.", "Done."],
    "SELECT ALL":     ["All selected.", "Everything selected.", "Done."],
    "SAVE":           ["Saved.", "File saved.", "Done."],
    "DELETE":         ["Deleted.", "Gone.", "Removed."],

    # ── Media ────────────────────────────────────────────
    "PLAY PAUSE":     ["Toggled.", "Done.", "Play pause."],
    "NEXT TRACK":     ["Next track.", "Skipping.", "Next one."],
    "PREVIOUS TRACK": ["Previous track.", "Going back.", "Last one."],
    "PLAY MUSIC":     ["Opening Spotify.", "Let's get some music going.", "Music time."],

    # ── System ───────────────────────────────────────────
    "SCREENSHOT":     ["Screenshot taken.", "Captured.", "Got it."],
    "LOCK":           ["Locking screen.", "Locked.", "Screen locked."],
    "MINIMIZE":       ["Minimized.", "Out of the way.", "Done."],
    "CLOSE":          ["Closing.", "Done.", "Closed."],
    "REFRESH":        ["Refreshed.", "Reloaded.", "Done."],
    "HARD REFRESH":   ["Hard refreshed.", "Cache cleared and reloaded.", "Done."],
    "SEARCH":         ["Opening search.", "Search bar up.", "Find away."],
    "PRINT":          ["Printing.", "Sent to printer.", "Done."],
    "TASK MANAGER":   ["Opening Task Manager.", "Here you go.", "Task Manager up."],
    "ENTER":          ["Done.", "Confirmed.", "Entered."],
    "ESCAPE":         ["Escaped.", "Cancelled.", "Done."],
    "HOME":           ["Home.", "Top of the page.", "Back to start."],
    "SCROLL TOP":     ["At the top.", "Jumped to top.", "Top of page."],
    "SCROLL BOTTOM":  ["At the bottom.", "Jumped to bottom.", "End of page."],
    "SHOW DESKTOP":   ["Desktop.", "Showing desktop.", "Here you go."],

    # ── DEFAULT fallback ──────────────────────────────────
    "DEFAULT": ["Done.", "Handled.", "Executed.", "Sorted.", "As you command.", "On it."],

    # =========================================================
    # HABIT RESPONSES
    # =========================================================

    "HABIT_MORNING_INTRO": [
        "Good morning, Sir. Let's do a quick habit check.",
        "Morning check-in time. How are the habits going?",
        "Rise and shine. Let me check in on your routine.",
        "Quick habit review before the day gets busy.",
    ],

    "HABIT_WAKEUP_YES": [
        "3:30 AM. Respect, Sir. That's pure discipline right there.",
        "Up at 3:30. Most people don't even dream of doing that. Keep it up.",
        "Early riser. That's how empires are built. Outstanding.",
        "3:30 AM wake up done. You're already ahead of 99 percent of people.",
        "Woke up at 3:30. That's not easy. Be proud of that.",
    ],
    "HABIT_WAKEUP_NO": [
        "Missed the 3:30 wake up today. Tomorrow is a fresh chance. Set that alarm tonight.",
        "Sleep won today. It happens. But remember — discipline beats motivation every time.",
        "Woke up late? No shame. Reset tonight. 3:30 AM is a habit built one day at a time.",
        "Missing one day doesn't break the chain. Just don't miss two in a row.",
        "The body resists early mornings at first. Keep pushing. It gets easier.",
    ],

    "HABIT_EXERCISE_YES": [
        "Exercise done. Your body will thank you in ten years.",
        "Workout complete. That's investment in yourself — the best kind.",
        "Exercise checked off. Endorphins are working. Keep the momentum.",
        "You moved today. That's more than most. Great work, Sir.",
        "Exercise done. Every rep, every step — it compounds over time.",
    ],
    "HABIT_EXERCISE_NO": [
        "No exercise yet. Even 20 minutes of movement changes everything. Go for a walk at least.",
        "Skipped exercise today? Your future self is watching. Make it right tonight or first thing tomorrow.",
        "Missing exercise is fine once. Making it a pattern is dangerous. Protect the habit.",
        "No workout today. Remember why you started. Don't let comfort steal your progress.",
        "Exercise skipped. The gym will be there tonight. Don't let the day end without moving.",
    ],

    "HABIT_MEDITATION_YES": [
        "Meditation done. A calm mind is a clear mind.",
        "You sat in silence today. That's strength, not weakness.",
        "Meditation complete. The world is loud — you chose stillness. Smart.",
        "Mind trained today. Keep going, Sir.",
        "Meditated. That's 10 minutes that saved you hours of scattered thinking.",
    ],
    "HABIT_MEDITATION_NO": [
        "Skipped meditation. Even 5 minutes of deep breathing counts. Try before bed.",
        "No meditation today. A busy mind never rests — give it some silence.",
        "Meditation missed. Tomorrow, before you pick up your phone — sit still for 10 minutes.",
        "Skipped it. That's okay. But your mind is your most important tool. Sharpen it.",
        "No meditation. Chaos outside is manageable when there's order inside.",
    ],

    "HABIT_GEETA_YES": [
        "Geeta read today. Every verse is a lesson that compounds over a lifetime.",
        "Shrimat Bhagwat Geeta done. Ancient wisdom for modern problems.",
        "Read the Geeta today. You're investing in timeless knowledge.",
        "Geeta complete. Krishna's words have guided great minds for centuries — and now yours.",
        "Done. The Geeta doesn't just inform — it transforms.",
    ],
    "HABIT_GEETA_NO": [
        "No Geeta today. Just one verse tomorrow morning — that's all it takes to begin.",
        "Skipped the Geeta. Knowledge is the one thing no one can take from you. Don't skip it.",
        "No reading from the Geeta. Start small — one page, one verse. Build from there.",
        "Missed the Geeta today. The wisdom is there whenever you return to it.",
        "No Geeta. Remember — the purpose of reading it is to live it, not just read it.",
    ],

    "HABIT_SHOWER_YES": [
        "Shower done before 7. Clean body, clear start.",
        "Shower done. Starting the day fresh — good discipline.",
        "Fresh and clean before 7 AM. That's order. Keep it.",
    ],
    "HABIT_SHOWER_NO": [
        "No shower before 7. Take one now — it changes your entire mood and energy.",
        "Shower skipped. External discipline starts with basic self-care. Go take one.",
        "Missed the early shower. Don't let it slide. A clean start is a strong start.",
    ],

    "HABIT_READING_YES": [
        "Reading done. Every book is a shortcut to someone else's lifetime of learning.",
        "Self improvement reading complete. Leaders are readers — fact.",
        "Read today. You're building the person you'll be in 5 years, one page at a time.",
        "Reading done. Your future self is grateful.",
        "Finished reading. Consistent learners consistently win.",
    ],
    "HABIT_READING_NO": [
        "No reading today. Even 10 pages a day is 3,600 pages a year. That's life-changing.",
        "Skipped reading. The knowledge you don't learn today is the mistake you'll make tomorrow.",
        "No self improvement today. You can't pour from an empty cup — keep filling it.",
        "Missed reading. Pick up the book tonight. 15 minutes before bed.",
        "No reading. Discipline in learning equals freedom in life.",
    ],

    "HABIT_DIET_YES": [
        "Clean eating today. Fuel in, results out.",
        "Diet on track. Your body is a machine — you're treating it right.",
        "No junk today. That's willpower. It gets stronger every time you use it.",
        "Healthy choices made. Your gut, brain, and future self all thank you.",
    ],
    "HABIT_DIET_NO": [
        "Ate junk today. It happens. But food is medicine or poison — choose wisely next meal.",
        "Diet slipped. One bad meal doesn't ruin a week. One bad week can ruin a month though.",
        "Sugar or fast food today? Reset at the next meal. Not tomorrow — next meal.",
        "Diet broken. Acknowledge it, learn from it, move on. Don't spiral.",
        "Bad food choice. Your cravings are loudest at first. Feed discipline, starve the craving.",
    ],

    "HABIT_DINNER_YES": [
        "Dinner done before 7. Your digestion and sleep will thank you.",
        "Early dinner done. Body gets more recovery time. Smart habit.",
        "Dinner before 7 PM — checked. Discipline even at meal time.",
    ],
    "HABIT_DINNER_NO": [
        "Ate late tonight. Try to keep dinner before 7 — your sleep quality depends on it.",
        "Late dinner. Digestion slows at night. Earlier is always better.",
        "Dinner after 7. Not the end of the world. Just aim earlier tomorrow.",
    ],

    "HABIT_PROJECT_YES": [
        "Project work done. Every session brings you closer to the goal.",
        "You worked on your project today. Progress is progress — even slow is forward.",
        "Project session complete. Consistency beats intensity every time.",
        "Work done. Small daily actions build great outcomes.",
    ],
    "HABIT_PROJECT_NO": [
        "No project work today. Even 30 minutes of focused work changes the trajectory.",
        "Skipped project work. Tomorrow — block one hour. Just one. No distractions.",
        "Project untouched today. Don't let the dream collect dust. Work on it daily.",
        "No project progress. The gap between where you are and where you want to be is effort.",
    ],

    "HABIT_DIARY_YES": [
        "Diary written. You're documenting your own evolution. Powerful habit.",
        "Diary done. The person who writes their thoughts rules their thoughts.",
        "Writing done. Clarity comes from pen to paper. Keep it up.",
        "Diary complete. Future you will read this and be grateful you wrote it.",
        "Wrote today. Self-reflection is one of the rarest habits. You have it.",
    ],
    "HABIT_DIARY_NO": [
        "No diary today. Just 5 minutes — what happened, what you felt, what you learned.",
        "Skipped the diary. Writing your thoughts is the fastest way to understand yourself.",
        "Diary missed. Don't let the day leave without recording it. Even one line counts.",
        "No diary. The unexamined life is the unlived life. Write something tonight.",
        "Diary skipped. Start with one sentence — what was today's best moment?",
    ],

    "HABIT_SLEEP_REMINDER": [
        "It's 9 PM, Sir. Wind down. Sleep between 9 and 10 for the 3:30 wake up.",
        "Time to start wrapping up. Sleep is recovery. 3:30 comes fast.",
        "9 PM. Close the screens and prepare for sleep. Your morning depends on it.",
        "Wind down window open. Dim the lights, drop the phone. Sleep soon.",
    ],
    "HABIT_SLEEP_FORCE": [
        "10 PM. You should be sleeping now, Sir. The 3:30 alarm needs this.",
        "It's past 10. Every minute of sleep you lose now — you'll feel at 3:30.",
        "Lights out. No excuses. Rest is part of the discipline.",
        "10 PM and still up. Protect your sleep like you protect your goals.",
    ],

    "HABIT_DISCIPLINE_YES": [
        "Clean day. That's willpower in action.",
        "Discipline held today. Every day you win this builds the next win.",
        "Strong today. That habit gets easier the more you protect it.",
        "Kept the standard today. Respect.",
    ],
    "HABIT_DISCIPLINE_NO": [
        "Slipped today. Don't let guilt spiral you. Reset now. Not tomorrow. Now.",
        "It happened. The comeback is always more powerful than the setback.",
        "One slip doesn't define the journey. Your pattern defines you — not one day.",
        "Fell today. Acknowledge it. Learn from it. Don't repeat it tomorrow.",
        "Hard habits fail sometimes. The only failure is quitting entirely.",
    ],

    "HABIT_SCORE_PERFECT": [
        "All habits done today, Sir. Absolutely elite. You're operating at your highest level.",
        "Perfect day. Every single habit hit. This is what mastery looks like.",
        "100 percent. No words needed. Just respect.",
    ],
    "HABIT_SCORE_HIGH": [
        "Excellent day. Strong performance. The few you missed — get them tomorrow.",
        "Nearly perfect. You showed up today. That's what matters most.",
        "High score today. You're building something real. Keep stacking days like this.",
    ],
    "HABIT_SCORE_MID": [
        "Decent day. You're halfway there. The other half needs more fight tomorrow.",
        "Middle ground today. Not bad — but you know you're capable of more.",
        "Some habits hit, some missed. That's human. Tomorrow — aim higher.",
    ],
    "HABIT_SCORE_LOW": [
        "Rough day on habits. It happens. What matters is you don't let it become a pattern.",
        "Low score today. Don't judge the day — learn from it and reset.",
        "Few habits today. The question isn't what went wrong — it's what will you do tomorrow.",
    ],

    "HABIT_EVENING_INTRO": [
        "Evening check-in time, Sir. Let's see how today went.",
        "End of day review. How did the habits hold up?",
        "Day's winding down. Quick habit check before you close out.",
    ],

    "HABIT_REREMINDER": [
        "Still time tonight, Sir. Exercise or reading can still happen before 9 PM.",
        "The day isn't over yet. Can you still get that exercise or reading in?",
        "Evening window open. Exercise and reading — one last chance tonight.",
    ],
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def get_response(key: str) -> str:
    return random.choice(RESPONSES.get(key, RESPONSES["DEFAULT"]))


def time_greeting() -> str:
    h = time.localtime().tm_hour
    if h < 12:  return "Good morning"
    if h < 18:  return "Good afternoon"
    if h < 21:  return "Good evening"
    return "Working late"


def wake_message(voice: str) -> str:
    pool = "WAKE_JARVIS" if voice == "david" else "WAKE_FRIDAY"
    return f"{time_greeting()}. {random.choice(RESPONSES[pool])}"