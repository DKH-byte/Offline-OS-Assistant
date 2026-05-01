import json
import os
import time
import threading
import random
from datetime import datetime, date


# =========================================================
# HABIT DEFINITIONS
# =========================================================

HABITS = [
    {
        "id":       "wakeup",
        "name":     "wake up at 3:30",
        "check_start": 7, "check_end": 9,
        "reremind": None,
        "yes_key":  "HABIT_WAKEUP_YES",
        "no_key":   "HABIT_WAKEUP_NO",
        "ask_msg":  "Sir, did you wake up at 3:30 this morning?",
    },
    {
        "id":       "exercise",
        "name":     "exercise",
        "check_start": 7, "check_end": 9,
        "reremind": 21,
        "yes_key":  "HABIT_EXERCISE_YES",
        "no_key":   "HABIT_EXERCISE_NO",
        "ask_msg":  "Did you get your exercise done today?",
    },
    {
        "id":       "meditation",
        "name":     "meditation",
        "check_start": 7, "check_end": 9,
        "reremind": None,
        "yes_key":  "HABIT_MEDITATION_YES",
        "no_key":   "HABIT_MEDITATION_NO",
        "ask_msg":  "Meditation done this morning?",
    },
    {
        "id":       "geeta",
        "name":     "Bhagwat Geeta",
        "check_start": 7, "check_end": 9,
        "reremind": None,
        "yes_key":  "HABIT_GEETA_YES",
        "no_key":   "HABIT_GEETA_NO",
        "ask_msg":  "Did you read the Shrimat Bhagwat Geeta today?",
    },
    {
        "id":       "shower",
        "name":     "shower",
        "check_start": 7, "check_end": 9,
        "reremind": None,
        "yes_key":  "HABIT_SHOWER_YES",
        "no_key":   "HABIT_SHOWER_NO",
        "ask_msg":  "Shower done before 7 AM?",
    },
    {
        "id":       "reading",
        "name":     "self improvement reading",
        "check_start": 7, "check_end": 9,
        "reremind": 21,
        "yes_key":  "HABIT_READING_YES",
        "no_key":   "HABIT_READING_NO",
        "ask_msg":  "Did you do your self improvement reading today?",
    },
    {
        "id":       "diet",
        "name":     "healthy diet",
        "check_start": 19, "check_end": 20,
        "reremind": None,
        "yes_key":  "HABIT_DIET_YES",
        "no_key":   "HABIT_DIET_NO",
        "ask_msg":  "Did you keep a healthy diet today? No sugar, no fast food?",
    },
    {
        "id":       "dinner",
        "name":     "dinner before 7",
        "check_start": 19, "check_end": 20,
        "reremind": None,
        "yes_key":  "HABIT_DINNER_YES",
        "no_key":   "HABIT_DINNER_NO",
        "ask_msg":  "Did you have dinner before 7 PM?",
    },
    {
        "id":       "project",
        "name":     "project work",
        "check_start": 19, "check_end": 20,
        "reremind": None,
        "yes_key":  "HABIT_PROJECT_YES",
        "no_key":   "HABIT_PROJECT_NO",
        "ask_msg":  "Did you work on your project today?",
    },
    {
        "id":       "diary",
        "name":     "diary writing",
        "check_start": 20, "check_end": 21,
        "reremind": None,
        "yes_key":  "HABIT_DIARY_YES",
        "no_key":   "HABIT_DIARY_NO",
        "ask_msg":  "Diary written for today?",
    },
]

HABIT_MAP    = {h["id"]: h for h in HABITS}
TOTAL_HABITS = len(HABITS)

DONE_PHRASES = {
    "done exercise":      "exercise",
    "done meditation":    "meditation",
    "done geeta":         "geeta",
    "done reading":       "reading",
    "done shower":        "shower",
    "done diary":         "diary",
    "done project":       "project",
    "done diet":          "diet",
    "done wakeup":        "wakeup",
    "finished exercise":  "exercise",
    "finished meditation":"meditation",
    "finished reading":   "reading",
    "finished diary":     "diary",
    "exercise done":      "exercise",
    "meditation done":    "meditation",
    "reading done":       "reading",
    "diary done":         "diary",
    "shower done":        "shower",
}


# =========================================================
# HABIT ENGINE
# =========================================================

