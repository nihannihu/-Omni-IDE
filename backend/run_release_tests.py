"""Release Test Runner — Executes all API-testable phases from RELEASE_TESTING.md"""
import requests, json, sys, time

BASE = "http://localhost:8000"
results = []

def test(phase, name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((phase, name, status, detail))
    icon = "✅" if condition else "❌"
    print(f"  {icon} [{status}] {phase} | {name} — {detail}")

print("=" * 60)
print("  OMNI-IDE — Automated Release Test Runner")
print("=" * 60)

# ——— Phase 1: Cold Start ———
print("\n🧊 Phase 1: Cold Start")
try:
    r = requests.get(f"{BASE}/health", timeout=5)
    test("1.1", "Health Check", r.status_code == 200, f"HTTP {r.status_code}")
except:
    test("1.1", "Health Check", False, "Server unreachable")

try:
    r = requests.get(BASE, timeout=5)
    test("1.3", "Static Served", r.status_code == 200 and "Omni-IDE" in r.text, "HTML loaded")
    test("1.4", "Monaco Init", "monaco" in r.text.lower() or "editor" in r.text.lower(), "Editor script found")
except:
    test("1.3", "Static Served", False, "Could not load frontend")

# ——— Phase 2: Folder Navigation ———
print("\n📂 Phase 2: Folder Navigation")
r = requests.post(f"{BASE}/api/change_dir", json={"path": "C:\\Users\\nihan\\Desktop\\FINAL-PROJECTS"})
test("2.2", "Open Folder", r.status_code == 200, r.json().get("path", "?"))

r = requests.get(f"{BASE}/api/files")
files = r.json().get("files", [])
test("2.2b", "Files Listed", len(files) > 0, f"{len(files)} items found")

dirs = [f for f in files if f["type"] == "directory"]
test("2.2c", "Directories Visible", len(dirs) > 0, f"{len(dirs)} subdirectories")

# Subfolder navigation
if dirs:
    subdir = dirs[0]["name"]
    r = requests.get(f"{BASE}/api/files", params={"subpath": subdir})
    sub_files = r.json().get("files", [])
    test("2.3", "Subfolder Drill", r.status_code == 200, f"{len(sub_files)} items in {subdir}/")

# Path traversal security
r = requests.get(f"{BASE}/api/files", params={"subpath": "../../Windows/System32"})
test("6.3", "Path Traversal Block", r.status_code == 403, "Access denied enforced")

# Close folder
r = requests.post(f"{BASE}/api/close_folder")
test("2.7", "Close Folder", r.status_code == 200, r.json().get("status", "?"))

r = requests.get(f"{BASE}/api/files")
test("2.7b", "Folder Closed State", r.json().get("no_directory") == True, "No directory active")

# Re-open for remaining tests
requests.post(f"{BASE}/api/change_dir", json={"path": "C:\\Users\\nihan\\Desktop\\FINAL-PROJECTS"})

# ——— Phase 4: IO Pipeline ———
print("\n📝 Phase 4: IO Pipeline")
# Read a file
r = requests.get(f"{BASE}/api/files")
files = [f for f in r.json().get("files", []) if f["type"] == "file"]
if files:
    fname = files[0]["name"]
    r = requests.get(f"{BASE}/api/read", params={"filename": fname})
    test("4.1", "Read File", r.status_code == 200 and "content" in r.json(), f"Read {fname}")
else:
    test("4.1", "Read File", False, "No files to read")

# Save file test (write then verify)
test_content = "# Release Test\nprint('QA OK')\n"
r = requests.post(f"{BASE}/api/save", params={"filename": "release_test_temp.py"}, json={"code": test_content})
test("4.6", "Save File", r.status_code == 200, "Ctrl+S simulation")

r = requests.get(f"{BASE}/api/read", params={"filename": "release_test_temp.py"})
test("4.6b", "Read Saved File", "QA OK" in r.json().get("content", ""), "Content persisted")

# Delete file test
r = requests.delete(f"{BASE}/api/delete", params={"filename": "release_test_temp.py"})
test("4.7", "Delete File", r.status_code == 200, "Cleanup successful")

# ——— Phase 5: Execution Loop ———
print("\n🚀 Phase 5: Execution Loop")

# Test 5.1: Simple print
r = requests.post(f"{BASE}/api/run", json={"code": "print('Hello QA')"})
data = r.json()
test("5.1", "Print Hello", "Hello QA" in data.get("stdout", ""), data.get("stdout", "").strip()[:50])

# Test 5.2: Error traceback
r = requests.post(f"{BASE}/api/run", json={"code": "print(1/0)"})
data = r.json()
test("5.2", "Error Traceback", "ZeroDivisionError" in data.get("stderr", ""), "Traceback captured")

# Test 5.4: sys.executable check (no WindowsApps)
r = requests.post(f"{BASE}/api/run", json={"code": "import sys; print(sys.executable)"})
data = r.json()
exe = data.get("stdout", "").strip()
test("5.4", "Real Python Path", "WindowsApps" not in exe and "python" in exe.lower(), exe[:60])

# Test 5.5: Pygame import
r = requests.post(f"{BASE}/api/run", json={"code": "import pygame; print(pygame.ver)"})
data = r.json()
has_pygame = "pygame" in data.get("stdout", "").lower() or "AUTO-PIP" in data.get("stdout", "")
test("5.5", "Pygame Available", has_pygame, data.get("stdout", "").strip()[:80])

# Test 5.7: Timeout handling (infinite loop)
r = requests.post(f"{BASE}/api/run", json={"code": "while True: pass"}, timeout=10)
data = r.json()
test("5.7", "Infinite Loop Safety", data.get("returncode") == 0 or "background" in data.get("stdout", "").lower(), "IDE didn't freeze")

# ——— Phase 3: Brain Link (Agent) ———
print("\n🧠 Phase 3: Brain Link")
try:
    r = requests.post(f"{BASE}/chat", json={"text": "Hello"}, timeout=30)
    data = r.json()
    has_reply = len(data.get("reply", "")) > 5
    no_internals = "Thought:" not in data.get("reply", "") and "Observation:" not in data.get("reply", "")
    test("3.1", "Agent Responds", has_reply, data.get("reply", "")[:60])
    test("3.4", "No Agent Internals", no_internals, "Clean response" if no_internals else "Leaked internals!")
except requests.exceptions.Timeout:
    test("3.1", "Agent Responds", False, "Timeout — model may not be loaded")
except Exception as e:
    test("3.1", "Agent Responds", False, str(e)[:60])

# ——— Summary ———
print("\n" + "=" * 60)
passes = sum(1 for _,_,s,_ in results if s == "PASS")
fails = sum(1 for _,_,s,_ in results if s == "FAIL")
print(f"  TOTAL:  {passes} PASS  |  {fails} FAIL  |  {len(results)} tests")
verdict = "🟢 GO" if fails == 0 else ("🟡 CONDITIONAL GO" if fails <= 2 else "🔴 NO-GO")
print(f"  VERDICT: {verdict}")
print("=" * 60)
