# AI Dating Project

## Key Features

- **Two‑level CLI menu** – quick start, intuitive settings, full removal of command‑line flags.
- **Automatic GEMINI API key rotator** – seamless switch to the next key when a `429 (Resource Exhausted)` error occurs.
- **AI‑generated criteria – "✨ Улучшить вкус"** – turn any plain‑language description into a structured VLM prompt.
- **Interactive cache & history cleanup** – one‑click removal of `history.md` and downloaded images.

## Quick Start

```bash
python tg_client.py
```

No flags, arguments or configuration files are required – the script will create a default `criteria.txt` if it does not exist and will launch the **Setup Wizard** on the first run.

## Documentation

Further details can be found in the `docs/` directory:
- **ARCHITECTURE.md** – high‑level overview of the CLI, `vlm_analyzer`, key rotator and Telethon integration.
- **PROMPTS.md** – description of system prompts and the “Improve Taste” workflow.
- **ROADMAP.md** – released features and future plans.
- **CONTRIBUTING.md** – how you can help.

