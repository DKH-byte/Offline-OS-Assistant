import time
import psutil
from datetime import datetime


class SuggestionEngine:


    def __init__(self, assistant):
        self.assistant         = assistant
        self.session_start     = time.time()
        self.high_volume_start = None

        self._last: dict[str, float] = {}

        self._cooldowns = {
            "stretch_break":  2700,
            "hydration":      3600,
            "screen_break":   7200,
            "night_mode":     3600,
            "volume_warning": 1800,
            "unplug":         3600,
        }

        self.SNOOZE_DURATION  = 420
        self._snoozed: dict[str, float] = {}

        self._global_last     = 0.0
        self._global_cooldown = 300

        print("Suggestion Engine ready.")

    def accept(self, sid: str):
        self._last[sid]   = time.time()
        self._global_last = time.time()
        self._snoozed.pop(sid, None)
        print(f"[Suggestion] Accepted: {sid} — next in {self._cooldowns.get(sid, 300)//60} min")

    def snooze(self, sid: str):
        self._snoozed[sid] = time.time()
        self._global_last  = time.time()
        print(f"[Suggestion] Snoozed: {sid} — retry in {self.SNOOZE_DURATION//60} min")

    def _minutes(self):
        return (time.time() - self.session_start) / 60

    def _vol(self):
        try:
            v = self.assistant.volume
            return v.GetMasterVolumeLevelScalar() if v else 0.0
        except:
            return 0.0

    def _ready(self, sid: str, now: float) -> bool:
        if sid in self._snoozed:
            elapsed = now - self._snoozed[sid]
            if elapsed >= self.SNOOZE_DURATION:
                self._snoozed.pop(sid)
                return True
            return False
        return now - self._last.get(sid, 0) > self._cooldowns.get(sid, 300)

    def _make(self, sid: str, message: str, category: str) -> dict:
        return {"id": sid, "message": message, "category": category}

    def check_suggestions(self) -> list[dict]:
        now        = time.time()
        session    = self._minutes()
        hour       = datetime.now().hour
        battery    = psutil.sensors_battery()
        pct        = battery.percent       if battery else None
        plugged    = battery.power_plugged if battery else False
        brightness = getattr(self.assistant, "current_brightness", 50)
        vol        = self._vol()

        snoozed_candidates: list[tuple[int, dict]] = []
        normal_candidates:  list[tuple[int, dict]] = []

        if session >= 60:
            if self._ready("stretch_break", now):
                entry = (70, self._make(
                    "stretch_break",
                    "You have been active for over an hour. Want to take a quick stretch?",
                    "health"
                ))
                if "stretch_break" in self._snoozed:
                    snoozed_candidates.append(entry)
                else:
                    normal_candidates.append(entry)

        if session >= 60:
            if self._ready("hydration", now):
                entry = (65, self._make(
                    "hydration",
                    "Have you had water recently? Should I remind you to drink some?",
                    "health"
                ))
                if "hydration" in self._snoozed:
                    snoozed_candidates.append(entry)
                else:
                    normal_candidates.append(entry)

        if session >= 90:
            if self._ready("screen_break", now):
                normal_candidates.append((90, self._make(
                    "screen_break",
                    "You have been working for over 90 minutes. Should I lock the screen for a short break?",
                    "health"
                )))

        if vol > 0.45:
            if not self.high_volume_start:
                self.high_volume_start = now
            elif (now - self.high_volume_start) / 60 >= 20:
                if self._ready("volume_warning", now):
                    normal_candidates.append((60, self._make(
                        "volume_warning",
                        "Volume has been high for 20 minutes. Should I reduce it to 40 percent?",
                        "comfort"
                    )))
        else:
            self.high_volume_start = None

        if hour >= 22 and brightness > 50:
            if self._ready("night_mode", now):
                normal_candidates.append((55, self._make(
                    "night_mode",
                    "It is late and brightness is high. Should I enable night mode?",
                    "comfort"
                )))

        if pct is not None and pct >= 75 and plugged:
            if self._ready("unplug", now):
                normal_candidates.append((40, self._make(
                    "unplug",
                    "Battery is fully charged. Should I remind you to unplug?",
                    "system"
                )))

        if snoozed_candidates:
            snoozed_candidates.sort(key=lambda x: x[0], reverse=True)
            best = snoozed_candidates[0][1]
            self._last[best["id"]] = now
            return [best]

        if not normal_candidates:
            return []

        if now - self._global_last < self._global_cooldown:
            return []

        normal_candidates.sort(key=lambda x: x[0], reverse=True)
        best = normal_candidates[0][1]
        self._last[best["id"]] = now
        self._global_last = now
        return [best]