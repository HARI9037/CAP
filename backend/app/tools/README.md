# tools/
Purpose:
Executes safe cloud-compatible actions dispatched by the orchestrator.
Tools included:
1. Research Retrieval Tool
   - Web search and content extraction
   - Stack: httpx + BeautifulSoup
   - Returns summarized research results
2. Workspace File Tool
   - Read, save, organize cloud workspace files only
   - Manages uploaded files, summaries, session notes
Rules:
- No access to judge's local filesystem or desktop
- No Playwright or heavy browser automation
- No permanent delete operations
- All actions must be approved via Confirmation Gate first