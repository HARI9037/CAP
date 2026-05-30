# data/logs/

## Purpose

Reserved directory for possible future local log artifacts.

## Current Status

This directory is EMPTY and unused at runtime.

## Runtime Logging

- Logs go to stdout.
- In production, Render captures stdout in its log stream.
- Log level is controlled by the `LOG_LEVEL` environment variable through `app/utils/logging.py`.
