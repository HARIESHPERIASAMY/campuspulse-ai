# Security Architecture & Data Privacy - CampusPulse AI 360

## Overview
CampusPulse AI 360 enforces a robust multi-layer security posture designed to safeguard student privacy, prevent unauthorized administrative escalation, and ensure zero real credentials or API keys are exposed.

## 1. Authentication & Dual-Stage Verification
- **Password Hashing**: Uses Werkzeug's salted password hashing algorithm (`generate_password_hash` / `check_password_hash`).
- **Dual-Stage Admin Verification**: 
  1. User authenticates via email and password.
  2. Server verifies role in database.
  3. If role is `ADMIN`, server requires secondary verification key entry (`ADMIN_VERIFICATION_KEY`).
  4. Server validates key against environment variable and stores authorization state in session.

## 2. Server-Side Role Authorization (RBAC)
- Frontend role claims are never trusted.
- Routes are protected via `@login_required` and `@admin_required` decorators executing server-side session checks.
- Students attempting to access `/admin/*` routes are automatically denied access.

## 3. Public Mobile QR Verification Safety
- Public QR code links point to `/notice/public/<notice_id>`.
- The public QR page displays verified notice content, AI summary, category, and deadline.
- Public QR endpoints do **NOT** expose:
  - User passwords or session tokens
  - API keys or secrets
  - Individual student viewer lists or privacy analytics
- Scan count inflation is prevented using a 5-minute session cooldown.

## 4. Secret Management & Git Security
- All sensitive configurations are read from environment variables via `python-dotenv`.
- Real API keys and credentials must be kept in `.env`, which is strictly ignored by `.gitignore`.
- `.env.example` contains development placeholders only.

## 5. Audit Logging
- Security events (login, logout, admin key verification, notice CRUD, publishing, archiving, student reads, acknowledgements) are recorded in the `audit_logs` database table.
