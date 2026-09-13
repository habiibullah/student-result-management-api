# Student Result Management API

A production-ready multi-school SaaS backend for managing schools, administrators, teachers, students, academic structures, assessments, scores, attendance, results, report publication, subscriptions, and payments.

## Overview

The Student Result Management API is built with FastAPI and PostgreSQL and is designed to serve multiple schools securely from a single backend platform.

Each school operates within its own isolated tenant environment while the platform supports centralized administration, term-based subscriptions, result publication, and Flutterwave payment processing.

The backend is currently frozen as API version **1.0.0** and is ready for Flutter mobile integration.

## Core Features

- Multi-school SaaS architecture
- Tenant-isolated school data
- Platform Administrator accounts
- Multiple School Administrator accounts per school
- Teacher accounts and profiles
- Student academic records
- Academic sessions and terms
- Classes and subjects
- Student enrollment
- Teacher teaching assignments
- Continuous assessments and examinations
- Student score management
- Attendance tracking
- Teacher and Principal report comments
- School-specific grading scales
- Automated result computation
- Class position calculation
- Report-sheet generation
- Result publication and reopening
- Published report snapshots
- Term-based subscription plans
- Flutterwave payment integration
- Secure payment verification
- PostgreSQL database migrations with Alembic
- Docker deployment support
- Automated regression and security testing

## Technology Stack

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- JWT authentication
- Argon2 password hashing
- Flutterwave API
- Pytest
- Docker
- Uvicorn

## Project Structure

```text
app/
├── api/
├── core/
├── database/
├── models/
├── schemas/
├── services/
└── main.py

alembic/
├── versions/
└── env.py

tests/
docs/

Environment Setup

Create a virtual environment:

python3 -m venv venv
source venv/bin/activate

Install dependencies:

pip install --upgrade pip
pip install -r requirements.txt

Create the environment file:

cp .env.example .env

Configure the required values in .env, including:

DATABASE_URL
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
FLUTTERWAVE_SECRET_KEY
FLUTTERWAVE_SECRET_HASH
FLUTTERWAVE_REDIRECT_URL
Database Migration

Apply all migrations:

alembic upgrade head

Verify the migration state:

alembic current
alembic heads
alembic check

Current frozen migration head:

7b933b5b8b78
Run the API

Start the development server:

uvicorn app.main:app --reload

or:

python -m uvicorn app.main:app --reload

The local API will normally be available at:

http://127.0.0.1:8000
API Documentation

When enabled through configuration:

http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc
http://127.0.0.1:8000/openapi.json
Health Endpoints
GET /
GET /health
GET /health/database
Testing

The backend contains a PostgreSQL-backed automated regression suite covering authentication, authorization, tenant isolation, subscriptions, result publication, publication locks, and payment security.

Run:

pytest -q

Current verified backend result:

178 passed
0 failed
0 errors

Tests use a dedicated database:

student_result_test_db

and must never be run against the production database.

Multi-School Security

School-bound operations derive tenancy from the authenticated user's school_id.

The backend prevents cross-school access to:

Classes
Subjects
Teachers
Students
Enrollments
Assessments
Scores
Attendance
Comments
Subscriptions
Payments
Results and reports
Subscription Model

Subscriptions are term-based.

A school must have an active subscription for the exact:

School
Academic Session
Term

before protected academic write operations are allowed.

Historical academic data remains readable after subscription expiry.

Result Publication

Results follow this lifecycle:

Academic Data
    ↓
Result Computation
    ↓
Publication Readiness
    ↓
Publish
    ↓
Snapshot
    ↓
Academic Data Locked

Corrections require:

Reopen
    ↓
Edit
    ↓
Republish
Payment Integration

Flutterwave is used for subscription payments.

The backend verifies:

Transaction ID
Transaction reference
Payment status
Currency
Amount
Transaction reuse

Only the backend may activate subscriptions after successful provider verification.

Docker

Build:

docker build -t student-result-management-api .

Run:

docker run --rm \
  --env-file .env \
  -p 8000:8000 \
  student-result-management-api

Database migrations should be executed separately before starting the production application.

Full Documentation

Complete backend documentation is available at:

docs/BACKEND_DOCUMENTATION.md

It contains detailed coverage of:

Architecture
Database models
API contracts
Authentication
Role permissions
Multi-school tenancy
Academic workflows
Result computation
Report publication
Subscription logic
Flutterwave payments
Environment configuration
Alembic migrations
Testing
Security
Troubleshooting
Flutter integration architecture
Deployment guidance
Backend Status
Backend implementation      COMPLETE
Backend regression audit    COMPLETE
Backend freeze              COMPLETE
Backend documentation       COMPLETE
Flutter integration         NEXT PHASE
Frozen Backend Reference

API version:

1.0.0

Migration head:

7b933b5b8b78

Verified regression tests:

178 passed

Frozen backend commit:

074f4df
Next Phase

The next development phase is Flutter integration for Android.

The mobile application will consume the FastAPI REST API and preserve the backend as the trusted authority for:

Authentication
Authorization
Tenant isolation
Academic validation
Subscription enforcement
Result computation
Publication state
Payment verification
