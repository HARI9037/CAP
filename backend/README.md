# backend/
Purpose:
FastAPI backend for CAP — Context-Aware Partner.
Stack: Python 3.11+, FastAPI, Groq API, SQLite, httpx, BeautifulSoup
Hosting: Render
Entry point: main.py
Core philosophy: THINK IN CLOUD → ACT LOCALLY → CONFIRM EVERYTHING
Responsibilities:
- Orchestration via Groq API
- Memory via SQLite
- Research retrieval via httpx + BeautifulSoup
- Workspace file management
- Confirmation gate enforcement before every action
Rules:
- No Playwright
- No local OS access
- No autonomous actions without user confirmation