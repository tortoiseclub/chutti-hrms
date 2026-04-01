# Deploy Chutti on Vercel (two projects)

Use **two Vercel projects** from the same Git repository: one for the API, one for the CRA frontend.

## 1. MongoDB Atlas

1. Create a free (M0) or paid cluster.
2. Database Access → create a user; Network Access → allow `0.0.0.0/0` (or Vercel-only if you use static egress later).
3. Copy the connection string and pick a database name (e.g. `chutti`).

## 2. API project (`chutti-api` or similar)

1. [Vercel](https://vercel.com) → **Add New** → **Project** → import this repo.
2. **Root Directory**: `backend`
3. **Environment variables** (Production):

| Name | Notes |
|------|--------|
| `MONGO_URL` | Atlas SRV connection string |
| `DB_NAME` | e.g. `chutti` |
| `SENDGRID_API_KEY` | Optional if email flows unused in dev |
| `SENDER_EMAIL` | From address for SendGrid |
| `FRONTEND_URL` | Final frontend URL, e.g. `https://chutti.vercel.app` |
| `CORS_ORIGINS` | Same as frontend origin(s), comma-separated |
| `GOOGLE_CALENDAR_CREDENTIALS_JSON` | Optional: full service account JSON as one line |
| `GOOGLE_CALENDAR_CREDENTIALS_JSON_B64` | Optional: base64 of that JSON (easier for multiline) |
| `HR_CALENDAR_DELEGATE_EMAIL` | Workspace user the service account delegates to |

4. Deploy. Note the **production URL** (e.g. `https://chutti-api.vercel.app`).
5. Smoke test: `GET https://<api>/api/health` → `{"status":"ok"}`.

## 3. Frontend project (`chutti-frontend`)

1. **Add New Project** → same repo.
2. **Root Directory**: `frontend`
3. **Build**: `yarn install && yarn build` (or default if Vercel detects CRA).
4. **Output**: `build`
5. **Environment variables** (Production):

| Name | Value |
|------|--------|
| `REACT_APP_BACKEND_URL` | API URL **without** trailing slash, e.g. `https://chutti-api.vercel.app` |

6. Deploy. Open the site and try login.

**Important:** Changing `REACT_APP_BACKEND_URL` requires a **new deployment** of the frontend (CRA bakes it at build time).

## 4. Custom domains (optional)

Attach domains to each project in Vercel, then update `REACT_APP_BACKEND_URL`, `FRONTEND_URL`, and `CORS_ORIGINS`, and redeploy both.

## Notes

- First API deploy may take a while: `backend/requirements.txt` is large. You can trim unused packages later for faster cold starts.
- Do not commit `.env`; use `.env.example` as a template locally.
