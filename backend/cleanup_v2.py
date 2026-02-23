# ══════════════════════════════════════════════════════════════════
# 🧹 Omni-IDE — Safe Legacy Cleanup Script (cleanup_v2.py)
# ══════════════════════════════════════════════════════════════════
#
# This script:
#   1. Creates _BACKUP_BEFORE_PURGE/ folder
#   2. Moves dead files into the backup folder (safe delete)
#   3. Updates requirements.txt to remove huggingface_hub
#   4. Runs smoke test — if it fails, ROLLS BACK automatically
#
# RUN: python cleanup_v2.py
# ══════════════════════════════════════════════════════════════════

import os
import sys
import shutil
import subprocess
import time

# Colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BACKEND_DIR, "_BACKUP_BEFORE_PURGE")

# Files to be moved to backup
DEAD_FILES = [
    "qa_test_phase2.py",
    "qa_test_phase3.py",
    "qa_test_phase4.py",
    "qa_test_phase45.py",
    "qa_test_phase5_api.py",
    "qa_test_phase5_staging.py",
    "qa_test_phase6_router.py",
    "qa_test_autopip.py",
    "qa_test_memory_phase6.py",
    "qa_audit.py",
    "test_analytics.py",
    "test_explainability.py",
    "test_feedback.py",
    "test_templates.py",
    "verify_gatekeeper.py",
    "verify_ux_polish.py",
    "validate_env.py",
    "status_report.txt",
]

# Directories to be moved to backup
DEAD_DIRS = [
    "myproject",
    "testproject",
    "project",
    "webapp",
    "book",
]

# Lines to remove from requirements.txt
DEAD_DEPS = [
    "huggingface_hub",
]


def header(text):
    print(f"\n{BOLD}{CYAN}{'═' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 60}{RESET}\n")


def section(text):
    print(f"\n{YELLOW}{'─' * 60}{RESET}")
    print(f"  {BOLD}{text}{RESET}")
    print(f"{YELLOW}{'─' * 60}{RESET}")


def backup_file(filename):
    """Move a file to the backup directory."""
    src = os.path.join(BACKEND_DIR, filename)
    if not os.path.exists(src):
        print(f"  {YELLOW}⚠️ SKIP: {filename} (not found){RESET}")
        return None
    
    dst = os.path.join(BACKUP_DIR, filename)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    print(f"  {GREEN}📦 MOVED: {filename} → _BACKUP_BEFORE_PURGE/{filename}{RESET}")
    return (src, dst)


def backup_dir(dirname):
    """Move a directory to the backup directory."""
    src = os.path.join(BACKEND_DIR, dirname)
    if not os.path.exists(src):
        print(f"  {YELLOW}⚠️ SKIP: {dirname}/ (not found){RESET}")
        return None
    
    dst = os.path.join(BACKUP_DIR, dirname)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.move(src, dst)
    print(f"  {GREEN}📦 MOVED: {dirname}/ → _BACKUP_BEFORE_PURGE/{dirname}/{RESET}")
    return (src, dst)


def restore_file(src, dst):
    """Restore a file from backup."""
    if os.path.exists(dst):
        shutil.move(dst, src)
        print(f"  {YELLOW}🔄 RESTORED: {os.path.basename(src)}{RESET}")


def restore_dir(src, dst):
    """Restore a directory from backup."""
    if os.path.exists(dst):
        shutil.move(dst, src)
        print(f"  {YELLOW}🔄 RESTORED: {os.path.basename(src)}/{RESET}")


def clean_requirements():
    """Remove dead dependencies from requirements.txt."""
    req_path = os.path.join(BACKEND_DIR, "requirements.txt")
    
    with open(req_path, "r") as f:
        lines = f.readlines()
    
    # Backup original
    backup_path = os.path.join(BACKUP_DIR, "requirements.txt.bak")
    with open(backup_path, "w") as f:
        f.writelines(lines)
    
    # Filter out dead deps and their comments
    cleaned = []
    skip_next_comment = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this line is a dead dep
        is_dead = any(dep in stripped for dep in DEAD_DEPS)
        
        # Check if previous line was a comment for a dead dep
        if is_dead:
            # Also remove the comment line above if it exists
            if cleaned and cleaned[-1].strip().startswith("#"):
                removed_comment = cleaned.pop()
                print(f"  {RED}🗑️ REMOVED comment: {removed_comment.strip()}{RESET}")
            print(f"  {RED}🗑️ REMOVED dep: {stripped}{RESET}")
            continue
        
        cleaned.append(line)
    
    # Add litellm if not present
    has_litellm = any("litellm" in l for l in cleaned)
    if not has_litellm:
        # Add after smolagents line
        new_cleaned = []
        for line in cleaned:
            new_cleaned.append(line)
            if "smolagents" in line:
                new_cleaned.append("litellm\n")
                print(f"  {GREEN}➕ ADDED dep: litellm{RESET}")
        cleaned = new_cleaned
    
    with open(req_path, "w") as f:
        f.writelines(cleaned)
    
    return backup_path


def restore_requirements(backup_path):
    """Restore requirements.txt from backup."""
    req_path = os.path.join(BACKEND_DIR, "requirements.txt")
    if os.path.exists(backup_path):
        shutil.copy2(backup_path, req_path)
        print(f"  {YELLOW}🔄 RESTORED: requirements.txt{RESET}")


