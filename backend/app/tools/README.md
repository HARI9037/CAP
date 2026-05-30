# tools/

## Purpose

Planned location for future action execution modules.
CAP can store pending actions today, but this directory does not execute them.

## Current Status

EMPTY.

- No tools are implemented.
- No action executor is wired into the backend.
- Confirmed actions are recorded in SQLite only.

## Intended Tool Contract

From `docs/ORCHESTRATION_SPEC.md`.

Input:

```json
{
  "action_id": "uuid-v4",
  "action_type": "write | update | organize | save | delete",
  "description": "Human readable description shown in the UI",
  "payload": {
    "target_resource": "string",
    "parameters": {}
  }
}
```

Output:

```json
{
  "success": true,
  "message": "Tool executed successfully",
  "data": {}
}
```

## What Is Not Here

- No BeautifulSoup.
- No web scraping.
- No file manager.

## Rules

- No local filesystem access.
- No Playwright.
- All actions must pass the confirmation gate first.
