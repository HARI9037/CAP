# pages/
Purpose:
Top-level page components for routing.
Responsibilities:
- HomePage — main entry point, loads chat interface
- NotFoundPage — 404 fallback
Rules:
- Pages compose components only
- No direct API calls inside pages
- Use hooks for data fetching