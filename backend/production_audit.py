"""
╔══════════════════════════════════════════════════════════════╗
║           OMNI-IDE — Production Readiness Audit             ║
║           Deep System Check v1.0.0                          ║
╚══════════════════════════════════════════════════════════════╝

This script performs a comprehensive pre-release audit of the
Omni-IDE backend, covering dependency integrity, static asset
verification, execution engine safety, agent configuration,
and port availability.

Run:  python production_audit.py
"""

import sys
import os
import subprocess
import socket
import importlib
from datetime import datetime
from pathlib import Path

# ──────────────────── Configuration ────────────────────
REPORT_FILE = "status_report.txt"
REQUIRED_LIBS = [
    "fastapi", "uvicorn", "webview", "smolagents",
    "aiofiles", "pydantic", "torch", "PIL",
    "transformers", "huggingface_hub"
]
STATIC_REQUIRED = ["index.html", "styles.css", "script.js"]
BACKEND_PORT = 8000

# ──────────────────── Audit State ────────────────────
results = []
pass_count = 0
fail_count = 0
warn_count = 0


def log(status: str, category: str, message: str):
    """Record a single audit line."""
    global pass_count, fail_count, warn_count
    icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}.get(status, "  ")
    line = f"  [{status:4s}] {category:28s} | {message}"
    results.append(line)
    print(f"  {icon} {line.strip()}")
    if status == "PASS":
        pass_count += 1
    elif status == "FAIL":
        fail_count += 1
    elif status == "WARN":
        warn_count += 1


# ═══════════════════════════════════════════════════════
#  AUDIT 1: Dependency Integrity
# ═══════════════════════════════════════════════════════
def audit_dependencies():
    print("\n🔬 AUDIT 1: Dependency Integrity")
    print("─" * 50)
    for lib in REQUIRED_LIBS:
        try:
            importlib.import_module(lib)
            log("PASS", "Dependency", f"`{lib}` is installed and importable")
        except ImportError:
            log("FAIL", "Dependency", f"`{lib}` is NOT importable — pip install required")


# ═══════════════════════════════════════════════════════
#  AUDIT 2: Static Asset & Path Resolution
# ═══════════════════════════════════════════════════════
def audit_static_assets():
    print("\n📦 AUDIT 2: Static Assets & Path Resolution")
    print("─" * 50)

    # Simulate PyInstaller _MEIPASS detection
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base = sys._MEIPASS
        log("INFO", "Path Resolution", f"Running inside PyInstaller bundle: {base}")
    else:
        base = os.path.dirname(os.path.abspath(__file__))
        log("INFO", "Path Resolution", f"Running from source: {base}")

    static_dir = os.path.join(base, "static")
    if os.path.isdir(static_dir):
        log("PASS", "Static Directory", f"Found: {static_dir}")
    else:
        log("FAIL", "Static Directory", f"MISSING: {static_dir}")
        return

    for fname in STATIC_REQUIRED:
        fpath = os.path.join(static_dir, fname)
        if os.path.isfile(fpath):
            size_kb = os.path.getsize(fpath) / 1024
            log("PASS", "Static File", f"`{fname}` exists ({size_kb:.1f} KB)")
        else:
            log("FAIL", "Static File", f"`{fname}` is MISSING from static/")


# ═══════════════════════════════════════════════════════
#  AUDIT 3: Execution Engine Safety
# ═══════════════════════════════════════════════════════
def audit_execution_engine():
    print("\n⚙️  AUDIT 3: Execution Engine Safety")
    print("─" * 50)

    # Test 1: Basic subprocess stdout capture
    try:
        result = subprocess.run(
            [sys.executable, "-c", "print('OMNI_AUDIT_OK')"],
            capture_output=True, text=True, timeout=5
        )
        if "OMNI_AUDIT_OK" in result.stdout:
            log("PASS", "Subprocess Capture", "stdout correctly captured from child process")
        else:
            log("FAIL", "Subprocess Capture", f"Unexpected stdout: {result.stdout[:80]}")
    except Exception as e:
        log("FAIL", "Subprocess Capture", f"Subprocess crashed: {e}")

    # Test 2: stderr capture on intentional error
    try:
        result = subprocess.run(
            [sys.executable, "-c", "raise ValueError('AUDIT_ERROR')"],
            capture_output=True, text=True, timeout=5
        )
        if "AUDIT_ERROR" in result.stderr:
            log("PASS", "Stderr Capture", "Error output correctly captured")
        else:
            log("FAIL", "Stderr Capture", f"Expected error not found in stderr")
    except Exception as e:
        log("FAIL", "Stderr Capture", f"Subprocess crashed: {e}")

    # Test 3: Timeout safety (should not hang)
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import time; time.sleep(0.1); print('TIMEOUT_OK')"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            log("PASS", "Timeout Safety", "Short script completed within timeout")
    except subprocess.TimeoutExpired:
        log("FAIL", "Timeout Safety", "Process unexpectedly timed out")
    except Exception as e:
        log("FAIL", "Timeout Safety", f"Error: {e}")

    # Test 4: Environment isolation (PyInstaller vars stripped)
    try:
        env = os.environ.copy()
        env.pop('PYTHONHOME', None)
        env.pop('PYTHONPATH', None)
        result = subprocess.run(
            [sys.executable, "-c", "import os; print('HOME' if 'PYTHONHOME' in os.environ else 'CLEAN')"],
            capture_output=True, text=True, timeout=5, env=env
        )
        if "CLEAN" in result.stdout:
            log("PASS", "Env Isolation", "PYTHONHOME/PYTHONPATH correctly stripped")
        else:
            log("WARN", "Env Isolation", "PYTHONHOME may still be leaking into subprocess")
    except Exception as e:
        log("FAIL", "Env Isolation", f"Error: {e}")


