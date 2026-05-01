# Offline-OS-Assistant
Jarvis/Friday , system wakes up with responses accordingly to command , provides alert and suggestions based on your activity.
Got it—stripped down to a **voice-only assistant**, and I’ve added clear **user-editable links/files** (for commands, grammar, and model path).

---

# 🎙️ Offline Voice Assistant (Jarvis)

A **fully offline, privacy-focused voice assistant** that performs system-level tasks using **deterministic, grammar-based speech recognition** powered by VOSK.

---

## 🚀 Overview

This project implements a **real-time offline voice assistant** capable of:

* Wake word detection (`"Jarvis"`)
* Recognizing predefined commands (no ambiguity)
* Executing OS-level actions
* Providing voice feedback

🔒 **No internet required — all processing runs locally**

🎯 Features
 🗣️ Voice Recognition (Offline)

* Powered by VOSK
* Fast, lightweight, and works without internet
* Grammar-based command recognition (high reliability)

⚙️ System Control

* Open applications (Chrome, VS Code, etc.)
* Volume control
* Brightness control
* Scrolling and navigation
* Clipboard actions

🔊 Voice Feedback

* Offline TTS using pyttsx3
* Instant response with no latency

🧠 Deterministic Design

* No AI hallucination
* Only predefined commands are executed
* Stable and production-ready loop

🏗️ Architecture

```text
Microphone Input
        │
        ▼
+----------------------+
|   VOSK Engine        |
| (Speech Recognition) |
+----------+-----------+
           │
           ▼
+----------------------+
| Command Processor    |
| (Grammar-based)      |
+----------+-----------+
           │
           ▼
+----------------------+
| OS Controller        |
| (System Actions)     |
+----------+-----------+
           │
           ▼
+----------------------+
| Voice Feedback (TTS) |
+----------------------+
```

 🛠️ Tech Stack

* Python
* VOSK
* pyttsx3
* PyAudio
* PyAutoGUI


🔗 User Editable Files (IMPORTANT)

These are the **main customization points**:

"Main file to run - Voice_assistantV3"
- all file editable accordingly to user 

### 1️⃣ Command Grammar (Speech Input)

📄 File: `voice/grammar.json`

* Defines what phrases the assistant can understand
* Example:

```json
{
  "commands": [
    "open chrome",
    "increase volume",
    "scroll down",
    "sleep"
  ]
}
```

---

### 2️⃣ Command Execution Mapping

📄 File: `system/commands.py`

* Maps recognized commands → system actions
* Example:

```python
COMMANDS = {
    "open chrome": open_chrome,
    "increase volume": volume_up,
    "scroll down": scroll_down
}
```

---

### 3️⃣ VOSK Model Path

📄 File: `Voice_assistantV3.py`

```python
VOSK_MODEL_PATH = "models/vosk-model"
```

👉 You can change model location here

 4️⃣ Microphone Configuration

📄 File: `config/settings.py`

```python
MIC_DEVICE_INDEX = None  # Set manually if needed
```

 📥 VOSK Model Setup

Download model from official source:

🔗 [https://alphacephei.com/vosk/models](https://alphacephei.com/vosk/models)

### Steps:

1. Download a model (recommended: small English model)
2. Extract it
3. Place inside:

```text
models/vosk-model/
```

 ⚙️ Installation

```bash
git clone https://github.com/yourusername/offline-voice-assistant.git
cd offline-voice-assistant
pip install -r requirements.txt
```

 ▶️ Usage

```bash
python core/main.py
```

 🎤 Example Commands

* "Jarvis open chrome"
* "Jarvis increase volume"
* "Jarvis scroll down"
* "Jarvis sleep"

🔒 Design Principles

* 🔐 Fully offline (no data leakage)
* ⚡ Real-time response
* 🎯 Deterministic (no guessing)
* 🧠 Stable loop (production-ready)

 📊 Use Cases

* Hands-free PC control
* Accessibility tools
* Offline secure environments
* Defense / restricted systems

🔮 Future Scope

* Multi-language support
* Local LLM integration (optional layer)
* Context-aware command chaining


