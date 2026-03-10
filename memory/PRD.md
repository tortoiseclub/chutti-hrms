# TortoiseHR - Attendance Management App

## Original Problem Statement
Build an attendance management app where employees can apply for leaves (Out of Office - OOO) or Work From Home (WFH), and the requests are deducted from their leave balance.

## Core Requirements

### Authentication (Updated)
- **Password-protected login** for both HR and employees
- HR creates employee → **auto-generated password sent via email**
- **Forgot password** → email link with reset token (1 hour expiry)
- **Password reset** via token in URL
- Secure password hashing with bcrypt
- Case-insensitive email matching

### Leave Policy
- **Earned Leave (EL)**: 1.5 per month (18 per year)
- **Casual/Sick Leave (CL/SL)**: 0.5 per month (6 per year)
- **Work From Home (WFH)**: 1 per month (12 per year)
- Balances calculated based on joining month
- OOO deducts from CL first, then EL
- EL carry forward: max 50% of year's eligible ELs

### User Roles
- **HR**: Add employees, add holidays, manage leaves
- **Employee**: Apply leaves, view balance/history

### Leave Year
- January to December cycle

## Tech Stack
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + TailwindCSS + shadcn/ui
- **Database**: MongoDB
- **Email**: SendGrid (LIVE integration)

## What's Implemented

### Backend (`/app/backend/server.py`)
- [x] Password-protected authentication (bcrypt hashing)
- [x] Auto-generated passwords for new employees
- [x] Forgot password with email reset link
- [x] Password reset with token validation (1hr expiry)
- [x] Case-insensitive email lookup
- [x] SendGrid email integration (LIVE)
- [x] Employee CRUD operations
- [x] Leave balance calculation
- [x] Leave application with balance validation
- [x] OOO deduction logic (CL first, then EL)
- [x] Holiday management
- [x] Calendar API

### Frontend
- [x] Login page with email + password
- [x] Forgot password page
- [x] Reset password page (with token)
- [x] Dashboard with leave balances
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
| `/api/balances` | GET | All employees' balances |
| `/api/leaves` | GET/POST | List/Apply leaves |
| `/api/leaves/{id}` | DELETE | Cancel leave |
| `/api/holidays` | GET/POST | List/Add holidays |
| `/api/holidays/{id}` | DELETE | Remove holiday |
| `/api/calendar` | GET | Calendar events |

## Test Coverage
- **Iteration 1**: Backend 27/27, Frontend 5/5 (basic features)
- **Iteration 2**: Backend 42/42, Frontend all flows passed (+ auth)

## Credentials
- **HR Login**: `ipshita@Tortoise.pro` / `TortoiseHR@2024`

## Email Integration
- **Provider**: SendGrid (LIVE)
- **Status**: Working (emails sent with status 202)
- **Emails sent**: Welcome emails, password reset emails, leave notifications

## Upcoming Tasks (P0-P1)
- [ ] Year-end EL carry forward script (capped at 50%)
- [ ] HR can add leaves on behalf of employees
- [ ] Employee delete/deactivate functionality

## Future Tasks (P2-P3)
- [ ] Leave approval workflow (if required)
- [ ] Reports and analytics
- [ ] Export functionality (CSV/Excel)
- [ ] Change password from profile

## Architecture
```
/app
├── backend/
│   ├── .env              # MONGO_URL, DB_NAME, SENDGRID_API_KEY, SENDER_EMAIL, FRONTEND_URL
│   ├── requirements.txt
│   ├── server.py         # All API routes and business logic
│   └── tests/
│       ├── test_attendance_api.py
│       └── test_auth_password.py
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   │   ├── Layout.js
    │   │   └── ui/       # shadcn components
    │   ├── pages/
    │   │   ├── Login.js
    │   │   ├── ForgotPassword.js
    │   │   ├── ResetPassword.js
    │   │   ├── Dashboard.js
    │   │   ├── Calendar.js
    │   │   ├── Employees.js
    │   │   └── Holidays.js
    │   └── App.js
    └── .env              # REACT_APP_BACKEND_URL
```

## Last Updated
- Date: 2026-03-10
- Status: Password Authentication Complete, SendGrid LIVE
