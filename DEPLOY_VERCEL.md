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
| `HR_CALENDAR_DELEGATE_EMAIL` | Real Workspace user for domain-wide delegation (not a group) |
| `HR_CALENDAR_ID` | OOO roster calendar (full ID or name) |
| `HR_CALENDAR_GROUP_EMAIL` | Google Group invited on each event (e.g. `ooo@yourdomain.com`) |

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

## 5. Google Calendar (Google Workspace) checklist

Leave and holiday flows create events on **`HR_CALENDAR_ID`** (default: the delegated user’s primary calendar) using a **service account** and **domain-wide delegation** as **`HR_CALENDAR_DELEGATE_EMAIL`**. All of the following must be true or Calendar calls return 403 and only show up in server logs.

### Google Cloud (project that owns the service account)

1. Enable **Google Calendar API**: APIs & Services → Library → “Google Calendar API” → Enable.
2. Create a **service account** (IAM → Service Accounts), then **Keys** → Add key → JSON. That file is what you base64 for Vercel (`GOOGLE_CALENDAR_CREDENTIALS_JSON_B64`) or place as `backend/google_calendar_credentials.json` locally.
3. Copy the service account’s **numeric Client ID** (not the email) from the service account details page — you need it for Admin Console.

### Google Admin Console (workspace admin)

1. **Security** → **Access and data control** → **API controls** → **Domain-wide delegation** → **Manage domain-wide delegation** → **Add new**.
2. Enter the service account **Client ID**.
3. OAuth scopes (comma-separated, exact):

   `https://www.googleapis.com/auth/calendar`

4. Save. Propagation can take a few minutes.

### App environment variables

| Variable | Purpose |
|----------|---------|
| `GOOGLE_CALENDAR_CREDENTIALS_JSON_B64` | **Recommended on Vercel**: base64-encode the entire JSON key file (`base64 -i key.json \| tr -d '\n'`) and paste the string. Avoids broken escaping from multiline JSON. |
| `GOOGLE_CALENDAR_CREDENTIALS_JSON` | Alternative: single-line JSON (fragile in dashboards). |
| `HR_CALENDAR_DELEGATE_EMAIL` | A **real Workspace user** (not a Google Group) used only for domain-wide delegation. Example: `ipshita@yourdomain.com`. |
| `HR_CALENDAR_ID` | Calendar that stores the master OOO roster (full `@group.calendar.google.com` ID or calendar name like `OOO Calendar`). |
| `HR_CALENDAR_GROUP_EMAIL` | Google Group given **read access to the roster calendar** via ACL (e.g. `ooo@yourdomain.com`). **Do not rely on inviting this group on each event** — the Calendar API does not propagate group-attendee events to member calendars. |
| `HR_CALENDAR_INVITE_TEAM` | `true` (default): invite **each employee email individually** on every leave/holiday so events appear on their primary calendars. |
| `HR_CALENDAR_SEND_UPDATES` | `all` (default), `externalOnly`, or `none`. |

**Google Calendar API limitation (important):** Creating an event with `ooo@yourdomain.com` as an attendee via the API **does not** make the event visible on group members' calendars. This is a [known API limitation](https://groups.google.com/g/google-calendar-api/c/mpCsVKMQi48); it works in the Google Calendar UI but not via API. The app works around this by:
1. Inviting every employee in the HRMS database individually (`HR_CALENDAR_INVITE_TEAM=true`).
2. Sharing the OOO roster calendar with the Google Group via ACL so members can subscribe to the shared calendar.

**Verify an event:** `GET /api/calendar/google/verify?event_id=<id>` returns what Google stored (attendees, link, organizer).

**Google Group calendar setup:**
1. Admin Console → Groups → OOO group → enable **Calendar** and share with members.
2. Set `HR_CALENDAR_GROUP_EMAIL` to the group address (`ooo@…`).
3. Optionally share the OOO roster calendar with the group: Google Calendar → OOO Calendar → **Share with specific people** → add `ooo@…` with “See all event details”.
4. The delegate user must have **Make changes to events** on `HR_CALENDAR_ID`.

Local dev: put the JSON next to `server.py` as `google_calendar_credentials.json` (gitignored via `*credentials*` patterns).

### Verify after deploy

- `GET /api/health` includes a `calendar` object: `credentials_loaded`, and after startup `reachable` + `probe_detail` from a lightweight `calendarList` probe.
- If `reachable` is false, check Vercel logs for `Google Calendar` lines (HTTP status and error body).

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
