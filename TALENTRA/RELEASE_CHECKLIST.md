# TALENTRA.ID — RELEASE CANDIDATE INFRASTRUCTURE CHECKLIST

This checklist defines the operational gates required to promote the project from:
`APPLICATION_COMPLETE_INFRA_PENDING` $\rightarrow$ `RELEASE_CANDIDATE`.

---

## 1. Application Baseline Verification
- [x] Backend Unit & API Tests Passing (119/119)
- [x] Frontend Invariant Suites Passing (39/39)
- [x] TypeScript Typecheck Clean (0 errors)
- [x] Next.js Production Build Succeeded (18/18 routes)
- [x] Architecture & State Kit Validator Succeeded (0 errors, 0 warnings)
- [x] Git Baseline Repository Initialized & Clean Commit Created

---

## 2. Security & Compliance Gates
- [x] Secret Scan Clean (No production keys, passwords, or salts committed)
- [x] Frontend Client Bundle Verified (Zero leaked backend secrets/database URLs)
- [x] Production Fail-Fast Enforced (`APP_ENV=production` fails on default/insecure keys)
- [x] Strict CORS Enforced (No wildcard `*` allowed in production)
- [x] Cookie Security Enforced (`HttpOnly`, `Secure=True`, `SameSite=Lax`)
- [x] Initial Admin Bootstrap CLI Implemented (`python -m app.scripts.bootstrap_school_admin`)
- [x] Referrer Policy Hardened (`no-referrer` on `/verify/[token]` and strict origin)
- [x] Container Artifacts Created (`backend/Dockerfile`, `Dockerfile`, `.dockerignore`)
- [x] CI/CD Pipeline Configured (`.github/workflows/ci.yml`)

---

## 3. Real Infrastructure Gates (Staging Environment Required)
- [ ] Real PostgreSQL Tested (Version $\ge$ 15, Alembic migrations 0001–0006 verified)
- [ ] Real MongoDB Tested (Version $\ge$ 6.0, compound indexes, collections verified)
- [ ] Real S3/MinIO Tested (Private bucket, presigned PUT/GET, binary integrity)
- [ ] Real Multi-Store E2E Passed (`pytest -m integration_real` green)
- [ ] Real Container Builds Verified Locally / Staging Registry
- [ ] Real Database Backup & Restore Tested (PostgreSQL `pg_dump` restore verified)
- [ ] Real MongoDB Backup & Restore Tested (`mongodump` restore verified)
- [ ] Live Object Persistence Verified Across Container Restarts
- [ ] Staging Smoke Test Passed on All Role Routes

---

## 4. Current Status
- **Host Docker Availability**: `UNAVAILABLE` (`docker` command not found on host)
- **Current Gate Verdict**: `APPLICATION_COMPLETE_INFRA_PENDING`
- **Next Operational Step**: Install Docker / Docker Desktop or provision a Linux staging VM to run `docker compose -f docker-compose.dev.yml up -d` and execute `pytest -m integration_real`.