class HabitEngine:
    """
    Daily habit tracker with voice interaction.

    BUG FIXES APPLIED:
      BUG 1 — _ask_next() no longer switches to confirm_mode while sleeping.
               Habits queue until assistant wakes, then resume.
               Recognizer always restored to correct mode when queue empties.
      BUG 2 — on_yes / on_no wait for TTS to finish before asking next habit
               so speak() is never silently dropped due to IS_SPEAKING=True.
      BUG 8 — LAST_COMMAND_TIME reset when habit question is asked so
               auto-sleep doesn't interrupt mid-conversation.
    """

    def __init__(self, assistant, persistence_file="habit_log.json"):
        self.assistant        = assistant
        self.persistence_file = persistence_file

        self.daily_data = self._load()

        self.pending_habit: dict | None = None
        self._check_queue: list[str]    = []
        self._asking: bool              = False

        self._triggered:  set[str] = set(self.daily_data.get("triggered",  []))
        self._rereminded: set[str] = set(self.daily_data.get("rereminded", []))

        print(f"Habit Engine ready. Today: {self._score()}/{TOTAL_HABITS} habits done.")

    # ── Persistence ───────────────────────────────────────

    def _load(self) -> dict:
        if not os.path.exists(self.persistence_file):
            return self._fresh()
        try:
            with open(self.persistence_file) as f:
                data = json.load(f)
            if data.get("date") != date.today().isoformat():
                return self._fresh()
            return data
        except:
            return self._fresh()

    def _fresh(self) -> dict:
        return {
            "date":       date.today().isoformat(),
            "done":       {},
            "triggered":  [],
            "rereminded": [],
        }

    def _save(self):
        try:
            self.daily_data["triggered"]  = list(self._triggered)
            self.daily_data["rereminded"] = list(self._rereminded)
            with open(self.persistence_file, "w") as f:
                json.dump(self.daily_data, f, indent=2)
        except Exception as e:
            print(f"Habit save error: {e}")

    # ── Score ─────────────────────────────────────────────

    def _score(self) -> int:
        return sum(1 for v in self.daily_data["done"].values() if v is True)

    def get_score_message(self) -> str:
        from responses import get_response
        done  = self._score()
        total = TOTAL_HABITS
        pct   = done / total if total else 0

        missing_names = [h["name"] for h in HABITS
                         if self.daily_data["done"].get(h["id"]) is not True]

        if pct == 1.0:
            score_key = "HABIT_SCORE_PERFECT"
        elif pct >= 0.7:
            score_key = "HABIT_SCORE_HIGH"
        elif pct >= 0.4:
            score_key = "HABIT_SCORE_MID"
        else:
            score_key = "HABIT_SCORE_LOW"

        motivation = get_response(score_key)

        if done == 0:
            summary = "No habits logged yet today, Sir."
        elif done == total:
            summary = f"All {total} habits completed today."
        else:
            summary = f"{done} out of {total} habits done today."

        if missing_names and done < total:
            missing_str = ", ".join(missing_names[:3])
            if len(missing_names) > 3:
                missing_str += f" and {len(missing_names) - 3} more"
            detail = f" Still pending: {missing_str}."
        else:
            detail = ""

        return f"{summary}{detail} {motivation}"

    # ── Mark done via voice ───────────────────────────────

    def mark_done(self, habit_id: str) -> str:
        from responses import get_response
        habit = HABIT_MAP.get(habit_id)
        if not habit:
            return "I don't recognise that habit."
        self.daily_data["done"][habit_id] = True
        self._save()
        print(f"[Habit] Marked done: {habit_id}")
        return get_response(habit["yes_key"])

    # ── Yes / No handlers ─────────────────────────────────
    # BUG 2 FIX: After speaking the response, wait for TTS to finish
    # before calling _ask_next(). This prevents speak() being silently
    # dropped because IS_SPEAKING is still True from the previous call.

    def on_yes(self):
        from responses import get_response
        if not self.pending_habit:
            return
        hid = self.pending_habit["id"]
        self.daily_data["done"][hid] = True
        self._save()
        response = get_response(self.pending_habit["yes_key"])
        self.assistant.speak(response)
        print(f"[Habit] YES: {hid}")
        self.pending_habit = None

        def _then_ask():
            t = self.assistant._tts_thread
            if t and t.is_alive():
                t.join(timeout=10)
            time.sleep(0.3)
            self._ask_next()

        threading.Thread(target=_then_ask, daemon=True).start()

    def on_no(self):
        from responses import get_response
        if not self.pending_habit:
            return
        hid = self.pending_habit["id"]
        self.daily_data["done"][hid] = False
        self._save()
        response = get_response(self.pending_habit["no_key"])
        self.assistant.speak(response)
        print(f"[Habit] NO: {hid}")
        self.pending_habit = None

        def _then_ask():
            t = self.assistant._tts_thread
            if t and t.is_alive():
                t.join(timeout=10)
            time.sleep(0.3)
            self._ask_next()

        threading.Thread(target=_then_ask, daemon=True).start()

    # ── Internal: queue and ask ───────────────────────────

    def _queue_habits(self, habit_ids: list[str], window_key: str):
        if window_key in self._triggered:
            return
        self._triggered.add(window_key)
        self._save()
        to_ask = [hid for hid in habit_ids
                  if self.daily_data["done"].get(hid) is None]
        if not to_ask:
            return
        self._check_queue.extend(to_ask)
        if not self._asking:
            self._ask_next()

    def _ask_next(self):
        """
        BUG 1 FIX:
        - If not awake, put habit back in queue and wait.
          Never switch to confirm_mode while sleeping — that traps
          the recognizer and prevents wake word detection.
        - When queue empties, restore correct recognizer based on IS_AWAKE.
        """
        if not self._check_queue:
            self._asking = False
            self.pending_habit = None
            # Restore recognizer to correct mode
            if not self.assistant.IS_AWAKE:
                self.assistant.switch_to_wake_mode()
            else:
                self.assistant.switch_to_command_mode()
            return

        hid   = self._check_queue.pop(0)
        habit = HABIT_MAP.get(hid)

        if not habit:
            self._ask_next()
            return

        # Skip already answered
        if self.daily_data["done"].get(hid) is not None:
            self._ask_next()
            return

        if not self.assistant.IS_AWAKE:
            self._check_queue.insert(0, hid)
            self._asking = False
            print(f"[Habit] Sleeping — deferred: {hid}")
            return

        self._asking = True
        self.pending_habit = habit

        self.assistant.LAST_COMMAND_TIME = time.time()

        self.assistant.speak(habit["ask_msg"])
        self.assistant.switch_to_confirm_mode()
        print(f"[Habit] Asking: {hid}")

    # ── Called on wake to resume deferred habits ──────────

    def resume_on_wake(self):

        if self._check_queue and not self._asking and not self.pending_habit:
            def _ask_after_wake_tts():
                t = self.assistant._tts_thread
                if t and t.is_alive():
                    t.join(timeout=10)
                time.sleep(1.0)   # small gap after wake greeting
                self._ask_next()
            threading.Thread(target=_ask_after_wake_tts, daemon=True).start()

    # ── Main tick ─────────────────────────────────────────

    def tick(self):
        """Called every 60s."""
        if self.pending_habit or self._check_queue:
            return

        now = datetime.now()
        h   = now.hour
        m   = now.minute

        # Morning window: 7:30 – 9:00 AM
        if (h == 7 and m >= 30) or h == 8:
            morning = ["wakeup", "exercise", "meditation", "geeta", "shower", "reading"]
            self._queue_habits(morning, "morning")

        # Evening window: 7:00 – 8:00 PM
        if h == 19:
            self._queue_habits(["diet", "dinner", "project"], "evening")

        # Diary window: 8:00 – 9:00 PM
        if h == 20:
            self._queue_habits(["diary"], "diary")

        # Re-remind missed exercise/reading at 9 PM
        if h == 21 and m < 10:
            for habit in HABITS:
                hid = habit["id"]
                if habit.get("reremind") == 21:
                    if self.daily_data["done"].get(hid) is False:
                        if hid not in self._rereminded:
                            self._rereminded.add(hid)
                            self._save()
                            self.daily_data["done"][hid] = None
                            self._check_queue.append(hid)
                            if not self._asking:
                                from responses import get_response
                                self.assistant.speak(get_response("HABIT_REREMINDER"))

                                def _ask_after():
                                    t = self.assistant._tts_thread
                                    if t and t.is_alive():
                                        t.join(timeout=10)
                                    time.sleep(0.5)
                                    self._ask_next()

                                threading.Thread(target=_ask_after, daemon=True).start()

        # Sleep reminder at 9 PM
        if h == 21 and m == 0:
            if "sleep_remind" not in self._triggered:
                self._triggered.add("sleep_remind")
                self._save()
                from responses import get_response
                self.assistant.speak(get_response("HABIT_SLEEP_REMINDER"))

        # Force sleep at 10 PM
        if h == 22 and m == 0:
            if "sleep_force" not in self._triggered:
                self._triggered.add("sleep_force")
                self._save()
                from responses import get_response
                self.assistant.speak_blocking(get_response("HABIT_SLEEP_FORCE"))