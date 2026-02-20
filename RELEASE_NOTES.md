# 🚀 Omni-IDE v1.1.0 — The "Gatekeeper" Update 

Welcome to the first major feature update for **Omni-IDE**! We are transitioning from a prototype lab into a polished, commercial-ready AI application. 

This release introduces the **First-Run Authentication Gate**, extensive UX polish, safety guards for workspace management, and our brand-new **Windows Installer**!

---

## 🌟 What's New

### 1. 🔐 First-Run Authentication Gate
No more hardcoded or confusing `.env` setups! When you launch Omni-IDE for the first time, you are immediately greeted by our new, secure **Auth Modal**.
- Seamlessly paste your HuggingFace API key directly in the app.
- Keys are automatically validated, stored permanently in a PyInstaller-safe local relative `.env` file, and instantly applied without restarting the IDE.
- Full privacy standard: Your key is rigorously stored strictly on your local machine and completely excluded from logs. 

### 2. 📦 Zero-Friction Windows Installer
Omni-IDE is now easier to install than ever:
- **`OmniIDE-Setup-v1.1.0.exe`**: All Python runtimes, HuggingFace PyTorch binaries, and Node/Electron-styled UI components are compressed into a single 38MB payload.
- One-click setup wizard featuring the official Omni-IDE logo.
- Automatically handles background deployment to `AppData` and drops a shortcut right on your Windows Desktop!

### 3. 🛡️ Workspace Safety Guards
The AI Agent now protects you from ambiguous commands:
- **No-Folder Guard:** If you try to prompt the AI to write or edit code without first selecting a project folder via "Open Folder", the AI politely intercepts the request with a polished `🛑 Workspace Missing` alert, preventing out-of-bounds file creation errors.

### 4. 💅 Production Polish
We stripped out the development cruft to give you a pristine application:
- **DevTools Disabled:** The right-click `Inspect Element` browser suite is now native-locked. 
- **Clean Naming:** The application window title is finalized as simply `Omni-IDE`.
- **System Stability:** Background processes like `uvicorn` and console shells are completely hidden from the end-user.

---

## 📥 How to Install

1. Download the **`OmniIDE-Setup-v1.1.0.exe`** file below.
2. Double-click to run the setup wizard (Windows may show a SmartScreen warning since this is a new indie app — just click "More info" -> "Run anyway").
3. Launch Omni-IDE from your Start Menu or Desktop shortcut!

---

### Security Audit Note
*Release v1.1.0 passed a rigorous 15-point automated QA check ensuring zero polling loops, correct PyInstaller architecture paths, and zero key-logging vulnerabilities.*
