# TortoiseHR - Attendance Management App

## Original Problem Statement
Build an attendance management app where employees can apply for leaves (Out of Office - OOO) or Work From Home (WFH), and the requests are deducted from their leave balance.

## Core Requirements

### Authentication
- **Password-protected login** for both HR and employees
- HR creates employee → **auto-generated password sent via email**
- **Forgot password** → email link with reset token (1 hour expiry)
- **Password reset** via token in URL
- Secure password hashing with bcrypt
- Case-insensitive email matching

### Leave Balance Visibility (NEW)
- **HR**: Can see all employees' leave balances
- **Employees**: Can only see their own balance (not other employees')

### Google Calendar Integration (NEW)
- **OOO/WFH Leaves**: Creates calendar event on HR's calendar (ipshita@tortoise.pro)
- **Holidays**: Creates calendar event for national holidays
- **Event Format**: "OOO - Employee Name" or "WFH - Employee Name"
- **Delete**: Removes calendar event when leave/holiday is cancelled

### Leave Policy
- **Earned Leave (EL)**: 1.5 per month (18 per year)
- **Casual/Sick Leave (CL/SL)**: 0.5 per month (6 per year)
- **Work From Home (WFH)**: 1 per month (12 per year)
- Balances calculated based on joining month
- OOO deducts from CL first, then EL
- EL carry forward: max 50% of year's eligible ELs

### User Roles
- **HR**: Add employees, add holidays, manage leaves, view all balances
- **Employee**: Apply leaves, view own balance/history only

### Leave Year
- January to December cycle

## Tech Stack
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TailwindCSS + shadcn/ui
- **Database**: MongoDB
- **Email**: SendGrid (LIVE)
- **Calendar**: Google Calendar API with Service Account + Domain-Wide Delegation

## What's Implemented

### Backend (`/app/backend/server.py`)
- [x] Password-protected authentication (bcrypt hashing)
- [x] Auto-generated passwords for new employees
- [x] Forgot password with email reset link
- [x] Password reset with token validation (1hr expiry)
- [x] Case-insensitive email lookup
- [x] SendGrid email integration (LIVE)
- [x] Leave balance visibility restriction (HR vs employee)
- [x] Google Calendar integration for leaves and holidays
- [x] Employee CRUD operations
- [x] Leave balance calculation
- [x] Leave application with balance validation
- [x] OOO deduction logic (CL first, then EL)
- [x] Holiday management with calendar events

### Frontend
- [x] Login page with email + password
- [x] Forgot password page
- [x] Reset password page (with token)
- [x] Dashboard with leave balances
- [x] Team Leave Balances (HR only)
- [x] Leave application dialog
- [x] Employee management (HR only)
- [x] Holiday management (HR only)
- [x] Calendar view

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Login with email + password |
| `/api/auth/forgot-password` | POST | Request password reset email |
| `/api/auth/reset-password` | POST | Reset password with token |
| `/api/auth/verify-reset-token` | GET | Validate reset token |
| `/api/employees` | GET/POST | List/Create employees |
| `/api/employees/{id}/balance` | GET | Get leave balance |
| `/api/balances` | GET | All balances (HR) or own balance (employee) - uses X-Employee-Role header |
| `/api/leaves` | GET/POST | List/Apply leaves (creates Google Calendar event) |
| `/api/leaves/{id}` | DELETE | Cancel leave (deletes Google Calendar event) |
| `/api/holidays` | GET/POST | List/Add holidays (creates Google Calendar event) |
| `/api/holidays/{id}` | DELETE | Remove holiday (deletes Google Calendar event) |
| `/api/calendar` | GET | Calendar events |

## Test Coverage
- **Iteration 1**: Backend 27/27, Frontend 5/5 (basic features)
- **Iteration 2**: Backend 42/42, Frontend all flows (+ auth)
- **Iteration 3**: Backend 50/50, Frontend all flows (+ visibility & calendar)

## Credentials
- **HR Login**: `ipshita@Tortoise.pro` / `TortoiseHR@2024`

## Integrations
- **Email**: SendGrid (LIVE) - `ipshita@tortoise.pro` as sender
- **Calendar**: Google Calendar API with service account `hrdashboard@tortoise-89870.iam.gserviceaccount.com`
  - Domain-Wide Delegation enabled
  - Events created on `ipshita@tortoise.pro`'s calendar

## Upcoming Tasks (P0-P1)
- [ ] Year-end EL carry forward script (capped at 50%)
- [ ] HR can add leaves on behalf of employees
- [ ] Change password from profile option

## Future Tasks (P2-P3)
- [ ] Employee delete/deactivate
- [ ] Reports and analytics
- [ ] Export functionality (CSV/Excel)

## Architecture
```
/app
├── backend/
│   ├── .env                           # MONGO_URL, SENDGRID_API_KEY, etc.
│   ├── google_calendar_credentials.json  # Service account for Calendar API
│   ├── requirements.txt
│   ├── server.py                      # All API routes and business logic
│   └── tests/
│       ├── test_attendance_api.py
│       ├── test_auth_password.py
│       └── test_leave_balance_visibility.py
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── Login.js
    │   │   ├── ForgotPassword.js
    │   │   ├── ResetPassword.js
    │   │   ├── Dashboard.js           # Team Balances visible for HR only
    │   │   ├── Calendar.js
    │   │   ├── Employees.js
    │   │   └── Holidays.js
    │   └── App.js
    └── .env
```

## Last Updated
- Date: 2026-03-24
- Status: Leave Balance Visibility + Google Calendar Integration Complete