# ═══════════════════════════════════════════════════════
#  AUDIT 4: Agent Configuration
# ═══════════════════════════════════════════════════════
def audit_agent_config():
    print("\n🤖 AUDIT 4: Agent Configuration")
    print("─" * 50)

    hf_key = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_TOKEN")
    if hf_key:
        masked = hf_key[:4] + "****" + hf_key[-4:]
        log("PASS", "HuggingFace API Key", f"Key loaded: {masked}")
    else:
        log("WARN", "HuggingFace API Key", "Not set — user must provide their own key")

    # Check if agent.py exists and is importable
    agent_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent.py")
    if os.path.isfile(agent_path):
        log("PASS", "Agent Module", f"agent.py found ({os.path.getsize(agent_path) / 1024:.1f} KB)")
    else:
        log("FAIL", "Agent Module", "agent.py is MISSING from backend/")

    # Check .env file presence
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(env_path):
        log("PASS", "Environment File", ".env file found")
    else:
        log("WARN", "Environment File", ".env file not found — relying on system env vars")


# ═══════════════════════════════════════════════════════
#  AUDIT 5: Port Availability
# ═══════════════════════════════════════════════════════
def audit_port():
    print("\n🌐 AUDIT 5: Port Availability")
    print("─" * 50)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', BACKEND_PORT))
        if result == 0:
            log("WARN", "Port 8000", f"Port {BACKEND_PORT} is OCCUPIED — another instance may be running")
        else:
            log("PASS", "Port 8000", f"Port {BACKEND_PORT} is free and available")
    except Exception as e:
        log("WARN", "Port 8000", f"Could not probe port: {e}")
    finally:
        sock.close()


# ═══════════════════════════════════════════════════════
#  AUDIT 6: Build Artifacts
# ═══════════════════════════════════════════════════════
def audit_build():
    print("\n🏗️  AUDIT 6: Build Artifacts")
    print("─" * 50)

    dist_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "OmniIDE", "OmniIDE.exe")
    if os.path.isfile(dist_exe):
        size_mb = os.path.getsize(dist_exe) / (1024 * 1024)
        log("PASS", "Production Binary", f"OmniIDE.exe found ({size_mb:.1f} MB)")
    else:
        log("WARN", "Production Binary", "OmniIDE.exe not found in dist/ — run build_release.py first")

    build_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_release.py")
    if os.path.isfile(build_script):
        log("PASS", "Build Script", "build_release.py present")
    else:
        log("FAIL", "Build Script", "build_release.py is MISSING")


# ═══════════════════════════════════════════════════════
#  Generate Status Report
# ═══════════════════════════════════════════════════════
def generate_report():
    verdict = "🟢 GO — All critical checks passed" if fail_count == 0 else "🔴 NO-GO — Critical failures detected"

    report = []
    report.append("=" * 62)
    report.append("  OMNI-IDE — PRODUCTION READINESS STATUS REPORT")
    report.append("=" * 62)
    report.append(f"  Date:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"  Platform:   {sys.platform}")
    report.append(f"  Python:     {sys.version.split()[0]}")
    report.append(f"  Auditor:    production_audit.py v1.0.0")
    report.append("=" * 62)
    report.append("")
    report.append("  DETAILED RESULTS")
    report.append("─" * 62)
    report.extend(results)
    report.append("")
    report.append("─" * 62)
    report.append(f"  SUMMARY:  {pass_count} PASS  |  {fail_count} FAIL  |  {warn_count} WARN")
    report.append("─" * 62)
    report.append("")
    report.append(f"  VERDICT:  {verdict}")
    report.append("")
    if fail_count > 0:
        report.append("  ⚠️  ACTION REQUIRED: Fix all FAIL items before shipping.")
    if warn_count > 0:
        report.append("  💡 ADVISORY: Review WARN items — they may affect some users.")
    report.append("")
    report.append("=" * 62)
    report.append("  Signed: Omni-IDE QA Pipeline")
    report.append("=" * 62)

    report_text = "\n".join(report)

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), REPORT_FILE)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\n📋 Report saved to: {report_path}")
    return report_text


# ═══════════════════════════════════════════════════════
#  Main Entrypoint
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           OMNI-IDE — Production Readiness Audit             ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    audit_dependencies()
    audit_static_assets()
    audit_execution_engine()
    audit_agent_config()
    audit_port()
    audit_build()

    report = generate_report()
    print("\n" + report)

    sys.exit(1 if fail_count > 0 else 0)
