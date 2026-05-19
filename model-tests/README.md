# Polyglot model tests

Compare OpenAI models on the **same prompts** as production (`backend/app/services/openai_service.py`), with token usage and estimated USD cost per run.

## Setup (dedicated venv)

Uses **Python 3.13.4** from `C:\Users\marce\tech\python3.13.4\python.exe` by default. Override with `$env:MODEL_TESTS_PYTHON` if needed.

**Windows (PowerShell):**

```powershell
cd model-tests
.\scripts\setup.ps1
```

**Manual:**

```powershell
C:\Users\marce\tech\python3.13.4\python.exe -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

Ensure `OPENAI_API_KEY` is set in `backend/.env` or the environment.

## Quick start

```powershell
cd model-tests
.\scripts\run.ps1 --task correction --dry-run
.\scripts\run.ps1 --task correction --limit 3 --models gpt-4.1,gpt-5.4-mini,gpt-5.3-chat-latest
```

Or with the venv activated:

```powershell
.\.venv\Scripts\Activate.ps1
python compare_models.py --task correction
```

## Tasks

| `--task` | Fixtures | What it runs |
|----------|------------|--------------|
| `correction` | `fixtures/corrections.yaml` | `make_system_correction_prompt` + message to correct |
| `chat_reply` | `fixtures/chat_reply.yaml` | `make_system_chat_prompt` + history |
| `translation` | `fixtures/translations.yaml` | Translation JSON prompt |
| `title` | `fixtures/titles.yaml` | Thread title JSON prompt |
| `turn` | `fixtures/turns.yaml` | Correction + chat reply in parallel (like the API) |

## Output

Each run writes to `model-tests/output/<task>_<timestamp>/`:

- **`run.json`** — full results for agents/scripts
- **`summary.md`** — cost table + side-by-side outputs
- **`summary.csv`** — spreadsheet-friendly

`output/` and `.venv/` are gitignored.

## Configuration

- **`models.yaml`** — default model lists per task and `turn_pairs`
- **`pricing.yaml`** — input/output USD per 1M tokens (update from [OpenAI pricing](https://developers.openai.com/api/docs/pricing))
- **`fixtures/*.yaml`** — add cases with `id`, fields per task, and optional `notes` for human/agent review

## CLI reference

```
--task          correction | chat_reply | translation | title | turn
--fixtures      Path to fixture YAML (optional)
--models        Comma-separated model IDs
--pair          turn only: correction=MODEL,chat=MODEL
--models-file   Default models (models.yaml)
--pricing       pricing.yaml path
--out           Output directory
--limit N       First N fixtures only
--delay-ms      Pause between calls (rate limits)
--dry-run       Print plan, no API calls
```

## Tips for agents

1. Run `correction` across models first — quality matters most there.
2. Read `summary.md` for cost per configuration; use `run.json` for structured diffs.
3. Use fixture `notes` to judge behavior (e.g. “must not correct prior turn”).
4. After picking models, set `OPENAI_MODEL_CORRECT`, `OPENAI_MODEL_CHAT`, etc. in `backend/.env`.
