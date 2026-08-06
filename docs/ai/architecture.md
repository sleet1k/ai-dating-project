# Архитектура ADP v0.9

## Стек
- **Язык:** Python 3.11+
- **Telegram Client:** Telethon (MTProto API)
- **VLM/LLM Ядро:** Google GenAI Cloud API (выбирается через Setup Wizard, дефолт `gemini-3.5-flash-lite`)
- **Формат данных:** JSON (`my_profile.json`, `phrases.json`), Markdown (`history.md`)

## Структура проекта
- `tg_client.py` — Точка входа, CLI-меню, асинхронный Queue Worker.
- `vlm_analyzer.py` — Конвейер взаимодействия с Gemini API (кодирование медиа, промпты, JSON Mode).
- `config/settings.py` — Setup Wizard, валидатор `.env`, интерактивный менеджер `criteria.txt`.
- `engines/` — Модульные обработчики площадок (`leomatch.py`, `bibinto.py`, `blur.py`).
- `data/` — Локальная история, профили, временные медиа.
- `docs/ai/` — Контекст разработки для ИИ-ассистентов.
