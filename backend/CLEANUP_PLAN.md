# 🧹 Omni-IDE — Legacy Code Cleanup Plan (DEPRECATION SPRINT)

> **Status:** DRY RUN — No files have been deleted.
> **Date:** 2026-02-23
> **Author:** SRE Pipeline

---

## ⚠️ TO BE DELETED

### Dead Dependencies (`requirements.txt`)

| # | Item | Reason |
|---|---|---|
| 1 | `huggingface_hub` (line 9) | Replaced by `smolagents` + `litellm`. Zero HF imports remain in core pipeline. |

### Dead / Ghost Files

| # | File | Reason |
|---|---|---|
| 2 | `backend/qa_test_phase2.py` | Old Phase 2 QA — not imported by any core module. |
| 3 | `backend/qa_test_phase3.py` | Old Phase 3 QA — not imported by any core module. |
| 4 | `backend/qa_test_phase4.py` | Old Phase 4 QA — not imported by any core module. |
| 5 | `backend/qa_test_phase45.py` | Old Phase 4.5 QA — not imported by any core module. |
| 6 | `backend/qa_test_phase5_api.py` | Old Phase 5 API QA — not imported by any core module. |
| 7 | `backend/qa_test_phase5_staging.py` | Old Phase 5 Staging QA — not imported by any core module. |
| 8 | `backend/qa_test_phase6_router.py` | Old Phase 6 Router QA — not imported by any core module. |
| 9 | `backend/qa_test_autopip.py` | Old auto-pip QA — not imported by any core module. |
| 10 | `backend/qa_test_memory_phase6.py` | Old Phase 6 Memory QA — not imported by any core module. |
| 11 | `backend/qa_audit.py` | Old QA audit — replaced by `qa_god_mode.py`. |
| 12 | `backend/test_analytics.py` | Standalone test — not part of test suite. |
| 13 | `backend/test_explainability.py` | Standalone test — not part of test suite. |
| 14 | `backend/test_feedback.py` | Standalone test — not part of test suite. |
| 15 | `backend/test_templates.py` | Standalone test — not part of test suite. |
| 16 | `backend/verify_gatekeeper.py` | Old gatekeeper verification — outdated. |
| 17 | `backend/verify_ux_polish.py` | Old UX polish verification — outdated. |
| 18 | `backend/status_report.txt` | Old report artifact. |
| 19 | `backend/validate_env.py` | Old env validation — replaced by Gateway boot diagnostics. |

### Dead Code Blocks

| # | File | Lines | Reason |
|---|---|---|---|
| 20 | `backend/production_audit.py:28` | String ref `"huggingface_hub"` | Old dependency check — HF is no longer a dependency. |
| 21 | `backend/tests/test_backend.py:48-59` | `@patch('agent.InferenceClientModel')` | Mocks a class that no longer exists in agent.py. |

### Dead Directories

| # | Directory | Reason |
|---|---|---|
| 22 | `backend/myproject/` | Test project scaffold — not part of production. |
| 23 | `backend/testproject/` | Test project scaffold — not part of production. |
| 24 | `backend/project/` | Test project scaffold — not part of production. |
| 25 | `backend/webapp/` | Old webapp scaffold — not part of production. |
| 26 | `backend/book/` | Test scaffold — not part of production. |

---

## ✅ TO BE KEPT (CRITICAL)

| File | Role | Status |
|---|---|---|
| `backend/gateway.py` | The Brain (Smart Model Router) | **v2.0 — Gemini + Local Qwen** |
| `backend/agent.py` | The Body (God-Tier Agent + TerminalTool) | **Active — zero HF** |
| `backend/intent_router.py` | Intent Classification | **v2.0 — uses Gemini/LiteLLM** |
| `backend/main.py` | FastAPI Server | **Active** |
| `backend/config.py` | Portable Config | **Active** |
| `backend/intelligence_core.py` | Workspace Context Engine | **Active — imported by agent.py** |
| `backend/agent_orchestrator.py` | Multi-Agent Router | **Active — imported by agent.py** |
| `backend/planner.py` | Task Graph Planner | **Active — imported by agent.py** |
| `backend/memory.py` | Project Memory | **Active — imported by agent.py** |
| `backend/diff_staging_layer.py` | Diff Staging | **Active — imported by agent.py** |
| `backend/analytics_engine.py` | Telemetry | **Active — imported by intent_router** |
| `backend/explainability.py` | Reasoning Trace | **Active — imported by agent.py** |
| `backend/feedback_store.py` | User Feedback | **Active — imported by main.py** |
| `backend/insights_engine.py` | Background Insights | **Active — imported by agent.py** |
| `backend/offline_engine.py` | Offline Fallback | **Active — imported by agent.py** |
| `backend/template_runner.py` | Template Engine | **Active — imported by offline_engine** |
| `backend/session_manager.py` | Session Persistence | **Active — imported by main.py** |
| `backend/desktop.py` | Desktop Entry Point | **Active** |
| `backend/run.py` | Dev Entry Runner | **Active** |
| `backend/transcriber.py` | Audio Transcription | **Active — imported by main.py** |
| `backend/dependency_manager.py` | Auto-pip | **Active — imported by main.py** |
| `backend/environment_manager.py` | Env Manager | **Active — imported by main.py** |
| `backend/qa_god_mode.py` | God Mode QA Test | **Keep — latest QA** |
| `backend/verify_hybrid.py` | Hybrid Verification | **Keep — latest QA** |
| `backend/requirements.txt` | Dependencies | **Needs update (remove huggingface_hub)** |
| `backend/tests/` | Test Suite | **Needs updating (remove HF mocks)** |
