# PROMPTS

## System Prompt for Profile Analysis

The VLM receives a **system instruction** that sets the role and rules:
```
Role: Strict dating profile evaluator.
Rules: Evaluate target photo and bio based on user criteria and my_profile context.
Output: Response MUST be a valid JSON object matching the requested schema. Reason MUST be concise (under 15 words).
```
The prompt is built dynamically:
1. **My profile** – loaded once from `data/my_profile.json` and inserted into the instruction.
2. **Translated criteria** – the English version of `criteria.txt` (`translated_criteria_text`).
3. **Incoming profile** – the raw text (and optionally an image) of the candidate.

Two modes are supported:
- **binary** – return `{"action": "like"/"dislike", "reason": "..."}`.
- **score** – return a numeric rating `1‑10` (or `skip`).

## "✨ Улучшить вкус" – AI‑generated Criteria

When the user selects **Improve Taste** in the Settings submenu:
1. The user provides a free‑form description of the desired partner (e.g., "хочу junior разработчицу, играющую в доту и любящую котов").
2. The assistant calls Gemini (`gemini-3.5-flash`) with the following **system prompt**:
```
Преобразуй пользовательский список пожеланий к кандидату в четкие, структурированные критерии оценки для VLM на русском языке. Только текст критериев, без вступления.
```
3. The model returns a plain‑text list of criteria (e.g., age range, appearance, interests, red flags).
4. The result is displayed. Upon confirmation, the file `criteria.txt` is overwritten with the new content and subsequently translated by `load_and_translate_criteria`.

This workflow allows non‑technical users to quickly refine the search criteria using natural language.
