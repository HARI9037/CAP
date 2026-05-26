# frontend/
Purpose:
React + Vite chat interface for CAP.
Stack: React, Vite, TailwindCSS, Axios
Hosting: Netlify
Responsibilities:
- Chat UI and message rendering
- Send user prompts to backend API
- Display AI responses
- Show Confirmation Gate UI for pending actions
- Display workflow memory summary panel
- Show warmup screen on cold start: "Warming up CAP..."
Rules:
- No hardcoded backend URLs — use VITE_API_URL environment variable
- No local filesystem access
- Keep components small and single-purpose