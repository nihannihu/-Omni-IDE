# Omni-IDE v2.0.0 🚀 - The "Smart Engine" Update

Welcome to the largest and most robust update to Omni-IDE yet! Version 2.0.0 marks a massive architectural shift, transitioning from a heavy, monolithic application to a blazing-fast, intelligent, and highly optimized development environment.

## 🌟 What's New in v2.0.0?

### 🧠 The Smart Onboarding Wizard
Omni-IDE now intelligently adapts to your hardware on the very first launch. 
- **System Scanning**: Automatically detects your System RAM and Ollama daemon status.
- **Dynamic Recommendations**: Recommends the perfect AI engine setup based on your rig.
- **Cloud Speed (Gemini)**: Instantly connect your free Gemini API key for zero-overhead, lightning-fast orchestration.
- **Hybrid Power (Ollama + Gemini)**: Download and install local weights (Qwen 2.5 Coder) directly from the UI via background threaded downloads, completely eliminating HTTP timeouts. 

### ⚡ Ultra-Lightweight Architecture (99% Smaller Executable)
We've completely re-engineered how the AI pipeline interacts with the core package.
- **Heavy ML Weights Removed**: By moving local inference entirely to the external Ollama daemon, we have successfully stripped massive libraries like `torch` and `transformers` from the compiled executable.
- **Lightning Fast Boot**: The core `.exe` is now an incredibly lightweight ~20MB (down from several Gigabytes).
- **Stateless Environment**: A completely bulletproof config manager ensures that fresh installs are always perfectly clean, eliminating any legacy crash loops.

### 🛡️ Production Hardened & Bulletproof Tooling
- **Cloud-Primary Gateway Strategy**: The core IDE gateway now prioritizes the immensely powerful Gemini 2.5 Flash architecture for complex multi-step routines, ensuring rigid and reliable system tool-calling.
- **Transparent Fallback**: If standard local models fail, the Omni-IDE automatically and gracefully pivots to the cloud brain to ensure your code generation never stops.
- **HuggingFace Dependency Purge**: Legacy, hard-coded authentication loops have been completely eradicated from the system. 

## 📦 Installation Instructions

1. Download the `OmniIDE-Setup-v2.0.0.exe` attached below.
2. Run the installer and follow the prompts.
3. On first launch, the **Smart Setup Wizard** will guide you through connecting your Gemini API key and, optionally, configuring your local AI models.

### ⚠️ Upgrading from v1.x?
Omni-IDE v2.0.0 uses a completely upgraded `onedir` architecture and environment mapping. We highly recommend uninstalling older versions of Omni-IDE before installing this fresh v2.0.0 setup to ensure all configurations apply cleanly.

---
*Built with ❤️ for AI-Assisted Development.*
