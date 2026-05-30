# data/sessions/

## Purpose

Reserved directory for possible future session artifacts.

## Current Status

This directory is EMPTY and unused at runtime.

## Runtime Session Storage

- Sessions live as rows in `backend/data/cap.db`.
- SQLite access is managed by `app/memory/store.py`.
- Session data is not stored as files in this directory.
