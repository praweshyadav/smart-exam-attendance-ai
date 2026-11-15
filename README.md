# Smart Exam Attendance System

An end-to-end, contactless, AI-driven biometric attendance and examination verification platform built with **React 19 + Vite**, **Python FastAPI**, **InsightFace (SCRFD + ArcFace)**, **MediaPipe Face Landmarker**, **OpenCV**, and **MySQL**.

Developed at the **School of Computer Science and Engineering, KIIT Deemed to be University, Bhubaneswar**.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Technology Stack](#technology-stack)
4. [Project Directory Structure](#project-directory-structure)
5. [System Architecture](#system-architecture)
6. [Core Workflows & Flowcharts](#core-workflows--flowcharts)
7. [Role-Based Access Control (RBAC)](#role-based-access-control-rbac)
8. [Database Schema](#database-schema)
9. [REST API Endpoints](#rest-api-endpoints)
10. [Installation & Setup](#installation--setup)
11. [Testing](#testing)
12. [Team Members](#team-members)

---

## Overview

Traditional examination and classroom attendance workflows rely on manual roll calls, paper signature sheets, or hardware proximity cards. These methods consume exam/instructional time, remain vulnerable to proxy attendance, and lack real-time auditing.

The **Smart Exam Attendance System** automates identity verification using real-time webcam facial recognition backed by multi-layered anti-spoofing and active liveness detection. It prevents photo, phone-screen, and video-replay attacks while enforcing institutional policies such as weekend/holiday blocking, single-day attendance deduplication, and exam-roster validation.

---

## Key Features

- **Fast Contactless Face Recognition:** Uses InsightFace `buffalo_l` (`detection` + `recognition` modules only) to extract L2-normalized 512-dimensional embeddings and matches them via vectorized NumPy BLAS matrix dot-product search.
- **Dual-Synchronized Face Database:** Combines fast in-memory/local disk pickle caching (`data/ai/face_database.pkl`) with persistent MySQL `MEDIUMBLOB` storage.
- **Simplified 1-Click Face Registration:** Streamlined 2-step registration (Student Information -> Webcam Oval Guide -> Single Capture button) with passive anti-spoof validation on upload.
- **Multi-Cue Passive Anti-Spoofing (`AntiSpoofDetector`):**
  - Duplicate/replayed frame hash detection
  - Temporal face-ROI pixel & landmark micro-motion check (blocks static photos)
  - Hough line rectangular bezel/screen-border detection
  - 2D FFT Moire / LCD pixel-grid frequency analysis
  - Specular glare and blur checks
- **Active 2-Step Challenge-Response & Blink Liveness (`ChallengeLivenessService` + `BlinkDetector`):**
  - MediaPipe 478-point Face Landmarker (`face_landmarker.task`)
  - 6-point Eye Aspect Ratio (EAR) blink detection with live UI blink guidance
  - Randomized 2-step challenges (`BLINK`, `OPEN_MOUTH`, `TURN_LEFT`, `TURN_RIGHT`)
  - Anchor embedding continuity across steps to prevent mid-session face swaps
- **Role-Based Access Control (RBAC):**
  - **Admin Console:** Full access to Dashboard (with clickable metric cards), Students, Classes, Exams, Exam Rosters, Live Attendance, Attendance Reports, Calendar/Holidays, Admin & User Management, and Admin Account Settings (change password and unique username).
  - **Student Portal (`user`):** Restricted strictly to self-service **Register Face**, **Take Attendance**, and **My Attendance** (self-only records).
- **Institutional Policies & Telemetry:**
  - Weekend (Saturday/Sunday) and configured Holiday attendance blocking
  - Single-day attendance deduplication (`unique_student_date`)
  - Real-time latency telemetry (`decode_ms`, `inference_ms`, `total_ms`, `fps`)
  - Multi-format report exports in **CSV**, **Excel (`.xlsx`)**, and **PDF**

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 19, Vite 8, React Router DOM 7, Lucide React, HTML5 Canvas & WebRTC (`getUserMedia`) |
| **Backend API** | Python, FastAPI, Uvicorn, Pydantic |
| **Authentication** | Custom HS256 JWT (`AUTH_SECRET_KEY`), PBKDF2-HMAC-SHA256 (200,000 iterations), Token Revocation |
| **AI / Computer Vision** | InsightFace (`buffalo_l`), ONNX Runtime, MediaPipe Face Landmarker (`face_landmarker.task`), OpenCV, NumPy |
| **Database** | MySQL 8.0 (`mysql-connector-python` with `MySQLConnectionPool`, pool size 15) |
| **Exports & Reporting** | OpenPyXL (`.xlsx`), ReportLab (`.pdf`), Python `csv` |
| **Testing** | Pytest |

---

## Project Directory Structure

```text
Smart_Exam_Attendance_v2/
├── README.md
├── README.docx
├── Smart_Exam_Attendance_Presentation.pptx
├── Smart_Exam_Attendance_Project_Report.docx
├── face_landmarker.task
├── data/
│   ├── ai/
│   │   └── face_database.pkl
│   └── exports/
├── logs/
├── scratch/
│   └── benchmark_final_suite.py
├── backend/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── models.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── anti_spoof.py
│   │   ├── blink_detector.py
│   │   ├── eye_aspect_ratio.py
│   │   ├── eye_landmarks.py
│   │   ├── face_database.py
│   │   ├── face_engine.py
│   │   ├── face_matcher.py
│   │   ├── face_validator.py
│   │   └── liveness_detector.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── dependencies.py
│   │   ├── auth_api.py
│   │   ├── student_api.py
│   │   ├── class_api.py
│   │   ├── exam_api.py
│   │   ├── exam_roster_api.py
│   │   ├── face_registration_api.py
│   │   ├── attendance_api.py
│   │   ├── attendance_session_api.py
│   │   ├── attendance_verification_api.py
│   │   ├── attendance_verification_session_api.py
│   │   ├── verification_api.py
│   │   ├── verification_attempt_api.py
│   │   ├── dashboard_api.py
│   │   ├── analytics_api.py
│   │   └── export_router.py
│   └── services/
│       ├── __init__.py
│       ├── activity_service.py
│       ├── analytics_service.py
│       ├── attendance_processing_service.py
│       ├── attendance_service.py
│       ├── attendance_session_service.py
│       ├── auth_service.py
│       ├── challenge_liveness_service.py
│       ├── class_service.py
│       ├── dashboard_service.py
│       ├── exam_roster_service.py
│       ├── exam_service.py
│       ├── export_service.py
│       ├── face_registration_service.py
│       ├── holiday_service.py
│       ├── liveness_service.py
│       ├── notification_service.py
│       ├── report_service.py
│       ├── student_service.py
│       ├── verification_attempt_service.py
│       ├── verification_service.py
│       └── verification_session_service.py
├── frontend/
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── context/
│       │   └── AuthContext.jsx
│       ├── utils/
│       │   └── date.js
│       ├── services/
│       │   ├── api.js
│       │   ├── attendanceService.js
│       │   ├── authService.js
│       │   ├── classService.js
│       │   ├── dashboardService.js
│       │   ├── examService.js
│       │   ├── faceService.js
│       │   └── studentService.js
│       ├── components/
│       │   ├── AttendanceCalendar.jsx
│       │   ├── AttendanceTrendChart.jsx
│       │   ├── DashboardHeader.jsx
│       │   ├── ErrorMessage.jsx
│       │   ├── Loading.jsx
│       │   ├── QuickAction.jsx
│       │   ├── QuickActions.jsx
│       │   ├── RecentActivityFeed.jsx
│       │   ├── Sidebar.jsx
│       │   ├── StatCard.jsx
│       │   ├── TodayAttendanceCard.jsx
│       │   └── TopNav.jsx
│       └── pages/
│           ├── AdminUsers.jsx
│           ├── AttendanceRegister.jsx
│           ├── AttendanceReport.jsx
│           ├── CalendarPage.jsx
│           ├── Classes.jsx
│           ├── Dashboard.jsx
│           ├── Exams.jsx
│           ├── Login.jsx
│           ├── RegisterStudent.jsx
│           ├── Reports.jsx
│           ├── Sessions.jsx
│           ├── Signup.jsx
│           ├── Students.jsx
│           ├── TakeAttendance.jsx
│           ├── VerificationLogs.jsx
│           └── ViewAttendance.jsx
└── tests/
    └── test_*.py (28 automated test suites)
```

---

## System Architecture

```text
+-------------------------------------------------------------------------+
|                        FRONTEND (React 19 + Vite)                       |
|   Login / Signup  |  Admin Console (Dashboard, Students, Classes, etc.) |
|                   |  Student Portal (Register Face, Take & My Att.)     |
+------------------------------------+------------------------------------+
                                     | REST API (HTTP + JWT Bearer Token)
                                     v
+-------------------------------------------------------------------------+
|                       BACKEND (FastAPI - 15 Routers)                    |
|   Auth & RBAC Dependencies  |  Session & Roster Validation  |  Exports  |
+------------------+-----------------------------------+------------------+
                   |                                   |
                   v                                   v
+----------------------------------+  +-----------------------------------+
|      AI & LIVENESS PIPELINE      |  |    MYSQL 8.0 + CACHE LAYER        |
|  - InsightFace (SCRFD + ArcFace) |  |  - 12 Normalized InnoDB Tables    |
|  - Vectorized BLAS FaceMatcher   |  |  - 15-Connection Pool             |
|  - MediaPipe 478-Pt Landmarker   |  |  - Dual-Sync face_database.pkl    |
|  - EAR Blink + Passive AntiSpoof |  |  - In-Memory Marked/Student Cache |
+----------------------------------+  +-----------------------------------+
```

---

## Core Workflows & Flowcharts

### 1. Face Registration Flow

```text
[Start: Register Face Page]
         |
         v
[Step 1: Enter / Confirm Roll No., Name, Branch, Semester, Section]
         |
         v
[Step 2: Open Webcam + Oval Guide Overlay]
         |
         v
[Click "Capture Face & Register"] --> [POST /students + POST /face-registration/]
                                                |
                                                v
                                     [Static Anti-Spoof Check]
                                       (Bezel / Moire / Glare)
                                                |
                                    +-----------+-----------+
                                    | Spoof                 | Genuine
                                    v                       v
                          [Reject & Alert]     [InsightFace Detect & Validate]
                                                            |
                                                            v
                                               [Extract 512-D Unit Embedding]
                                                            |
                                                            v
                                               [Duplicate Face Check in Matcher]
                                                            |
                                                            v
                                               [Save to MySQL + face_database.pkl]
                                                            |
                                                            v
                                               [Step 3: Registration Complete]
```

### 2. Real-Time Attendance & Anti-Spoof Flow

```text
[Start Session: POST /attendance-sessions/ + POST /attendance/verify/start]
         |
         v
[Webcam Frame Loop -> POST /attendance/verify/frame]
         |
         v
[InsightFace Face Detection (Filter min size >= 70px, det_score >= 0.60)]
         |
         +--> [No Face / Multiple Prominent Faces] --> [Prompt User]
         |
         v (Single Valid Face)
[Passive Anti-Spoof Check: Hash, Micro-Motion, Bezel, FFT Moire, Glare]
         |
         +--> [Spoof Detected] --> [Block & Show Red Spoof Warning]
         |
         v (Genuine Frame)
[Active 2-Step Liveness: MediaPipe EAR Blink + Mouth/Pose Challenge]
         |
         +--> [Not Completed] --> [Show Blink Hint & Challenge Step]
         |
         v (Liveness Verified)
[ArcFace 512-D Embedding -> Vectorized Cosine Similarity Match]
         |
         v
[POST /attendance/verify/complete]
         |
         v
[Check Weekend/Holiday Policy + Exam Roster + Daily Deduplication]
         |
         v
[Record Attendance in MySQL + Log Attempt + Play Confirmation]
```

---

## Role-Based Access Control (RBAC)

| Role | Allowed Routes & Capabilities | Restrictions |
|---|---|---|
| **Admin** (`admin`) | Full administrative access: Dashboard (clickable metric cards), Register Student Face, Take Real-Time Attendance, View Attendance (class-wide), Attendance Reports, Calendar & Holidays, Students, Classes, Exams & Rosters, Admin & Users management, and Account Settings (password and unique username changes) | Primary System Admin account cannot be deleted |
| **Student** (`user`) | View My Attendance (`/view-attendance`) only | Restricted strictly to viewing and exporting **self** attendance history; cannot register faces, initiate attendance sessions, or access administrative records |

---

## Database Schema

`initialize_database()` in `backend/database/database.py` automatically creates the MySQL database (default `7th`) and **12 normalized InnoDB tables**:

1. `classes` — Department, semester, and section definitions.
2. `students` — Student profile, `face_registered` flag, `face_image` (`LONGTEXT`), and `face_embedding` (`MEDIUMBLOB`).
3. `exams` — Scheduled exam details linked to `classes`.
4. `exam_roster` — Eligible students mapped per exam (`unique_exam_student`).
5. `attendance_sessions` — Active/completed attendance sessions (`exam_id`, `created_by`, timestamps).
6. `attendance` — Marked attendance records with `unique_student_date` deduplication constraint and `verification_score`.
7. `verification_attempts` — Audit log of verification outcomes, similarity scores, and liveness results.
8. `holidays` — Configured academic holidays blocking attendance.
9. `activity_logs` — System audit trail (signups, admin creation, password/username updates, attendance events).
10. `notifications` — Admin dashboard notifications and read states.
11. `users` — User accounts (`username`, `password_hash`, `role`, `is_system_admin`, `student_id`, `is_active`).
12. `revoked_tokens` — Invalidated JWT `jti` blacklist for secure logout.

---

## REST API Endpoints

| Router Prefix | Purpose |
|---|---|
| `/auth` | Student signup, login, logout, current user (`/me`), admin registration, user management, admin password (`PUT /auth/me/password`) & unique username (`PUT /auth/me/username`) updates |
| `/students` | CRUD operations for student profiles |
| `/classes` | CRUD operations for branches, semesters, and sections |
| `/exams` | Exam scheduling and management |
| `/exam-roster` | Assign and verify students in exam rosters |
| `/face-registration` | Face capture upload, passive anti-spoof check, 512-D embedding storage |
| `/attendance-sessions` | Create and close attendance sessions |
| `/attendance/verify` | Stateful real-time verification session (`/start`, `/frame`, `/complete`, `/reset`, `/close`) |
| `/attendance` | Attendance records retrieval (`GET /attendance/me` for students, full query for admins) |
| `/verification` & `/attendance-verification` | Single-frame verification and verification attempt endpoints |
| `/verification-attempts` | Verification audit attempt logs |
| `/dashboard` (and `/api/dashboard`) | Summary stats, attendance trends, today's breakdown, calendar, notifications, global search |
| `/analytics` | Attendance analytics aggregations |
| `/exports` | Authenticated CSV, Excel (`.xlsx`), and PDF downloads for student, class, exam, and daily reports |

---

## Installation & Setup

### Prerequisites

- **Python 3.11+** (with virtual environment)
- **Node.js 18+** and **npm**
- **MySQL 8.0** running locally (default port `3306`)
- Webcam access in a modern browser

### 1. Environment Variables (Optional Overrides)

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | `Gautam@12` | MySQL password |
| `DB_NAME` | `7th` | MySQL database name |
| `FACE_RECOGNITION_THRESHOLD` | `0.55` | Cosine similarity match threshold |
| `LIVENESS_ENABLED` | `true` | Enable active liveness challenge |
| `BLINK_THRESHOLD` | `0.20` | EAR threshold for eye blink detection |
| `SYSTEM_ADMIN_USERNAME` | `admin` | Default seeded System Admin username |
| `SYSTEM_ADMIN_PASSWORD` | `Admin@123` | Default seeded System Admin password |

### 2. Backend Setup

```bash
# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Start FastAPI backend server
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

---

## Testing

Run the automated backend and AI test suites from the project root:

```bash
pytest tests/
```

---

## Team Members

- Dipendra Kumar Yadav
- Raj
- Prawesh Yadav
- Vivek
- Anmol
- Aditya
