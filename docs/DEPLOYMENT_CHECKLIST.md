# CAP Deployment Checklist

## Environment Variables
Ensure the following variables are configured in both local `.env` and production environments:
### Backend (Render)
- `CORS_ORIGINS`: e.g. `https://your-cap-frontend.netlify.app`
- `DEMO_MODE`: `true` (for hackathon judging mode to enable realistic pre-seeded memory)
- `GROQ_API_KEY`: [Your Groq API Key]
- `LOG_LEVEL`: `INFO` (or `DEBUG` for troubleshooting)

### Frontend (Netlify)
- `VITE_API_URL`: URL of your deployed backend (e.g. `https://cap-backend.onrender.com`)

## Backend Deployment (Render)
1. **Type**: Web Service
2. **Environment**: Python
3. **Build Command**: `pip install -r backend/requirements.txt`
4. **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. **Health Check URL**: `GET /health`
6. **Free-Tier Constraints**: The backend uses minimal packages (FastAPI, httpx, sqlite) to avoid Render's memory limits and cold-start timeouts. **Do not** add Playwright or heavy Chromium dependencies.

## Frontend Deployment (Netlify)
1. **Build Command**: `npm run build`
2. **Publish Directory**: `dist`
3. **Redirects**: Ensure SPAs redirect to `index.html` by adding a `_redirects` file in `public/` containing `/* /index.html 200` (Vite usually handles this or Netlify settings can enforce it).

## CORS Configuration
Ensure that the backend `CORS_ORIGINS` accurately reflects the deployed Netlify frontend URL. Failing to set this will result in Network Errors on the frontend.

## Final Validation Steps
- Open the frontend URL.
- Wait for the "Warming up CAP..." screen to clear (handling potential Render cold starts).
- Verify the seeded memory from the Demo Mode correctly appears in the Memory Panel.
- Perform a workflow action and verify the Confirmation Gate renders correctly.
