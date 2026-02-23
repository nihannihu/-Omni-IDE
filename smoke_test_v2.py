import sys
import time

# FORCE FLUSH so logs appear instantly
sys.stdout.reconfigure(line_buffering=True)

print("🧪 Starting Omni-IDE v2.0 Smoke Test...")
print(f"🐍 Python Executable: {sys.executable}")

# --- CRITICAL SECTION ---
# We intentionally import WITHOUT try/except.
# If this fails, the Backend will see the crash and auto-install 'colorama'.
import colorama
from colorama import Fore, Style

print(Fore.GREEN + "✅ PASS: Auto-Pip is working! Colorama imported successfully." + Style.RESET_ALL)
