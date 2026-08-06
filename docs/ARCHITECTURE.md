# ARCHITECTURE

## High‑level Overview

- **Two‑level CLI menu** (`tg_client.py`)
  - Main menu: Launch, Settings, Exit.
  - Settings submenu: criteria wizard, VLM model switch, API‑key rotator, cache/history cleanup, test analysis, setup wizard.
  - All user interaction is performed via clear, colour‑coded prompts; no `argparse` flags are used.

- **VLM Analyzer (`vlm_analyzer.py`)
  - Loads and translates `criteria.txt` once at startup.
  - Provides `analyze_profile` which builds a system prompt, optionally attaches an image, and calls the Gemini model via the global `client`.
  - Implements **automatic API‑key rotation**: on a `429` response it switches to the next key from `GEMINI_API_KEYS` and retries.

- **Key Rotator**
  - Environment variable `GEMINI_API_KEYS` contains a comma‑separated list of keys.
  - `init_client` parses this list, creates the global `client` with the first key and stores the list in `api_keys`.
  - During inference, if a `429` error occurs the rotator logs a warning, updates `current_key_idx`, recreates the client and repeats the request.

- **Telethon Integration**
  - `tg_client.py` creates a `TelegramClient` session stored under `data/ai_agent_session`.
  - The session directory is created automatically before client initialization, preventing `sqlite3.OperationalError`.
  - The bot loops through configured services, invoking `process_dating_bot` which in turn calls `analyze_profile`.

## Data Flow

1. **Startup** → `run_setup_wizard` (if `.env` missing) → `load_config` → `init_client`.
2. **User selects "Launch"** → `auto_rotate_history` checks `history.md`.
3. **Main loop** selects service and speed, creates Telethon client.
4. For each profile, `analyze_profile` is called.
5. If the Gemini client returns `429`, the rotator rotates the key and retries.
6. Verdict written to `data/history.md` and optionally cached images stored in `data/downloads/`.

---
