# Deploy Chutti on Vercel (two projects)

Use **two Vercel projects** from the same Git repository: one for the API, one for the CRA frontend.

## Provisioning checklist

1. **MongoDB Atlas** — cluster, database user, network access `0.0.0.0/0`, copy SRV connection string.
2. **Vercel API project** — import repo, set **Root Directory** to `backend`, add env vars (below), deploy.
3. **Vercel frontend project** — import the **same** repo again, **Root Directory** `frontend`, set `REACT_APP_BACKEND_URL` to the API’s production URL (no trailing slash), deploy.
4. **CORS** — set `CORS_ORIGINS` on the API to your frontend URL (e.g. `https://chutti-frontend.vercel.app`).

## 1. MongoDB Atlas

1. Create a free (M0) or paid cluster.
2. Database Access → create a user; Network Access → allow `0.0.0.0/0` (or Vercel-only if you use static egress later).
3. Copy the connection string and pick a database name (e.g. `chutti`).

## 2. API project (`chutti-api` or similar)

1. [Vercel](https://vercel.com) → **Add New** → **Project** → import this repo.
2. **Root Directory**: `backend` (required).
3. **Framework Preset**: Vercel should detect **FastAPI** / Python. Uses [`backend/vercel.json`](backend/vercel.json) → `pip install -r requirements-vercel.txt` (slim list; do **not** use full `requirements.txt` on Vercel).
4. **Settings → General → Node.js Version**: N/A for Python. For **Python**, set **Python 3.12** (or 3.11) under Project → Settings if the build picks the wrong runtime.
5. **Environment variables** (Production):

| Name | Notes |
|------|--------|
| `MONGO_URL` | Atlas SRV connection string (**required** for API to work) |
| `DB_NAME` | e.g. `chutti` |
| `SENDGRID_API_KEY` | For password reset / mail |
| `SENDER_EMAIL` | From address for SendGrid |
| `FRONTEND_URL` | Final frontend URL, e.g. `https://chutti.vercel.app` |
| `CORS_ORIGINS` | Frontend origin(s), comma-separated, no spaces (e.g. `https://app.vercel.app`) |
| `GOOGLE_CALENDAR_CREDENTIALS_JSON` | Optional: service account JSON one line |
| `GOOGLE_CALENDAR_CREDENTIALS_JSON_B64` | Optional: base64 of that JSON |
| `HR_CALENDAR_DELEGATE_EMAIL` | Workspace user for domain-wide delegation |

6. Deploy. Note the **production URL** (e.g. `https://chutti-api.vercel.app`).
7. Smoke test: `GET https://<api>/api/health` → `{"status":"ok"}`.

## 3. Frontend project (`chutti-frontend`)

1. **Add New Project** → same repo (Vercel allows one repo → multiple projects).
2. **Root Directory**: `frontend`.
3. [`frontend/vercel.json`](frontend/vercel.json) sets **Create React App**, `yarn install --frozen-lockfile`, output `build`.
4. **Environment variables** (Production):

| Name | Value |
|------|--------|
| `REACT_APP_BACKEND_URL` | API URL **without** trailing slash, e.g. `https://chutti-api.vercel.app` |

5. Deploy. Open the site and try login.

**Important:** Changing `REACT_APP_BACKEND_URL` requires a **redeploy** of the frontend (CRA bakes it at build time).

## 4. Custom domains (optional)

Attach domains to each project in Vercel, then update `REACT_APP_BACKEND_URL`, `FRONTEND_URL`, and `CORS_ORIGINS`, and redeploy both.

## Fixes already in this repo

- **Frontend:** Vercel sets `CI=true`, so ESLint warnings fail the CRA build. `react-hooks/exhaustive-deps` issues in Calendar / Dashboard / Holidays were fixed with `useCallback`.
- **Backend:** Deploy uses **`requirements-vercel.txt`** (minimal deps). The full **`requirements.txt`** pulls in ML/AI stacks and often **times out or exceeds limits** on Vercel.
- **Backend:** If `MONGO_URL` is missing at import time, the app still loads; configure `MONGO_URL` in Vercel for any real traffic.

## Local checks

```bash
# Frontend (same as Vercel)
cd frontend && CI=true yarn build

# Backend slim deps
cd backend && pip install -r requirements-vercel.txt && python -c "import server"
```

Do not commit `.env`; use `.env.example` files as templates.
