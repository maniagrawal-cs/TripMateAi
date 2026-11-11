# EduVoyage

AI-powered educational field-trip platform built with FastAPI, SQLite, and vanilla JavaScript.

## Recommended local setup (Windows)

Use **Python 3.11 or 3.12** for the smoothest compatibility with the pinned dependencies.

Open PowerShell in the project root (the folder containing `backend` and `frontend`):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

If PowerShell blocks activation, run this once in that terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Environment variables

Copy `backend/.env.example` to `backend/.env`:

```powershell
Copy-Item backend\.env.example backend\.env
```

Open `backend/.env` and add your own Gemini API key to `GEMINI_API_KEY`. AI features have fallback responses if the key is empty or unavailable. Set `SECRET_KEY` to a long random value before deployment.

**Never commit or share `backend/.env`.** The supplied project archive has had its previous `.env` removed for safety.

## Run the complete application

From the **project root**, run:

```powershell
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- Website: http://127.0.0.1:8000
- API health check: http://127.0.0.1:8000/api/health
- Interactive API docs: http://127.0.0.1:8000/docs

Do **not** open `frontend/index.html` directly or use VS Code Live Server for the recommended local setup. FastAPI serves both the frontend and API from the same origin, so the browser's `/api/...` requests reach the correct backend.

If the terminal reports an error, keep that terminal open and read the first traceback. The browser Network tab can also show the exact failing `/api/...` request.

## Demo accounts

Password for all demo accounts: `demo12345`

- Teacher: `teacher@demo.com`
- Student: `aarav@demo.com`
- Student: `diya@demo.com`

Invitation code: `TAJ123`.

## Project structure

- `backend/main.py`: FastAPI app entry point and static frontend hosting
- `backend/models.py`: SQLAlchemy models and SQLite connection
- `backend/routers.py`: API endpoints
- `backend/security.py`: JWT and password hashing
- `backend/ai.py`: Gemini calls and fallback behaviour
- `backend/kb.py`: Taj Mahal knowledge base
- `backend/seed.py`: demo data
- `frontend/`: HTML, CSS, and JavaScript

## Notes

- Run Uvicorn from the project root using `backend.main:app`.
- Do not run `python backend/main.py` or `uvicorn main:app`.
- The SQLite database is local to the project and is not suitable for multi-instance production deployment.