def run_smoke_test():
    """Run the gateway self-test as a smoke test."""
    section("🧪 SMOKE TEST (Post-Cleanup Verification)")
    
    python = os.path.join(BACKEND_DIR, "venv_prod", "Scripts", "python.exe")
    if not os.path.exists(python):
        python = sys.executable
    
    # Test 1: Gateway imports and routes correctly
    print(f"\n  Testing gateway.py...")
    result = subprocess.run(
        [python, "gateway.py"],
        capture_output=True, text=True, timeout=30,
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print(f"  {RED}❌ gateway.py FAILED:{RESET}")
        print(f"     {result.stderr[:200]}")
        return False
    print(f"  {GREEN}✅ gateway.py OK{RESET}")
    
    # Test 2: Agent module imports without error
    print(f"  Testing agent.py imports...")
    result = subprocess.run(
        [python, "-c", "from agent import TerminalTool; t = TerminalTool(); print(t.forward('echo OK'))"],
        capture_output=True, text=True, timeout=30,
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print(f"  {RED}❌ agent.py import FAILED:{RESET}")
        print(f"     {result.stderr[:200]}")
        return False
    if "OK" not in result.stdout:
        print(f"  {RED}❌ agent.py TerminalTool FAILED:{RESET}")
        print(f"     {result.stdout[:200]}")
        return False
    print(f"  {GREEN}✅ agent.py imports OK | TerminalTool OK{RESET}")
    
    # Test 3: intent_router.py imports
    print(f"  Testing intent_router.py imports...")
    result = subprocess.run(
        [python, "-c", "from intent_router import IntentRouter; r = IntentRouter(); print('Router OK')"],
        capture_output=True, text=True, timeout=30,
        cwd=BACKEND_DIR,
    )
    if result.returncode != 0:
        print(f"  {RED}❌ intent_router.py import FAILED:{RESET}")
        print(f"     {result.stderr[:200]}")
        return False
    print(f"  {GREEN}✅ intent_router.py OK{RESET}")
    
    print(f"\n  {GREEN}{BOLD}ALL SMOKE TESTS PASSED ✅{RESET}")
    return True


# ══════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    header("🧹 Omni-IDE — Legacy Code Cleanup v2.0")
    
    print(f"  Backend Dir: {BACKEND_DIR}")
    print(f"  Backup Dir:  {BACKUP_DIR}")
    
    # Phase 1: Create Backup Directory
    section("📦 PHASE 1: Creating Backup Directory")
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"  {GREEN}✅ Created: _BACKUP_BEFORE_PURGE/{RESET}")
    
    # Phase 2: Move Dead Files
    section("🗑️ PHASE 2: Moving Dead Files to Backup")
    moved_files = []
    for f in DEAD_FILES:
        result = backup_file(f)
        if result:
            moved_files.append(result)
    
    # Phase 3: Move Dead Directories
    section("🗑️ PHASE 3: Moving Dead Directories to Backup")
    moved_dirs = []
    for d in DEAD_DIRS:
        result = backup_dir(d)
        if result:
            moved_dirs.append(result)
    
    # Phase 4: Clean Requirements
    section("📝 PHASE 4: Cleaning requirements.txt")
    req_backup = clean_requirements()
    
    # Phase 5: Smoke Test
    smoke_passed = run_smoke_test()
    
    if smoke_passed:
        header("🏆 CLEANUP COMPLETE")
        print(f"  {GREEN}{BOLD}╔══════════════════════════════════════════════════╗{RESET}")
        print(f"  {GREEN}{BOLD}║  🟢 CLEANUP SUCCESSFUL                           ║{RESET}")
        print(f"  {GREEN}{BOLD}║  Files: {len(moved_files)} moved | Dirs: {len(moved_dirs)} moved       ║{RESET}")
        print(f"  {GREEN}{BOLD}║  Deps: {len(DEAD_DEPS)} removed | Smoke Test: PASS  ║{RESET}")
        print(f"  {GREEN}{BOLD}║                                                   ║{RESET}")
        print(f"  {GREEN}{BOLD}║  To permanently delete backups:                   ║{RESET}")
        print(f"  {GREEN}{BOLD}║  rm -rf _BACKUP_BEFORE_PURGE/                     ║{RESET}")
        print(f"  {GREEN}{BOLD}╚══════════════════════════════════════════════════╝{RESET}")
    else:
        # ROLLBACK
        header("🚨 SMOKE TEST FAILED — ROLLING BACK")
        
        print(f"  {RED}{BOLD}Restoring all moved files and directories...{RESET}\n")
        
        for src, dst in moved_files:
            restore_file(src, dst)
        
        for src, dst in moved_dirs:
            restore_dir(src, dst)
        
        restore_requirements(req_backup)
        
        print(f"\n  {YELLOW}{BOLD}╔══════════════════════════════════════════════════╗{RESET}")
        print(f"  {YELLOW}{BOLD}║  🔄 ROLLBACK COMPLETE                             ║{RESET}")
        print(f"  {YELLOW}{BOLD}║  All files have been restored to their             ║{RESET}")
        print(f"  {YELLOW}{BOLD}║  original locations. No damage done.               ║{RESET}")
        print(f"  {YELLOW}{BOLD}╚══════════════════════════════════════════════════╝{RESET}")
    
    print(f"\n  Signed: Omni-IDE SRE Pipeline | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    sys.exit(0 if smoke_passed else 1)
