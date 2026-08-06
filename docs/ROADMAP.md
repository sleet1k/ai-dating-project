# ROADMAP

## Implemented Features
- **Two‑level CLI menu** with full settings submenu, no argparse flags.
- **Automatic GEMINI API‑key rotator** that switches keys on `429` errors.
- **AI‑generated criteria ("✨ Улучшить вкус")** – free‑form description → structured criteria.
- **Interactive cache & history cleanup** (history.md and `data/downloads`).
- **Setup Wizard** for initial `.env` generation.
- **Telethon session auto‑creation** to avoid SQLite errors.

## Planned Enhancements
| Feature | Status | Notes |
|---|---|---|
| KV‑Cache for prompts (e.g., `llama.cpp` context cache) | 📅 Planned | Reduce latency for repeated system prompts. |
| SQLite persistence of verdict history | 📅 Planned | Faster look‑ups, avoid duplicate processing. |
| Dashboard UI (web) | 📅 Planned | Visual overview of processed profiles, stats. |
| Auto‑reply generation after a match | 📅 Planned | Friendly AI‑generated greeting based on interests. |
| Multi‑language support for criteria | 📅 Planned | Translate criteria to other languages for VLMs. |
| Unit‑tests & CI pipeline | 📅 In progress | Ensure stability on future changes.

---

*Feel free to open issues or submit PRs to help shape the roadmap!*
