# TortoiseHR - Attendance Management App

## Original Problem Statement
Build an attendance management app where employees can apply for leaves (Out of Office - OOO) or Work From Home (WFH), and the requests are deducted from their leave balance.

## Core Requirements

### Authentication
- Email-only login (no password/OTP required)
- Pre-seeded HR user: `ipshita@Tortoise.pro`
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

## What's Implemented

### Backend (`/app/backend/server.py`)
- [x] Email-only authentication with case-insensitive matching
- [x] Pre-seeded HR user on startup
- [x] Employee CRUD operations
- [x] Leave balance calculation (prorated by joining date)
- [x] Leave application with balance validation
- [x] OOO deduction logic (CL first, then EL)
- [x] Holiday management
- [x] Calendar API with leave and holiday events

### Frontend
- [x] Login page with Tortoise branding
- [x] Dashboard with leave balances and team overview
- [x] Leave application dialog
- [x] Employee management (HR only)
- [x] Holiday management (HR only)
- [x] Calendar view
- [x] Role-based navigation

### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/login` | POST | Email-only login |
| `/api/employees` | GET/POST | List/Create employees |
| `/api/employees/{id}/balance` | GET | Get leave balance |
| `/api/balances` | GET | All employees' balances |
| `/api/leaves` | GET/POST | List/Apply leaves |
| `/api/leaves/{id}` | DELETE | Cancel leave |
| `/api/holidays` | GET/POST | List/Add holidays |
| `/api/holidays/{id}` | DELETE | Remove holiday |
| `/api/calendar` | GET | Calendar events |

## Test Coverage
- **Backend**: 27/27 tests passed (100%)
- **Frontend**: 5/5 UI flows passed (100%)
- Test file: `/app/backend/tests/test_attendance_api.py`

## Mocked/Deferred Features
- **Email notifications**: Logged only (Resend API key not configured)

## Credentials
- **HR Login**: `ipshita@Tortoise.pro`

## Upcoming Tasks (P0-P1)
- [ ] Year-end EL carry forward script (capped at 50%)
- [ ] Email notification integration (when credentials provided)
- [ ] HR can add leaves on behalf of employees
- [ ] Employee delete/deactivate functionality

## Future Tasks (P2-P3)
- [ ] Leave approval workflow (if required)
- [ ] Reports and analytics
- [ ] Export functionality (CSV/Excel)

## Architecture
```
/app
├── backend/
│   ├── .env              # MONGO_URL, DB_NAME, RESEND_API_KEY
│   ├── requirements.txt
│   ├── server.py         # All API routes and business logic
│   └── tests/
│       └── test_attendance_api.py
└── frontend/
    ├── public/
    ├── src/
    │   ├── components/
    │   │   ├── Layout.js
    │   │   └── ui/       # shadcn components
    │   ├── pages/
    │   │   ├── Login.js
    │   │   ├── Dashboard.js
    │   │   ├── Calendar.js
    │   │   ├── Employees.js
    │   │   └── Holidays.js
    │   └── App.js
    └── .env              # REACT_APP_BACKEND_URL
```

## Last Updated
- Date: 2026-02-23
- Status: MVP Complete, Testing Passed
