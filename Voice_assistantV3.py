import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def resource_path(relative: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(os.path.dirname(sys.executable), relative)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative)

CREATE_NO_WINDOW = 0x08000000

import json
import queue
import time
import threading
import subprocess
import sounddevice as sd
import pyautogui
import webbrowser
import pyttsx3
from vosk import Model, KaldiRecognizer
from pycaw.pycaw import AudioUtilities
import screen_brightness_control as sbc
import random
from datetime import datetime
import psutil
import re

from Alert_engine import AlertEnginePersistent
from suggestions  import SuggestionEngine
from habits       import HabitEngine, DONE_PHRASES, HABIT_MAP

from responses import (
    WAKE_VOICE_MAP, WAKE_WORDS, RESPONSES,
    get_response, wake_message
)

pyautogui.FAILSAFE = False


def get_sample_rate(device=None) -> int:
    try:
        return int(sd.query_devices(device, kind='input')['default_samplerate'])
    except:
        return 16000


class VoiceAssistant:
    def __init__(self):
        print("Initializing Voice Assistant...")

        print("\n── Audio devices ──")
        print(sd.query_devices())
        print("───────────────────\n")

        self.MIC_INDEX = None

        # ── TTS ──────────────────────────────────────────────
        self.current_voice = "david"
        self._tts_thread = None
        self.IS_SPEAKING = False
        self.IGNORE_UNTIL = 0
        self.LAST_TTS_END = 0
        self.VOICE_FEEDBACK_ENABLED = True

        # ── Volume ───────────────────────────────────────────
        try:
            self.device = AudioUtilities.GetSpeakers()
            self.volume = self.device.EndpointVolume
        except Exception as e:
            print(f"Volume interface failed: {e}")
            self.volume = None

        # ── Brightness ───────────────────────────────────────
        try:
            self.current_brightness = sbc.get_brightness(display=0)[0]
        except:
            self.current_brightness = 50

        # ── State ────────────────────────────────────────────
        self.IS_AWAKE = False
        self.LAST_COMMAND_TIME = 0.0
        self.WAKE_WORD_TIMEOUT = 300.0

        self.pending_suggestion = None
        self.pending_system_action = None
        self.pending_system_parameter = None
        self.system_confirm_time = 0
        self.SYSTEM_CONFIRM_TIMEOUT = 15

        self.ACTIVE_REPEAT_COMMAND = None
        self.LAST_REPEAT_TIME = 0.0
        self.REPEAT_INTERVAL = 1.5
        self.REPEAT_TIMEOUT = 12.0
        self.LAST_SCROLL_TIME = 0.0
        self.SCROLL_DELAY = 0.02

        # ── Constants ────────────────────────────────────────
        self.VOLUME_STEP = 0.05
        self.BRIGHTNESS_STEP = 10
        self.SCROLL_STEP = 60

        # ── Timers ───────────────────────────────────────────
        self.last_alert_check = 0
        self.ALERT_INTERVAL = 60.0
        self.last_suggestion_check = 0
        self.SUGGESTION_INTERVAL = 600.0
        self.last_habit_check = 0
        self.HABIT_CHECK_INTERVAL = 60.0

        # ── Audio watchdog ───────────────────────────────────
        self.LAST_AUDIO_TIME = time.time()
        self.AUDIO_WATCHDOG_TIMEOUT = 10.0
        self.TTS_GRACE_PERIOD = 5.0

        self.SAMPLE_RATE = get_sample_rate(self.MIC_INDEX)

        self.BLOCK_SIZE = max(1024, int(self.SAMPLE_RATE * 0.25))

        # ── Commands ─────────────────────────────────────────
        self.COMMANDS = {
            "TIME":           ["what time is it", "time", "current time"],
            "DATE":           ["date", "today's date", "what is the date"],
            "DAY":            ["day", "what day is it", "today"],
            "BATTERY":        ["battery", "battery percentage", "battery status"],
            "STATUS":         ["status", "date and time", "what's up"],
            "HABITS":         ["habits", "habit score", "how am i doing", "my habits"],
            "CLOSE":          ["close"],
            "MINIMIZE":       ["minimize"],
            "MAXIMIZE":       ["maximize", "maximise", "fullscreen", "full screen"],
            "ZOOM IN":        ["zoom in", "bigger"],
            "ZOOM OUT":       ["zoom out", "smaller"],
            "VOLUME UP":      ["volume up", "louder"],
            "VOLUME DOWN":    ["volume down", "quieter"],
            "BRIGHTNESS UP":  ["brightness up", "brighter"],
            "BRIGHTNESS DOWN":["brightness down", "dimmer"],
            "MUTE":           ["mute"],
            "SCREENSHOT":     ["screenshot"],
            "TASK MANAGER":   ["task manager"],
            "LOCK":           ["lock", "lock screen"],
            "DELETE":         ["delete"],
            "COPY":           ["copy"],
            "PASTE":          ["paste", "apply"],
            "CUT":            ["cut"],
            "SAVE":           ["save"],
            "SELECT ALL":     ["select all"],
            "UNDO":           ["undo"],
            "REDO":           ["redo"],
            "SCROLL UP":      ["scroll up"],
            "SCROLL DOWN":    ["scroll down"],
            "NEXT WINDOW":    ["next window", "switch window"],
            "PREVIOUS WINDOW":["previous window"],
            "NEW TAB":        ["new tab"],
            "CLOSE TAB":      ["close tab"],
            "NEXT TAB":       ["next tab"],
            "PREVIOUS TAB":   ["previous tab"],
            "REFRESH":        ["refresh", "reload"],
            "SEARCH":         ["search", "find"],
            "PLAY PAUSE":     ["play", "pause", "play pause"],
            "NEXT TRACK":     ["next song", "next track"],
            "PREVIOUS TRACK": ["previous song", "previous track"],
            "SHUTDOWN":       ["shut down", "power off"],
            "RESTART":        ["restart", "reboot"],
            "SHOW DESKTOP":   ["show desktop", "go to desktop"],
            "SNAP LEFT":      ["snap left", "tile left"],
            "SNAP RIGHT":     ["snap right", "tile right"],
            "SNAP UP":        ["snap up", "tile up"],
            "SNAP DOWN":      ["snap down", "tile down"],
            "PRINT":          ["print"],
            "HOME":           ["home"],
            "SCROLL TOP":     ["scroll top", "go to top"],
            "SCROLL BOTTOM":  ["scroll bottom", "go to bottom"],
            "INCOGNITO":      ["incognito", "private mode"],
            "REOPEN TAB":     ["reopen tab", "open closed tab"],
            "CLOSE ALL TABS": ["close all tabs", "close every tab"],
            "HARD REFRESH":   ["hard refresh", "force refresh"],
            "ENTER":          ["enter", "okay", "ok"],
            "PLAY MUSIC":     ["play music", "play some music", "start music"],
            "THANK YOU":      ["thank you", "thanks", "appreciate it", "thanks a lot"],
            "ESCAPE":         ["escape"],
        }

        self.REPEATABLE_COMMANDS = {
            "VOLUME UP", "VOLUME DOWN",
            "BRIGHTNESS UP", "BRIGHTNESS DOWN",
            "ZOOM IN", "ZOOM OUT",
            "SCROLL UP", "SCROLL DOWN"
        }

        self.OPEN_TARGETS = {
            "youtube":       "https://youtube.com",
            "mail":          "https://mail.google.com",
            "chat":          "https://chatgpt.com",
            "claude":        "https://claude.ai/new",
            "computer":      "explorer",
            "files":         "explorer",
            "note":          "notepad",
            "chrome":        "chrome",
            "calculator":    "calc",
            "jam":           "https://gemini.google.com/app",
            "settings":      "ms-settings:",
            "control panel": "control",
            "spotify":       "",
            "discord":       "",
            "llama":         ""
        }

        self.PROCESS_MAP = {
            "spotify":      "Spotify.exe",
            "discord":      "Discord.exe",
            "chrome":       "chrome.exe",
            "note":         "notepad.exe",
            "notepad":      "notepad.exe",
            "calculator":   "CalculatorApp.exe",
            "task manager": "Taskmgr.exe",
            "llama":        "ollama.exe"
        }

        # Precompile word-boundary regex patterns for fast, accurate matching
        self._sorted_cmd_phrases = sorted(
            [(cmd, phrase) for cmd, keys in self.COMMANDS.items() for phrase in keys],
            key=lambda x: len(x[1]),
            reverse=True
        )
        self._cmd_patterns = [(cmd, re.compile(r"\b" + re.escape(phrase) + r"\b"))
                              for cmd, phrase in self._sorted_cmd_phrases]

        # ── Operations ───────────────────────────────────────
        self.OPERATIONS = {
            "VOLUME UP":      self.do_volume_up,
            "VOLUME DOWN":    self.do_volume_down,
            "BRIGHTNESS UP":  self.do_brightness_up,
            "BRIGHTNESS DOWN":self.do_brightness_down,
            "MUTE":           self.do_mute,
            "TIME":           self.do_time,
            "DATE":           self.do_date,
            "DAY":            self.do_day,
            "STATUS":         self.do_status,
            "BATTERY":        self.do_battery,
            "HABITS":         self.do_habits,
            "COPY":           self.do_copy,
            "PASTE":          self.do_paste,
            "CUT":            self.do_cut,
            "SELECT ALL":     self.do_select_all,
            "UNDO":           self.do_undo,
            "REDO":           self.do_redo,
            "CLOSE":          self.do_close,
            "MINIMIZE":       self.do_minimize,
            "MAXIMIZE":       self.do_maximize,
            "ZOOM IN":        self.do_zoom_in,
            "ZOOM OUT":       self.do_zoom_out,
            "SCREENSHOT":     self.do_screenshot,
            "TASK MANAGER":   self.do_task_manager,
            "LOCK":           self.do_lock,
            "SAVE":           self.do_save,
            "SCROLL UP":      self.do_scroll_up,
            "SCROLL DOWN":    self.do_scroll_down,
            "NEXT WINDOW":    self.do_next_window,
            "PREVIOUS WINDOW":self.do_previous_window,
            "DELETE":         self.do_delete,
            "SEARCH":         self.do_search,
            "NEW TAB":        self.do_new_tab,
            "ESCAPE":         self.do_escape,
            "CLOSE TAB":      self.do_close_tab,
            "NEXT TAB":       self.do_next_tab,
            "PREVIOUS TAB":   self.do_previous_tab,
            "REFRESH":        self.do_refresh,
            "PLAY PAUSE":     self.do_play_pause,
            "NEXT TRACK":     self.do_next_track,
            "PREVIOUS TRACK": self.do_previous_track,
            "SHUTDOWN":       self.do_shutdown,
            "RESTART":        self.do_restart,
            "STOP":           self.do_stop,
            "SHOW DESKTOP":   self.do_show_desktop,
            "SNAP LEFT":      self.do_snap_left,
            "SNAP RIGHT":     self.do_snap_right,
            "SNAP UP":        self.do_snap_up,
            "SNAP DOWN":      self.do_snap_down,
            "HOME":           self.do_home,
            "SCROLL TOP":     self.do_scroll_top,
            "SCROLL BOTTOM":  self.do_scroll_bottom,
            "INCOGNITO":      self.do_incognito,
            "REOPEN TAB":     self.do_reopen_tab,
            "CLOSE ALL TABS": self.do_close_all_tabs,
            "HARD REFRESH":   self.do_hard_refresh,
            "THANK YOU":      self.do_thank_you,
            "PLAY MUSIC":     self.do_play_music,
            "ENTER":          self.do_enter,
        }

        # ── Grammars ─────────────────────────────────────────
        # BUG 5 FIX: removed empty string "" from grammar list
        self.WAKE_GRAMMAR = json.dumps(WAKE_WORDS)
        self.COMMAND_GRAMMAR = json.dumps(
            [kw for words in self.COMMANDS.values() for kw in words] +
            [f"open {k}" for k in self.OPEN_TARGETS] +
            [f"close {k}" for k in self.PROCESS_MAP] +
            list(DONE_PHRASES.keys()) +
            ["sleep"]
        )
        self.CONFIRM_GRAMMAR = json.dumps(["yes", "no", "yeah", "yep", "nah", "nope"])
        self.STOP_GRAMMAR    = json.dumps(["stop", "stop it", "stop now", "enough"])

        # ── Model ─────────────────────────────────────────────
        self.MODEL_PATH = resource_path("model")

        try:
            self.model = Model(self.MODEL_PATH)
        except Exception as e:
            raise SystemExit(f"VOSK model load failed: {e}")

        self._build_recognizers()
        self.q = queue.Queue(maxsize=70)

        # ── Engines ──────────────────────────────────────────
        self.alert_engine      = AlertEnginePersistent(self)
        self.suggestion_engine = SuggestionEngine(self)
        self.habit_engine      = HabitEngine(self)

        print("Voice Assistant Ready.\n")

    # =========================================================
    # RECOGNIZERS
    # =========================================================

    def _build_recognizers(self):
        self.recognizer_stop_only = KaldiRecognizer(self.model, self.SAMPLE_RATE, self.STOP_GRAMMAR)
        self.recognizer_wake      = KaldiRecognizer(self.model, self.SAMPLE_RATE, self.WAKE_GRAMMAR)
        self.recognizer_command   = KaldiRecognizer(self.model, self.SAMPLE_RATE, self.COMMAND_GRAMMAR)
        self.recognizer_confirm   = KaldiRecognizer(self.model, self.SAMPLE_RATE, self.CONFIRM_GRAMMAR)
        self.recognizer = self.recognizer_wake

    # =========================================================
    # TTS
    # =========================================================

    def speak(self, text):
        if not self.VOICE_FEEDBACK_ENABLED or self.IS_SPEAKING:
            return
        self.IS_SPEAKING = True

        def _worker():
            try:
                engine = pyttsx3.init(driverName="sapi5")
                engine.setProperty("rate", 180)
                engine.setProperty("volume", 1.0)
                for v in engine.getProperty("voices"):
                    if self.current_voice.lower() in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
                engine.say(text)
                engine.runAndWait()
                engine.stop()
                del engine
            except Exception as e:
                print(f"TTS error: {e}")
            finally:
                self.IS_SPEAKING = False
                self.LAST_TTS_END = time.time()
                self.IGNORE_UNTIL = time.time() + 0.05

        t = threading.Thread(target=_worker, daemon=True)
        self._tts_thread = t
        t.start()

    def speak_blocking(self, text):
        t = self._tts_thread
        if t and t.is_alive():
            t.join(timeout=10)
        if not self.VOICE_FEEDBACK_ENABLED:
            return
        try:
            self.IS_SPEAKING = True
            engine = pyttsx3.init(driverName="sapi5")
            engine.setProperty("rate", 180)
            engine.setProperty("volume", 1.0)
            for v in engine.getProperty("voices"):
                if self.current_voice.lower() in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()
            engine.stop()
            del engine
        except Exception as e:
            print(f"TTS blocking error: {e}")
        finally:
            self.IS_SPEAKING = False
            self.LAST_TTS_END = time.time()
            self.IGNORE_UNTIL = time.time() + 0.05

    # =========================================================
    # HELPERS
    # =========================================================

    def get_command(self, text):
        # Use precompiled word-boundary regex patterns for accurate matching
        for cmd, pattern in self._cmd_patterns:
            if pattern.search(text):
                return cmd
        return None

    def open_target(self, name):
        target = self.OPEN_TARGETS.get(name)
        if not target:
            return
        try:
            if target.startswith("http"):
                webbrowser.open_new_tab(target)
            else:
                os.startfile(target)
            print(f"   Opened {name}")
        except Exception as e:
            print(f"Open failed: {e}")

    def close_target(self, name):
        process = self.PROCESS_MAP.get(name)
        if process:
            try:
                subprocess.run(
                    ["taskkill", "/f", "/im", process],
                    creationflags=CREATE_NO_WINDOW,
                    capture_output=True
                )
                print(f"   Closed {name} ({process})")
                self.speak(f"Closing {name}.")
            except Exception as e:
                print(f"Close failed: {e}")
        else:
            print(f"Unknown close target: {name}")

    def execute_suggestion(self, suggestion):
        sid = suggestion.get("id", "")
        if sid == "night_mode":
            try:
                sbc.set_brightness(20)
                self.current_brightness = 20
                self.speak("Night mode activated.")
            except:
                self.speak("Failed to dim screen.")
        elif sid == "volume_warning":
            if self.volume:
                try:
                    self.volume.SetMasterVolumeLevelScalar(0.4, None)
                    self.speak("Volume reduced to 40 percent.")
                except: pass
        elif sid == "stretch_break":
            self.speak("Stand up and stretch for a minute.")
        elif sid == "screen_break":
            self.speak("Locking screen for a break.")
            time.sleep(1)
            subprocess.run(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                creationflags=CREATE_NO_WINDOW
            )
        elif sid == "idle_sleep":
            self.IS_AWAKE = False
            self.switch_to_wake_mode()
            self.speak("Going to sleep.")
        else:
            self.speak("Done.")

    def switch_to_wake_mode(self):
        self.ACTIVE_REPEAT_COMMAND = None
        self.recognizer = self.recognizer_wake

    def switch_to_command_mode(self):
        self.ACTIVE_REPEAT_COMMAND = None
        self.recognizer = self.recognizer_command

    def switch_to_confirm_mode(self):
        self.ACTIVE_REPEAT_COMMAND = None
        self.recognizer = self.recognizer_confirm

    def switch_to_stop_mode(self):
        self.recognizer = self.recognizer_stop_only
        try: self.recognizer.Reset()
        except: pass

    # =========================================================
    # OPERATIONS
    # =========================================================

    def do_thank_you(self):   self.speak(get_response("THANK YOU"))
    def do_habits(self):      self.speak(self.habit_engine.get_score_message())

    def do_play_music(self):
        spotify = r"C:\Users\deshh\AppData\Roaming\Spotify\Spotify.exe"
        try:
            os.startfile(spotify)
            time.sleep(3)
            pyautogui.press("playpause")
            self.speak(get_response("PLAY MUSIC"))
        except Exception as e:
            print(f"Spotify error: {e}")
            self.speak("Could not open Spotify.")

    def do_volume_up(self):
        if not self.volume: return
        try:
            v = self.volume.GetMasterVolumeLevelScalar() + self.VOLUME_STEP
            self.volume.SetMasterVolumeLevelScalar(min(1.0, v), None)
        except: pass

    def do_volume_down(self):
        if not self.volume: return
        try:
            v = self.volume.GetMasterVolumeLevelScalar() - self.VOLUME_STEP
            self.volume.SetMasterVolumeLevelScalar(max(0.0, v), None)
        except: pass

    def do_mute(self):
        if not self.volume: return
        try: self.volume.SetMute(0 if self.volume.GetMute() else 1, None)
        except: pass

    def do_brightness_up(self):
        try:
            self.current_brightness = min(100, self.current_brightness + self.BRIGHTNESS_STEP)
            sbc.set_brightness(self.current_brightness)
        except: pass

    def do_brightness_down(self):
        try:
            self.current_brightness = max(0, self.current_brightness - self.BRIGHTNESS_STEP)
            sbc.set_brightness(self.current_brightness)
        except: pass

    def do_time(self):    self.speak(f"It is {time.strftime('%I:%M %p')}")
    def do_date(self):    self.speak(f"Today's date is {datetime.now().strftime('%B %d, %Y')}")
    def do_day(self):     self.speak(f"Today is {datetime.now().strftime('%A')}")
    def do_status(self):
        n = datetime.now()
        self.speak(f"It is {n.strftime('%I:%M %p')}. Today is {n.strftime('%A, %B %d, %Y')}.")

    def do_battery(self):
        b = psutil.sensors_battery()
        if b:
            self.speak(f"Battery is at {b.percent:.0f} percent, {'charging' if b.power_plugged else 'on battery'}.")
        else:
            self.speak("Battery information not available.")

    def do_escape(self):      pyautogui.press("esc");              time.sleep(0.05)
    def do_copy(self):        pyautogui.hotkey("ctrl", "c");       time.sleep(0.05)
    def do_paste(self):       pyautogui.hotkey("ctrl", "v");       time.sleep(0.05)
    def do_cut(self):         pyautogui.hotkey("ctrl", "x");       time.sleep(0.05)
    def do_select_all(self):  pyautogui.hotkey("ctrl", "a");       time.sleep(0.05)
    def do_undo(self):        pyautogui.hotkey("ctrl", "z");       time.sleep(0.05)
    def do_redo(self):        pyautogui.hotkey("ctrl", "y");       time.sleep(0.05)
    def do_close(self):       pyautogui.hotkey("alt",  "f4");      time.sleep(0.05)
    def do_minimize(self):    pyautogui.hotkey("win",  "d");       time.sleep(0.05)
    def do_maximize(self):    pyautogui.hotkey("win",  "up");      time.sleep(0.05)
    def do_zoom_in(self):     pyautogui.hotkey("ctrl", "+");       time.sleep(0.05)
    def do_zoom_out(self):    pyautogui.hotkey("ctrl", "-");       time.sleep(0.05)
    def do_save(self):        pyautogui.hotkey("ctrl", "s");       time.sleep(0.05)
    def do_enter(self):       pyautogui.press("enter");            time.sleep(0.05)
    def do_delete(self):      pyautogui.press("delete")
    def do_search(self):      pyautogui.hotkey("ctrl", "f")
    def do_new_tab(self):     pyautogui.hotkey("ctrl", "t")
    def do_close_tab(self):   pyautogui.hotkey("ctrl", "w")
    def do_next_tab(self):    pyautogui.hotkey("ctrl", "tab")
    def do_previous_tab(self):pyautogui.hotkey("ctrl", "shift", "tab")
    def do_refresh(self):     pyautogui.hotkey("ctrl", "r")
    def do_hard_refresh(self):pyautogui.hotkey("ctrl", "shift", "r")
    def do_reopen_tab(self):  pyautogui.hotkey("ctrl", "shift", "t")
    def do_close_all_tabs(self): pyautogui.hotkey("ctrl", "shift", "w")
    def do_incognito(self):   pyautogui.hotkey("ctrl", "shift", "n")
    def do_next_window(self): pyautogui.hotkey("alt",  "tab")
    def do_previous_window(self): pyautogui.hotkey("alt", "shift", "tab")
    def do_play_pause(self):  pyautogui.press("playpause")
    def do_next_track(self):  pyautogui.press("nexttrack")
    def do_previous_track(self): pyautogui.press("prevtrack")
    def do_screenshot(self):  pyautogui.hotkey("win", "shift", "s")
    def do_show_desktop(self):pyautogui.hotkey("win", "d")
    def do_snap_left(self):   pyautogui.hotkey("win", "left")
    def do_snap_right(self):  pyautogui.hotkey("win", "right")
    def do_snap_up(self):     pyautogui.hotkey("win", "up")
    def do_snap_down(self):   pyautogui.hotkey("win", "down")
    def do_home(self):        pyautogui.press("home")
    def do_scroll_top(self):  pyautogui.hotkey("ctrl", "home")
    def do_scroll_bottom(self): pyautogui.hotkey("ctrl", "end")
    def do_scroll_up(self):   pyautogui.scroll(self.SCROLL_STEP)
    def do_scroll_down(self): pyautogui.scroll(-self.SCROLL_STEP)

    def do_task_manager(self):
        subprocess.Popen(["taskmgr.exe"], creationflags=CREATE_NO_WINDOW)
    def do_lock(self):
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], creationflags=CREATE_NO_WINDOW)
    def do_shutdown(self):
        subprocess.run(["shutdown", "/s", "/t", "0"], creationflags=CREATE_NO_WINDOW)
    def do_restart(self):
        subprocess.run(["shutdown", "/r", "/t", "0"], creationflags=CREATE_NO_WINDOW)
    def do_stop(self):
        self.ACTIVE_REPEAT_COMMAND = None
        self.LAST_REPEAT_TIME = time.time()

    def callback(self, indata, frames, time_info, status):
        if self.IS_SPEAKING:
            return
        self.LAST_AUDIO_TIME = time.time()

        try:
            self.q.put_nowait(bytes(indata))
        except queue.Full:
            while not self.q.empty():
                try: self.q.get_nowait()
                except: break

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def run(self):
        print("Voice Assistant Running — say 'jarvis' or 'friday' to wake.")
        print("Press Ctrl+C to stop.\n")

        while True:
            try:
                self.SAMPLE_RATE = get_sample_rate(self.MIC_INDEX)
                self._build_recognizers()

                try:
                    info = sd.query_devices(self.MIC_INDEX, kind='input')
                    print(f"Using mic: {info['name']}  ({self.SAMPLE_RATE} Hz)")
                except Exception as e:
                    print(f"No microphone: {e}. Retrying in 2s...")
                    time.sleep(2)
                    continue

                with sd.InputStream(
                        device=self.MIC_INDEX,
                        samplerate=self.SAMPLE_RATE,
                        blocksize=self.BLOCK_SIZE,
                        dtype="int16",
                        channels=1,
                        callback=self.callback):

                    print("Audio stream started.")
                    self.LAST_AUDIO_TIME = time.time()

                    while True:
                        now = time.time()

                        # ── Watchdog ──────────────────────────
                        if (not self.IS_SPEAKING and
                                now - self.LAST_TTS_END > self.TTS_GRACE_PERIOD and
                                now - self.LAST_AUDIO_TIME > self.AUDIO_WATCHDOG_TIMEOUT):
                            print("No audio 10s — restarting.")
                            raise RuntimeError("timeout")

                        # ── Alert tick ────────────────────────
                        if now - self.last_alert_check > self.ALERT_INTERVAL:
                            self.alert_engine.tick()
                            self.last_alert_check = now

                        # ── Habit tick ────────────────────────
                        # BUG 7 FIX: don't tick while speaking, pending suggestion,
                        # or pending system action
                        if now - self.last_habit_check > self.HABIT_CHECK_INTERVAL:
                            if (not self.IS_SPEAKING
                                    and not self.pending_suggestion
                                    and not self.pending_system_action):
                                self.habit_engine.tick()
                            self.last_habit_check = now

                        # ── Suggestion check ──────────────────
                        if now - self.last_suggestion_check > self.SUGGESTION_INTERVAL:
                            if (self.IS_AWAKE
                                    and not self.pending_suggestion
                                    and not self.IS_SPEAKING
                                    and not self.ACTIVE_REPEAT_COMMAND
                                    and not self.pending_system_action
                                    and not self.habit_engine.pending_habit):
                                suggestions = self.suggestion_engine.check_suggestions()
                                if suggestions:
                                    self.pending_suggestion = suggestions[0]
                                    self.speak(suggestions[0].get("message", "I have a suggestion."))
                                    self.switch_to_confirm_mode()
                            self.last_suggestion_check = now

                        # ── System confirmation timeout ───────
                        if self.pending_system_action:
                            if now - self.system_confirm_time > self.SYSTEM_CONFIRM_TIMEOUT:
                                self.pending_system_action = None
                                self.pending_system_parameter = None
                                self.switch_to_command_mode()
                                self.speak("Confirmation timed out.")
                                continue

                        # ── Auto-sleep ────────────────────────
                        # BUG 3 FIX: don't auto-sleep while a habit question is pending
                        if self.IS_AWAKE:
                            if (now - self.LAST_COMMAND_TIME > self.WAKE_WORD_TIMEOUT
                                    and not self.habit_engine.pending_habit
                                    and not self.habit_engine._check_queue):
                                self.IS_AWAKE = False
                                self.ACTIVE_REPEAT_COMMAND = None
                                self.switch_to_wake_mode()
                                self.speak(random.choice(RESPONSES["SLEEP"]))
                                print("Auto-sleep.")
                                continue

                        # ── Echo grace ────────────────────────
                        if now < self.IGNORE_UNTIL:
                            try: self.q.get_nowait()
                            except queue.Empty: pass
                            continue

                        # ── Get audio ─────────────────────────
                        try:
                            data = self.q.get(timeout=0.001)
                        except queue.Empty:
                            data = None


                        # ── Full recognition ──────────────────
                        if data and self.recognizer.AcceptWaveform(data):
                            text = json.loads(
                                self.recognizer.Result()
                            ).get("text", "").strip().lower()

                            if self.recognizer == self.recognizer_stop_only:
                                if text.startswith("stop"):
                                    self.ACTIVE_REPEAT_COMMAND = None
                                    self.switch_to_command_mode()
                                    self.IGNORE_UNTIL = now + 0.5
                                    self.speak("Stopped.")
                                continue

                            if not text:
                                continue

                            print("Heard:", text)

                            # ── Wake word ─────────────────────
                            if not self.IS_AWAKE:
                                for word, voice in WAKE_VOICE_MAP.items():
                                    if word in text:
                                        self.current_voice = voice
                                        self.IS_AWAKE = True
                                        self.LAST_COMMAND_TIME = now
                                        self.switch_to_command_mode()
                                        print(f"Awake ({word})")
                                        self.speak(wake_message(self.current_voice))
                                        self.alert_engine.deliver_pending_alerts()
                                        # BUG 1 FIX: resume any deferred habit questions
                                        self.habit_engine.resume_on_wake()
                                        break
                                continue

                            # ── Sleep ─────────────────────────
                            if "sleep" in text:
                                self.IS_AWAKE = False
                                self.pending_system_action = None
                                self.pending_suggestion = None
                                self.switch_to_wake_mode()
                                self.speak(random.choice(RESPONSES["SLEEP"]))
                                continue

                            # ── Habit yes/no ──────────────────
                            # Handled BEFORE suggestion/system confirms
                            if self.habit_engine.pending_habit:
                                if text in ["yes", "yeah", "yep"]:
                                    self.habit_engine.on_yes()
                                elif text in ["no", "nah", "nope"]:
                                    self.habit_engine.on_no()
                                else:
                                    continue   # wait for a valid yes/no
                                # Recognizer restored inside on_yes/on_no → _ask_next
                                continue

                            # ── Suggestion confirmation ───────
                            if self.pending_suggestion:
                                sid = self.pending_suggestion.get("id", "")
                                if text in ["yes", "yeah", "yep"]:
                                    self.suggestion_engine.accept(sid)
                                    self.execute_suggestion(self.pending_suggestion)
                                else:
                                    self.suggestion_engine.snooze(sid)
                                    self.speak("Okay. I'll remind you again shortly.")
                                self.pending_suggestion = None
                                self.switch_to_command_mode()
                                continue

                            # ── System confirmation ───────────
                            if self.pending_system_action:
                                if text in ["yes", "yeah", "yep"]:
                                    action    = self.pending_system_action
                                    parameter = self.pending_system_parameter
                                    self.pending_system_action    = None
                                    self.pending_system_parameter = None
                                    self.switch_to_command_mode()
                                    self.speak(parameter or f"Executing {action.lower()}.")
                                    time.sleep(0.5)
                                    if action in self.OPERATIONS:
                                        self.OPERATIONS[action]()
                                else:
                                    self.pending_system_action    = None
                                    self.pending_system_parameter = None
                                    self.switch_to_command_mode()
                                    self.speak("Cancelled.")
                                continue

                            # ── Done X (habit mark) ───────────
                            if text in DONE_PHRASES:
                                hid = DONE_PHRASES[text]
                                msg = self.habit_engine.mark_done(hid)
                                self.speak(msg)
                                self.LAST_COMMAND_TIME = now
                                continue

                            # ── Open command ──────────────────
                            if text.startswith("open "):
                                name = text.split(" ", 1)[1].strip()
                                if name in self.OPEN_TARGETS:
                                    self.speak(f"Opening {name}.")
                                    self.open_target(name)
                                else:
                                    self.speak(f"I don't know how to open {name}.")
                                continue

                            # ── Close app by name ─────────────
                            if text.startswith("close "):
                                name = text.split(" ", 1)[1].strip()
                                if name in self.PROCESS_MAP:
                                    self.close_target(name)
                                    continue

                            # ── Normal command ────────────────
                            cmd = self.get_command(text)
                            if not cmd:
                                print("No match.")
                                continue

                            print("Command:", cmd)
                            self.LAST_COMMAND_TIME = now

                            if cmd in ("SHUTDOWN", "RESTART"):
                                self.pending_system_action = cmd
                                self.system_confirm_time = now
                                self.switch_to_confirm_mode()
                                self.speak(f"Are you sure you want to {cmd.lower()}?")
                                continue

                            if cmd in ("TIME", "DATE", "DAY", "BATTERY", "STATUS",
                                       "THANK YOU", "HABITS"):
                                self.OPERATIONS[cmd]()
                                continue

                            self.speak(get_response(cmd))
                            try:
                                if cmd in self.REPEATABLE_COMMANDS:
                                    self.ACTIVE_REPEAT_COMMAND = cmd
                                    self.OPERATIONS[cmd]()
                                    self.LAST_REPEAT_TIME = now + self.REPEAT_INTERVAL
                                    self.LAST_SCROLL_TIME = now + self.SCROLL_DELAY
                                    self.switch_to_stop_mode()
                                else:
                                    self.OPERATIONS[cmd]()
                            except Exception as e:
                                print(f"Operation error: {e}")

                        # ── Repeat handler ────────────────────
                        now = time.time()
                        if self.ACTIVE_REPEAT_COMMAND:
                            if now - self.LAST_COMMAND_TIME > self.REPEAT_TIMEOUT:
                                self.ACTIVE_REPEAT_COMMAND = None
                                self.switch_to_command_mode()
                            elif now < self.IGNORE_UNTIL or self.IS_SPEAKING:
                                pass
                            elif self.ACTIVE_REPEAT_COMMAND in ("SCROLL UP", "SCROLL DOWN"):
                                if now - self.LAST_SCROLL_TIME >= self.SCROLL_DELAY:
                                    try:
                                        self.OPERATIONS[self.ACTIVE_REPEAT_COMMAND]()
                                        self.LAST_SCROLL_TIME = now
                                    except: self.ACTIVE_REPEAT_COMMAND = None
                            else:
                                if now - self.LAST_REPEAT_TIME >= self.REPEAT_INTERVAL:
                                    try:
                                        self.OPERATIONS[self.ACTIVE_REPEAT_COMMAND]()
                                        self.LAST_REPEAT_TIME = now
                                    except: self.ACTIVE_REPEAT_COMMAND = None

            except KeyboardInterrupt:
                print("\nStopped.")
                break
            except RuntimeError as e:
                print(f"Audio error: {e}. Restarting in 1s...")
                time.sleep(1)
            except Exception as e:
                print(f"Unexpected error: {e}. Restarting in 2s...")
                time.sleep(2)

        t = self._tts_thread
        if t and t.is_alive():
            t.join(timeout=5)
        self.alert_engine.cleanup()
        print("Goodbye.")


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()