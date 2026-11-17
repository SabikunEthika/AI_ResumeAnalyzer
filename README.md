# ResumeOrbit

ResumeOrbit is a stateless AI resume-analysis application. It accepts PDF and DOCX resumes, extracts recognised skills, evaluates job alignment, reviews resume quality and ATS-readiness, and creates a browser-generated PDF report.

## Stack

- Backend: FastAPI, Python, Google Gemini, `pypdf`, `python-docx`
- Frontend: React, TypeScript, Vite, jsPDF
- Storage: none. Resume analysis is not persisted by the application.

## Project structure

```text
backend/       FastAPI API and automated tests
frontend/      React/Vite browser application
render.yaml    Render backend deployment blueprint
```

## Local development

Prerequisites: Python 3.11+ and Node.js 20+.

1. Copy `.env.example` to `.env` and set `GEMINI_API_KEY`. Never commit the real `.env` file.
2. Start the backend:

   ```bash
   cd backend
   python -m venv venv
   # Windows PowerShell: .\venv\Scripts\Activate.ps1
   # Git Bash: source venv/Scripts/activate
   pip install -r requirements.txt
   uvicorn main:app --reload
   ```

3. In a second terminal, start the frontend:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

The frontend uses `http://127.0.0.1:8000` by default. Set `VITE_API_BASE_URL` in `frontend/.env` if your API is hosted elsewhere.

## Verification

```bash
cd backend
python -m pytest -q

cd ../frontend
npm run lint
npm run build
```

## Deployment

Deploy the frontend to Vercel and the API to Render.

### Backend on Render

1. Push this repository to GitHub, GitLab, or Bitbucket.
2. In Render, create a **Web Service** from the repository. Render detects `render.yaml`; otherwise set the root directory to `backend`.
3. Set environment variables in Render:

   ```text
   GEMINI_API_KEY=<your secret key>
   APP_ENV=production
   CORS_ALLOWED_ORIGINS=https://<your-vercel-domain>.vercel.app
   GEMINI_MODEL=gemini-3.5-flash-lite
   GEMINI_FALLBACK_MODEL=gemini-3.5-flash
   GEMINI_SECOND_FALLBACK_MODEL=gemini-3.8-flash
   GEMINI_TIMEOUT_MS=30000
   ```

4. Confirm `https://<your-render-domain>/health` returns `{"status":"ok"}`.

### Frontend on Vercel

1. Import the same repository into Vercel.
2. Set the Vercel project root directory to `frontend`.
3. Add this Vercel environment variable for Production and Preview:

   ```text
   VITE_API_BASE_URL=https://<your-render-domain>.onrender.com
   ```

4. Deploy, then update Render’s `CORS_ALLOWED_ORIGINS` with the final Vercel URL if it changed and redeploy Render.

The free Render service can spin down after inactivity, so the first analysis request after idling can take longer. A paid always-on backend is recommended before presenting the service as production-grade.

## Privacy and limitations

- Resume text is sent to Google Gemini to perform AI analysis.
- ResumeOrbit does not use accounts or a database and does not persist analysis results.
- AI feedback and ATS scores are guidance, not hiring, screening, or ATS-acceptance guarantees.
- Gemini availability, safety controls, quotas, and pricing are managed by Google; the application retries transient capacity errors and uses configured fallback models.
