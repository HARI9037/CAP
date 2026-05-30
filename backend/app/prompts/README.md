# prompts/

## Purpose

Planned location for future prompt templates.
This directory is not part of the active runtime path today.

## Current Status

EMPTY.

- No prompt files are implemented here.
- No Python code loads templates from this directory.

## Active System Prompt

The real system prompt lives in:

```text
docs/ORCHESTRATION_SPEC.md
```

`app/orchestrator/service.py` loads that prompt at runtime through `_load_system_prompt_template()` with `lru_cache`.

## Intent

Future prompt templates may live here if the prompt system is split out of `docs/ORCHESTRATION_SPEC.md`.

## Rule

Every prompt must reinforce:

```text
THINK IN CLOUD -> ACT LOCALLY -> CONFIRM EVERYTHING
```
