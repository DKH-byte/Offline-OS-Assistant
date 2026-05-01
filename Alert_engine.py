import time
import json
import os
import psutil
import subprocess
import threading
from datetime import datetime, date


CREATE_NO_WINDOW = 0x08000000


class AlertEnginePersistent:

    def __init__(self, assistant, persistence_file="daily_usage.json"):
        self.assistant       = assistant
        self.persistence_file = persistence_file

        self.daily_data      = self._load_daily_data()
        self.session_start   = time.time()
        self.last_break_time = time.time()
        self.last_save_time  = time.time()

        self.last_battery_emergency = 0
        self.last_emergency_sleep   = 0
        self.last_battery_critical  = 0
        self.last_eye_strain        = 0
        self.last_posture           = 0
        self.last_screen_time       = 0
        self.last_cpu_temp          = 0
        self.last_battery_full      = 0
        self.last_volume            = 0
        self.last_brightness        = 0
        self.last_break             = 0
        self.last_midnight          = 0

        self.CD_BATTERY_EMERGENCY = 300
        self.CD_EMERGENCY_SLEEP   = 1800
        self.CD_BATTERY_CRITICAL  = 900
        self.CD_EYE_STRAIN        = 1200
        self.CD_POSTURE           = 2400
        self.CD_SCREEN_TIME       = 5400
        self.CD_CPU_TEMP          = 300
        self.CD_BATTERY_FULL      = 1800
        self.CD_VOLUME            = 1200
        self.CD_BRIGHTNESS        = 1800
        self.CD_BREAK             = 5400
        self.CD_MIDNIGHT          = 3600

        self.CPU_TEMP_THRESHOLD = 85.0
        self.pending_alerts: list[dict] = []

        self._cached_temp: float | None = None
        self._temp_lock = threading.Lock()
        self._start_temp_thread()

        print(f"Alert Engine ready. Session: {self._session_min():.0f} min")

    # ── Temperature background thread ─────────────────────

    def _start_temp_thread(self):
        def _loop():
            while True:
                temp = self._fetch_temperature()
                with self._temp_lock:
                    self._cached_temp = temp
                time.sleep(30)
        threading.Thread(target=_loop, daemon=True).start()

    @staticmethod
    def _fetch_temperature() -> float | None:
        try:
            result = subprocess.run(
                ["wmic", "/namespace:\\\\root\\WMI",
                 "path", "MSAcpi_ThermalZoneTemperature",
                 "get", "CurrentTemperature"],
                capture_output=True, text=True,
                timeout=5, creationflags=CREATE_NO_WINDOW
            )
            values = []
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                try:
                    values.append((int(line) / 10.0) - 273.15)
                except ValueError:
                    continue
            return max(values) if values else None
        except:
            return None

    @staticmethod
    def _cpu_temperature() -> float | None:
        try:
            result = subprocess.run(
                ["wmic", "/namespace:\\\\root\\WMI",
                 "path", "MSAcpi_ThermalZoneTemperature",
                 "get", "CurrentTemperature"],
                capture_output=True, text=True,
                timeout=5, creationflags=CREATE_NO_WINDOW
            )
            values = []
            for line in result.stdout.strip().splitlines():
                line = line.strip()
                try:
                    values.append((int(line) / 10.0) - 273.15)
                except ValueError:
                    continue
            return max(values) if values else None
        except:
            return None

    # ── Persistence ───────────────────────────────────────

    def _load_daily_data(self):
        if not os.path.exists(self.persistence_file):
            return self._fresh_data()
        try:
            with open(self.persistence_file) as f:
                data = json.load(f)
            if data.get("date") != date.today().isoformat():
                return self._fresh_data()
            return data
        except:
            return self._fresh_data()

    def _fresh_data(self):
        return {"date": date.today().isoformat(),
                "total_screen_minutes": 0, "last_updated": time.time()}

    def _save_daily_data(self):
        try:
            self.daily_data["total_screen_minutes"] = self._session_min()
            self.daily_data["last_updated"] = time.time()
            with open(self.persistence_file, "w") as f:
                json.dump(self.daily_data, f, indent=2)
        except Exception as e:
            print(f"Alert save error: {e}")

    def _session_min(self):
        return (time.time() - self.session_start) / 60

    @staticmethod
    def _battery():
        b = psutil.sensors_battery()
        return (b.percent, b.power_plugged) if b else (None, None)

    @staticmethod
    def _hour():
        return datetime.now().hour

    # ── Main tick ─────────────────────────────────────────

    def tick(self):
        now = time.time()
        if now - self.last_save_time > 300:
            self._save_daily_data()
            self.last_save_time = now
        self._tier1(now)
        self._tier2(now)
        if not self.assistant.IS_AWAKE:
            self._queue_tier3(now)
            return
        self._tier3(now)

    # ── Tier 1 ────────────────────────────────────────────

    def _tier1(self, now):
        pct, plugged = self._battery()
        if pct is not None and pct <= 10 and not plugged:
            if now - self.last_battery_emergency > self.CD_BATTERY_EMERGENCY:
                self._force("Emergency. Battery at 10 percent. Plug in immediately.", tier=1)
                self.last_battery_emergency = now
        h = self._hour()
        if 0 <= h <= 5:
            if now - self.last_emergency_sleep > self.CD_EMERGENCY_SLEEP:
                self._force("Health alert. It is very late. You should rest now.", tier=1)
                self.last_emergency_sleep = now

    # ── Tier 2 ────────────────────────────────────────────

    def _tier2(self, now):
        pct, plugged = self._battery()
        total = self._session_min()

        if pct is not None and 10 < pct <= 20 and not plugged:
            if now - self.last_battery_critical > self.CD_BATTERY_CRITICAL:
                self._force("Battery at 20 percent. Please plug in soon.", tier=2)
                self.last_battery_critical = now

        if total >= 20:
            if now - self.last_eye_strain > self.CD_EYE_STRAIN:
                self._force("Eye care. Look at something far away for 20 seconds.", tier=2)
                self.last_eye_strain = now

        if total >= 40:
            if now - self.last_posture > self.CD_POSTURE:
                self._force("Posture check. Sit up straight and adjust your screen.", tier=2)
                self.last_posture = now

        if total >= 180:
            if now - self.last_screen_time > self.CD_SCREEN_TIME:
                self._force(
                    f"You have been at the screen for {int(total / 60)} hours. Seriously, take a break.",
                    tier=2)
                self.last_screen_time = now

        with self._temp_lock:
            temp = self._cached_temp
        if temp is not None and temp >= self.CPU_TEMP_THRESHOLD:
            if now - self.last_cpu_temp > self.CD_CPU_TEMP:
                self._force(
                    f"Warning. CPU temperature is {temp:.0f} degrees. Consider closing heavy applications.",
                    tier=2)
                self.last_cpu_temp = now

    # ── Tier 3 ────────────────────────────────────────────

    def _tier3(self, now):
        pct, plugged = self._battery()
        h = self._hour()

        if pct is not None and pct >= 80 and plugged:
            if now - self.last_battery_full > self.CD_BATTERY_FULL:
                self.assistant.speak("Battery fully charged. You can unplug.")
                self.last_battery_full = now

        vol = self.assistant.volume
        if vol:
            try:
                if vol.GetMasterVolumeLevelScalar() > 0.70:
                    if now - self.last_volume > self.CD_VOLUME:
                        self.assistant.speak("Volume is very high. Consider lowering it.")
                        self.last_volume = now
            except: pass

        brightness = getattr(self.assistant, "current_brightness", None)
        if brightness and h >= 22 and brightness > 60:
            if now - self.last_brightness > self.CD_BRIGHTNESS:
                self.assistant.speak("Screen brightness is high. Consider dimming it for night.")
                self.last_brightness = now

        if (now - self.last_break_time) / 60 >= 90:
            if now - self.last_break > self.CD_BREAK:
                self.assistant.speak("You have been working for 90 minutes. Take a short break.")
                self.last_break = now
                self.last_break_time = now

        if h == 0:
            if now - self.last_midnight > self.CD_MIDNIGHT:
                self.assistant.speak("It is midnight. Consider wrapping up soon.")
                self.last_midnight = now

    # ── Queue tier 3 while sleeping ───────────────────────

    def _queue_tier3(self, now):
        pct, plugged = self._battery()
        queued = []

        if pct is not None and pct >= 80 and plugged:
            if now - self.last_battery_full > self.CD_BATTERY_FULL:
                queued.append({"type": "battery_full", "msg": "Battery is fully charged."})
                self.last_battery_full = now

        if (now - self.last_break_time) / 60 >= 90:
            if now - self.last_break > self.CD_BREAK:
                queued.append({"type": "break", "msg": "You have been working a long time. Take a break."})
                self.last_break = now
                self.last_break_time = now

        existing = {a["type"] for a in self.pending_alerts}
        for alert in queued:
            if alert["type"] not in existing:
                self.pending_alerts.append(alert)

        if queued:
            print(f"[Sleeping] Queued: {', '.join(a['type'] for a in queued)}")

    # ── Force alert ───────────────────────────────────────

    def _force(self, message, tier=1):

        label = "EMERGENCY" if tier == 1 else "CRITICAL"
        print(f"[{label}] {message}")

        was_awake = self.assistant.IS_AWAKE

        # Save and clear any pending habit question
        pending_habit_backup = None
        if hasattr(self.assistant, 'habit_engine'):
            he = self.assistant.habit_engine
            if he.pending_habit:
                pending_habit_backup = he.pending_habit["id"]
                he._check_queue.insert(0, pending_habit_backup)
                he.pending_habit = None
                he._asking = False

        if not was_awake:
            self.assistant.IS_AWAKE = True
            self.assistant.switch_to_command_mode()

        if hasattr(self.assistant, "speak_blocking"):
            self.assistant.speak_blocking(message)
        else:
            self.assistant.speak(message)
            time.sleep(1.5)

        if not was_awake:
            self.assistant.IS_AWAKE = False
            self.assistant.switch_to_wake_mode()
            print("Returned to sleep mode.")

    # ── Deliver on wake ───────────────────────────────────

    def deliver_pending_alerts(self):
        if not self.pending_alerts:
            return
        msgs = [a["msg"] for a in self.pending_alerts]
        if len(msgs) == 1:
            self.assistant.speak(msgs[0])
        else:
            self.assistant.speak(f"{len(msgs)} reminders. " + " ".join(msgs[:2]))
        self.pending_alerts.clear()

    # ── Cleanup ───────────────────────────────────────────

    def cleanup(self):
        self._save_daily_data()
        print("Daily usage saved.")