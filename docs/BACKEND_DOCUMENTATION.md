Student Result Management API
Backend Technical Documentation
Project Type: Multi-School SaaS Student Result Management System
Backend Framework: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Migration Tool: Alembic
Authentication: JWT
Payment Provider: Flutterwave
Current Backend Version: 1.0.0
Backend Freeze Commit: 074f4df
Alembic Head: 7b933b5b8b78
Regression Test Status: 178 tests passed

1. Project Overview
The Student Result Management API is a multi-school Software-as-a-Service backend designed to support the academic and administrative operations required for managing student results across multiple schools.
The system allows independent schools to register on the platform and manage their own academic records while maintaining strict separation between tenants.
Each school operates inside its own logical data boundary.
The backend supports major academic workflows including:
school registration
administrator management
teacher management
student management
classes
subjects
academic sessions
academic terms
student enrollments
teaching assignments
assessments
student scores
attendance
term report comments
result computation
grading
result publication
published report snapshots
subscription management
Flutterwave payment processing
The backend is designed to serve client applications through REST APIs.
The primary planned client is a Flutter mobile application, initially targeting Android.
The backend may also support browser-based administrative interfaces in the future.

2. Product Objectives
The main objective of the system is to provide schools with a centralized and secure platform for managing academic results.
The platform is designed around the following principles.
2.1 Multi-School Support
Multiple schools can register and use the same backend infrastructure.
Each school has its own:
administrators
teachers
students
subjects
classes
academic sessions
terms
grading configuration
report settings
assessments
results
subscriptions
payments
Data belonging to one school must never be exposed to another school.

2.2 Role-Based Access
The platform distinguishes between different types of users.
The current major roles are:
Platform Administrator
School Administrator
Teacher
Student role reserved in the user model
Students are primarily represented as academic records and do not currently require login accounts.

2.3 Subscription-Based SaaS Model
Schools use the platform through term-based subscriptions.
A school must have an active subscription for the relevant academic session and term before performing certain write operations related to academic result processing.
The subscription system is integrated with Flutterwave for online payment processing.

2.4 Result Integrity
Once results are published, important academic data becomes locked.
This protects published results from being changed accidentally.
The system stores published student report snapshots so historical results can remain available even if the underlying academic data changes after results are reopened.

3. System Architecture
The system follows a layered backend architecture.
The major layers are:
Client Applications
        ↓
FastAPI Routes
        ↓
Authentication / Authorization Dependencies
        ↓
Business Services
        ↓
SQLAlchemy ORM
        ↓
PostgreSQL Database

External payment communication follows:
Flutter / Client
        ↓
FastAPI Backend
        ↓
Flutterwave API
        ↓
Payment Verification
        ↓
Subscription Activation
        ↓
PostgreSQL


4. High-Level SaaS Architecture
The platform uses a shared application and shared database architecture with tenant-aware records.
Conceptually:
                       PLATFORM
                           │
               ┌───────────┴───────────┐
               │                       │
          Platform Admin          Platform Admin
               │
       ┌───────┼────────┐
       │       │        │
    School A School B School C
       │       │        │
       │       │        │
   Admins   Admins   Admins
   Teachers Teachers Teachers
   Students Students Students
   Results  Results  Results

Each tenant is represented by a School.
Most school-owned database records contain or derive a school_id.
The authenticated user's school_id determines the tenant context.
The system does not depend on a school identifier supplied by an ordinary client request to determine tenancy.
Instead, protected school-level operations derive the school from:
current_user.school_id

This prevents users from changing a request parameter in an attempt to access another school's data.

5. Technology Stack
5.1 Core Backend Technologies
Technology
Purpose
Python 3.12
Backend programming language
FastAPI 0.141.1
REST API framework
Starlette 1.6.0
ASGI/web foundation used by FastAPI
Uvicorn 0.52.4
ASGI application server
PostgreSQL
Relational database
SQLAlchemy 2.0.52
ORM and database access
Psycopg 3.3.5
PostgreSQL driver
Alembic 1.19.1
Database migrations
Pydantic 2.13.5
Request/response validation
pydantic-settings 2.15.0
Environment-based configuration
PyJWT 2.13.0
JWT token handling
pwdlib 0.3.1
Password hashing abstraction
Argon2
Password hashing algorithm
Pytest 9.1.1
Automated testing
HTTPX 0.28.1
HTTP client support


5.2 Payment Integration
The project integrates with Flutterwave.
Flutterwave is used for:
payment initialization
payment link generation
transaction verification
payment webhook processing
subscription activation
The backend independently verifies payment information before activating a subscription.

5.3 Deployment Support
The project includes:
Dockerfile
.dockerignore
.env.example
Environment-specific configuration is provided through environment variables.
Production secrets must not be committed to source control.

6. Repository Structure
The major repository structure is:
student-result-management-api/
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── app/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── __init__.py
│   └── main.py
│
├── docs/
│
├── scripts/
│
├── tests/
│
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── alembic.ini
├── Dockerfile
├── README.md
└── requirements.txt

The .env file contains local secrets and is excluded from Git.
The .env.example file contains configuration placeholders and may safely be committed.

7. Application Directory
The app/ directory contains the main backend application.
app/
├── api/
├── core/
├── database/
├── models/
├── schemas/
├── services/
└── main.py


8. API Layer
The app/api/ directory contains the application's REST API routers.
Current routers include:
academic_sessions.py
admin_management.py
assessments.py
auth.py
classes.py
enrollments.py
grading_scales.py
payments.py
report_settings.py
report_sheets.py
result_publications.py
results.py
roles.py
schools.py
student_attendance.py
student_scores.py
students.py
subjects.py
subscription_plans.py
subscriptions.py
teachers.py
teaching_assignments.py
term_report_comments.py
term_results.py
terms.py
users.py

The API layer is responsible for:
accepting HTTP requests
validating request parameters
enforcing authentication
enforcing authorization
applying tenant boundaries
invoking business services
interacting with database models
returning validated API responses

9. Models Layer
The app/models/ directory contains SQLAlchemy ORM models.
Current models include:
AcademicSession
Assessment
Class
Enrollment
GradingScale
PaymentTransaction
PublishedReportSnapshot
ReportSettings
ResultPublication
School
Student
StudentAttendance
StudentScore
Subject
Subscription
SubscriptionPlan
Teacher
TeachingAssignment
Term
TermReportComment
User

These models map Python objects to PostgreSQL tables.

10. Schemas Layer
The app/schemas/ directory contains Pydantic models used for:
request validation
response serialization
API contracts
data type enforcement
Schema files exist for the major application resources including:
schools
administrators
teachers
students
classes
subjects
sessions
terms
assessments
scores
attendance
report comments
results
publications
subscriptions
payments

11. Services Layer
The app/services/ directory contains important business logic that should not be duplicated across API routers.
Current service modules include:
flutterwave_service.py
payment_service.py
report_sheet_service.py
result_publication_service.py
result_service.py
subscription_service.py

Their responsibilities include:
flutterwave_service.py
Handles communication with Flutterwave.
payment_service.py
Handles verified payment processing and subscription activation.
report_sheet_service.py
Builds structured student report sheets.
result_publication_service.py
Enforces result publication locks.
result_service.py
Performs student result computation.
subscription_service.py
Checks whether a school has a valid active subscription for a specific academic session and term.

12. Core Layer
The app/core/ directory contains cross-cutting configuration and security components.
Important files include:
config.py
dependencies.py
security.py

12.1 Configuration
config.py manages application configuration through environment variables.
Examples include:
application environment
database URL
JWT configuration
access token expiration
CORS origins
allowed hosts
documentation visibility
Flutterwave credentials

12.2 Security
security.py provides functionality for:
hashing passwords
verifying passwords
generating JWT access tokens
Passwords are never stored directly.

12.3 Dependencies
dependencies.py provides FastAPI dependencies for:
identifying the current authenticated user
checking user activation
checking school activation
enforcing administrator access
enforcing platform administrator access
enforcing school administrator access
enforcing teacher access

13. Database Layer
The app/database/ directory contains database infrastructure.
database/
├── base.py
└── connection.py

connection.py creates the SQLAlchemy engine and session factory.
The database URL is retrieved through centralized application settings.
The request-scoped database dependency opens a SQLAlchemy session and closes it automatically after each request.

14. Database Migration Architecture
Database schema changes are managed through Alembic.
The migrations are stored in:
alembic/versions/

The project currently contains migrations covering:
users
schools
school tenancy
teachers
students
subjects
classes
academic sessions
terms
enrollments
teaching assignments
assessments
student scores
attendance
comments
grading scales
report settings
result publication
report snapshots
subscriptions
payment transactions
The current migration head is:
7b933b5b8b78

At backend freeze, Alembic reports:
Current revision: 7b933b5b8b78
Head revision:    7b933b5b8b78
Schema drift:     None detected


15. Multi-School Tenant Model
The School model is the primary tenant boundary.
A typical school-owned hierarchy can be represented as:
School
 ├── Users
 ├── Teachers
 ├── Students
 ├── Subjects
 ├── Classes
 ├── Academic Sessions
 │    └── Terms
 ├── Grading Scales
 ├── Report Settings
 ├── Subscriptions
 └── Payments

Other academic entities are linked through these records.

16. Tenant Isolation Principle
The most important security rule in the platform is:
A school user must only access data belonging to their own school.
The backend enforces this using the authenticated user.
For example:
Authenticated User
        ↓
current_user.school_id
        ↓
Database query filter
        ↓
Only records belonging to that school

A normal school administrator is not trusted to provide their own school_id.
The tenant ID is determined server-side.

17. Platform Administrator
A platform administrator is represented as:
role = "admin"
school_id = NULL

Platform administrators operate outside a specific tenant.
They can perform platform-wide administrative functions such as managing schools, subscription plans, and school administrators where authorized.
More than one platform administrator may exist.

18. School Administrator
A school administrator is represented as:
role = "admin"
school_id = <school ID>

School administrators operate only inside their assigned school.
Multiple school administrators may exist for one school.
School administrators cannot manage another school's administrators or tenant data.

19. Teacher Account
Teachers use authenticated User accounts.
A teacher user belongs to a school:
role = "teacher"
school_id = <school ID>

The teacher account is associated with a Teacher profile.
Teacher-related permissions remain subject to school tenancy and teaching-assignment rules.

20. Student Architecture
Students are primarily academic records.
The current architecture does not require every student to have an authenticated user account.
This decision separates:
Authentication identity

from:
Academic student record

This allows a school to manage students even when those students do not log into the platform.
The user model still contains a student role for compatibility and possible future use.

21. Core Academic Hierarchy
The academic structure is:
School
   ↓
Academic Session
   ↓
Term

Students are assigned to classes through enrollments.
Subjects are associated with assessments.
Teachers are associated with academic work through teaching assignments.
The resulting workflow is approximately:
School
   ↓
Academic Session
   ↓
Term
   ↓
Class
   ↓
Enrollment
   ↓
Student

Combined with:
Subject
   ↓
Teaching Assignment
   ↓
Assessment
   ↓
Student Score


22. Complete Academic Processing Lifecycle
The principal backend lifecycle is:
School Registration
        ↓
School Administration
        ↓
Academic Session Creation
        ↓
Term Creation
        ↓
Class and Subject Setup
        ↓
Teacher Setup
        ↓
Student Registration
        ↓
Student Enrollment
        ↓
Teaching Assignment
        ↓
Term Subscription
        ↓
Assessment Creation
        ↓
Student Scores
        ↓
Attendance
        ↓
Report Comments
        ↓
Result Computation
        ↓
Publication Readiness Validation
        ↓
Result Publication
        ↓
Published Report Snapshot
        ↓
Historical Report Retrieval


23. Subscription-Aware Academic Workflow
Some academic write operations require an active subscription for the relevant term.
The general pattern is:
School
  ↓
Academic Session
  ↓
Term
  ↓
Subscription
  ↓
Subscription Plan

Before protected academic operations are allowed, the backend verifies:
school_id
+
academic_session_id
+
term_id
+
subscription.status == "active"

This ensures that a subscription for one school, session, or term cannot authorize work for another.

24. Result Publication Architecture
Result publication forms an important data-integrity boundary.
Before publication:
Scores
Attendance
Comments
Assessments
Enrollments

may be modified subject to normal authorization and subscription rules.
After publication:
Published Result
        ↓
Academic source records locked
        ↓
Report snapshot preserved

The system allows an authorized school administrator to reopen published results when corrections are required.
Reopening requires an active subscription.
After corrections, results may be republished.
The existing report snapshot is refreshed.
Therefore, the current design provides:
Immutable while published

rather than permanent multi-version historical snapshots.

25. Payment Architecture
The payment lifecycle is:
School Admin
      ↓
Subscription
      ↓
Initialize Payment
      ↓
Flutterwave Payment Link
      ↓
Customer Payment
      ↓
Flutterwave
      ↓
Verification / Webhook
      ↓
Backend verifies transaction
      ↓
Payment successful
      ↓
Subscription activated

The backend never activates a subscription solely because the client claims that payment succeeded.
Flutterwave transaction information is verified server-side.

26. Security Principles
The backend follows several important security principles.
Authentication
Protected routes require valid JWT authentication.
Authorization
Routes enforce the user's role before granting access.
Tenant Isolation
School-owned data is filtered using the authenticated user's school.
Password Security
Passwords are stored as hashes rather than plain text.
Subscription Enforcement
Term-level academic operations can require an active subscription.
Publication Locking
Published academic data is protected from unauthorized modification.
Payment Verification
Payment data is verified independently with Flutterwave.
Secret Management
Production secrets are supplied through environment variables and are excluded from Git.

27. Automated Test Coverage
The backend contains dedicated tests for:
admin management
assessment subscription enforcement
attendance subscription enforcement
authentication
health endpoints
payment security
published-result locks
report comment subscription enforcement
result publication
student score subscription enforcement
subscription enforcement
tenant isolation

At the backend freeze point:
178 tests passed
0 tests failed
0 errors

This regression suite acts as an important safety net for future backend development and Flutter integration.

28. Backend Freeze State
The backend audit was completed through the following phases:
Phase A  Structural integrity                 PASS
Phase B  Dependencies / deprecations          PASS
Phase C  Authentication / authorization       PASS
Phase D  Multi-school tenant isolation        PASS
Phase E  Subscription / payment integrity     PASS
Phase F  Result publication / data integrity  PASS
Phase G  Production / deployment readiness    PASS
Phase H  Final regression / backend freeze    PASS

The backend freeze commit is:
074f4df

Commit description:
chore: harden production configuration and deployment setup

At this point:
Git working tree: clean
Local main:       synchronized
origin/main:      synchronized
Alembic:          at head
Schema drift:     none
Tests:            178 passed


29. Known Technical Debt
The backend currently uses datetime.utcnow() in several model defaults and application services.
Modern Python versions deprecate this approach in favor of timezone-aware UTC timestamps.
The current PostgreSQL date/time columns are based on naive DateTime values.
Therefore, the timestamps should not be changed individually without considering the underlying database column types.
A future planned migration should evaluate changing timestamp columns to timezone-aware PostgreSQL timestamps and using timezone-aware Python UTC values.
This change was intentionally excluded from the backend freeze because it requires a coordinated schema migration and regression testing rather than a superficial code replacement.

30. Next Documentation Sections
The remaining documentation will expand the architecture above into detailed technical references covering:
database models and relationships
authentication implementation
authorization rules
administrator workflows
school management
academic configuration
teachers and teaching assignments
student registration and enrollment
assessments
scoring
attendance
comments
grading
result computation
report generation
publication and reopening
subscription plans
term subscriptions
Flutterwave payment workflow
every API endpoint
request and response formats
validation rules
error codes
development environment setup
migrations
testing
Docker deployment
production configuration
troubleshooting
Flutter integration

# 31. Database Architecture

The Student Result Management API uses PostgreSQL as its relational database and SQLAlchemy as its Object Relational Mapper.

The data model is designed around five major domains:

```text
Identity & Tenancy
Academic Structure
Academic Records
Result Publication
Subscription & Payments
```

The current ORM contains the following major entities:

```text
User
School
Teacher
Student
Class
Subject
AcademicSession
Term
Enrollment
TeachingAssignment
Assessment
StudentScore
StudentAttendance
TermReportComment
GradingScale
ReportSettings
ResultPublication
PublishedReportSnapshot
SubscriptionPlan
Subscription
PaymentTransaction
```

---

# 32. High-Level Entity Relationship Map

The database can be understood through the following logical relationship map:

```text
                           School
                              │
             ┌────────────────┼────────────────┐
             │                │                │
           Users           Students         Teachers
             │                                  │
             │                                  │
             │                          TeachingAssignments
             │                                  │
             │                    ┌─────────────┼─────────────┐
             │                    │             │             │
             │                 Subject        Class     AcademicSession
             │                                                │
             │                                               Term
             │
             ├─────────────────────────────────────────────────────┐
             │                                                     │
         Subscriptions                                      ReportSettings
             │
      SubscriptionPlan
             │
      PaymentTransactions

Student
   │
   ├── Enrollment ───── Class + AcademicSession
   │
   ├── StudentScore ─── Assessment
   │
   ├── StudentAttendance ─ AcademicSession + Term
   │
   └── TermReportComment ─ AcademicSession + Term

Assessment
   │
   ├── Class
   ├── Subject
   ├── AcademicSession
   └── Term

ResultPublication
   │
   ├── Class
   ├── AcademicSession
   ├── Term
   └── PublishedReportSnapshot
            │
            └── Student
```

---

# 33. Tenant Ownership Strategy

The database does not use a separate database per school.

Instead, tenant isolation is implemented through shared tables and school-aware foreign keys.

Important tenant-owned entities include:

```text
School
User
Teacher
Student
Class
Subject
AcademicSession
GradingScale
ReportSettings
Subscription
PaymentTransaction
```

Many downstream academic records do not store `school_id` directly because their school ownership is derived through parent records.

For example:

```text
StudentScore
    ↓
Assessment
    ↓
Class / Subject / AcademicSession
    ↓
School
```

and:

```text
Enrollment
    ↓
Student + Class + AcademicSession
    ↓
School
```

This means API queries must validate all referenced objects against the authenticated school's tenant boundary.

---

# 34. School Model

Database table:

```text
schools
```

The `School` entity is the root tenant record.

Core fields include:

```text
id
name
slug
email
phone
address
motto
logo_url
is_active
created_at
updated_at
```

The `slug` field is globally unique.

The model supports branding and school identity through:

```text
name
motto
logo_url
```

It also contains administrative contact information.

The `is_active` field allows a school to be disabled without removing its data.

Inactive schools are prevented from using protected application functionality.

---

# 35. User Model

Database table:

```text
users
```

The `User` model represents authenticated identities.

Fields include:

```text
id
email
password_hash
role
is_active
school_id
created_at
updated_at
```

The email address is globally unique.

Supported roles are:

```text
admin
teacher
student
```

The `school_id` field is nullable.

This nullable school relationship creates two distinct administrator types.

## Platform Administrator

```text
role = admin
school_id = NULL
```

## School Administrator

```text
role = admin
school_id = school.id
```

Teachers also use authenticated user accounts.

Students may optionally be associated with a user account, but an account is not mandatory.

The model contains one-to-one relationships with:

```text
Student
Teacher
```

---

# 36. Teacher Model

Database table:

```text
teachers
```

Fields include:

```text
id
user_id
school_id
employee_number
first_name
last_name
created_at
updated_at
```

A Teacher must have a User account.

The user relationship is one-to-one because `user_id` is unique.

Teacher employee numbers are unique within each school rather than globally.

The corresponding uniqueness rule is conceptually:

```text
UNIQUE(school_id, employee_number)
```

This allows different schools to use identical staff numbering systems while preventing duplicates within the same school.

Deleting the associated User cascades to the Teacher record.

---

# 37. Student Model

Database table:

```text
students
```

Fields include:

```text
id
user_id
school_id
admission_number
first_name
last_name
date_of_birth
gender
created_at
```

Unlike Teacher, the Student model allows:

```text
user_id = NULL
```

This is intentional.

A student's academic record therefore exists independently of an authentication account.

Admission numbers are unique per school:

```text
UNIQUE(school_id, admission_number)
```

This permits two schools to use the same admission numbering format without conflict.

If an associated student User account is deleted, the student academic record remains because the foreign key uses:

```text
ON DELETE SET NULL
```

---

# 38. Class Model

Database table:

```text
classes
```

Fields include:

```text
id
school_id
name
code
description
created_at
updated_at
```

Class codes are unique within a school:

```text
UNIQUE(school_id, code)
```

Examples could include:

```text
JSS1A
SS2SCI
GRADE7
```

The actual naming convention is determined by the school.

Classes participate in:

```text
Enrollments
TeachingAssignments
Assessments
ResultPublications
```

---

# 39. Subject Model

Database table:

```text
subjects
```

Fields include:

```text
id
school_id
name
code
description
created_at
updated_at
```

Both subject names and subject codes are unique within the school.

The following constraints therefore exist:

```text
UNIQUE(school_id, name)
UNIQUE(school_id, code)
```

This supports school-specific subject catalogs.

A Subject participates in teaching assignments and assessments.

---

# 40. Academic Session Model

Database table:

```text
academic_sessions
```

Fields include:

```text
id
school_id
name
is_current
created_at
```

Session names are unique per school:

```text
UNIQUE(school_id, name)
```

The system also defines a PostgreSQL partial unique index to guarantee that each school can have only one session marked as current at a time.

Conceptually:

```text
UNIQUE school_id
WHERE is_current = true
```

This protects the current-session state at the database level rather than relying only on application code.

Academic sessions are referenced by:

```text
Terms
Enrollments
TeachingAssignments
Assessments
Attendance
Report Comments
Subscriptions
Result Publications
```

---

# 41. Term Model

Database table:

```text
terms
```

Fields include:

```text
id
academic_session_id
name
closing_date
next_term_resumption_date
created_at
```

A Term belongs to an Academic Session.

The report-related date fields allow generated reports to display:

```text
Closing Date
Next Term Resumption Date
```

The current model itself links tenancy indirectly through:

```text
Term
   ↓
AcademicSession
   ↓
School
```

---

# 42. Enrollment Model

Database table:

```text
enrollments
```

Enrollment connects a student to a class for a particular academic session.

Fields include:

```text
id
student_id
class_id
academic_session_id
created_at
```

The unique constraint is:

```text
UNIQUE(
    student_id,
    class_id,
    academic_session_id
)
```

This prevents the same student from being enrolled more than once in the same class during the same academic session.

Enrollment is central to determining which students belong to a class when computing or publishing results.

---

# 43. Teaching Assignment Model

Database table:

```text
teaching_assignments
```

TeachingAssignment links:

```text
Teacher
Subject
Class
AcademicSession
```

Fields include:

```text
id
teacher_id
subject_id
class_id
academic_session_id
created_at
```

The uniqueness rule is:

```text
UNIQUE(
    teacher_id,
    subject_id,
    class_id,
    academic_session_id
)
```

This prevents duplicate assignment of the exact same teacher/subject/class/session combination.

Teaching assignments form the basis for determining what academic work a teacher is authorized to manage.

---

# 44. Assessment Model

Database table:

```text
assessments
```

Fields include:

```text
id
class_id
subject_id
academic_session_id
term_id
assessment_type
sequence
name
max_score
created_at
updated_at
```

An assessment belongs to a specific:

```text
Class
Subject
Academic Session
Term
```

The assessment also has:

```text
assessment_type
sequence
name
max_score
```

The uniqueness rule is:

```text
UNIQUE(
    class_id,
    subject_id,
    academic_session_id,
    term_id,
    assessment_type,
    sequence
)
```

This prevents duplicate assessment slots within the same class, subject, session, and term.

The backend's current result workflow expects configured assessment components before result publication readiness succeeds.

---

# 45. Student Score Model

Database table:

```text
student_scores
```

Fields include:

```text
id
student_id
assessment_id
score
created_at
updated_at
```

The score column uses:

```text
NUMERIC(5,2)
```

Each student may have only one score for a particular assessment.

This is enforced by:

```text
UNIQUE(student_id, assessment_id)
```

The relationship is:

```text
Student
   ↓
StudentScore
   ↓
Assessment
```

Because Assessment identifies the class, subject, session, and term, StudentScore does not need to duplicate those foreign keys.

---

# 46. Student Attendance Model

Database table:

```text
student_attendance
```

Fields include:

```text
id
student_id
academic_session_id
term_id
school_days
days_present
days_absent
created_at
updated_at
```

The system stores one attendance summary per student per session and term.

The uniqueness constraint is:

```text
UNIQUE(
    student_id,
    academic_session_id,
    term_id
)
```

Attendance is therefore stored as a term summary rather than individual daily attendance events.

---

# 47. Term Report Comment Model

Database table:

```text
term_report_comments
```

Fields include:

```text
id
student_id
academic_session_id
term_id
teacher_comment
principal_comment
created_at
updated_at
```

Each student can have one comment record for each academic session and term.

The database enforces:

```text
UNIQUE(
    student_id,
    academic_session_id,
    term_id
)
```

The record stores both:

```text
teacher_comment
principal_comment
```

Either comment may be null.

---

# 48. Grading Scale Model

Database table:

```text
grading_scales
```

Fields include:

```text
id
school_id
grade
minimum_score
maximum_score
remark
created_at
updated_at
```

Each grading scale belongs directly to a school.

A grade label is unique within a school:

```text
UNIQUE(school_id, grade)
```

Examples of grade labels may include:

```text
A
B
C
D
E
F
```

However, the database does not hard-code a particular grading system.

This allows each school to configure its own score ranges and remarks.

---

# 49. Report Settings Model

Database table:

```text
report_settings
```

Each school may have one report settings record.

This is enforced through:

```text
UNIQUE(school_id)
```

Fields include:

```text
id
school_id
report_title
show_class_position
show_class_size
show_attendance
show_teacher_comment
show_principal_comment
show_school_motto
show_school_logo
show_grading_remarks
principal_designation
created_at
updated_at
```

Default report title:

```text
Student Report Sheet
```

Default principal designation:

```text
Principal
```

These settings allow report presentation to vary by school without changing backend code.

---

# 50. Result Publication Model

Database table:

```text
result_publications
```

Fields include:

```text
id
class_id
academic_session_id
term_id
status
published_by_user_id
published_at
updated_at
```

One publication record is allowed for each:

```text
Class
Academic Session
Term
```

This is enforced through:

```text
UNIQUE(
    class_id,
    academic_session_id,
    term_id
)
```

The publication stores which authenticated user performed the publication through:

```text
published_by_user_id
```

Deletion of the publishing user is restricted because publication history must maintain its audit relationship.

The publication record acts as the lock boundary for published academic results.

---

# 51. Published Report Snapshot Model

Database table:

```text
published_report_snapshots
```

Fields include:

```text
id
publication_id
student_id
report_data
created_at
updated_at
```

`report_data` is stored using PostgreSQL:

```text
JSONB
```

This makes it possible to preserve the fully assembled report representation at the time of publication.

Each student can have one snapshot per result publication:

```text
UNIQUE(
    publication_id,
    student_id
)
```

The relationship is:

```text
ResultPublication
       ↓
PublishedReportSnapshot
       ↓
Student
```

Deletion behavior is deliberate:

```text
Publication deleted
    → snapshot CASCADE delete

Student deletion
    → RESTRICT when referenced by snapshot
```

The latter protects published historical reports from losing their student reference.

---

# 52. Subscription Plan Model

Database table:

```text
subscription_plans
```

Fields include:

```text
id
name
description
price_per_term
max_students
is_active
created_at
updated_at
```

Plan names are globally unique.

The price is stored using:

```text
NUMERIC(12,2)
```

`max_students` may be null.

A null student limit can therefore represent an unlimited plan.

Inactive plans remain stored but should not be available for new subscriptions.

---

# 53. Subscription Model

Database table:

```text
subscriptions
```

Fields include:

```text
id
school_id
subscription_plan_id
academic_session_id
term_id
status
activated_at
expires_at
created_at
updated_at
```

Allowed statuses are:

```text
pending
active
expired
cancelled
```

Only one subscription may exist for a specific school, academic session, and term:

```text
UNIQUE(
    school_id,
    academic_session_id,
    term_id
)
```

This is one of the core business constraints of the SaaS.

A subscription therefore answers:

```text
Which school?
Which academic session?
Which term?
Which plan?
What status?
```

---

# 54. Payment Transaction Model

Database table:

```text
payment_transactions
```

Fields include:

```text
id
school_id
subscription_id
tx_ref
flutterwave_transaction_id
amount
currency
status
payment_provider
payment_link
verified_at
created_at
updated_at
```

The transaction reference:

```text
tx_ref
```

is globally unique.

The Flutterwave transaction ID is also unique when present.

Supported payment transaction statuses are:

```text
pending
successful
failed
```

Default currency:

```text
NGN
```

Default payment provider:

```text
flutterwave
```

The amount uses:

```text
NUMERIC(12,2)
```

Both `school_id` and `subscription_id` use restrictive deletion behavior:

```text
ON DELETE RESTRICT
```

This helps preserve financial transaction history.

---

# 55. Database Uniqueness Constraints

Important uniqueness guarantees include:

| Entity                  | Database Constraint                                  |
| ----------------------- | ---------------------------------------------------- |
| School                  | `slug` globally unique                               |
| User                    | `email` globally unique                              |
| Teacher                 | `school_id + employee_number`                        |
| Student                 | `school_id + admission_number`                       |
| Class                   | `school_id + code`                                   |
| Subject                 | `school_id + name`                                   |
| Subject                 | `school_id + code`                                   |
| Academic Session        | `school_id + name`                                   |
| Current Session         | one current session per school                       |
| Enrollment              | `student + class + session`                          |
| Teaching Assignment     | `teacher + subject + class + session`                |
| Assessment              | `class + subject + session + term + type + sequence` |
| Student Score           | `student + assessment`                               |
| Attendance              | `student + session + term`                           |
| Report Comment          | `student + session + term`                           |
| Grading Scale           | `school + grade`                                     |
| Report Settings         | one record per school                                |
| Result Publication      | `class + session + term`                             |
| Published Snapshot      | `publication + student`                              |
| Subscription Plan       | plan name                                            |
| Subscription            | `school + session + term`                            |
| Payment                 | `tx_ref`                                             |
| Flutterwave Transaction | Flutterwave transaction ID                           |

These constraints protect data integrity even if application-layer validation fails.

---

# 56. Foreign-Key Deletion Strategy

The backend uses a mixture of deletion strategies based on data importance.

## CASCADE

Used when child records should disappear with their parent.

Examples include:

```text
Assessment → related academic objects
Enrollment → Student/Class/Session
TeachingAssignment → Teacher/Subject/Class/Session
Attendance → Student/Session/Term
ReportComment → Student/Session/Term
Subscription → School/Session/Term
```

## SET NULL

Used for optional authentication identity:

```text
Student.user_id
```

Deleting a student User account does not delete the student academic record.

## RESTRICT

Used where historical or financial integrity must be protected.

Examples include:

```text
ResultPublication.published_by_user_id
PublishedReportSnapshot.student_id
PaymentTransaction.school_id
PaymentTransaction.subscription_id
```

This prevents destructive operations from silently removing critical historical relationships.

---

# 57. Result Data Relationship

The core result chain is:

```text
School
  ↓
Class
  ↓
Enrollment
  ↓
Student

School
  ↓
Subject
  ↓
Assessment
  ↓
StudentScore
```

An Assessment additionally identifies:

```text
AcademicSession
Term
```

Therefore a score can be resolved to:

```text
Student
Class
Subject
Academic Session
Term
Assessment Type
Assessment Sequence
Score
Maximum Score
```

This provides the information required for result computation.

---

# 58. Report Data Relationship

A report sheet draws information from multiple sources:

```text
Student
Enrollment
Class
AcademicSession
Term
StudentScores
Assessments
Subjects
GradingScale
StudentAttendance
TermReportComment
School
ReportSettings
```

Once published, the resulting assembled report is preserved in:

```text
PublishedReportSnapshot.report_data
```

This reduces dependence on live mutable records when displaying a published result.

---

# 59. Subscription and Payment Relationship

The commercial model follows:

```text
SubscriptionPlan
       ↓
Subscription
       ↓
PaymentTransaction
```

while Subscription also belongs to:

```text
School
AcademicSession
Term
```

Therefore:

```text
School
  ↓
Subscription
  ├── SubscriptionPlan
  ├── AcademicSession
  └── Term
        ↓
PaymentTransaction
```

A payment does not stand alone.

It is always tied to the subscription that the school intends to activate.

---

# 60. Database Integrity Philosophy

The database design uses both application-level validation and database-level constraints.

Application validation handles business rules such as:

```text
tenant ownership
role permissions
active subscription requirements
publication state
score completeness
payment verification
```

Database constraints protect structural integrity such as:

```text
foreign-key relationships
required fields
unique records
restricted deletion
one-to-one identities
one current session per school
```

Using both layers significantly reduces the risk of inconsistent academic or financial data.

---

# 61. Timestamp Strategy

The current models primarily use:

```python
datetime.utcnow
```

for:

```text
created_at
updated_at
published_at
```

Most corresponding columns use SQLAlchemy:

```text
DateTime
```

without explicit timezone support.

The system therefore currently uses naive UTC timestamps.

This is internally consistent with the existing schema but represents known technical debt.

A future timestamp migration should coordinate:

```text
PostgreSQL timestamp types
SQLAlchemy DateTime(timezone=True)
timezone-aware Python UTC datetimes
existing stored data
regression tests
```

This should be performed as a dedicated schema migration rather than through isolated source-code changes.

---

# 62. Database Design Summary

The database architecture provides:

```text
✓ Multi-school tenant separation
✓ School-scoped identifiers
✓ Optional student authentication
✓ Mandatory teacher authentication
✓ Academic session and term structure
✓ Class enrollment history
✓ Teaching assignment tracking
✓ Flexible assessment structures
✓ Per-assessment student scoring
✓ Term attendance summaries
✓ Teacher and principal comments
✓ School-configurable grading
✓ School-configurable report formatting
✓ Result publication tracking
✓ Published JSON report snapshots
✓ Term-based SaaS subscriptions
✓ Payment transaction auditing
✓ Database-enforced uniqueness
✓ Referential integrity
```

This database structure forms the foundation for both the current REST API and the planned Flutter mobile application.
# 63. Authentication Architecture

The Student Result Management API uses stateless JWT authentication.

The authentication lifecycle is:

```text
User submits email + password
        ↓
Backend looks up User by email
        ↓
Account activation checked
        ↓
Password hash verified
        ↓
School status checked if school-bound
        ↓
JWT access token generated
        ↓
Client stores token
        ↓
Bearer token sent with protected requests
```

The authentication endpoint is:

```text
POST /api/auth/login
```

The login endpoint is intentionally public because users need access to it before obtaining an authentication token.

---

# 64. Password Security

Passwords are never stored in plain text.

Password handling is provided through:

```python
PasswordHash.recommended()
```

The backend exposes internal helper functions conceptually equivalent to:

```text
hash_password(password)
verify_password(password, hashed_password)
```

The password hashing implementation is delegated to the recommended `pwdlib` password hashing configuration.

The User model stores only:

```text
password_hash
```

and never stores the original password.

---

# 65. JWT Access Tokens

JWT access tokens are generated after successful authentication.

The token contains:

```text
sub
role
exp
```

Where:

```text
sub  = User ID
role = current database role
exp  = token expiration
```

The JWT is signed using:

```text
HS256
```

The token expiration timestamp is generated using timezone-aware UTC time.

Conceptually:

```text
expiration =
current UTC time
+
configured access token lifetime
```

The signing secret and token lifetime are supplied through application configuration rather than hard-coded into source files.

---

# 66. Login Validation Flow

When a user attempts to log in, the backend performs the following sequence.

## Step 1: User lookup

The User is retrieved using the supplied email address.

If the user does not exist:

```text
401 Unauthorized
Invalid email or password
```

Using the same error for an incorrect email and incorrect password avoids exposing whether a particular email address exists.

---

## Step 2: User activation check

If:

```text
user.is_active == False
```

authentication is denied with:

```text
403 Forbidden
User account is inactive
```

---

## Step 3: Password verification

The submitted password is verified against:

```text
user.password_hash
```

An invalid password returns:

```text
401 Unauthorized
Invalid email or password
```

---

## Step 4: School validation

If:

```text
user.school_id != NULL
```

the backend loads the associated School.

If the school no longer exists:

```text
403 Forbidden
School account is unavailable
```

If the school exists but is inactive:

```text
403 Forbidden
School account is inactive
```

Platform administrators bypass this school check because:

```text
school_id = NULL
```

---

## Step 5: Token creation

After all checks pass, a JWT access token is returned.

The API response includes:

```text
access_token
token_type = bearer
```

---

# 67. Protected Request Authentication

Protected routes use FastAPI's HTTP Bearer authentication mechanism.

The client sends:

```http
Authorization: Bearer <access_token>
```

The backend extracts the token and decodes it using:

```text
configured JWT secret
configured JWT algorithm
```

The JWT's `sub` claim is treated as the User ID.

---

# 68. Token Validation

The current-user dependency performs several validation steps.

## Token signature

The token must be correctly signed.

Invalid tokens return:

```text
401 Unauthorized
Invalid authentication token
```

## Token expiration

Expired tokens return:

```text
401 Unauthorized
Authentication token has expired
```

## Subject claim

The token must contain a valid:

```text
sub
```

claim.

The subject must also be convertible to an integer User ID.

Invalid subjects return:

```text
401 Unauthorized
Invalid authentication token
```

---

# 69. Database User Reload

The backend does not rely exclusively on the JWT contents.

After decoding the token, it retrieves the User again from PostgreSQL:

```text
JWT
 ↓
sub
 ↓
User ID
 ↓
Database lookup
```

This is an important security design.

It means account state changes can take effect immediately even if an old JWT remains technically valid.

For example, if an administrator deactivates a User:

```text
JWT still exists
       ↓
request received
       ↓
User reloaded from database
       ↓
is_active = false
       ↓
request rejected
```

Therefore, the system does not need to wait for token expiration before enforcing account deactivation.

---

# 70. School Activation Enforcement

For every authenticated school-bound account:

```text
user.school_id != NULL
```

the current-user dependency also checks the School.

The effective security chain is:

```text
Valid JWT
   ↓
Valid User
   ↓
Active User
   ↓
Valid School
   ↓
Active School
   ↓
Request may continue
```

This means deactivating a school effectively blocks authenticated access for all users assigned to that tenant.

Platform administrators remain unaffected because they do not belong to a school.

---

# 71. Authorization Dependencies

The backend defines several reusable authorization dependencies.

They are:

```text
get_current_user
require_admin
require_platform_admin
require_school_admin
require_teacher
require_student
```

These dependencies form a role hierarchy.

---

# 72. Generic Authentication

```text
get_current_user
```

means:

> Any active authenticated User whose school is valid and active, if school-bound.

This is used where authentication is required but a specific role is not.

---

# 73. Administrator Authorization

```text
require_admin
```

permits:

```text
Platform Administrator
School Administrator
```

The requirement is:

```text
current_user.role == "admin"
```

Non-admin users receive:

```text
403 Forbidden
Admin access required
```

---

# 74. Platform Administrator Authorization

A platform administrator must satisfy:

```text
role = "admin"
school_id = NULL
```

The dependency chain is:

```text
get_current_user
      ↓
require_admin
      ↓
require_platform_admin
```

If an admin account has a school assigned, it is considered a school administrator and cannot pass this dependency.

Failure returns:

```text
403 Forbidden
Platform admin access required
```

---

# 75. School Administrator Authorization

A school administrator must satisfy:

```text
role = "admin"
school_id != NULL
```

The dependency chain is:

```text
get_current_user
      ↓
require_admin
      ↓
require_school_admin
```

Platform administrators therefore do not automatically pass endpoints explicitly intended for a school's own administrator.

Failure returns:

```text
403 Forbidden
School admin access required
```

---

# 76. Teacher Authorization

A teacher must satisfy:

```text
role = "teacher"
school_id != NULL
```

Failure cases include:

```text
403 Teacher access required
```

or:

```text
403 Teacher is not assigned to a school
```

The school activation validation has already occurred before this dependency returns successfully.

---

# 77. Student Authorization

A legacy/reserved student-user authorization dependency also exists.

It requires:

```text
role = "student"
school_id != NULL
```

However, the current product design does not require Student academic records to have User accounts.

Therefore, this dependency should be regarded as available infrastructure for potential future authenticated student access rather than a requirement of the present academic workflow.

---

# 78. Account Type Resolution

The `/api/users/me` endpoint allows the client to inspect the authenticated account.

Endpoint:

```text
GET /api/users/me
```

The response includes:

```text
id
email
role
account_type
school_id
is_active
```

For administrators, `account_type` is derived from tenancy.

```text
role = admin + school_id = NULL
        ↓
platform_admin
```

```text
role = admin + school_id != NULL
        ↓
school_admin
```

For other roles:

```text
account_type = role
```

This endpoint is useful to a mobile application after login because the client can determine what interface and permissions to present.

---

# 79. Role and Tenant Model

The system does not define separate database roles for:

```text
platform_admin
school_admin
```

Instead, both use:

```text
role = "admin"
```

The distinction is determined by `school_id`.

The effective authorization matrix is:

| Account                | Role      | school_id |
| ---------------------- | --------- | --------- |
| Platform Administrator | `admin`   | `NULL`    |
| School Administrator   | `admin`   | school ID |
| Teacher                | `teacher` | school ID |
| Student User           | `student` | school ID |

This keeps the underlying User role enum relatively simple while supporting different administrator scopes.

---

# 80. Multiple Administrator Support

The backend supports multiple administrators.

A platform may contain multiple platform administrators.

A school may contain multiple school administrators.

This is necessary for operational resilience because administrative access does not depend on one individual account.

---

# 81. Platform Administrator Creation

Endpoint:

```text
POST /api/admin-management/platform-admins
```

Authorization:

```text
Platform Administrator only
```

The new account is created with:

```text
role = admin
school_id = NULL
is_active = true
```

Before creation, the email address is:

```text
trimmed
converted to lowercase
```

The backend rejects duplicate emails.

Duplicate accounts return:

```text
409 Conflict
A user with this email already exists
```

Database `IntegrityError` exceptions are also handled so that race conditions still result in a controlled conflict response.

---

# 82. Listing Platform Administrators

Endpoint:

```text
GET /api/admin-management/platform-admins
```

Authorization:

```text
Platform Administrator only
```

The query selects:

```text
role = admin
school_id IS NULL
```

Results are ordered by creation time.

---

# 83. School Administrator Creation

Endpoint:

```text
POST /api/admin-management/school-admins
```

This operation may be performed by:

```text
Platform Administrator
School Administrator
```

However, the permitted school scope differs.

---

# 84. Platform Admin Creating School Admin

Because a platform administrator does not belong to a tenant, the platform administrator must explicitly supply:

```text
school_id
```

If omitted:

```text
400 Bad Request
school_id is required when a platform admin creates a school admin
```

The selected school must exist and be active.

---

# 85. School Admin Creating Another School Admin

A school administrator does not choose their tenant context.

The backend derives it from:

```text
current_user.school_id
```

Therefore:

```text
target_school_id = current_user.school_id
```

If the request attempts to specify a different school:

```text
403 Forbidden
You cannot create an administrator for another school
```

This is an important tenant-security control.

---

# 86. Inactive-School Admin Creation Protection

Before creating a school administrator, the backend checks the selected School.

If it does not exist:

```text
404 Not Found
School not found
```

If inactive:

```text
409 Conflict
Cannot create an admin for an inactive school
```

This prevents adding new operational accounts to a disabled tenant.

---

# 87. Listing School Administrators

Endpoint:

```text
GET /api/admin-management/school-admins
```

The endpoint supports two security scopes.

## Platform administrator

A platform administrator can:

```text
view administrators from all schools
```

or optionally filter by:

```text
school_id
```

## School administrator

A school administrator can view only:

```text
administrators belonging to current_user.school_id
```

Attempting to filter for another tenant returns:

```text
403 Forbidden
You cannot view administrators from another school
```

---

# 88. Administrator Activation and Deactivation

Administrator accounts can be activated or deactivated without deleting them.

This preserves identity and historical relationships while allowing operational access to be withdrawn.

Two endpoints are provided:

```text
PATCH /api/admin-management/platform-admins/{admin_id}/status
```

and:

```text
PATCH /api/admin-management/school-admins/{admin_id}/status
```

---

# 89. Platform Administrator Deactivation Safety

Only a platform administrator can change another platform administrator's status.

Two important protections exist.

## Self-deactivation prevention

A currently authenticated platform administrator cannot deactivate their own account.

The API returns:

```text
409 Conflict
You cannot deactivate your own platform administrator account
```

## Last administrator protection

The backend counts active platform administrators.

If only one remains, deactivation is rejected:

```text
409 Conflict
The last active platform administrator cannot be deactivated
```

This prevents the platform from losing all administrative access.

---

# 90. School Administrator Deactivation Safety

School-admin status management is similarly protected.

A school administrator may manage only administrators belonging to the same tenant.

Attempting to manage another school's administrator returns:

```text
403 Forbidden
You cannot manage an administrator from another school
```

A school administrator also cannot deactivate their own currently authenticated account.

---

# 91. Last School Administrator Protection

Before deactivating an active school administrator, the backend counts active administrators in that school.

Conceptually:

```text
COUNT users
WHERE
    role = admin
    AND school_id = target school
    AND is_active = true
```

If the count is one or fewer, deactivation is blocked.

Response:

```text
409 Conflict
The last active administrator for this school cannot be deactivated
```

This ensures every active tenant retains at least one usable administrator account.

---

# 92. School Registration

School registration is intentionally a public SaaS onboarding endpoint.

Endpoint:

```text
POST /api/schools/register
```

It creates two records inside one database transaction:

```text
School
+
Initial School Administrator
```

The resulting structure is:

```text
New School
    ↓
Initial User
role = admin
school_id = new School ID
```

---

# 93. School Registration Normalization

Before registration, the backend normalizes several values.

The school slug is:

```text
trimmed
lowercased
```

The initial administrator email is:

```text
trimmed
lowercased
```

The optional school email is also normalized.

Other optional text values such as:

```text
phone
address
motto
```

are trimmed when provided.

---

# 94. School Registration Duplicate Protection

Before creating records, the backend checks:

```text
School.slug
```

and:

```text
User.email
```

Existing school slug:

```text
409 Conflict
A school with this slug already exists
```

Existing administrator email:

```text
409 Conflict
A user with this email already exists
```

The database transaction additionally catches `IntegrityError`, providing protection against concurrent duplicate registrations.

---

# 95. Atomic School Registration

School registration uses an atomic transaction.

Conceptually:

```text
BEGIN

Create School
     ↓
FLUSH
     ↓
obtain school.id
     ↓
Create initial admin with school.id
     ↓
FLUSH
     ↓
obtain admin.id
     ↓
COMMIT
```

If any operation fails:

```text
ROLLBACK
```

This prevents partially registered tenants such as:

```text
School without administrator
```

or inconsistent account creation.

---

# 96. Initial School Administrator

The initial account created during school registration has:

```text
role = admin
is_active = true
school_id = newly created School ID
```

The password is hashed before insertion.

The registration response returns:

```text
school_id
school_name
school_slug
school_email
admin_user_id
admin_email
role
message
```

---

# 97. School Self-Service Profile

School administrators can retrieve their own School using:

```text
GET /api/schools/me
```

Authorization:

```text
School Administrator only
```

The lookup is:

```text
School.id == current_user.school_id
```

No arbitrary school identifier is accepted.

This is a strong tenant-security pattern.

---

# 98. School Profile Update

Endpoint:

```text
PATCH /api/schools/me
```

Authorization:

```text
School Administrator only
```

Again, the School is selected using:

```text
current_user.school_id
```

rather than a request-controlled school ID.

Only fields actually supplied in the PATCH request are updated.

String values are trimmed before assignment.

---

# 99. Tenant Trust Boundary

One of the central security principles of the application is:

> Tenant identity is determined by authenticated server-side context, not by ordinary client input.

The safe pattern is:

```text
JWT
 ↓
Authenticated User
 ↓
current_user.school_id
 ↓
Tenant-scoped query
```

The unsafe pattern would be:

```text
Client sends school_id
 ↓
Backend trusts school_id
```

The backend intentionally avoids this pattern for normal school-admin operations.

---

# 100. Cross-Tenant Access Prevention

A school administrator cannot use administrator-management endpoints to:

```text
create an admin for another school
view another school's administrators
change another school's administrator status
```

The backend explicitly compares requested or target school ownership with:

```text
current_user.school_id
```

before permitting these operations.

---

# 101. Platform Scope vs Tenant Scope

The authorization system distinguishes two scopes.

## Platform Scope

```text
role = admin
school_id = NULL
```

Typical responsibilities:

```text
platform administration
platform administrator management
cross-school administrator management
subscription-plan administration
platform-level operations
```

## Tenant Scope

```text
school_id != NULL
```

Typical responsibilities:

```text
school profile
students
teachers
academic configuration
assessment data
results
subscriptions
payments
```

Tenant-scoped actors must remain inside their own School boundary.

---

# 102. Authentication and Authorization Flow

The complete protected-request flow is:

```text
Client Request
     ↓
Authorization: Bearer JWT
     ↓
JWT Decode
     ↓
Signature Valid?
     ├── No → 401
     ↓ Yes
Token Expired?
     ├── Yes → 401
     ↓ No
Valid sub?
     ├── No → 401
     ↓ Yes
Reload User
     ├── Missing → 401
     ↓
User Active?
     ├── No → 403
     ↓
School-bound?
     ├── No → Platform context
     ↓ Yes
School Exists?
     ├── No → 403
     ↓
School Active?
     ├── No → 403
     ↓
Role Dependency
     ↓
Tenant Validation
     ↓
Business Logic
```

---

# 103. HTTP Security Semantics

The backend makes an important distinction between:

```text
401 Unauthorized
```

and:

```text
403 Forbidden
```

## 401

Used when authentication itself is invalid.

Examples:

```text
invalid credentials
invalid token
expired token
invalid token subject
user no longer exists
```

## 403

Used when identity is valid but access is not allowed.

Examples:

```text
inactive user
inactive school
wrong role
wrong administrator type
cross-tenant access attempt
teacher not assigned to school
```

This provides consistent API semantics for mobile clients.

---

# 104. Conflict Responses

The API uses:

```text
409 Conflict
```

for state conflicts rather than authentication failures.

Examples include:

```text
duplicate user email
duplicate school slug
inactive-school admin creation
self-deactivation attempt
last-admin deactivation attempt
```

This helps clients distinguish invalid application state from permission failure.

---

# 105. Authentication Security Strengths

The finalized backend authentication architecture provides:

```text
✓ Password hashing
✓ No plain-text password storage
✓ JWT expiration
✓ Signed JWT tokens
✓ Database user reload per request
✓ Immediate account deactivation enforcement
✓ School activation enforcement
✓ Explicit role dependencies
✓ Platform/tenant administrator separation
✓ Server-derived tenant identity
✓ Cross-school administrator protections
✓ Self-deactivation protection
✓ Last-active-admin protection
✓ Atomic tenant registration
✓ Duplicate account protection
```

---

# 106. Client Integration Guidance

After login, the Flutter application should call:

```text
GET /api/users/me
```

This lets the application determine:

```text
role
account_type
school_id
is_active
```

The client can then route users to an appropriate interface.

Conceptually:

```text
Login
  ↓
Receive JWT
  ↓
GET /api/users/me
  ↓
account_type
  ├── platform_admin → Platform interface
  ├── school_admin   → School admin interface
  ├── teacher        → Teacher interface
  └── student        → Future student interface
```

The client should never use interface visibility as the actual security mechanism.

Even if a Flutter screen hides a button, the backend remains responsible for authorizing every request.

---

# 107. Security Principle for Mobile Development

The Flutter application must treat the backend as the authority for:

```text
identity
role
tenant
subscription status
publication state
academic ownership
payment state
```

The mobile client must not independently decide that a user is authorized based only on locally stored information.

Every sensitive operation must be validated again by the backend.

---

# 108. Public Endpoints

Within the reviewed authentication and school modules, the intentionally public endpoints are:

```text
POST /api/auth/login
POST /api/schools/register
```

These routes do not require a JWT by design.

School registration therefore represents a public SaaS onboarding surface.

Production environments may later add additional anti-abuse controls such as:

```text
rate limiting
email verification
CAPTCHA
registration monitoring
```

These would be production hardening enhancements rather than corrections to the current authorization model.

---

# 109. Security Design Summary

The system uses a layered approach:

```text
Authentication
     ↓
Account Activation
     ↓
School Activation
     ↓
Role Authorization
     ↓
Tenant Isolation
     ↓
Business Rules
     ↓
Database Constraints
```

No single layer is expected to protect the entire application.

Together these controls form the security boundary of the multi-school SaaS backend.
# 110. Academic Configuration Architecture

The academic configuration layer defines the structural data a school must create before entering assessments and student results.

The major components are:

```text
Academic Session
      ↓
Term

School
 ├── Classes
 ├── Subjects
 ├── Teachers
 └── Students

Teacher
   ↓
Teaching Assignment
   ↓
Subject + Class + Academic Session

Student
   ↓
Enrollment
   ↓
Class + Academic Session
```

The backend applies strict tenant isolation to each of these resources.

---

# 111. Academic Session API

Base route:

```text
/api/academic-sessions
```

Academic sessions organize school activity into periods such as:

```text
2025/2026
2026/2027
```

Each session belongs to exactly one school.

---

# 112. Create Academic Session

Endpoint:

```http
POST /api/academic-sessions
```

Authorization:

```text
School Administrator
```

The backend automatically assigns:

```text
school_id = current_user.school_id
```

The client does not determine the tenant.

The backend checks whether another session with the same name already exists for the current school.

Duplicate session names return:

```text
409 Conflict
Academic session with this name already exists in this school
```

---

# 113. Current Academic Session

An academic session may be marked:

```text
is_current = true
```

When a new or existing session is marked as current, the application first clears the current flag from other sessions belonging to the same school.

Conceptually:

```text
School
  │
  ├── 2025/2026  is_current = false
  └── 2026/2027  is_current = true
```

The database also contains a partial unique index enforcing one current session per school.

This creates two layers of protection:

```text
Application logic
+
Database constraint
```

---

# 114. List Academic Sessions

Endpoint:

```http
GET /api/academic-sessions
```

Authorization:

```text
Any authenticated school-bound user
```

The requesting user must have a non-null `school_id`.

Only sessions belonging to:

```text
current_user.school_id
```

are returned.

Sessions are ordered by name in descending order.

---

# 115. Get Academic Session

Endpoint:

```http
GET /api/academic-sessions/{session_id}
```

The lookup combines:

```text
session ID
+
current_user.school_id
```

Therefore, an ID belonging to another tenant is not returned.

Instead, the client receives:

```text
404 Not Found
Academic session not found
```

This avoids exposing whether another school's resource exists.

---

# 116. Update Academic Session

Endpoint:

```http
PUT /api/academic-sessions/{session_id}
```

Authorization:

```text
School Administrator
```

The administrator may update:

```text
name
is_current
```

Session-name uniqueness remains scoped to the current school.

If `is_current` becomes true, other current sessions for the school are unset.

---

# 117. Delete Academic Session

Endpoint:

```http
DELETE /api/academic-sessions/{session_id}
```

Authorization:

```text
School Administrator
```

The session cannot be deleted once dependent academic or commercial records exist.

The backend checks for:

```text
Teaching Assignments
Terms
Enrollments
Assessments
Attendance
Report Comments
Subscriptions
Result Publications
```

If any of these records exist:

```text
409 Conflict
Academic session cannot be deleted because it already has
academic records or related data.
```

This intentionally favors historical integrity over cascading deletion.

---

# 118. Term API

Base route:

```text
/api/terms
```

A Term always belongs to an Academic Session.

The tenant relationship is indirect:

```text
Term
  ↓
AcademicSession
  ↓
School
```

Therefore, term queries join AcademicSession when validating school ownership.

---

# 119. Create Term

Endpoint:

```http
POST /api/terms
```

Authorization:

```text
School Administrator
```

Before creating a term, the backend verifies that the supplied academic session belongs to:

```text
current_user.school_id
```

If it does not:

```text
404 Not Found
Academic session not found
```

This prevents attaching a term to another tenant's session.

---

# 120. Term Uniqueness

A term name must be unique inside its academic session.

For example:

```text
2026/2027
 ├── First Term
 ├── Second Term
 └── Third Term
```

A duplicate term returns:

```text
409 Conflict
Term already exists for this academic session
```

The backend also catches database `IntegrityError` to preserve the same behavior under concurrent requests.

---

# 121. Term Report Dates

Terms may store:

```text
closing_date
next_term_resumption_date
```

These values support report-sheet presentation.

They may be updated independently using the term update endpoint.

---

# 122. List Terms

Endpoint:

```http
GET /api/terms
```

Authorization:

```text
School Administrator
```

The query joins Terms to Academic Sessions and returns only terms whose session belongs to the current school.

---

# 123. Get Term

Endpoint:

```http
GET /api/terms/{term_id}
```

The backend resolves the term through its Academic Session and verifies school ownership.

A term from another school is effectively invisible to the requester.

---

# 124. Update Term

Endpoint:

```http
PATCH /api/terms/{term_id}
```

The following values may be changed:

```text
name
closing_date
next_term_resumption_date
```

If the name changes, uniqueness is rechecked within the same Academic Session.

---

# 125. Delete Term

Endpoint:

```http
DELETE /api/terms/{term_id}
```

Deletion is rejected if related records exist.

The backend checks:

```text
Assessments
Attendance
Report Comments
Subscriptions
Result Publications
```

If any are present:

```text
409 Conflict
Term cannot be deleted because it already has
academic records or related data.
```

---

# 126. Class API

Base route:

```text
/api/classes
```

Classes belong directly to a School.

Examples may include:

```text
JSS 1
JSS 2
SSS 1 Science
SSS 2 Commercial
```

The naming convention is controlled by the tenant.

---

# 127. Create Class

Endpoint:

```http
POST /api/classes
```

Authorization:

```text
School Administrator
```

Tenant assignment is automatic:

```text
school_id = current_user.school_id
```

The class code must be unique within that school.

Duplicate codes return:

```text
409 Conflict
Class with this code already exists in this school
```

---

# 128. List Classes

Endpoint:

```http
GET /api/classes
```

Authorization:

```text
Any authenticated school-bound user
```

Only classes belonging to the requesting user's school are returned.

The response is ordered by class name.

---

# 129. Get Class

Endpoint:

```http
GET /api/classes/{class_id}
```

The query requires both:

```text
Class.id = requested ID
Class.school_id = current_user.school_id
```

Cross-tenant class IDs therefore produce a `404`.

---

# 130. Update Class

Endpoint:

```http
PUT /api/classes/{class_id}
```

Authorization:

```text
School Administrator
```

The administrator may update:

```text
code
name
description
```

If the code changes, uniqueness is checked within the current school.

---

# 131. Delete Class

Endpoint:

```http
DELETE /api/classes/{class_id}
```

A class cannot be deleted once important dependent records exist.

The backend checks:

```text
Teaching Assignments
Enrollments
Assessments
Result Publications
```

If related data exists:

```text
409 Conflict
Class cannot be deleted because it already has
academic records or related assignments.
```

---

# 132. Subject API

Base route:

```text
/api/subjects
```

Subjects belong directly to a School.

A tenant may create subjects such as:

```text
Mathematics
English Language
Physics
Chemistry
Biology
```

---

# 133. Create Subject

Endpoint:

```http
POST /api/subjects
```

Authorization:

```text
School Administrator
```

The backend requires both subject name and code to be unique within the current school.

A conflict returns:

```text
409 Conflict
Subject with this name or code already exists in this school
```

---

# 134. List Subjects

Endpoint:

```http
GET /api/subjects
```

Authorization:

```text
Any authenticated school-bound user
```

Only subjects belonging to the current tenant are returned.

---

# 135. Get Subject

Endpoint:

```http
GET /api/subjects/{subject_id}
```

The Subject ID is always combined with:

```text
current_user.school_id
```

before the record is returned.

---

# 136. Update Subject

Endpoint:

```http
PUT /api/subjects/{subject_id}
```

Authorization:

```text
School Administrator
```

The administrator may update:

```text
name
code
description
```

Both name and code are checked separately for school-scoped uniqueness.

---

# 137. Delete Subject

Endpoint:

```http
DELETE /api/subjects/{subject_id}
```

Deletion is prohibited if the subject is referenced by:

```text
Teaching Assignments
Assessments
```

Conflict response:

```text
409 Conflict
Subject cannot be deleted because it already has
academic records or teaching assignments.
```

---

# 138. Teacher API

Base route:

```text
/api/teachers
```

Teacher creation is different from Student creation because every Teacher receives an authenticated User account.

The creation workflow is:

```text
Teacher Request
      ↓
Validate email
      ↓
Validate employee number
      ↓
Create User
role = teacher
      ↓
Create Teacher profile
      ↓
Commit
```

---

# 139. Create Teacher

Endpoint:

```http
POST /api/teachers
```

Authorization:

```text
School Administrator
```

The backend first checks global User email uniqueness.

If the email already exists:

```text
409 Conflict
User with this email already exists
```

---

# 140. Teacher Employee Number

The employee number is unique within the school.

The backend checks:

```text
Teacher.employee_number
+
Teacher.school_id = current_user.school_id
```

This allows two independent schools to use the same employee number without conflict.

---

# 141. Teacher User Creation

The backend creates:

```text
User
 role = teacher
 is_active = true
 school_id = current_user.school_id
```

The Teacher's password is hashed before storage.

The newly created User ID becomes:

```text
Teacher.user_id
```

The User is flushed before the Teacher is created so its ID is available.

---

# 142. Teacher Profile Creation

The Teacher profile contains:

```text
user_id
school_id
employee_number
first_name
last_name
```

Therefore:

```text
User
 ↓ one-to-one
Teacher
```

The Teacher account and profile belong to the same tenant.

---

# 143. List Teachers

Endpoint:

```http
GET /api/teachers
```

Authorization:

```text
Any authenticated school-bound user
```

Only Teachers belonging to:

```text
current_user.school_id
```

are returned.

Teachers are ordered by:

```text
last_name
first_name
```

---

# 144. Get Teacher

Endpoint:

```http
GET /api/teachers/{teacher_id}
```

A Teacher can be retrieved only if:

```text
Teacher.id = teacher_id
AND
Teacher.school_id = current_user.school_id
```

---

# 145. Update Teacher

Endpoint:

```http
PUT /api/teachers/{teacher_id}
```

Authorization:

```text
School Administrator
```

The backend loads both:

```text
Teacher
Associated User
```

and verifies that both belong to the current school.

Supported modifications include:

```text
email
employee_number
first_name
last_name
is_active
```

---

# 146. Teacher Account Activation

Teacher activation is stored on the associated User:

```text
User.is_active
```

Therefore:

```text
TeacherUpdate.is_active
      ↓
User.is_active
```

A deactivated Teacher cannot authenticate because the global current-user dependency rejects inactive User accounts.

---

# 147. Delete Teacher

Endpoint:

```http
DELETE /api/teachers/{teacher_id}
```

Before deletion, the backend checks Teaching Assignments.

If assignments exist:

```text
409 Conflict
Teacher cannot be deleted because they have teaching assignments.
Deactivate the teacher instead.
```

This deliberately encourages deactivation rather than deleting teachers whose academic history is already in use.

---

# 148. Teacher and User Deletion Sequence

If no teaching assignments exist, both the Teacher profile and User account are removed.

The backend deletes:

```text
Teacher
   ↓
flush
   ↓
User
   ↓
commit
```

The Teacher is deleted first because `Teacher.user_id` is non-nullable.

---

# 149. Student API

Base route:

```text
/api/students
```

Student handling intentionally differs from teacher handling.

Creating a Student does not create a User account.

Current student architecture:

```text
Student
 user_id = NULL
 school_id = current_user.school_id
```

This allows schools to manage academic records without requiring every student to authenticate.

---

# 150. Create Student

Endpoint:

```http
POST /api/students
```

Authorization:

```text
School Administrator
```

Before creation, the backend verifies admission-number uniqueness within the school.

Conflict:

```text
409 Conflict
A student with this admission number already exists in this school
```

The resulting Student is explicitly created with:

```text
user_id = None
```

---

# 151. Student Fields

The current Student creation workflow stores:

```text
admission_number
first_name
last_name
date_of_birth
gender
```

Tenant ownership comes exclusively from:

```text
current_user.school_id
```

---

# 152. List Students

Endpoint:

```http
GET /api/students
```

Authorization:

```text
School Administrator
```

Only the current school's students are returned.

Students are ordered by:

```text
last_name
first_name
```

---

# 153. Get Student

Endpoint:

```http
GET /api/students/{student_id}
```

The backend requires:

```text
Student.id = student_id
AND
Student.school_id = current_user.school_id
```

This prevents enumeration of students across tenants.

---

# 154. Update Student

Endpoint:

```http
PATCH /api/students/{student_id}
```

Authorization:

```text
School Administrator
```

Fields that may be updated include:

```text
admission_number
first_name
last_name
date_of_birth
gender
```

If the admission number changes, uniqueness is rechecked within the current school.

---

# 155. Delete Student

Endpoint:

```http
DELETE /api/students/{student_id}
```

The backend first checks whether the student has Enrollments.

If enrollments exist:

```text
409 Conflict
Student cannot be deleted because they have enrollments.
Delete the enrollments first.
```

Even after the explicit Enrollment check, database `IntegrityError` is caught in case other related records still prevent deletion.

That fallback returns:

```text
409 Conflict
Student could not be deleted because related records exist
```

---

# 156. Enrollment API

Base route:

```text
/api/enrollments
```

Enrollment connects:

```text
Student
+
Class
+
Academic Session
```

It records where a student belongs for a specific academic session.

---

# 157. Enrollment Tenant Validation

Before creating an Enrollment, the backend independently verifies all three parent records.

It verifies:

```text
Student.school_id == current_user.school_id
Class.school_id == current_user.school_id
AcademicSession.school_id == current_user.school_id
```

This is stronger than validating only one parent object.

It prevents building cross-tenant composite records.

---

# 158. Create Enrollment

Endpoint:

```http
POST /api/enrollments
```

Authorization:

```text
School Administrator
```

Before creating the Enrollment, the backend validates that class/session results are not currently published.

The publication-lock service is invoked using:

```text
class_id
academic_session_id
```

This ensures enrollment membership cannot be changed while relevant results are published.

---

# 159. Enrollment Duplicate Protection

The backend rejects duplicate combinations of:

```text
student_id
class_id
academic_session_id
```

Conflict:

```text
409 Conflict
Student is already enrolled in this class
for this academic session
```

Database `IntegrityError` is also handled in case concurrent requests bypass the pre-check.

---

# 160. List Enrollments

Endpoint:

```http
GET /api/enrollments
```

Authorization:

```text
School Administrator
```

The query joins:

```text
Enrollment
Student
Class
AcademicSession
```

and requires all three parent resources to belong to the current school.

This provides a robust tenant-boundary check.

---

# 161. Get Enrollment

Endpoint:

```http
GET /api/enrollments/{enrollment_id}
```

An Enrollment is returned only when:

```text
Student.school_id == current_user.school_id
Class.school_id == current_user.school_id
AcademicSession.school_id == current_user.school_id
```

Otherwise, the record is treated as not found.

---

# 162. Update Enrollment

Endpoint:

```http
PATCH /api/enrollments/{enrollment_id}
```

The current backend permits updates to:

```text
class_id
academic_session_id
```

The Student itself remains associated with the Enrollment.

Before modification, the original class/session is checked for publication locks.

---

# 163. Enrollment Destination Validation

If the Class changes, the new Class must belong to the current school.

If the Academic Session changes, the new Academic Session must belong to the current school.

If either the class or session changes, the destination class/session is also checked to ensure results there are not published.

Conceptually:

```text
Old Enrollment
      ↓
Old class/session unpublished?
      ↓
Validate destination tenant ownership
      ↓
New class/session unpublished?
      ↓
Duplicate check
      ↓
Update
```

---

# 164. Delete Enrollment

Endpoint:

```http
DELETE /api/enrollments/{enrollment_id}
```

Deletion requires:

```text
School Administrator
```

Tenant ownership is verified across:

```text
Student
Class
AcademicSession
```

The backend then confirms the class/session results are unpublished.

Only then may the Enrollment be deleted.

---

# 165. Why Enrollment Publication Locks Matter

Enrollment represents the student population used when generating class results.

If a published class could later have students added or removed without reopening the result, the historical class record would become inconsistent.

Therefore:

```text
Published class result
        ↓
Enrollment mutation blocked
```

This protects the relationship between:

```text
class membership
result computation
published report snapshots
```

---

# 166. Teaching Assignment API

Base route:

```text
/api/teaching-assignments
```

Teaching Assignment links:

```text
Teacher
Subject
Class
Academic Session
```

It defines a teacher's academic responsibility for a particular class and subject in an academic session.

---

# 167. Create Teaching Assignment

Endpoint:

```http
POST /api/teaching-assignments
```

Authorization:

```text
School Administrator
```

Before creation, the backend independently validates:

```text
Teacher
Subject
Class
AcademicSession
```

Each must belong to:

```text
current_user.school_id
```

If any object does not belong to the authenticated tenant, it is treated as unavailable.

For example:

```text
Teacher not found
Subject not found
Class not found
Academic session not found
```

The creation logic verifies each referenced object against the current school before writing the assignment.

---

# 168. Teaching Assignment Uniqueness

The exact combination of:

```text
teacher_id
subject_id
class_id
academic_session_id
```

must be unique.

Duplicate requests return:

```text
409 Conflict
This teaching assignment already exists
```

The database `IntegrityError` is also handled, providing a second layer of duplicate protection.

---

# 169. List Teaching Assignments

Endpoint:

```http
GET /api/teaching-assignments
```

Authorization:

```text
School Administrator
```

The query joins all ownership-bearing resources:

```text
Teacher
Subject
Class
AcademicSession
```

and requires all four to belong to the current school.

This prevents malformed or cross-tenant assignment records from being exposed.

---

# 170. Get Teaching Assignment

Endpoint:

```http
GET /api/teaching-assignments/{assignment_id}
```

A Teaching Assignment is returned only when the assignment ID matches and all related entities belong to the authenticated school.

Otherwise:

```text
404 Not Found
Teaching assignment not found
```

The lookup validates school ownership through Teacher, Subject, Class, and AcademicSession simultaneously.

---

# 171. Delete Teaching Assignment

Endpoint:

```http
DELETE /api/teaching-assignments/{assignment_id}
```

Authorization:

```text
School Administrator
```

The same four-way tenant ownership check is performed before deletion.

After successful validation:

```text
db.delete(assignment)
db.commit()
```

The current Teaching Assignment API does not define an update endpoint.

Therefore, changing an assignment requires deletion followed by creation of the desired assignment.

---

# 172. Academic Structure Deletion Philosophy

The academic setup APIs deliberately avoid allowing destructive cascading operations once meaningful dependent data exists.

Examples include:

```text
Academic Session
   cannot be deleted after academic/subscription/publication records exist

Term
   cannot be deleted after assessment/report/subscription/publication records exist

Class
   cannot be deleted after enrollment/assessment/assignment/publication data exists

Subject
   cannot be deleted after assessment/assignment data exists

Teacher
   cannot be deleted while teaching assignments exist

Student
   cannot be deleted while enrollments exist
```

This protects historical consistency.

---

# 173. Deactivation vs Deletion

For Teacher accounts in particular, the backend explicitly recommends:

```text
Deactivate instead of delete
```

when teaching assignments already exist.

This represents an important general SaaS data-management principle:

```text
Operational identity may become inactive
without destroying historical academic relationships.
```

---

# 174. Tenant Security Pattern

The academic setup modules use three major tenant-validation patterns.

## Direct ownership

Used for objects containing `school_id`.

Example:

```text
Class.school_id == current_user.school_id
```

## Parent ownership

Used when the object does not contain `school_id`.

Example:

```text
Term
  JOIN AcademicSession
  WHERE AcademicSession.school_id == current_user.school_id
```

## Composite ownership

Used for records linking several tenant-owned objects.

Example:

```text
Enrollment
   JOIN Student
   JOIN Class
   JOIN AcademicSession
```

and:

```text
TeachingAssignment
   JOIN Teacher
   JOIN Subject
   JOIN Class
   JOIN AcademicSession
```

Every linked tenant-owned record must match the authenticated school.

---

# 175. Read vs Write Authorization

Some structural resources allow broader authenticated read access than write access.

For example:

```text
Classes
Subjects
Academic Sessions
Teachers
```

may be read by authenticated school-bound users.

Their creation, update, and deletion operations require a School Administrator.

Other administrative resources, such as Students and Enrollments, currently require School Administrator access for both reading and writing.

This reflects the current backend access model and may later be expanded for teacher-facing mobile features if required.

---

# 176. Academic Setup Sequence

A recommended school onboarding sequence is:

```text
1. Register School
      ↓
2. Create Academic Session
      ↓
3. Create Terms
      ↓
4. Create Classes
      ↓
5. Create Subjects
      ↓
6. Create Teachers
      ↓
7. Create Students
      ↓
8. Create Teaching Assignments
      ↓
9. Enroll Students
      ↓
10. Begin Assessment / Result Workflow
```

Some of these resources may be created in a different order, but the full set is required for meaningful result processing.

---

# 177. Academic Administration Responsibility Matrix

| Resource             | Read                      | Create       | Update       | Delete       |
| -------------------- | ------------------------- | ------------ | ------------ | ------------ |
| Academic Sessions    | Authenticated school user | School Admin | School Admin | School Admin |
| Terms                | School Admin              | School Admin | School Admin | School Admin |
| Classes              | Authenticated school user | School Admin | School Admin | School Admin |
| Subjects             | Authenticated school user | School Admin | School Admin | School Admin |
| Teachers             | Authenticated school user | School Admin | School Admin | School Admin |
| Students             | School Admin              | School Admin | School Admin | School Admin |
| Enrollments          | School Admin              | School Admin | School Admin | School Admin |
| Teaching Assignments | School Admin              | School Admin | —            | School Admin |

The table reflects the current router dependencies in the frozen backend.

---

# 178. Structural Integrity Guarantees

The academic configuration and people-management layer provides:

```text
✓ Tenant-scoped academic sessions
✓ One current session per school
✓ Tenant-scoped classes
✓ Tenant-scoped subjects
✓ Teacher accounts linked to User identities
✓ Students independent of authentication accounts
✓ School-scoped teacher employee numbers
✓ School-scoped student admission numbers
✓ Enrollment tenant validation
✓ Teaching-assignment tenant validation
✓ Duplicate enrollment prevention
✓ Duplicate teaching-assignment prevention
✓ Published-result enrollment locking
✓ Destructive-operation safeguards
✓ Historical-data preservation
```

---

# 179. Relationship Between Configuration and Results

The result-processing layer depends directly on the structures documented above.

The dependency chain is:

```text
School
  ↓
Academic Session
  ↓
Term

School
  ↓
Class
  ↓
Enrollment
  ↓
Student

School
  ↓
Subject

Teacher
  ↓
Teaching Assignment
  ↓
Class + Subject + Academic Session
```

These structures eventually feed:

```text
Assessments
Student Scores
Attendance
Comments
Result Computation
Publication
```

Therefore, the academic setup layer must remain internally consistent before a result can be considered valid.
# 180. Result Processing Architecture

The result-processing subsystem is the academic core of the Student Result Management API.

Its lifecycle is:

```text
Assessment Configuration
        ↓
Student Score Entry
        ↓
Attendance
        ↓
Teacher / Principal Comments
        ↓
Subject Result Computation
        ↓
Term Result Computation
        ↓
Class Position Calculation
        ↓
Report Sheet Assembly
        ↓
Publication Readiness Validation
        ↓
Result Publication
        ↓
Published Report Snapshots
        ↓
Historical Retrieval
```

Two important business controls apply to result-related write operations:

```text
Active term subscription
+
Result must not currently be published
```

---

# 181. Assessment API

Base route:

```text
/api/assessments
```

Assessments define the individual score components used to calculate subject results.

Each assessment belongs to:

```text
Class
Subject
Academic Session
Term
```

and contains:

```text
assessment_type
sequence
name
max_score
```

---

# 182. Create Assessment

Endpoint:

```http
POST /api/assessments
```

Authorization:

```text
School Administrator
```

Before creation, the backend validates that:

```text
Class belongs to current school
Subject belongs to current school
Academic Session belongs to current school
Term belongs to current school
Term belongs to selected Academic Session
```

This prevents construction of cross-tenant or structurally invalid assessment records.

---

# 183. Assessment Subscription Enforcement

Assessment creation requires an active subscription for the exact:

```text
school_id
academic_session_id
term_id
```

Therefore, a subscription for another term cannot authorize assessment entry.

The same active-subscription requirement applies to:

```text
assessment update
assessment deletion
```

---

# 184. Assessment Publication Lock

Before creating, updating, or deleting an Assessment, the backend verifies that the associated class/session/term result is not currently published.

Conceptually:

```text
Assessment mutation
      ↓
Is result published?
      ├── Yes → 409 Conflict
      └── No  → Continue
```

The expected response when locked is:

```text
Results for this class and term are published
and cannot be modified.
Reopen the results first.
```

---

# 185. Assessment Uniqueness

The combination:

```text
class_id
subject_id
academic_session_id
term_id
assessment_type
sequence
```

must be unique.

Duplicate assessment creation returns:

```text
409 Conflict
Assessment already exists
```

---

# 186. Assessment Read Operations

Endpoints:

```http
GET /api/assessments
GET /api/assessments/{assessment_id}
```

Assessment queries are tenant-scoped through:

```text
Class
Subject
AcademicSession
```

All three must belong to the authenticated school.

---

# 187. Student Score API

Base route:

```text
/api/student-scores
```

Each StudentScore connects:

```text
Student
+
Assessment
```

The Assessment indirectly identifies:

```text
Class
Subject
Academic Session
Term
```

---

# 188. Create Student Score

Endpoint:

```http
POST /api/student-scores
```

Authorization:

```text
School Administrator
```

The backend validates:

```text
Student belongs to current school
Assessment belongs to current school
Active term subscription exists
Results are not published
Student is enrolled in the assessment's class/session
```

Only after these checks can a score be saved.

---

# 189. Enrollment Requirement for Scores

A Student may receive a score only if they are enrolled in:

```text
Assessment.class_id
+
Assessment.academic_session_id
```

If not:

```text
400 Bad Request
Student is not enrolled in the class and
academic session for this assessment
```

This prevents scores being entered for students who are not members of the relevant class.

---

# 190. Maximum Score Validation

The entered score must not exceed:

```text
Assessment.max_score
```

For example:

```text
Assessment max_score = 20
Submitted score = 25
```

results in:

```text
400 Bad Request
Score cannot be greater than 20
```

---

# 191. Duplicate Student Scores

Only one score may exist for each:

```text
student_id + assessment_id
```

Duplicate creation returns:

```text
409 Conflict
Score already exists for this student and assessment
```

---

# 192. Score Update and Deletion

Endpoints:

```http
PATCH /api/student-scores/{score_id}
DELETE /api/student-scores/{score_id}
```

Both operations require:

```text
school ownership
active term subscription
unpublished result state
```

Updated scores are also checked against the assessment maximum.

---

# 193. Attendance API

Base route:

```text
/api/student-attendance
```

Attendance is stored as a term-level summary rather than individual daily attendance events.

Each record contains:

```text
school_days
days_present
days_absent
```

for one:

```text
Student
Academic Session
Term
```

---

# 194. Attendance Validation

The backend enforces:

```text
days_present <= school_days
days_absent <= school_days
days_present + days_absent == school_days
```

Therefore:

```text
school_days = 100
days_present = 90
days_absent = 10
```

is valid.

But:

```text
school_days = 100
days_present = 90
days_absent = 5
```

is rejected.

---

# 195. Create Attendance

Endpoint:

```http
POST /api/student-attendance
```

Authorization:

```text
School Administrator
```

The backend validates:

```text
Student tenancy
Academic Session tenancy
Term tenancy
Term belongs to selected session
Active subscription
Student result is unpublished
Attendance values are mathematically consistent
```

Only one record may exist for the Student/session/term combination.

---

# 196. Attendance Publication Lock

Attendance mutations are student-aware.

The backend:

```text
Student
  ↓
Enrollment for session
  ↓
Class
  ↓
ResultPublication
```

If that class's relevant term result is published, attendance cannot be changed until results are reopened.

This applies to:

```text
create
update
delete
```

---

# 197. Attendance Percentage

When building a report sheet:

```text
attendance_percentage =
days_present / school_days × 100
```

When `school_days` is greater than zero.

If school days are zero, the report-sheet service uses:

```text
0.0%
```

rather than dividing by zero.

---

# 198. Term Report Comment API

Base route:

```text
/api/term-report-comments
```

Each record may contain:

```text
teacher_comment
principal_comment
```

for one Student/session/term.

---

# 199. Create Report Comment

Endpoint:

```http
POST /api/term-report-comments
```

The backend validates:

```text
Student belongs to school
Academic Session belongs to school
Term belongs to school
Term belongs to selected session
Active subscription exists
Result is unpublished
```

Only one TermReportComment record may exist per:

```text
student
session
term
```

---

# 200. Report Comment Update and Deletion

Endpoints:

```http
PATCH /api/term-report-comments/{comment_id}
DELETE /api/term-report-comments/{comment_id}
```

Both require:

```text
School Administrator
Active term subscription
Unpublished student result
```

Teacher and principal comments may therefore not be changed while the official result remains published.

---

# 201. Single-Subject Result API

Endpoint:

```http
GET /api/results/student/{student_id}
```

Required query parameters:

```text
subject_id
term_id
academic_session_id
```

The endpoint calculates the selected student's result for one subject.

---

# 202. Single-Subject Result Validation

Before calculation, the backend verifies:

```text
Student belongs to current school
Academic Session belongs to current school
Subject belongs to current school
Term belongs to selected session and school
Student has an Enrollment for the session
Assessments belong to the enrolled class
```

If no assessments exist:

```text
404 Not Found
No assessments found for this result
```

---

# 203. Required Subject Components

The current result engine recognizes:

```text
CA sequence 1 → CA1
CA sequence 2 → CA2
CA sequence 3 → CA3
EXAM          → Exam
```

A subject is considered complete only when all four scores are available:

```text
CA1
CA2
CA3
EXAM
```

---

# 204. Subject Total

For a complete subject:

```text
total = CA1 + CA2 + CA3 + EXAM
```

The current result implementation treats:

```text
percentage = total
```

This reflects the present backend assumption that the complete assessment structure produces a total directly usable as a percentage/grade score.

---

# 205. Incomplete Subject Result

If any required component is missing:

```text
total = null
percentage = null
grade = null
status = INCOMPLETE
```

The backend does not silently treat missing scores as zero.

This distinction is important because publication readiness depends on true completeness.

---

# 206. Grading Scale API

Base route:

```text
/api/grading-scales
```

Each school may configure its own grading system.

Fields include:

```text
grade
minimum_score
maximum_score
remark
```

---

# 207. Create Grading Scale

Endpoint:

```http
POST /api/grading-scales
```

Authorization:

```text
School Administrator
```

Grade labels are normalized using:

```text
trim
+
uppercase
```

For example:

```text
"a" → "A"
```

---

# 208. Grading Range Overlap Protection

Grading ranges may not overlap.

For example, if:

```text
A = 70–100
```

already exists, another scale such as:

```text
B = 60–75
```

is rejected because the ranges overlap.

Conflict response identifies the overlapping grade.

---

# 209. Update Grading Scale

Endpoint:

```http
PUT /api/grading-scales/{grading_scale_id}
```

The backend verifies:

```text
minimum_score <= maximum_score
unique grade label per school
no overlapping range
```

An invalid minimum/maximum relationship returns:

```text
422 Unprocessable Entity
```

---

# 210. Grading Scale Read Access

Endpoints:

```http
GET /api/grading-scales
GET /api/grading-scales/{grading_scale_id}
```

may be used by any authenticated school-bound user.

Only grading scales belonging to the authenticated school are returned.

---

# 211. Grade Calculation Service

The result service uses configured school grading scales when available.

The ranges are sorted by:

```text
minimum_score descending
```

and the score is matched against:

```text
minimum_score <= score <= maximum_score
```

---

# 212. Default Grade Fallback

If no configured grading scales are available, the service falls back to:

|        Score | Grade |
| -----------: | :---- |
| 70 and above | A     |
|        60–69 | B     |
|        50–59 | C     |
|        45–49 | D     |
|        40–44 | E     |
|     Below 40 | F     |

This ensures result computation can still produce grades when school-specific scales have not yet been configured.

---

# 213. Performance Remarks

The current overall performance remark is based on the student's average:

|  Average | Remark            |
| -------: | ----------------- |
|      80+ | Excellent         |
| 70–79.99 | Very Good         |
| 60–69.99 | Good              |
| 50–59.99 | Satisfactory      |
| 40–49.99 | Needs Improvement |
| Below 40 | Poor              |

These remarks are generated by the result service.

---

# 214. Term Result Computation

The core service function:

```text
compute_student_term_result(...)
```

groups Assessments by Subject.

For each subject it extracts:

```text
CA1
CA2
CA3
EXAM
```

and determines whether that subject is complete.

---

# 215. Subject-Level Computation

For a complete Subject:

```text
total = ca1 + ca2 + ca3 + exam
grade = calculate_grade(total)
status = COMPLETE
```

For an incomplete Subject:

```text
total = null
grade = null
status = INCOMPLETE
```

---

# 216. Whole-Term Completeness

After all subjects are processed:

```text
number_of_subjects
completed_subjects
```

are calculated.

The overall result is marked:

```text
COMPLETE
```

only when:

```text
number_of_subjects > 0
AND
completed_subjects == number_of_subjects
```

Otherwise:

```text
INCOMPLETE
```

---

# 217. Overall Term Performance

When the result is complete:

```text
total_score = sum(subject totals)

average =
total_score / number_of_subjects

overall_grade =
calculate_grade(average)

remark =
calculate_remark(average)
```

Incomplete results do not receive a final:

```text
total_score
average
overall_grade
remark
```

The complete computation logic is centralized in the result service rather than duplicated across report endpoints.

---

# 218. Class Position Calculation

Only students whose overall result is:

```text
COMPLETE
```

participate in class-position ranking.

Students are sorted by average in descending order.

The first student receives:

```text
1
```

the second:

```text
2
```

and so forth.

---

# 219. Position Ties

Students with exactly equal averages receive the same position.

Example:

```text
Student A  85.0 → Position 1
Student B  85.0 → Position 1
Student C  80.0 → Position 3
```

This is competition-style ranking rather than dense ranking.

---

# 220. Term Result API

Endpoint:

```http
GET /api/term-results/student/{student_id}
```

Parameters include:

```text
academic_session_id
term_id
```

The endpoint assembles a complete student term result.

It retrieves:

```text
Student
Enrollment
Class
Academic Session
Term
Assessments
Subjects
Class Students
Scores
Grading Scales
Attendance
Report Comments
```

It also calculates class positions for the entire class before returning the selected student's position.

---

# 221. Term Result Response

The resulting structure includes:

```text
student identity
class information
academic session
term
closing date
next-term resumption date
subjects
total score
number of subjects
completed subjects
average
overall grade
result status
class position
class size
performance remark
attendance
comments
```

---

# 222. Report Settings API

Base route:

```text
/api/report-settings
```

Report settings are school-specific.

Only one settings record may exist per school.

---

# 223. Automatic Report Settings Creation

Endpoint:

```http
GET /api/report-settings
```

If the school does not yet have a ReportSettings record, the backend automatically creates one using default values.

This means consuming clients do not have to manually initialize report settings before requesting them.

---

# 224. Create Report Settings

Endpoint:

```http
POST /api/report-settings
```

If settings already exist:

```text
409 Conflict
Report settings already exist for this school
```

---

# 225. Update Report Settings

Endpoint:

```http
PATCH /api/report-settings
```

If no settings record currently exists, one is created and the supplied update values are applied.

This endpoint therefore behaves as an update-or-initialize operation.

---

# 226. Report Presentation Controls

Report settings include:

```text
report_title
show_class_position
show_class_size
show_attendance
show_teacher_comment
show_principal_comment
show_school_motto
show_school_logo
show_grading_remarks
principal_designation
```

These values do not change academic results.

They control how the client should present the report.

---

# 227. Report Sheet API

Endpoint:

```http
GET /api/report-sheets/student/{student_id}
```

Parameters:

```text
academic_session_id
term_id
```

Authorization:

```text
School Administrator
```

The endpoint has two possible data sources:

```text
Published Snapshot
or
Live Result Computation
```

---

# 228. Published Report Retrieval

The report endpoint first determines the student's enrollment and checks whether a publication exists for the class/session/term with:

```text
status = published
```

If so, it searches for the student's:

```text
PublishedReportSnapshot
```

When found, the stored JSON report is validated into the report response schema and returned directly.

Therefore:

```text
Published result
       ↓
Snapshot returned
```

rather than:

```text
Published result
       ↓
Recompute current database state
```

This is a major historical-integrity feature.

---

# 229. Live Report Generation

If no published snapshot applies, the endpoint calls:

```text
build_student_report_sheet(...)
```

This generates the report from current academic data.

Conceptually:

```text
No published snapshot
        ↓
Student
Enrollment
Class
Session
Term
Assessments
Scores
Grading
Attendance
Comments
School identity
Report settings
        ↓
Live Report Sheet
```

---

# 230. Report School Information

A report sheet contains School information including:

```text
school_id
school_name
email
phone
address
motto
logo_url
```

This makes the report payload sufficiently self-contained for mobile rendering or later PDF generation.

---

# 231. Report Student Information

The report includes:

```text
student_id
admission_number
full_name
gender
date_of_birth
```

---

# 232. Report Class Information

The report includes:

```text
class_id
class_name
class_size
```

Class size is based on the number of Enrollments in that class/session.

---

# 233. Report Term Information

The term section contains:

```text
academic_session_id
academic_session_name
term_id
term_name
closing_date
next_term_resumption_date
```

---

# 234. Report Performance Section

The report performance summary contains:

```text
total_score
number_of_subjects
completed_subjects
average
overall_grade
class_position
result_status
performance_remark
```

The report-sheet service computes results for all enrolled students so the requested student's class position can be calculated consistently.

---

# 235. Report Settings Fallback

If no ReportSettings record exists when the report service runs, defaults are used.

Examples include:

```text
report_title = Student Report Sheet
show_class_position = true
show_class_size = true
show_attendance = true
show_teacher_comment = true
show_principal_comment = true
show_school_motto = true
show_school_logo = true
show_grading_remarks = true
principal_designation = Principal
```

The response therefore remains renderable even without explicit customization.

---

# 236. Result Publication API

Base route:

```text
/api/result-publications
```

Result publication converts a live, editable term result into an official published state.

The publication boundary controls:

```text
Result immutability
Historical report snapshots
Subsequent academic edits
```

---

# 237. Publish Results

Endpoint:

```http
POST /api/result-publications
```

Authorization:

```text
School Administrator
```

The requested:

```text
Class
Academic Session
Term
```

must belong to the authenticated school's academic structure.

The selected Term must belong to the selected Academic Session.

---

# 238. Subscription Required for Publication

Publication requires an active subscription for the exact:

```text
School
Academic Session
Term
```

A school cannot publish a result merely because it had an active subscription for another term.

---

# 239. Duplicate Publication Protection

If an existing publication for the same:

```text
Class
Academic Session
Term
```

already has:

```text
status = published
```

the operation is rejected:

```text
409 Conflict
Results are already published for this class,
session and term
```

---

# 240. Publication Readiness Validation

Before publication, the backend verifies that the class result is ready.

The checks include:

```text
At least one enrolled Student
At least one Assessment
Assessment Subjects belong to School
All enrolled Student results are COMPLETE
```

---

# 241. No-Student Publication Protection

If no students are enrolled:

```text
400 Bad Request
Cannot publish results because the class has
no enrolled students for this session
```

---

# 242. No-Assessment Publication Protection

If no assessments exist:

```text
400 Bad Request
Cannot publish results because no assessments
exist for this class and term
```

---

# 243. Assessment Subject Tenant Validation

The publication readiness service extracts all Assessment subject IDs and loads them within the specified School.

If any Assessment references a Subject outside that school:

```text
400 Bad Request
One or more assessment subjects do not belong to this school
```

---

# 244. Incomplete Student Publication Protection

The backend computes the term result for every enrolled Student.

If one or more are incomplete, publication fails.

The error includes:

```text
message
incomplete_student_ids
```

No partial class publication is performed.

---

# 245. Publication Record

For a first publication, the backend creates:

```text
ResultPublication
```

with:

```text
class_id
academic_session_id
term_id
status = published
published_by_user_id
published_at
```

The publication is flushed before snapshots are created so the database ID is available.

---

# 246. Report Snapshot Creation

For each Enrollment in the class:

```text
build_student_report_sheet(...)
```

is called.

The complete report is converted to JSON-compatible data and stored in:

```text
PublishedReportSnapshot.report_data
```

The storage type is PostgreSQL JSONB.

---

# 247. Atomic Publication

Publication and report snapshots are committed together.

Conceptually:

```text
BEGIN
   Create / update publication
   Build Student 1 snapshot
   Build Student 2 snapshot
   Build Student 3 snapshot
   ...
COMMIT
```

This reduces the risk of a state where a publication is marked official but only some student snapshots exist.

---

# 248. Result Publication Listing

Endpoints:

```http
GET /api/result-publications
GET /api/result-publications/{publication_id}
```

Both are tenant-scoped through:

```text
Class.school_id
AcademicSession.school_id
```

A publication belonging to another school is not returned.

---

# 249. Result Publication Locks

The service:

```text
require_result_unpublished(...)
```

looks for a publication matching:

```text
class_id
academic_session_id
term_id
status = published
```

If present, protected mutations fail with `409 Conflict`.

---

# 250. Student-Level Publication Lock

For attendance and report comments, the service:

```text
require_student_result_unpublished(...)
```

first resolves the student's Enrollment to identify the Student's Class.

It then applies the class result lock for the selected term.

This creates the chain:

```text
Student
  ↓
Enrollment
  ↓
Class
  ↓
Publication
```

---

# 251. Enrollment Publication Lock

Enrollments use a broader protection:

```text
require_class_session_results_unpublished(...)
```

This blocks Enrollment changes whenever any published result exists for that:

```text
Class + Academic Session
```

The lock is deliberately broader than a single term because changing class membership could affect previously published results within that session.

---

# 252. Reopen Results

Endpoint:

```http
PATCH /api/result-publications/{publication_id}/reopen
```

Authorization:

```text
School Administrator
```

The publication must belong to the current school.

Only a publication currently in:

```text
published
```

state can be reopened.

---

# 253. Reopen Subscription Requirement

Reopening requires an active subscription for the publication's exact:

```text
Academic Session
Term
```

This prevents expired subscriptions from reopening official results for editing.

---

# 254. Reopened State

Reopening changes:

```text
status = published
```

to:

```text
status = reopened
```

Once reopened, publication-lock services no longer find a `published` record.

Academic corrections may then occur subject to the normal:

```text
authorization
tenant isolation
subscription enforcement
```

rules.

---

# 255. Republishing

When a previously reopened result is published again, the backend does not create a second ResultPublication record.

Instead, the existing publication is reused.

The backend updates:

```text
status = published
published_by_user_id
published_at
```

and regenerates report snapshots.

---

# 256. Snapshot Refresh on Republish

If a Student already has a snapshot for the publication:

```text
existing_snapshot.report_data
```

is replaced with the newly generated report data.

Its:

```text
updated_at
```

timestamp is refreshed.

If no snapshot exists, one is created.

---

# 257. Snapshot Versioning Semantics

The current system therefore provides:

```text
Immutable while published
```

rather than:

```text
Permanent multi-version history
```

Workflow:

```text
Publish Version A
      ↓
Snapshot A stored
      ↓
Reopen
      ↓
Correct academic data
      ↓
Republish
      ↓
Existing snapshot updated to Version B
```

The system does not currently retain both Snapshot A and Snapshot B as separate historical versions.

---

# 258. Published vs Reopened Report Retrieval

When publication status is:

```text
published
```

the report endpoint returns the stored Snapshot.

When publication status is:

```text
reopened
```

the published-snapshot path is not used, and the report is generated from current live academic data.

This supports the correction workflow while ensuring officially published reports remain stable.

---

# 259. Complete Result Integrity Flow

The complete workflow is:

```text
Create Assessments
       ↓
Enter Student Scores
       ↓
Record Attendance
       ↓
Record Comments
       ↓
Compute Subject Results
       ↓
Compute Term Results
       ↓
Validate Completeness
       ↓
Require Active Subscription
       ↓
Publish
       ↓
Create Report Snapshots
       ↓
Lock Academic Mutations
       ↓
Serve Historical Snapshot
```

Correction workflow:

```text
Published Result
       ↓
Active Subscription Required
       ↓
Reopen
       ↓
Academic Locks Released
       ↓
Correct Scores / Attendance / Comments / Assessments
       ↓
Validate Completeness Again
       ↓
Republish
       ↓
Refresh Snapshots
       ↓
Locks Restored
```

---

# 260. Result-System Security Guarantees

The current result subsystem provides:

```text
✓ School-scoped Assessments
✓ School-scoped Student Scores
✓ Enrollment validation before score entry
✓ Maximum-score validation
✓ Duplicate score prevention
✓ Attendance consistency validation
✓ School-scoped grading scales
✓ Non-overlapping grade ranges
✓ Explicit COMPLETE / INCOMPLETE result state
✓ Missing scores are not silently treated as zero
✓ Class position from completed results
✓ Active-subscription enforcement on academic writes
✓ Active-subscription enforcement on publication
✓ Publication readiness validation
✓ Publication locks
✓ Student-level result locks
✓ Enrollment locks
✓ Immutable published snapshots
✓ Tenant-scoped publication retrieval
✓ Controlled reopening
✓ Republish snapshot refresh
```

---

# 261. Result Processing Design Summary

The architecture separates three concepts:

```text
Raw Academic Data
        ↓
Computed Result
        ↓
Published Historical Representation
```

Raw academic data consists of:

```text
Assessments
Scores
Attendance
Comments
```

Computed results are generated by service functions and are not stored as duplicate result rows.

Official published reports are then preserved as JSONB snapshots.

This approach avoids maintaining multiple conflicting calculated-result tables while still preserving an official representation after publication.

---

# 262. Important Architectural Distinction

The database does not store a conventional permanent `results` table containing calculated totals.

Instead:

```text
Assessments + StudentScores
       ↓
Result Service
       ↓
Computed Result
```

The final official representation becomes persistent only through:

```text
PublishedReportSnapshot
```

after publication.

This keeps calculated results derived from their source data until they cross the publication boundary.

---

# 263. Flutter Result Workflow

A future Flutter school-admin interface can follow:

```text
Assessment Setup Screen
       ↓
Score Entry Screen
       ↓
Attendance Screen
       ↓
Comments Screen
       ↓
Result Preview
       ↓
Readiness Check / Publication
       ↓
Published Report Screen
```

When the backend returns a publication-lock conflict, the Flutter client should display that the result must first be reopened rather than attempting to bypass the restriction.

Likewise, subscription errors should direct the administrator toward the subscription/payment workflow.

---

# 264. Report Rendering Responsibility

The backend provides structured report data.

The Flutter application may determine the visual presentation based on:

```text
school_info
report_settings
student
class_info
term_info
subjects
performance
attendance
comments
```

The frontend should respect settings such as:

```text
show_class_position
show_attendance
show_school_logo
show_teacher_comment
```

but the underlying backend report data remains the authoritative academic source.

---

# 265. Historical Result Principle

Once results are published:

```text
Live database data
≠
Official report source
```

Instead:

```text
PublishedReportSnapshot
=
Official stored representation
```

until the result is deliberately reopened and republished.

This publication boundary is one of the most important integrity mechanisms in the entire SaaS.
# 266. Commercial SaaS Architecture

The Student Result Management API operates as a term-based commercial SaaS platform.

The commercial lifecycle is:

```text
Platform Admin
      ↓
Creates Subscription Plans
      ↓
School Admin
      ↓
Creates Term Subscription
      ↓
Subscription = pending
      ↓
Payment Initialized
      ↓
Flutterwave Checkout
      ↓
Payment Verification
      ↓
Subscription = active
      ↓
Academic Term Operations Enabled
```

The core relationship is:

```text
School
  ↓
Subscription
  ├── Subscription Plan
  ├── Academic Session
  └── Term
```

---

# 267. Subscription Plan API

Base route:

```text
/api/subscription-plans
```

Subscription plans are global platform-level products.

They are not owned by individual schools.

Typical plan attributes include:

```text
name
description
price_per_term
max_students
is_active
```

---

# 268. Create Subscription Plan

Endpoint:

```http
POST /api/subscription-plans
```

Authorization:

```text
Platform Administrator only
```

The plan name is trimmed before storage.

Plan names must be globally unique.

Duplicate creation returns:

```text
409 Conflict
A subscription plan with this name already exists
```

---

# 269. Subscription Plan Pricing

The commercial price is stored as:

```text
price_per_term
```

This confirms that billing is designed around:

```text
School + Academic Session + Term
```

rather than a monthly recurring SaaS interval.

The payment initialization process later uses the server-side plan price rather than accepting an amount from the client.

---

# 270. Student Limits

A SubscriptionPlan may contain:

```text
max_students
```

A null value may represent an unrestricted plan depending on the commercial configuration.

The field is part of the pricing/product model.

The reviewed subscription and payment routes do not themselves enforce this limit during payment.

Any actual student-cap enforcement should therefore be documented separately if implemented elsewhere.

---

# 271. Active and Inactive Plans

Plans contain:

```text
is_active
```

This allows plans to be retired without deleting them.

School users only see active plans.

Platform administrators may see both active and inactive plans.

This preserves historical subscriptions tied to discontinued products.

---

# 272. List Subscription Plans

Endpoint:

```http
GET /api/subscription-plans
```

Authorization:

```text
Authenticated User
```

Behavior differs by account type.

For a Platform Administrator:

```text
Active plans
+
Inactive plans
```

are visible.

For other users:

```text
Only active plans
```

are returned.

Plans are ordered by:

```text
price_per_term ascending
```

---

# 273. Get Subscription Plan

Endpoint:

```http
GET /api/subscription-plans/{plan_id}
```

An inactive plan is hidden from non-platform users.

For these users, requesting an inactive plan returns:

```text
404 Not Found
Subscription plan not found
```

rather than revealing a retired plan.

---

# 274. Update Subscription Plan

Endpoint:

```http
PATCH /api/subscription-plans/{plan_id}
```

Authorization:

```text
Platform Administrator
```

The platform administrator may change:

```text
name
description
price_per_term
max_students
is_active
```

Plan-name uniqueness is checked again when the name changes.

---

# 275. Subscription API

Base route:

```text
/api/subscriptions
```

A Subscription represents access purchased by one school for one academic term.

The commercial key is:

```text
school_id
academic_session_id
term_id
```

Only one subscription may exist for that combination.

---

# 276. Create Subscription

Endpoint:

```http
POST /api/subscriptions
```

Authorization:

```text
School Administrator
```

The tenant is always determined from:

```text
current_user.school_id
```

The client does not submit an authoritative school ID.

---

# 277. Subscription Plan Validation

Before creating a Subscription, the backend verifies that the selected plan:

```text
exists
AND
is_active = true
```

If not:

```text
404 Not Found
Active subscription plan not found
```

A school therefore cannot create a new subscription using a retired plan.

---

# 278. Subscription Academic Validation

The backend verifies that:

```text
Academic Session belongs to current school
```

and that:

```text
Term belongs to selected Academic Session
```

The Term query also verifies the owning Academic Session belongs to the current tenant.

This prevents a School from subscribing to another School's academic structure.

---

# 279. Subscription Uniqueness

Before creation, the backend searches for an existing Subscription matching:

```text
school_id
academic_session_id
term_id
```

If found:

```text
409 Conflict
A subscription already exists for this school,
academic session, and term
```

This means changing plan does not create parallel subscriptions for the same term under the current design.

---

# 280. Initial Subscription Status

New subscriptions are created with:

```text
status = pending
```

The lifecycle begins as:

```text
School chooses plan
      ↓
Subscription created
      ↓
pending
      ↓
Payment required
```

---

# 281. School Subscription History

Endpoint:

```http
GET /api/subscriptions/me
```

Authorization:

```text
School Administrator
```

Only subscriptions belonging to:

```text
current_user.school_id
```

are returned.

They are ordered with newest subscriptions first.

---

# 282. Get School Subscription

Endpoint:

```http
GET /api/subscriptions/me/{subscription_id}
```

The lookup requires:

```text
Subscription.id = requested ID
AND
Subscription.school_id = current_user.school_id
```

A subscription belonging to another tenant is not exposed.

---

# 283. Platform Subscription Listing

Endpoint:

```http
GET /api/subscriptions
```

Authorization:

```text
Platform Administrator
```

This endpoint returns subscriptions across all schools.

It provides the platform-level commercial view.

---

# 284. Subscription Statuses

The supported statuses are:

```text
pending
active
expired
cancelled
```

Any other status returns:

```text
422 Unprocessable Entity
```

---

# 285. Subscription State Machine

The manually permitted transitions are:

```text
pending
 ├── active
 └── cancelled

active
 ├── expired
 └── cancelled

cancelled
 └── pending

expired
 └── no further transition
```

The implementation also permits an idempotent request that leaves the Subscription in its current status.

---

# 286. Invalid Status Transitions

An invalid transition returns:

```text
409 Conflict
```

with a message describing the forbidden state change.

For example:

```text
expired → active
```

is not permitted through the manual status endpoint.

---

# 287. Manual Platform Override

Endpoint:

```http
PATCH /api/subscriptions/{subscription_id}/status
```

Authorization:

```text
Platform Administrator
```

This endpoint means a Platform Administrator can manually activate or otherwise transition a subscription within the allowed state machine.

This is a privileged administrative override.

Payment remains the normal commercial activation path.

---

# 288. Subscription Activation Timestamp

When a Subscription becomes:

```text
active
```

the backend sets:

```text
activated_at
```

if it has not already been set.

If a cancelled subscription is moved back to:

```text
pending
```

the activation timestamp is cleared.

---

# 289. Active Subscription Enforcement

The central commercial access-control service is:

```text
require_active_term_subscription(...)
```

It searches for an exact match on:

```text
school_id
academic_session_id
term_id
status = active
```

If no such Subscription exists:

```text
403 Forbidden
An active subscription is required
for this academic term
```

This is the core monetization gate for term-level academic operations.

---

# 290. Exact-Term Enforcement

A Subscription does not grant general platform-wide academic access.

For example:

```text
School A
2026/2027
First Term
status = active
```

does not authorize writes for:

```text
2026/2027
Second Term
```

The check is exact.

This is important because the commercial model is explicitly term-based.

---

# 291. Subscription-Gated Academic Operations

The active-subscription requirement is integrated into academic workflows including:

```text
Assessment creation
Assessment modification
Assessment deletion
Student score creation
Student score modification
Student score deletion
Attendance writes
Report comment writes
Result publication
Result reopening
```

Historical read operations remain separately accessible according to their router authorization.

---

# 292. Payment API

Base route:

```text
/api/payments
```

The payment provider is:

```text
Flutterwave
```

The current payment currency is:

```text
NGN
```

---

# 293. Payment Initialization

Endpoint:

```http
POST /api/payments/initialize
```

Authorization:

```text
School Administrator
```

The request identifies a:

```text
subscription_id
```

The backend then loads the Subscription using:

```text
Subscription.id
+
current_user.school_id
```

This prevents one tenant from paying for another tenant's subscription through the endpoint.

---

# 294. Pending-Only Payment Initialization

Payment may only be initialized when:

```text
Subscription.status = pending
```

Otherwise:

```text
409 Conflict
Payment can only be initialized for a pending subscription
```

This avoids initiating checkout for subscriptions that are already active, expired, or cancelled.

---

# 295. Server-Side Payment Amount

The payment amount is not trusted from the client.

Instead:

```text
Subscription
      ↓
SubscriptionPlan
      ↓
price_per_term
      ↓
PaymentTransaction.amount
```

The backend therefore remains authoritative over commercial pricing.

---

# 296. Successful Payment Duplicate Protection

Before initialization, the backend checks whether the Subscription already has a:

```text
PaymentTransaction.status = successful
```

If so:

```text
409 Conflict
This subscription already has a successful payment
```

This prevents unnecessary duplicate payment attempts.

---

# 297. Pending Payment Reuse

If a pending PaymentTransaction already exists with a valid payment link, the backend returns that transaction instead of creating another one.

Therefore repeated initialization behaves as:

```text
Pending checkout exists
      ↓
Return existing payment link
```

rather than:

```text
Generate unlimited new payment transactions
```

This reduces unnecessary duplicate Flutterwave checkout sessions.

---

# 298. Transaction Reference Generation

A unique transaction reference is generated using a structure similar to:

```text
SRMS-S{school_id}-SUB{subscription_id}-{uuid}
```

This embeds useful internal context while including a UUID component for uniqueness.

---

# 299. Payment Transaction Creation

Before contacting Flutterwave, the backend creates a local PaymentTransaction containing:

```text
school_id
subscription_id
tx_ref
amount
currency = NGN
status = pending
payment_provider = flutterwave
```

The record is flushed so it has a local database ID before the external request completes.

---

# 300. Flutterwave Payment Initialization Service

The Flutterwave integration communicates with:

```text
https://api.flutterwave.com/v3
```

The initialization endpoint is:

```text
POST /payments
```

Authorization uses:

```text
Bearer <FLUTTERWAVE_SECRET_KEY>
```

The secret key comes from application configuration.

---

# 301. Flutterwave Initialization Payload

The payment provider receives:

```text
tx_ref
amount
currency
redirect_url
customer
customizations
meta
```

Customer information includes:

```text
email
name
phonenumber (when available)
```

Metadata includes:

```text
subscription_id
```

---

# 302. Flutterwave Payment Description

The current integration sends:

```text
title:
School Subscription Payment

description:
Termly school subscription
```

This reflects the term-based SaaS commercial model.

---

# 303. Flutterwave Service Errors

The integration converts provider/network failures into:

```text
FlutterwaveServiceError
```

Examples include:

```text
Secret key not configured
Redirect URL not configured
Unable to connect to Flutterwave
Payment initialization failed
Invalid Flutterwave response
Missing payment link
```

---

# 304. Failed Payment Initialization

If Flutterwave initialization fails after the local PaymentTransaction has been created:

```text
PaymentTransaction.status = failed
```

is stored.

The API then returns:

```text
502 Bad Gateway
```

with the integration error.

This preserves a local audit trail of the failed attempt.

---

# 305. Payment Initialization Response

Successful initialization returns:

```text
payment_id
subscription_id
tx_ref
amount
currency
status
payment_link
```

The Flutter client can open:

```text
payment_link
```

for the user to complete payment.

---

# 306. Manual Payment Verification

Endpoint:

```http
POST /api/payments/{payment_id}/verify
```

Authorization:

```text
School Administrator
```

The PaymentTransaction must belong to:

```text
current_user.school_id
```

The associated Subscription must also belong to that same tenant.

---

# 307. Verification Principle

The backend never activates a subscription simply because the client says payment succeeded.

Instead:

```text
Client supplies Flutterwave transaction ID
        ↓
Backend calls Flutterwave API
        ↓
Provider response verified
        ↓
Payment fields checked
        ↓
Subscription activated
```

This keeps payment authority server-side.

---

# 308. Payment Verification Service

The shared service is:

```text
process_verified_payment(...)
```

It verifies the provider transaction before activating the Subscription.

The function is used by the manual verification workflow and represents the core provider-verification logic.

---

# 309. Verification Idempotency

If the local payment is already:

```text
successful
```

and the same Flutterwave transaction ID is supplied again, the verified Payment and Subscription are returned without reprocessing.

However, if a different transaction ID is supplied for an already-successful payment:

```text
409 Conflict
Payment has already been verified with another transaction
```

---

# 310. Pending Subscription Requirement

Before activation through payment verification:

```text
subscription.status
```

must still equal:

```text
pending
```

Otherwise:

```text
409 Conflict
The subscription is no longer pending
and cannot be activated by this payment
```

---

# 311. Provider Transaction ID Validation

The Flutterwave verification response must contain the same transaction ID requested by the backend.

Mismatch results in:

```text
400 Bad Request
Flutterwave transaction ID does not match
```

---

# 312. Transaction Reference Validation

The provider-returned:

```text
tx_ref
```

or equivalent reference must equal:

```text
PaymentTransaction.tx_ref
```

A mismatch causes:

```text
400 Bad Request
Payment transaction reference does not match
```

This prevents one valid Flutterwave transaction from being attached to the wrong local PaymentTransaction.

---

# 313. Provider Payment Status Validation

The Flutterwave transaction must have:

```text
status = successful
```

Otherwise the Subscription is not activated.

Manual verification returns:

```text
409 Conflict
Flutterwave payment is not successful
```

---

# 314. Currency Validation

The returned provider currency must match the local PaymentTransaction currency.

The comparison is case-insensitive after uppercasing.

Mismatch:

```text
400 Bad Request
Payment currency does not match
```

---

# 315. Amount Validation

The provider amount is converted using:

```text
Decimal
```

for financial-safe comparison.

The returned payment amount must satisfy:

```text
returned_amount >= expected_amount
```

Underpayment is rejected.

The backend therefore accepts the expected amount or a greater verified amount but never a lower amount.

---

# 316. Flutterwave Transaction Reuse Protection

Before accepting a verified Flutterwave transaction ID, the backend searches PaymentTransaction records for the same:

```text
flutterwave_transaction_id
```

attached to another payment.

If found:

```text
409 Conflict
Flutterwave transaction has already been used
for another payment
```

This prevents replaying one provider transaction to activate multiple subscriptions.

---

# 317. Atomic Payment Activation

After successful verification, the backend updates:

```text
PaymentTransaction
    flutterwave_transaction_id
    status = successful
    verified_at
```

and:

```text
Subscription
    status = active
    activated_at
```

inside the same database transaction.

Conceptually:

```text
BEGIN
    Mark Payment successful
    Activate Subscription
COMMIT
```

If the transaction fails:

```text
ROLLBACK
```

This prevents states such as:

```text
Payment successful
but
Subscription still pending
```

or the reverse.

---

# 318. Payment Verification Result

Successful verification returns:

```text
payment_id
subscription_id
flutterwave_transaction_id
payment_status
subscription_status
verified_at
```

The expected final state is:

```text
payment_status = successful
subscription_status = active
```

---

# 319. Payment History

Endpoint:

```http
GET /api/payments
```

Authorization:

```text
School Administrator
```

Only transactions where:

```text
PaymentTransaction.school_id
==
current_user.school_id
```

are returned.

They are ordered newest first.

---

# 320. Single Payment Retrieval

Endpoint:

```http
GET /api/payments/{payment_id}
```

A transaction is returned only when both:

```text
payment ID matches
AND
school_id matches authenticated tenant
```

Otherwise:

```text
404 Not Found
Payment transaction not found
```

This prevents payment-history leakage between schools.

---

# 321. Flutterwave Webhook Endpoint

Endpoint:

```http
POST /api/payments/webhook
```

The webhook does not use normal JWT authentication.

This is intentional because the request originates from Flutterwave rather than an authenticated SaaS user.

Instead, webhook-specific cryptographic authentication is performed.

---

# 322. Supported Webhook Authentication

The implementation supports two Flutterwave authentication mechanisms:

```text
verif-hash
```

and:

```text
flutterwave-signature
```

The first compares the received verification hash with:

```text
settings.flutterwave_secret_hash
```

using constant-time comparison.

The second verifies an HMAC-SHA256 signature over the raw request body.

---

# 323. Constant-Time Comparison

Webhook secrets/signatures are compared using:

```text
hmac.compare_digest(...)
```

rather than ordinary string comparison.

This is appropriate for authentication secrets because it reduces timing-based comparison leakage.

---

# 324. HMAC Webhook Verification

For the signature-based webhook mechanism:

```text
HMAC-SHA256(
    secret_hash,
    raw_request_body
)
```

is computed.

The digest is Base64 encoded and compared to:

```text
flutterwave-signature
```

from the request header.

---

# 325. Invalid Webhook Authentication

If neither supported authentication mechanism validates:

```text
401 Unauthorized
Invalid Flutterwave webhook authentication
```

The payload is not processed further.

---

# 326. Webhook JSON Validation

After authentication, the raw request body is parsed as JSON.

Malformed payload:

```text
400 Bad Request
Invalid webhook JSON payload
```

---

# 327. Supported Webhook Events

The current webhook recognizes:

```text
charge.completed
charge.completed.successful
```

Other event types are acknowledged as ignored.

This prevents unrelated provider events from entering payment activation logic.

---

# 328. Missing Webhook Data

If the payload does not contain a valid:

```text
data
```

object, the endpoint responds with:

```text
status = ignored
reason = Missing webhook data
```

Likewise, events missing a transaction ID or transaction reference are ignored rather than processed.

---

# 329. Unknown Transaction References

The webhook looks up the local PaymentTransaction using:

```text
tx_ref
```

If no local transaction exists:

```text
status = ignored
reason = Unknown transaction reference
```

This prevents arbitrary provider payloads from creating new commercial records.

---

# 330. Webhook Idempotency

If the local PaymentTransaction already has:

```text
status = successful
```

the webhook returns:

```text
status = already_processed
payment_id = ...
```

No duplicate activation occurs.

---

# 331. Subscription-State Webhook Guard

The Subscription linked to the local PaymentTransaction must still be:

```text
pending
```

If not:

```text
status = ignored
reason = Subscription is no longer pending
```

This prevents a late webhook from unexpectedly modifying an already transitioned Subscription.

---

# 332. Webhook Provider Re-Verification

A valid webhook signature is not treated as proof that payment succeeded.

The webhook still calls:

```text
verify_transaction(transaction_id)
```

directly against Flutterwave.

The security model is therefore:

```text
Valid webhook authentication
        ↓
Locate local Payment
        ↓
Call Flutterwave verification API
        ↓
Validate provider transaction
        ↓
Activate Subscription
```

This is significantly safer than trusting webhook body fields alone.

---

# 333. Webhook Transaction Validation

The re-verified provider response is checked for:

```text
transaction ID
transaction reference
status
currency
amount
```

The Flutterwave transaction ID must match the webhook transaction ID.

The Flutterwave transaction reference must match the local Payment's `tx_ref`.

---

# 334. Webhook Payment Amount Protection

The verified amount is converted to:

```text
Decimal
```

and compared against the locally stored expected amount.

If:

```text
received_amount < expected_amount
```

the webhook rejects activation.

This prevents an underpaid transaction from unlocking the subscription.

---

# 335. Webhook Transaction Replay Protection

The webhook searches for any other PaymentTransaction already using the same:

```text
flutterwave_transaction_id
```

If found:

```text
409 Conflict
Flutterwave transaction has already been used
```

This provides payment replay protection at the application layer.

---

# 336. Webhook Activation Transaction

After successful validation:

```text
payment.flutterwave_transaction_id = transaction_id
payment.status = successful
payment.verified_at = now

subscription.status = active
subscription.activated_at = now
```

are committed together.

Failure during commit triggers:

```text
ROLLBACK
```

and:

```text
500 Internal Server Error
Unable to process payment webhook
```

---

# 337. Webhook Success Acknowledgment

A successful webhook returns information including:

```text
status = processed
payment_id
subscription_id
payment_status
subscription_status
```

The expected commercial state is:

```text
Payment = successful
Subscription = active
```

---

# 338. Manual Verification vs Webhook

The backend supports two ways for successful payment to be recognized:

```text
Manual verification endpoint
```

and:

```text
Flutterwave webhook
```

Both ultimately depend on direct provider verification.

Conceptually:

```text
Flutter App
   ↓
Manual Verify
   ↓
Flutterwave API
   ↓
Activate
```

or:

```text
Flutterwave
   ↓
Webhook
   ↓
Authenticate Webhook
   ↓
Flutterwave API Re-Verification
   ↓
Activate
```

---

# 339. Payment Source of Truth

The client is never the source of truth for payment success.

The authoritative chain is:

```text
Local PaymentTransaction
        +
Flutterwave Verified Transaction
        ↓
Payment success
        ↓
Subscription activation
```

Client-side redirect success alone must never be used to unlock academic features.

---

# 340. Recommended Flutter Payment Flow

The future Flutter application should follow:

```text
1. School Admin creates Subscription
       ↓
2. POST /api/payments/initialize
       ↓
3. Receive payment_link
       ↓
4. Open Flutterwave checkout
       ↓
5. User completes payment
       ↓
6. Flutterwave redirects app/user
       ↓
7. App calls verification endpoint
       ↓
8. Backend independently verifies Flutterwave
       ↓
9. GET /api/subscriptions/me/{id}
       ↓
10. Confirm status = active
```

The webhook may activate the Subscription before step 7.

Therefore verification and status refresh should be designed to be idempotent.

---

# 341. Flutter Client Payment Rules

The Flutter client should never:

```text
set subscription status locally
trust only the payment redirect
send its own authoritative amount
assume payment succeeded because checkout closed
```

Instead it should rely on backend states.

Recommended UI states:

```text
pending
processing
active
failed payment attempt
cancelled
expired
```

---

# 342. Commercial Tenant Isolation

Payment and Subscription operations maintain tenant boundaries.

A School Administrator can access only:

```text
their subscriptions
their payment transactions
their checkout sessions
their payment verification operations
```

Platform-wide subscription management is reserved for:

```text
Platform Administrator
```

---

# 343. Commercial Security Layers

The payment architecture applies multiple security controls:

```text
Authenticated School Admin
        ↓
Tenant-scoped Subscription
        ↓
Server-controlled price
        ↓
Unique tx_ref
        ↓
Flutterwave checkout
        ↓
Provider verification
        ↓
Transaction-ID validation
        ↓
Reference validation
        ↓
Status validation
        ↓
Currency validation
        ↓
Amount validation
        ↓
Transaction replay check
        ↓
Atomic activation
```

For webhook processing, additional layers are added:

```text
Webhook secret/signature authentication
+
Direct provider re-verification
```

---

# 344. Payment Failure Philosophy

External provider failures do not automatically corrupt Subscription state.

For example:

```text
Flutterwave initialization fails
        ↓
PaymentTransaction = failed
        ↓
Subscription remains pending
```

Therefore the School can make another valid payment attempt later without an incorrectly activated Subscription.

---

# 345. Subscription and Academic Access Relationship

The Subscription system is integrated directly into the academic write path.

Conceptually:

```text
School wants to modify term academic data
              ↓
Authenticated?
              ↓
Correct tenant?
              ↓
Active subscription for exact term?
       ├── No → 403
       └── Yes
              ↓
Published lock?
       ├── Yes → 409
       └── No
              ↓
Academic operation permitted
```

This combines the commercial access boundary with academic-integrity controls.

---

# 346. Commercial Lifecycle

The complete commercial lifecycle is:

```text
Platform creates plan
        ↓
School selects plan
        ↓
Subscription created as pending
        ↓
Payment initialized
        ↓
Flutterwave checkout
        ↓
Provider verifies transaction
        ↓
Payment successful
        ↓
Subscription active
        ↓
Term academic writes permitted
        ↓
Result publication permitted
        ↓
Subscription eventually expired/cancelled
```

---

# 347. Subscription Status and Payment Status Are Separate

The system intentionally maintains two different state objects.

PaymentTransaction may have:

```text
pending
successful
failed
```

Subscription may have:

```text
pending
active
expired
cancelled
```

These concepts should not be confused.

A Payment records a financial transaction.

A Subscription records commercial access entitlement.

---

# 348. Why Separate Payment and Subscription Records Matter

Separating these entities allows:

```text
Multiple payment attempts
Provider audit trail
Failed-payment history
Commercial subscription status
Future payment-provider expansion
```

without overloading the Subscription record with provider-specific transaction data.

---

# 349. Payment Provider Abstraction

Flutterwave-specific network logic resides in:

```text
app/services/flutterwave_service.py
```

while broader payment-processing logic resides in:

```text
app/services/payment_service.py
```

This separation means:

```text
API Router
     ↓
Payment Service
     ↓
Flutterwave Service
     ↓
External Flutterwave API
```

The architecture therefore keeps HTTP-provider concerns separate from business activation logic.

---

# 350. Current Payment Provider

The current implemented provider is:

```text
Flutterwave
```

The PaymentTransaction model also contains a:

```text
payment_provider
```

field.

This leaves architectural room for additional providers later, although no other payment provider is currently implemented.

---

# 351. External Payment Error Semantics

Failures communicating with Flutterwave typically result in:

```text
502 Bad Gateway
```

This correctly distinguishes:

```text
Backend/client validation error
```

from:

```text
External provider failure
```

---

# 352. Financial Numeric Handling

Payment amounts are stored and compared using decimal-based values rather than binary floating-point arithmetic.

Provider amounts are converted through:

```text
Decimal(...)
```

before comparisons.

This is appropriate for monetary values.

---

# 353. Subscription Expiration

The Subscription model supports:

```text
expires_at
```

and the status:

```text
expired
```

The reviewed API contains the status transition:

```text
active → expired
```

However, this reviewed code does not show an automatic scheduler that marks subscriptions expired based on `expires_at`.

Therefore automatic expiration should not be claimed as implemented unless another component explicitly performs it.

At present, the verified API supports the expired state and manual platform transition.

---

# 354. Known Commercial Timestamp Technical Debt

Some commercial components still use:

```python
datetime.utcnow()
```

for values such as:

```text
activated_at
verified_at
published_at
```

The current database timestamp strategy is intentionally retained for backend freeze compatibility.

A future migration should move the application deliberately toward timezone-aware UTC timestamps and corresponding PostgreSQL timezone-aware columns rather than changing individual calls independently.

---

# 355. Commercial Security Summary

The commercial subsystem currently provides:

```text
✓ Platform-managed subscription plans
✓ Active/inactive plans
✓ Term-specific subscriptions
✓ School/session/term uniqueness
✓ Tenant-scoped subscription history
✓ Controlled subscription state machine
✓ Exact-term active-subscription enforcement
✓ Server-controlled pricing
✓ Tenant-scoped payment initialization
✓ Duplicate successful-payment protection
✓ Pending payment-link reuse
✓ Unique transaction references
✓ Provider-side payment verification
✓ Transaction-reference validation
✓ Currency validation
✓ Amount validation
✓ Provider transaction replay protection
✓ Atomic payment/subscription activation
✓ Tenant-scoped payment history
✓ Authenticated Flutterwave webhook handling
✓ HMAC-SHA256 webhook support
✓ Legacy verif-hash support
✓ Webhook idempotency
✓ Provider re-verification after webhook
✓ Financial Decimal handling
```

---

# 356. Commercial Architecture Summary

The monetization architecture can be summarized as:

```text
Subscription Plan
      ↓
Subscription
      ↓
Payment Transaction
      ↓
Flutterwave
      ↓
Verified Payment
      ↓
Active Subscription
      ↓
Academic Access
```

This design keeps:

```text
pricing
payment
access entitlement
academic operations
```

as separate but connected concerns.

That separation is important for both security and future product growth.
# 357. Schema Layer Overview

The backend uses Pydantic models to define request and response contracts.

These schemas provide:

```text
Field typing
Required/optional values
Length validation
Numeric validation
Email validation
Cross-field validation
Response serialization
ORM-to-schema conversion
```

The schema layer is important for Flutter integration because it defines exactly what the mobile client must send and what it should expect in return.

---

# 358. Authentication Schemas

## LoginRequest

Used by:

```http
POST /api/auth/login
```

Fields:

| Field    | Type     | Required |
| -------- | -------- | -------- |
| email    | EmailStr | Yes      |
| password | string   | Yes      |

The email field must be syntactically valid.

Example:

```json
{
  "email": "admin@school.com",
  "password": "StrongPassword123"
}
```

## TokenResponse

Fields:

```text
access_token: string
token_type: string
```

Default:

```text
token_type = bearer
```

Example:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

---

# 359. Platform Administrator Creation Schema

Schema:

```text
PlatformAdminCreate
```

Fields:

| Field    | Type   | Validation       |
| -------- | ------ | ---------------- |
| email    | string | Required         |
| password | string | 8–128 characters |

The schema itself uses a plain string for `email`, rather than `EmailStr`.

The router still normalizes and checks uniqueness.

---

# 360. School Administrator Creation Schema

Schema:

```text
SchoolAdminCreate
```

Fields:

| Field     | Type         | Validation       |
| --------- | ------------ | ---------------- |
| email     | string       | Required         |
| password  | string       | 8–128 characters |
| school_id | integer/null | Optional         |

`school_id` is required in practice when a Platform Administrator creates a School Administrator.

For a School Administrator creating another admin, the backend derives the School from the authenticated user.

---

# 361. Administrator Response Schema

Schema:

```text
AdminUserResponse
```

Fields:

```text
id
email
role
account_type
school_id
is_active
created_at
```

`school_id` may be null for a Platform Administrator.

---

# 362. Administrator Status Schema

Schema:

```text
AdminStatusUpdate
```

Field:

```text
is_active: bool
```

Example:

```json
{
  "is_active": false
}
```

---

# 363. School Registration Request

Schema:

```text
SchoolRegistrationRequest
```

Fields:

| Field          | Type          | Validation  |
| -------------- | ------------- | ----------- |
| school_name    | string        | 2–255 chars |
| school_slug    | string        | 2–150 chars |
| school_email   | EmailStr/null | Optional    |
| phone          | string/null   | Max 50      |
| address        | string/null   | Optional    |
| motto          | string/null   | Max 255     |
| admin_email    | EmailStr      | Required    |
| admin_password | string        | 8–128 chars |

---

# 364. School Slug Validation

The School slug must match:

```regex
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

Valid examples:

```text
an-nur-islamic-college
right-vision-academy
school1
```

Invalid examples include:

```text
An Nur
school_name
-school
school-
```

The slug therefore uses lowercase letters, digits, and single hyphen-separated segments.

---

# 365. School Registration Response

Fields:

```text
school_id
school_name
school_slug
school_email
admin_user_id
admin_email
role
message
```

This gives the Flutter client enough information to confirm successful tenant registration.

---

# 366. School Update Schema

Optional fields:

```text
name
email
phone
address
motto
logo_url
```

Validation includes:

```text
name: 2–255
phone: max 50
motto: max 255
logo_url: max 500
```

Only supplied fields need to be changed.

---

# 367. School Response Schema

Fields:

```text
id
name
slug
email
phone
address
motto
logo_url
is_active
created_at
updated_at
```

The schema supports ORM conversion using:

```text
from_attributes = true
```

---

# 368. Academic Session Create Schema

Fields:

```text
name
is_current
```

Validation:

```text
name: 4–20 characters
is_current: default false
```

Example:

```json
{
  "name": "2026/2027",
  "is_current": true
}
```

---

# 369. Academic Session Update Schema

Optional fields:

```text
name
is_current
```

`name` remains constrained to:

```text
4–20 characters
```

---

# 370. Academic Session Response

Fields:

```text
id
school_id
name
is_current
created_at
```

---

# 371. Term Create Schema

Fields:

| Field                     | Type      | Validation |
| ------------------------- | --------- | ---------- |
| academic_session_id       | int       | > 0        |
| name                      | string    | 2–20 chars |
| closing_date              | date/null | Optional   |
| next_term_resumption_date | date/null | Optional   |

Example:

```json
{
  "academic_session_id": 1,
  "name": "First Term",
  "closing_date": "2026-12-18",
  "next_term_resumption_date": "2027-01-11"
}
```

---

# 372. Term Update Schema

Optional fields:

```text
name
closing_date
next_term_resumption_date
```

`name` must remain 2–20 characters when supplied.

---

# 373. Term Response Schema

Fields:

```text
id
academic_session_id
name
created_at
closing_date
next_term_resumption_date
```

---

# 374. Class Create Schema

Fields:

```text
name
code
description
```

Validation:

```text
name: 2–100 characters
code: 2–50 characters
description: max 255
```

---

# 375. Class Update Schema

All fields are optional:

```text
name
code
description
```

with the same validation constraints as creation.

---

# 376. Class Response Schema

Fields:

```text
id
school_id
name
code
description
created_at
updated_at
```

---

# 377. Subject Create Schema

Fields:

```text
name
code
description
```

Validation:

```text
name: 2–100
code: 2–20
description: max 255
```

---

# 378. Subject Update Schema

Optional fields:

```text
name
code
description
```

with the same length restrictions.

---

# 379. Subject Response

Fields:

```text
id
school_id
name
code
description
```

The current Subject response schema does not expose created/updated timestamps.

---

# 380. Teacher Create Schema

Fields:

| Field           | Type     | Validation |
| --------------- | -------- | ---------- |
| email           | EmailStr | Required   |
| password        | string   | 8–128      |
| employee_number | string   | 2–50       |
| first_name      | string   | 2–100      |
| last_name       | string   | 2–100      |

Example:

```json
{
  "email": "teacher@school.com",
  "password": "StrongPassword123",
  "employee_number": "EMP001",
  "first_name": "Aisha",
  "last_name": "Yusuf"
}
```

---

# 381. Teacher Update Schema

Optional fields:

```text
email
first_name
last_name
employee_number
is_active
```

No password-change field exists in the current TeacherUpdate schema.

Therefore teacher-password change is not part of this endpoint's current contract.

---

# 382. Teacher Response

Fields:

```text
id
user_id
school_id
employee_number
first_name
last_name
created_at
```

The response does not directly include:

```text
email
is_active
```

even though those values exist on the associated User.

---

# 383. Student Create Schema

Fields:

```text
admission_number
first_name
last_name
date_of_birth
gender
```

Validation:

```text
admission_number: 2–50
first_name: 2–100
last_name: 2–100
gender: max 20
```

`date_of_birth` and `gender` are optional.

---

# 384. Student Update Schema

Optional fields:

```text
admission_number
first_name
last_name
date_of_birth
gender
```

No authentication/password fields appear in the Student schema.

This is consistent with the current design where Students need not have User accounts.

---

# 385. Student Response

Fields:

```text
id
user_id
school_id
admission_number
first_name
last_name
date_of_birth
gender
created_at
```

`user_id` may be null.

---

# 386. Enrollment Create Schema

Fields:

```text
student_id
class_id
academic_session_id
```

All IDs must satisfy:

```text
> 0
```

---

# 387. Enrollment Update Schema

Optional fields:

```text
class_id
academic_session_id
```

The Student itself is not replaceable through the update schema.

---

# 388. Enrollment Response

Fields:

```text
id
student_id
class_id
academic_session_id
created_at
```

---

# 389. Teaching Assignment Create Schema

Fields:

```text
teacher_id
subject_id
class_id
academic_session_id
```

All IDs must be positive integers.

There is no TeachingAssignmentUpdate schema in the current backend.

---

# 390. Teaching Assignment Response

Fields:

```text
id
teacher_id
subject_id
class_id
academic_session_id
created_at
```

---

# 391. Assessment Create Schema

Fields:

```text
class_id
subject_id
academic_session_id
term_id
assessment_type
sequence
name
max_score
```

All IDs must be greater than zero.

`sequence` must be greater than zero.

`name` must contain 2–50 characters.

`max_score` must be greater than zero.

---

# 392. Assessment Cross-Field Validation

AssessmentCreate contains strict business validation.

Supported assessment types are:

```text
CA
EXAM
```

The value is converted to uppercase automatically.

---

# 393. Continuous Assessment Contract

For:

```text
assessment_type = CA
```

the following rules apply:

```text
sequence ∈ {1, 2, 3}
max_score = 10
```

Therefore the current fixed structure is:

```text
CA1 = 10
CA2 = 10
CA3 = 10
```

Total continuous assessment:

```text
30 marks
```

---

# 394. Examination Contract

For:

```text
assessment_type = EXAM
```

the schema requires:

```text
sequence = 1
max_score = 70
```

Therefore:

```text
CA1  10
CA2  10
CA3  10
Exam 70
---------
Total 100
```

This confirms the result engine's 100-mark structure directly from schema validation.

---

# 395. Invalid Assessment Types

Any value other than:

```text
CA
EXAM
```

fails validation.

For example:

```json
{
  "assessment_type": "TEST"
}
```

is invalid under the current schema.

---

# 396. Assessment Update Schema

The current update contract only allows:

```text
name
```

to be changed.

The following cannot be modified through AssessmentUpdate:

```text
class_id
subject_id
academic_session_id
term_id
assessment_type
sequence
max_score
```

This prevents structural changes to an existing Assessment.

---

# 397. Assessment Response

Fields:

```text
id
class_id
subject_id
academic_session_id
term_id
assessment_type
sequence
name
max_score
created_at
updated_at
```

---

# 398. Student Score Create Schema

Fields:

```text
student_id
assessment_id
score
```

Validation:

```text
student_id > 0
assessment_id > 0
score >= 0
```

The schema itself does not know the Assessment maximum.

The router performs the additional:

```text
score <= assessment.max_score
```

validation.

---

# 399. Student Score Update Schema

Field:

```text
score
```

Validation:

```text
score >= 0
```

Again, the router verifies the assessment maximum.

---

# 400. Student Score Response

Fields:

```text
id
student_id
assessment_id
score
created_at
updated_at
```

---

# 401. Attendance Create Schema

Fields:

```text
student_id
academic_session_id
term_id
school_days
days_present
days_absent
```

ID constraints:

```text
> 0
```

Attendance constraints:

```text
school_days > 0
days_present >= 0
days_absent >= 0
```

---

# 402. Attendance Cross-Field Validation

The schema requires:

```text
days_present <= school_days
days_absent <= school_days
days_present + days_absent = school_days
```

An inconsistent attendance payload therefore fails Pydantic validation before entering normal route business logic.

---

# 403. Attendance Update Schema

Optional fields:

```text
school_days
days_present
days_absent
```

The update schema validates each individual value.

Because partial updates may change only one component, the router subsequently validates the complete resulting attendance combination.

---

# 404. Attendance Response

Fields:

```text
id
student_id
academic_session_id
term_id
school_days
days_present
days_absent
created_at
updated_at
```

---

# 405. Term Report Comment Create Schema

Fields:

```text
student_id
academic_session_id
term_id
teacher_comment
principal_comment
```

IDs must be positive.

Both comments are optional.

Maximum length:

```text
1000 characters each
```

---

# 406. Term Report Comment Update

Optional fields:

```text
teacher_comment
principal_comment
```

Each may contain up to:

```text
1000 characters
```

---

# 407. Term Report Comment Response

Fields:

```text
id
student_id
academic_session_id
term_id
teacher_comment
principal_comment
created_at
updated_at
```

---

# 408. Single-Subject Result Response

Schema:

```text
ResultResponse
```

Fields:

```text
student_id
subject_id
class_id
academic_session_id
term_id
ca1
ca2
ca3
exam
total
percentage
grade
status
```

The score components, total, percentage, and grade may be null while a result is incomplete.

---

# 409. Attendance Summary Schema

Fields:

```text
school_days
days_present
days_absent
attendance_percentage
```

Used inside the Student term-result response.

---

# 410. Report Comment Summary Schema

Fields:

```text
teacher_comment
principal_comment
```

Both values may be null.

---

# 411. Subject Result Summary Schema

Fields:

```text
subject_id
subject_name
ca1
ca2
ca3
exam
total
grade
status
```

This represents one subject inside a complete term result.

---

# 412. Student Term Result Response

The term-result response includes:

```text
student_id
admission_number
student_name

class_id
academic_session_id
term_id

subjects

total_score
number_of_subjects
completed_subjects

average
overall_grade

result_status
class_position
class_size

remark

attendance
comments

closing_date
next_term_resumption_date
```

Several computed values may be null while the overall result remains incomplete.

---

# 413. Grading Scale Create Schema

Fields:

```text
grade
minimum_score
maximum_score
remark
```

Validation:

```text
grade: 1–10 characters
minimum_score: 0–100
maximum_score: 0–100
remark: max 255
```

---

# 414. Grading Range Validation

The schema requires:

```text
minimum_score <= maximum_score
```

This is enforced with a model-level validator.

The API layer additionally checks that the range does not overlap any other grading scale in that school.

---

# 415. Grading Scale Update Schema

Optional fields:

```text
grade
minimum_score
maximum_score
remark
```

Numeric values remain constrained to:

```text
0–100
```

---

# 416. Grading Scale Response

Fields:

```text
id
school_id
grade
minimum_score
maximum_score
remark
created_at
updated_at
```

---

# 417. Report Settings Create Schema

Fields and defaults:

```text
report_title = "Student Report Sheet"

show_class_position = true
show_class_size = true
show_attendance = true
show_teacher_comment = true
show_principal_comment = true
show_school_motto = true
show_school_logo = true
show_grading_remarks = true

principal_designation = "Principal"
```

---

# 418. Report Settings Validation

`report_title`:

```text
1–255 characters
```

`principal_designation`:

```text
1–100 characters
```

All display flags are Boolean.

---

# 419. Report Settings Update Schema

Every setting is optional.

The Flutter app can therefore update one preference without resending the entire settings object.

Example:

```json
{
  "show_class_position": false,
  "show_school_logo": true
}
```

---

# 420. Report Settings Response

Fields:

```text
id
school_id
report_title
show_class_position
show_class_size
show_attendance
show_teacher_comment
show_principal_comment
show_school_motto
show_school_logo
show_grading_remarks
principal_designation
created_at
updated_at
```

---

# 421. Report Sheet Subject Contract

Each subject contains:

```text
subject_id
subject_name
ca1
ca2
ca3
exam
total
grade
status
```

Scores and grades may be null for incomplete results.

---

# 422. Report Sheet Attendance

Fields:

```text
school_days
days_present
days_absent
attendance_percentage
```

The entire attendance object may be absent from the final report.

---

# 423. Report Sheet Comments

Fields:

```text
teacher_comment
principal_comment
```

The entire comments object may be null.

---

# 424. Report Sheet School Contract

Fields:

```text
school_id
school_name
email
phone
address
motto
logo_url
```

Most branding/contact fields may be null.

---

# 425. Report Sheet Settings Contract

Fields:

```text
report_title
show_class_position
show_class_size
show_attendance
show_teacher_comment
show_principal_comment
show_school_motto
show_school_logo
show_grading_remarks
principal_designation
```

---

# 426. Report Sheet Student Contract

Fields:

```text
student_id
admission_number
full_name
gender
date_of_birth
```

`gender` and `date_of_birth` may be null.

---

# 427. Report Sheet Class Contract

Fields:

```text
class_id
class_name
class_size
```

---

# 428. Report Sheet Term Contract

Fields:

```text
academic_session_id
academic_session_name
term_id
term_name
closing_date
next_term_resumption_date
```

Both dates may be null.

---

# 429. Report Performance Summary

Fields:

```text
total_score
number_of_subjects
completed_subjects
average
overall_grade
class_position
result_status
performance_remark
```

The following may be null:

```text
total_score
average
overall_grade
class_position
performance_remark
```

depending on result completeness and ranking eligibility.

---

# 430. Complete Student Report Sheet Contract

Top-level structure:

```json
{
  "school_info": {},
  "report_settings": {},
  "student": {},
  "class_info": {},
  "term_info": {},
  "subjects": [],
  "performance": {},
  "attendance": {},
  "comments": {}
}
```

`report_settings`, `attendance`, and `comments` may be null under the schema where applicable.

The report object is therefore structured for direct presentation in Flutter or conversion into a PDF/report view.

---

# 431. Result Publication Create Schema

Fields:

```text
class_id
academic_session_id
term_id
```

All must be positive integers.

Example:

```json
{
  "class_id": 3,
  "academic_session_id": 2,
  "term_id": 5
}
```

---

# 432. Result Publication Response

Fields:

```text
id
class_id
academic_session_id
term_id
status
published_by_user_id
published_at
updated_at
```

---

# 433. Subscription Plan Create Schema

Fields:

```text
name
description
price_per_term
max_students
is_active
```

Validation:

```text
name: 2–100 characters
price_per_term > 0
price_per_term: max 12 digits, 2 decimal places
max_students > 0 when provided
is_active: default true
```

---

# 434. Financial Decimal Contract

`price_per_term` uses:

```text
Decimal
```

rather than floating-point.

The schema permits:

```text
max_digits = 12
decimal_places = 2
```

This aligns the API contract with financial-safe monetary handling.

---

# 435. Subscription Plan Update Schema

Optional fields:

```text
name
description
price_per_term
max_students
is_active
```

The same validation rules apply when the fields are provided.

---

# 436. Subscription Plan Response

Fields:

```text
id
name
description
price_per_term
max_students
is_active
created_at
updated_at
```

---

# 437. Subscription Create Schema

Fields:

```text
subscription_plan_id
academic_session_id
term_id
```

All three IDs must be greater than zero.

Notice that:

```text
school_id
status
price
```

are not supplied by the client.

They are derived or controlled by the backend.

This is an important trust-boundary decision.

---

# 438. Subscription Status Update Schema

Field:

```text
status: string
```

The schema itself does not define an enum.

The router validates the allowed values:

```text
pending
active
expired
cancelled
```

---

# 439. Subscription Response

Fields:

```text
id
school_id
subscription_plan_id
academic_session_id
term_id
status
activated_at
expires_at
created_at
updated_at
```

`activated_at` and `expires_at` may be null.

---

# 440. Payment Initialization Request

Schema:

```text
PaymentInitializeRequest
```

Field:

```text
subscription_id: int
```

The schema does not currently apply `gt=0` validation to this field.

Invalid/nonexistent IDs are instead handled by the router/database lookup.

---

# 441. Payment Verification Request

Schema:

```text
PaymentVerifyRequest
```

Field:

```text
transaction_id: string
```

The provider transaction identifier is supplied after Flutterwave checkout.

---

# 442. Payment Initialization Response

Fields:

```text
payment_id
subscription_id
tx_ref
amount
currency
status
payment_link
```

`amount` is a Decimal.

`payment_link` is required in this initialization-response schema.

---

# 443. Payment Verification Response

Fields:

```text
payment_id
subscription_id
flutterwave_transaction_id
payment_status
subscription_status
verified_at
```

A successful response therefore confirms both payment and subscription state.

---

# 444. Payment Transaction Response

Fields:

```text
id
school_id
subscription_id
tx_ref
flutterwave_transaction_id
amount
currency
status
payment_provider
payment_link
verified_at
created_at
updated_at
```

Nullable fields include:

```text
flutterwave_transaction_id
payment_link
verified_at
```

---

# 445. Client-Supplied vs Server-Controlled Fields

A critical integration principle is distinguishing fields supplied by Flutter from fields controlled by the backend.

For example, when creating a Subscription, Flutter supplies:

```text
subscription_plan_id
academic_session_id
term_id
```

The backend controls:

```text
school_id
status
activated_at
```

For Payment initialization, Flutter supplies:

```text
subscription_id
```

The backend controls:

```text
amount
currency
tx_ref
payment_provider
status
```

This prevents the client from deciding commercial state.

---

# 446. Flutter Validation Strategy

The Flutter application should duplicate basic validation for user experience, but the backend remains authoritative.

Examples:

```text
Password minimum 8 characters
Required positive IDs
Score cannot be negative
School days must be positive
CA maximum is 10
Exam maximum is 70
Grade scores must be 0–100
```

Flutter validation improves usability.

Backend Pydantic validation provides security and consistency.

---

# 447. Flutter JSON Date Handling

The schema layer uses both:

```text
date
datetime
```

types.

Examples of `date`:

```text
date_of_birth
closing_date
next_term_resumption_date
```

Typical JSON representation:

```text
YYYY-MM-DD
```

Examples of `datetime`:

```text
created_at
updated_at
published_at
verified_at
activated_at
```

Flutter should deserialize these separately rather than treating every temporal field identically.

---

# 448. Nullable Field Handling

Many API values may legally be null.

Examples:

```text
school email
phone
address
motto
logo
student date of birth
student gender
comments
attendance
scores for incomplete results
grade
average
class position
activation timestamp
expiration timestamp
Flutterwave transaction ID
verification timestamp
```

Flutter models must therefore preserve nullable types rather than assuming all response properties exist.

---

# 449. 422 Validation Errors

Invalid Pydantic input normally produces:

```text
422 Unprocessable Entity
```

Examples include:

```text
invalid email
password shorter than minimum
negative score
invalid School slug
ID <= 0
CA sequence = 4
CA max_score != 10
EXAM max_score != 70
attendance arithmetic inconsistency
minimum grade score > maximum grade score
```

Flutter should distinguish validation failures from business-rule conflicts such as `409`.

---

# 450. Validation Layers

The backend performs validation at several levels.

## Pydantic schema validation

Examples:

```text
string lengths
numeric limits
email format
assessment structure
attendance arithmetic
grading ranges
```

## Router/business validation

Examples:

```text
tenant ownership
duplicate resources
subscription status
publication status
score <= assessment max
academic-session/term relationship
```

## Database constraints

Examples:

```text
uniqueness
foreign keys
one-to-one relationships
```

This layered validation design reduces dependence on any single validation mechanism.

---

# 451. Assessment Contract as a Core Academic Standard

The schema confirms that the current platform has a fixed academic scoring structure:

```text
CA1  = 10
CA2  = 10
CA3  = 10
Exam = 70
-------------
Total = 100
```

This is not merely a UI convention.

It is enforced at Pydantic validation level.

Changing this scoring architecture in the future would therefore require deliberate changes to:

```text
Assessment schemas
Result computation
Publication readiness
Tests
Flutter UI
Documentation
```

rather than only changing frontend labels.

---

# 452. Request Contract Principle

Flutter should send only fields defined by the relevant request schema.

For example, Student creation should send:

```json
{
  "admission_number": "ANIC/2026/001",
  "first_name": "Amina",
  "last_name": "Ibrahim",
  "date_of_birth": "2011-05-15",
  "gender": "Female"
}
```

It should not send:

```text
school_id
user_id
created_at
```

because those are not part of `StudentCreate`.

---

# 453. Response Contract Principle

Flutter models should be based on response schemas rather than database models.

For example:

```text
TeacherResponse
```

does not currently expose the associated User email even though the database contains it.

Therefore the frontend must not assume every database field will appear in API responses.

---

# 454. Schema/API Evolution Principle

Future backend changes should treat Pydantic response schemas as public API contracts.

Changes such as:

```text
renaming fields
removing fields
changing nullability
changing field type
changing score structure
```

may break existing Flutter clients.

Such changes should therefore be versioned or coordinated carefully once the mobile app enters production.

---

# 455. Schema Security Benefits

The schema layer currently provides:

```text
✓ Email validation where EmailStr is used
✓ Password length validation
✓ Positive resource IDs
✓ String-length limits
✓ School-slug validation
✓ Fixed assessment structure
✓ Non-negative scores
✓ Attendance consistency validation
✓ Grade range limits
✓ Decimal financial values
✓ Nullable-value declarations
✓ ORM serialization support
✓ Structured nested report output
```

---

# 456. API Contract Summary

The schema architecture creates a clean boundary:

```text
Flutter JSON
      ↓
Pydantic Request Schema
      ↓
Router / Business Rules
      ↓
SQLAlchemy Models
      ↓
PostgreSQL
      ↓
Pydantic Response Schema
      ↓
Flutter JSON
```

This provides a predictable interface between the mobile application and the frozen backend.
# 457. API Endpoint Reference

This section provides the consolidated REST API catalog for the frozen backend.

The FastAPI application is configured as:

```text
Title: Student Result Management API
Version: 1.0.0
```

Interactive API documentation is available when enabled through configuration:

```text
/docs
/redoc
/openapi.json
```

---

# 458. API Authorization Legend

The endpoint tables use the following authorization labels.

| Label          | Meaning                                    |
| -------------- | ------------------------------------------ |
| Public         | No JWT required                            |
| Authenticated  | Any valid active authenticated User        |
| Platform Admin | Admin account with `school_id = null`      |
| School Admin   | Admin account linked to a School           |
| Admin          | Either Platform Admin or School Admin      |
| Teacher        | Authenticated teacher User                 |
| Student        | Legacy/reserved authenticated student User |

For ordinary protected requests, the client sends:

```http
Authorization: Bearer <access_token>
```

---

# 459. Root and Health Endpoints

| Method | Endpoint           | Authorization | Purpose                  |
| ------ | ------------------ | ------------- | ------------------------ |
| GET    | `/`                | Public        | API availability message |
| GET    | `/health`          | Public        | Application health       |
| GET    | `/health/database` | Public        | Database connectivity    |

## Root response

```json
{
  "message": "Student Result Management API is running"
}
```

## Health response

```json
{
  "status": "healthy"
}
```

## Database health response

```json
{
  "status": "healthy",
  "database": "connected"
}
```

The database health endpoint executes:

```sql
SELECT 1
```

against the configured PostgreSQL connection.

---

# 460. Authentication Endpoints

Base route:

```text
/api/auth
```

| Method | Endpoint          | Authorization | Request        | Response        |
| ------ | ----------------- | ------------- | -------------- | --------------- |
| POST   | `/api/auth/login` | Public        | `LoginRequest` | `TokenResponse` |

Purpose:

```text
Authenticate User
      ↓
Verify password
      ↓
Validate User active state
      ↓
Validate School active state when school-bound
      ↓
Issue JWT
```

---

# 461. Current User Endpoint

Base route:

```text
/api/users
```

| Method | Endpoint        | Authorization | Purpose                                       |
| ------ | --------------- | ------------- | --------------------------------------------- |
| GET    | `/api/users/me` | Authenticated | Return current User identity and account type |

Response includes:

```text
id
email
role
account_type
school_id
is_active
```

For Admin users:

```text
school_id = null
→ account_type = platform_admin
```

and:

```text
school_id != null
→ account_type = school_admin
```

---

# 462. Authorization Test Endpoints

These routes exist primarily as authorization/test endpoints.

| Method | Endpoint             | Authorization |
| ------ | -------------------- | ------------- |
| GET    | `/api/admin/test`    | Admin         |
| GET    | `/api/teachers/test` | Teacher       |
| GET    | `/api/students/test` | Student       |

These are not core production business endpoints.

The Student test route is especially considered legacy/reserved because the current Student academic architecture does not require Student login accounts.

---

# 463. School Endpoints

Base route:

```text
/api/schools
```

| Method | Endpoint          | Authorization | Purpose                                |
| ------ | ----------------- | ------------- | -------------------------------------- |
| POST   | `/api/schools`    | Public        | Register School and first School Admin |
| GET    | `/api/schools/me` | School Admin  | Retrieve own School                    |
| PATCH  | `/api/schools/me` | School Admin  | Update own School                      |

School registration creates:

```text
School
+
Initial School Administrator User
```

as part of the SaaS onboarding flow.

---

# 464. Administrator Management Endpoints

Base route:

```text
/api/admin-management
```

## Platform administrators

| Method | Endpoint                                                  | Authorization  | Purpose                            |
| ------ | --------------------------------------------------------- | -------------- | ---------------------------------- |
| POST   | `/api/admin-management/platform-admins`                   | Platform Admin | Create Platform Admin              |
| GET    | `/api/admin-management/platform-admins`                   | Platform Admin | List Platform Admins               |
| PATCH  | `/api/admin-management/platform-admins/{admin_id}/status` | Platform Admin | Activate/deactivate Platform Admin |

## School administrators

| Method | Endpoint                                                | Authorization | Purpose                                    |
| ------ | ------------------------------------------------------- | ------------- | ------------------------------------------ |
| POST   | `/api/admin-management/school-admins`                   | Admin         | Create School Admin                        |
| GET    | `/api/admin-management/school-admins`                   | Admin         | List permitted School Admins               |
| PATCH  | `/api/admin-management/school-admins/{admin_id}/status` | Admin         | Activate/deactivate permitted School Admin |

School Admin operations are restricted to the authenticated admin's own School.

Platform Admins may manage School Admins across Schools.

---

# 465. Academic Session Endpoints

Base route:

```text
/api/academic-sessions
```

| Method | Endpoint                              | Authorization                   | Purpose                  |
| ------ | ------------------------------------- | ------------------------------- | ------------------------ |
| POST   | `/api/academic-sessions`              | School Admin                    | Create session           |
| GET    | `/api/academic-sessions`              | Authenticated school-bound user | List sessions            |
| GET    | `/api/academic-sessions/{session_id}` | Authenticated school-bound user | Retrieve session         |
| PATCH  | `/api/academic-sessions/{session_id}` | School Admin                    | Update session           |
| DELETE | `/api/academic-sessions/{session_id}` | School Admin                    | Delete session when safe |

Academic Sessions are tenant-scoped.

Only one Session may be current per School.

---

# 466. Term Endpoints

Base route:

```text
/api/terms
```

| Method | Endpoint               | Authorization                   | Purpose               |
| ------ | ---------------------- | ------------------------------- | --------------------- |
| POST   | `/api/terms`           | School Admin                    | Create Term           |
| GET    | `/api/terms`           | Authenticated school-bound user | List Terms            |
| GET    | `/api/terms/{term_id}` | Authenticated school-bound user | Retrieve Term         |
| PATCH  | `/api/terms/{term_id}` | School Admin                    | Update Term           |
| DELETE | `/api/terms/{term_id}` | School Admin                    | Delete Term when safe |

Terms belong to Academic Sessions.

---

# 467. Class Endpoints

Base route:

```text
/api/classes
```

| Method | Endpoint                  | Authorization                   | Purpose                |
| ------ | ------------------------- | ------------------------------- | ---------------------- |
| POST   | `/api/classes`            | School Admin                    | Create Class           |
| GET    | `/api/classes`            | Authenticated school-bound user | List Classes           |
| GET    | `/api/classes/{class_id}` | Authenticated school-bound user | Retrieve Class         |
| PATCH  | `/api/classes/{class_id}` | School Admin                    | Update Class           |
| DELETE | `/api/classes/{class_id}` | School Admin                    | Delete Class when safe |

Class codes are unique within a School.

---

# 468. Subject Endpoints

Base route:

```text
/api/subjects
```

| Method | Endpoint                     | Authorization                   | Purpose                  |
| ------ | ---------------------------- | ------------------------------- | ------------------------ |
| POST   | `/api/subjects`              | School Admin                    | Create Subject           |
| GET    | `/api/subjects`              | Authenticated school-bound user | List Subjects            |
| GET    | `/api/subjects/{subject_id}` | Authenticated school-bound user | Retrieve Subject         |
| PATCH  | `/api/subjects/{subject_id}` | School Admin                    | Update Subject           |
| DELETE | `/api/subjects/{subject_id}` | School Admin                    | Delete Subject when safe |

Subject names and codes are unique per School.

---

# 469. Teacher Endpoints

Base route:

```text
/api/teachers
```

| Method | Endpoint                     | Authorization                   | Purpose                        |
| ------ | ---------------------------- | ------------------------------- | ------------------------------ |
| POST   | `/api/teachers`              | School Admin                    | Create Teacher and login User  |
| GET    | `/api/teachers`              | Authenticated school-bound user | List Teachers                  |
| GET    | `/api/teachers/{teacher_id}` | Authenticated school-bound user | Retrieve Teacher               |
| PATCH  | `/api/teachers/{teacher_id}` | School Admin                    | Update Teacher                 |
| DELETE | `/api/teachers/{teacher_id}` | School Admin                    | Delete Teacher where permitted |

Teacher creation creates both:

```text
User
+
Teacher Profile
```

linked one-to-one.

---

# 470. Student Endpoints

Base route:

```text
/api/students
```

| Method | Endpoint                     | Authorization | Purpose                  |
| ------ | ---------------------------- | ------------- | ------------------------ |
| POST   | `/api/students`              | School Admin  | Create Student           |
| GET    | `/api/students`              | School Admin  | List Students            |
| GET    | `/api/students/{student_id}` | School Admin  | Retrieve Student         |
| PATCH  | `/api/students/{student_id}` | School Admin  | Update Student           |
| DELETE | `/api/students/{student_id}` | School Admin  | Delete Student when safe |

Students are academic records and are not required to have login accounts.

---

# 471. Enrollment Endpoints

Base route:

```text
/api/enrollments
```

| Method | Endpoint                           | Authorization | Purpose                           |
| ------ | ---------------------------------- | ------------- | --------------------------------- |
| POST   | `/api/enrollments`                 | School Admin  | Enroll Student into Class/session |
| GET    | `/api/enrollments`                 | School Admin  | List Enrollments                  |
| GET    | `/api/enrollments/{enrollment_id}` | School Admin  | Retrieve Enrollment               |
| PATCH  | `/api/enrollments/{enrollment_id}` | School Admin  | Change Class/session              |
| DELETE | `/api/enrollments/{enrollment_id}` | School Admin  | Delete Enrollment                 |

Enrollment mutations are protected by published-result locks.

---

# 472. Teaching Assignment Endpoints

Base route:

```text
/api/teaching-assignments
```

| Method | Endpoint                                    | Authorization | Purpose                                 |
| ------ | ------------------------------------------- | ------------- | --------------------------------------- |
| POST   | `/api/teaching-assignments`                 | School Admin  | Assign Teacher to Subject/Class/session |
| GET    | `/api/teaching-assignments`                 | School Admin  | List assignments                        |
| GET    | `/api/teaching-assignments/{assignment_id}` | School Admin  | Retrieve assignment                     |
| DELETE | `/api/teaching-assignments/{assignment_id}` | School Admin  | Delete assignment                       |

There is currently no update endpoint.

To change an assignment:

```text
Delete old assignment
        ↓
Create replacement
```

---

# 473. Assessment Endpoints

Base route:

```text
/api/assessments
```

| Method | Endpoint                           | Authorization | Subscription | Publication Lock |
| ------ | ---------------------------------- | ------------- | ------------ | ---------------- |
| POST   | `/api/assessments`                 | School Admin  | Required     | Required         |
| GET    | `/api/assessments`                 | School Admin  | No           | No               |
| GET    | `/api/assessments/{assessment_id}` | School Admin  | No           | No               |
| PATCH  | `/api/assessments/{assessment_id}` | School Admin  | Required     | Required         |
| DELETE | `/api/assessments/{assessment_id}` | School Admin  | Required     | Required         |

Assessment structure:

```text
CA1  = 10
CA2  = 10
CA3  = 10
EXAM = 70
```

---

# 474. Student Score Endpoints

Base route:

```text
/api/student-scores
```

| Method | Endpoint                         | Authorization | Subscription | Publication Lock |
| ------ | -------------------------------- | ------------- | ------------ | ---------------- |
| POST   | `/api/student-scores`            | School Admin  | Required     | Required         |
| GET    | `/api/student-scores`            | School Admin  | No           | No               |
| GET    | `/api/student-scores/{score_id}` | School Admin  | No           | No               |
| PATCH  | `/api/student-scores/{score_id}` | School Admin  | Required     | Required         |
| DELETE | `/api/student-scores/{score_id}` | School Admin  | Required     | Required         |

Score entry additionally requires valid Student Enrollment.

---

# 475. Student Attendance Endpoints

Base route:

```text
/api/student-attendance
```

| Method | Endpoint                                  | Authorization | Subscription | Publication Lock |
| ------ | ----------------------------------------- | ------------- | ------------ | ---------------- |
| POST   | `/api/student-attendance`                 | School Admin  | Required     | Required         |
| GET    | `/api/student-attendance`                 | School Admin  | No           | No               |
| GET    | `/api/student-attendance/{attendance_id}` | School Admin  | No           | No               |
| PATCH  | `/api/student-attendance/{attendance_id}` | School Admin  | Required     | Required         |
| DELETE | `/api/student-attendance/{attendance_id}` | School Admin  | Required     | Required         |

Attendance satisfies:

```text
days_present + days_absent = school_days
```

---

# 476. Term Report Comment Endpoints

Base route:

```text
/api/term-report-comments
```

| Method | Endpoint                                 | Authorization | Subscription | Publication Lock |
| ------ | ---------------------------------------- | ------------- | ------------ | ---------------- |
| POST   | `/api/term-report-comments`              | School Admin  | Required     | Required         |
| GET    | `/api/term-report-comments`              | School Admin  | No           | No               |
| GET    | `/api/term-report-comments/{comment_id}` | School Admin  | No           | No               |
| PATCH  | `/api/term-report-comments/{comment_id}` | School Admin  | Required     | Required         |
| DELETE | `/api/term-report-comments/{comment_id}` | School Admin  | Required     | Required         |

---

# 477. Single-Subject Result Endpoint

Base route:

```text
/api/results
```

| Method | Endpoint                            | Authorization | Purpose                    |
| ------ | ----------------------------------- | ------------- | -------------------------- |
| GET    | `/api/results/student/{student_id}` | School Admin  | Compute one Subject result |

Query parameters:

```text
subject_id
term_id
academic_session_id
```

Response schema:

```text
ResultResponse
```

---

# 478. Term Result Endpoint

Base route:

```text
/api/term-results
```

| Method | Endpoint                                 | Authorization | Purpose                              |
| ------ | ---------------------------------------- | ------------- | ------------------------------------ |
| GET    | `/api/term-results/student/{student_id}` | School Admin  | Compute complete Student term result |

Parameters:

```text
academic_session_id
term_id
```

The response contains:

```text
Subject results
Overall average
Overall grade
Class position
Class size
Attendance
Comments
Term dates
```

---

# 479. Grading Scale Endpoints

Base route:

```text
/api/grading-scales
```

| Method | Endpoint                                 | Authorization                   | Purpose            |
| ------ | ---------------------------------------- | ------------------------------- | ------------------ |
| POST   | `/api/grading-scales`                    | School Admin                    | Create grade range |
| GET    | `/api/grading-scales`                    | Authenticated school-bound user | List grade ranges  |
| GET    | `/api/grading-scales/{grading_scale_id}` | Authenticated school-bound user | Retrieve range     |
| PUT    | `/api/grading-scales/{grading_scale_id}` | School Admin                    | Update grade range |
| DELETE | `/api/grading-scales/{grading_scale_id}` | School Admin                    | Delete range       |

Note that this resource uses:

```http
PUT
```

for updates rather than PATCH.

---

# 480. Report Settings Endpoints

Base route:

```text
/api/report-settings
```

| Method | Endpoint               | Authorization | Purpose                              |
| ------ | ---------------------- | ------------- | ------------------------------------ |
| GET    | `/api/report-settings` | School Admin  | Retrieve/default-initialize settings |
| POST   | `/api/report-settings` | School Admin  | Explicitly create settings           |
| PATCH  | `/api/report-settings` | School Admin  | Update settings                      |

There is no settings ID in the route because ReportSettings is a one-to-one School configuration.

---

# 481. Report Sheet Endpoint

Base route:

```text
/api/report-sheets
```

| Method | Endpoint                                  | Authorization | Purpose                                   |
| ------ | ----------------------------------------- | ------------- | ----------------------------------------- |
| GET    | `/api/report-sheets/student/{student_id}` | School Admin  | Retrieve live or published Student report |

Parameters:

```text
academic_session_id
term_id
```

Data-source behavior:

```text
Published snapshot exists
        ↓
Return snapshot
```

otherwise:

```text
Build current live report
```

---

# 482. Result Publication Endpoints

Base route:

```text
/api/result-publications
```

| Method | Endpoint                                           | Authorization | Subscription | Purpose                  |
| ------ | -------------------------------------------------- | ------------- | ------------ | ------------------------ |
| POST   | `/api/result-publications`                         | School Admin  | Required     | Publish Class results    |
| GET    | `/api/result-publications`                         | School Admin  | No           | List publications        |
| GET    | `/api/result-publications/{publication_id}`        | School Admin  | No           | Retrieve publication     |
| PATCH  | `/api/result-publications/{publication_id}/reopen` | School Admin  | Required     | Reopen published results |

Publication requires:

```text
Students enrolled
Assessments configured
All results complete
Active subscription
```

---

# 483. Subscription Plan Endpoints

Base route:

```text
/api/subscription-plans
```

| Method | Endpoint                            | Authorization  | Purpose               |
| ------ | ----------------------------------- | -------------- | --------------------- |
| POST   | `/api/subscription-plans`           | Platform Admin | Create Plan           |
| GET    | `/api/subscription-plans`           | Authenticated  | List visible Plans    |
| GET    | `/api/subscription-plans/{plan_id}` | Authenticated  | Retrieve visible Plan |
| PATCH  | `/api/subscription-plans/{plan_id}` | Platform Admin | Update Plan           |

Inactive plans are hidden from non-platform users.

---

# 484. Subscription Endpoints

Base route:

```text
/api/subscriptions
```

| Method | Endpoint                                      | Authorization  | Purpose                         |
| ------ | --------------------------------------------- | -------------- | ------------------------------- |
| POST   | `/api/subscriptions`                          | School Admin   | Create term Subscription        |
| GET    | `/api/subscriptions/me`                       | School Admin   | List own School subscriptions   |
| GET    | `/api/subscriptions/me/{subscription_id}`     | School Admin   | Retrieve own Subscription       |
| GET    | `/api/subscriptions`                          | Platform Admin | List all platform subscriptions |
| PATCH  | `/api/subscriptions/{subscription_id}/status` | Platform Admin | Change Subscription status      |

New subscriptions start as:

```text
pending
```

---

# 485. Payment Endpoints

Base route:

```text
/api/payments
```

| Method | Endpoint                            | Authorization                      | Purpose                        |
| ------ | ----------------------------------- | ---------------------------------- | ------------------------------ |
| POST   | `/api/payments/initialize`          | School Admin                       | Initialize Flutterwave payment |
| POST   | `/api/payments/{payment_id}/verify` | School Admin                       | Verify provider transaction    |
| GET    | `/api/payments`                     | School Admin                       | List own payment transactions  |
| GET    | `/api/payments/{payment_id}`        | School Admin                       | Retrieve own payment           |
| POST   | `/api/payments/webhook`             | Flutterwave webhook authentication | Provider callback              |

The webhook deliberately does not use JWT.

---

# 486. Endpoint Groups by Actor

## Public

```text
GET  /
GET  /health
GET  /health/database

POST /api/auth/login
POST /api/schools

POST /api/payments/webhook
    └── cryptographically authenticated by Flutterwave
```

---

# 487. Platform Administrator Endpoints

Platform Administrators manage platform-wide functions including:

```text
Platform Admin accounts
School Admin accounts across tenants
Subscription Plans
All Subscriptions
Manual Subscription state changes
```

Principal routes include:

```text
/api/admin-management/platform-admins
/api/admin-management/school-admins
/api/subscription-plans
/api/subscriptions
```

---

# 488. School Administrator Endpoints

School Administrators are the principal operational users of the SaaS.

They manage:

```text
School profile
Other School Admins
Academic Sessions
Terms
Classes
Subjects
Teachers
Students
Enrollments
Teaching Assignments
Assessments
Scores
Attendance
Comments
Grading
Reports
Publications
Subscriptions
Payments
```

Every school-scoped operation derives or validates tenant ownership against the authenticated School.

---

# 489. Teacher API Exposure

Teacher login support exists through the User/Teacher architecture.

However, the current major academic administration routers are predominantly School Admin controlled.

The explicit Teacher role route currently included is:

```http
GET /api/teachers/test
```

The backend therefore has the role foundation for future Teacher-specific academic workflows even though full teacher-facing result-entry endpoints are not yet exposed in the frozen version.

---

# 490. Student API Exposure

The current Student entity is primarily an academic record.

Student login is intentionally decoupled from Student creation.

The legacy authorization test endpoint remains:

```http
GET /api/students/test
```

but Student-facing portal functionality is not a current core backend feature.

---

# 491. HTTP Method Conventions

The backend generally uses:

```text
POST
→ create or trigger action

GET
→ retrieve

PATCH
→ partial update

DELETE
→ delete

PUT
→ grading scale update
```

Special action-style endpoints include:

```text
PATCH /result-publications/{id}/reopen
PATCH /subscriptions/{id}/status
PATCH /admin-management/.../{id}/status
POST  /payments/{id}/verify
```

---

# 492. HTTP Status Convention

Common success codes include:

| Code | Meaning                            |
| ---- | ---------------------------------- |
| 200  | Successful retrieval/update/action |
| 201  | Resource created                   |
| 204  | Successful deletion                |

Common error codes include:

| Code | Meaning                                     |
| ---- | ------------------------------------------- |
| 400  | Invalid business relationship/data          |
| 401  | Authentication failure                      |
| 403  | Authenticated but not permitted             |
| 404  | Resource unavailable within permitted scope |
| 409  | Resource/business-state conflict            |
| 422  | Pydantic/input validation failure           |
| 500  | Internal processing/configuration problem   |
| 502  | External Flutterwave/provider failure       |

---

# 493. Tenant-Safe 404 Behavior

For many school-owned resources, requesting another School's resource behaves as:

```text
404 Not Found
```

rather than revealing:

```text
403 — resource exists but belongs to another School
```

This prevents resource enumeration across tenants.

---

# 494. 403 Commercial Access Behavior

Academic term mutations without an active Subscription return:

```text
403 Forbidden
```

with:

```text
An active subscription is required for this academic term
```

This is an entitlement failure rather than a resource-not-found condition.

---

# 495. 409 Publication Lock Behavior

Attempts to alter protected academic data while results are published return:

```text
409 Conflict
```

Conceptually:

```text
Requested mutation is valid
but
current publication state forbids it
```

The administrator must reopen the result first.

---

# 496. API Resource Hierarchy

The practical resource hierarchy is:

```text
School
│
├── Users / Administrators
├── Academic Sessions
│   └── Terms
│
├── Classes
├── Subjects
├── Teachers
├── Students
│   └── Enrollments
│
├── Teaching Assignments
│
├── Assessments
│   └── Student Scores
│
├── Attendance
├── Report Comments
├── Grading Scales
├── Report Settings
├── Results
│   ├── Subject Results
│   ├── Term Results
│   ├── Report Sheets
│   └── Publications / Snapshots
│
└── Commercial
    ├── Subscriptions
    └── Payments
```

Global platform resources include:

```text
Platform Administrators
Subscription Plans
Cross-school Subscription administration
```

---

# 497. Recommended Flutter API Modules

The Flutter application should organize its API client into modules aligned with backend domains.

Suggested structure:

```text
ApiClient
│
├── AuthApi
├── UserApi
├── SchoolApi
├── AdminApi
│
├── AcademicSessionApi
├── TermApi
├── ClassApi
├── SubjectApi
│
├── TeacherApi
├── StudentApi
├── EnrollmentApi
├── TeachingAssignmentApi
│
├── AssessmentApi
├── ScoreApi
├── AttendanceApi
├── CommentApi
│
├── ResultApi
├── ReportApi
├── PublicationApi
│
├── GradingApi
├── ReportSettingsApi
│
├── SubscriptionPlanApi
├── SubscriptionApi
└── PaymentApi
```

This keeps mobile networking code aligned with backend domains.

---

# 498. Recommended Flutter Authentication Interceptor

After login:

```text
access_token
```

should be stored securely by the Flutter application.

Protected requests should automatically attach:

```http
Authorization: Bearer <access_token>
```

using a shared API/network interceptor rather than adding the token separately in every screen.

---

# 499. `/api/users/me` as Session Bootstrap

After authentication, Flutter should call:

```http
GET /api/users/me
```

to determine:

```text
user id
role
account_type
school_id
is_active
```

The application can then route the user appropriately.

Example:

```text
Login
  ↓
Receive JWT
  ↓
GET /api/users/me
  ↓
account_type?
  ├── platform_admin → Platform Dashboard
  ├── school_admin   → School Dashboard
  └── teacher        → Teacher Experience
```

---

# 500. OpenAPI Support

FastAPI automatically exposes an OpenAPI definition when documentation is enabled:

```text
/openapi.json
```

This can be valuable during Flutter development for:

```text
Endpoint discovery
Request-field verification
Response-model verification
Testing
Potential API-client generation
```

However, the manually maintained backend documentation remains valuable because it explains business rules that an automatically generated OpenAPI schema cannot fully express.

---

# 501. API Documentation Availability

Documentation routes are controlled through:

```text
settings.enable_docs
```

When enabled:

```text
/docs
/redoc
/openapi.json
```

are available.

When disabled:

```text
docs_url = null
redoc_url = null
openapi_url = null
```

This allows public production deployments to disable interactive API documentation if desired.

---

# 502. CORS Behavior

CORS is enabled only when configured origins exist.

Configured origins come from:

```text
settings.cors_origin_list
```

When enabled:

```text
allow_credentials = true
allow_methods = ["*"]
allow_headers = ["*"]
```

Only configured origins are accepted.

For the Flutter native Android application, browser CORS is generally not the primary transport restriction, but it remains relevant for web-based clients and Flutter Web.

---

# 503. Trusted Host Protection

The application can use Starlette:

```text
TrustedHostMiddleware
```

based on:

```text
settings.allowed_host_list
```

If the configuration is:

```text
["*"]
```

the middleware is not installed.

For production, the recommended configuration is the backend's real host/domain rather than unrestricted hosts.

---

# 504. Router Registration Integrity

The running application registers all of the following routers:

```text
Authentication
Users
Admin Management
Authorization Tests

Subjects
Teachers
Teaching Assignments

Classes
Academic Sessions
Students
Enrollments
Terms

Assessments
Student Scores

Subject Results
Term Results

Attendance
Term Report Comments

Report Sheets
Schools

Subscription Plans
Subscriptions
Payments

Result Publications

Grading Scales
Report Settings
```

This confirms the previously documented domain modules are wired into the actual FastAPI application.

---

# 505. API Version

The frozen backend currently identifies itself as:

```text
1.0.0
```

through FastAPI configuration:

```python
version="1.0.0"
```

This version should be considered the initial documented backend contract for mobile integration.

---

# 506. Versioning Recommendation

The current routes do not contain a URL version prefix such as:

```text
/api/v1/
```

Instead, the application currently uses:

```text
/api/
```

For the first Flutter release this is acceptable because the frontend and backend are being developed together.

Once external production clients depend on the API, breaking changes should either:

```text
preserve backward compatibility
```

or introduce explicit versioning such as:

```text
/api/v2/
```

rather than silently altering existing contracts.

---

# 507. Complete Backend API Flow

The complete API lifecycle can now be represented as:

```text
PUBLIC
│
├── Register School
└── Login
      ↓
JWT
      ↓
GET /api/users/me
      ↓
Determine Account Type
      ↓
SCHOOL ADMIN
      ↓
Academic Setup
      ↓
Students / Teachers
      ↓
Enrollment / Assignment
      ↓
Subscription
      ↓
Flutterwave Payment
      ↓
Subscription Active
      ↓
Assessments
      ↓
Scores
      ↓
Attendance / Comments
      ↓
Result Calculation
      ↓
Report Preview
      ↓
Publication
      ↓
Published Snapshot
      ↓
Historical Retrieval
```

Platform management operates alongside this flow:

```text
PLATFORM ADMIN
│
├── Platform Admin Management
├── Cross-School Admin Management
├── Subscription Plan Management
├── All Subscription Monitoring
└── Manual Subscription Status Administration
```

---

# 508. Endpoint Catalog Summary

The API has clear separation between:

```text
Public onboarding
Authentication
Platform administration
School administration
Academic configuration
People management
Assessment processing
Result computation
Report generation
Publication integrity
Commercial subscriptions
Payment processing
```

The endpoint design consistently combines:

```text
JWT authentication
Role authorization
Tenant isolation
Business validation
Subscription enforcement
Publication locking
Database constraints
```

to provide the backend contract that the Flutter mobile application will consume.
# 509. Configuration Architecture

The backend uses a centralized configuration model built with:

```text
pydantic-settings
```

The main configuration object is:

```text
app.core.config.settings
```

Application, database, authentication, CORS, trusted-host, and Flutterwave settings are all read through this single configuration source.

This avoids maintaining separate configuration paths for FastAPI, SQLAlchemy, Alembic, and payment integrations.

---

# 510. Settings Source

The configuration class extends:

```python
BaseSettings
```

and loads environment variables from:

```text
.env
```

using:

```text
UTF-8
```

encoding.

Unknown additional environment variables are ignored.

Conceptually:

```text
Operating-system environment
        +
.env
        ↓
Settings
        ↓
Application components
```

---

# 511. Application Environment Variables

The application configuration includes:

```text
APP_ENV
ENABLE_DOCS
CORS_ORIGINS
ALLOWED_HOSTS
```

Defaults are:

```text
APP_ENV=development
ENABLE_DOCS=true
CORS_ORIGINS=
ALLOWED_HOSTS=*
```

---

# 512. `APP_ENV`

Configuration field:

```text
app_env
```

Default:

```text
development
```

This currently provides an environment label.

Typical future values might include:

```text
development
testing
staging
production
```

The reviewed code does not currently contain environment-specific branching based directly on `app_env`, so it should presently be treated primarily as environment metadata.

---

# 513. API Documentation Configuration

Configuration field:

```text
enable_docs
```

Default:

```text
true
```

When enabled, FastAPI exposes:

```text
/docs
/redoc
/openapi.json
```

When disabled, all three are unavailable.

Production environments may choose:

```text
ENABLE_DOCS=false
```

if interactive documentation should not be publicly exposed.

---

# 514. CORS Configuration

Environment variable:

```text
CORS_ORIGINS
```

stores browser origins as a comma-separated string.

Example:

```env
CORS_ORIGINS=https://admin.example.com,https://portal.example.com
```

The configuration property:

```text
cors_origin_list
```

converts this string into:

```text
[
  "https://admin.example.com",
  "https://portal.example.com"
]
```

Whitespace and empty entries are removed.

---

# 515. Empty CORS Configuration

If:

```env
CORS_ORIGINS=
```

the parsed value becomes:

```text
[]
```

and CORS middleware is not added to the FastAPI application.

This is suitable for a native Flutter Android application because browser-origin CORS enforcement does not normally apply to native mobile HTTP requests.

---

# 516. Trusted Host Configuration

Environment variable:

```text
ALLOWED_HOSTS
```

also accepts comma-separated values.

Example:

```env
ALLOWED_HOSTS=api.example.com,www.api.example.com
```

The parsed result is:

```text
[
  "api.example.com",
  "www.api.example.com"
]
```

---

# 517. Trusted Host Development Default

The default configuration is:

```env
ALLOWED_HOSTS=*
```

When the parsed list equals:

```text
["*"]
```

TrustedHostMiddleware is not installed.

This is suitable for local development.

Production should normally use the actual API hostname instead.

---

# 518. Database Configuration

Required environment variable:

```text
DATABASE_URL
```

Example format:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/DATABASE_NAME
```

The backend uses:

```text
PostgreSQL
+
psycopg
+
SQLAlchemy
```

---

# 519. Current Local Development Database Example

The established development environment uses a connection of the form:

```text
postgresql+psycopg://student_api:********@localhost:5432/student_result_db
```

Credentials should remain in the local `.env` file and must not be committed to source control.

---

# 520. SQLAlchemy Engine

The application creates its SQLAlchemy engine using:

```python
create_engine(
    settings.database_url,
    pool_pre_ping=True,
)
```

`pool_pre_ping=True` causes SQLAlchemy to test pooled connections before reuse.

This helps detect stale or disconnected database connections.

---

# 521. SQLAlchemy Session Factory

The backend configures:

```text
SessionLocal
```

with:

```text
autocommit = false
autoflush = false
```

and binds it to the application Engine.

---

# 522. Database Dependency

FastAPI routes access the database through:

```text
get_db()
```

The lifecycle is:

```text
Create Session
      ↓
Yield Session to request
      ↓
Route performs database work
      ↓
Close Session
```

The `finally` block ensures the Session is closed after request processing.

---

# 523. Declarative ORM Base

SQLAlchemy models inherit from:

```text
Base
```

defined as:

```python
class Base(DeclarativeBase):
    pass
```

This metadata is also used by Alembic for schema comparison.

---

# 524. JWT Configuration

Authentication configuration includes:

```text
JWT_SECRET_KEY
JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES
```

The `.env.example` defaults to:

```env
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

`JWT_SECRET_KEY` has no safe production default and must be supplied.

---

# 525. JWT Secret Requirement

The example configuration contains:

```env
JWT_SECRET_KEY=replace-with-a-secure-random-secret
```

This value is only a placeholder.

Production must replace it with a long cryptographically random secret.

A committed or predictable JWT secret would compromise all authentication tokens.

---

# 526. Access Token Lifetime

Default token lifetime:

```text
60 minutes
```

controlled through:

```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

This can be changed without source-code modification.

---

# 527. Flutterwave Configuration

The payment integration uses:

```text
FLUTTERWAVE_SECRET_KEY
FLUTTERWAVE_SECRET_HASH
FLUTTERWAVE_REDIRECT_URL
```

Default values in `.env.example` are empty.

This means payment operations cannot operate correctly until real provider credentials/configuration are supplied.

---

# 528. Flutterwave Secret Key

Environment variable:

```text
FLUTTERWAVE_SECRET_KEY
```

is used by backend-to-Flutterwave API requests.

It must never be exposed to:

```text
Flutter application
browser frontend
public repository
API response
```

Only the backend should possess this secret.

---

# 529. Flutterwave Secret Hash

Environment variable:

```text
FLUTTERWAVE_SECRET_HASH
```

is used to authenticate incoming Flutterwave webhooks.

It participates in both:

```text
verif-hash comparison
```

and:

```text
HMAC webhook verification
```

---

# 530. Flutterwave Redirect URL

Environment variable:

```text
FLUTTERWAVE_REDIRECT_URL
```

is sent during Flutterwave checkout initialization.

This URL should point to the intended post-payment redirect location for the deployed product.

---

# 531. Example Environment File

The repository contains:

```text
.env.example
```

with safe placeholders only.

Its purpose is to document required configuration without exposing real credentials.

A developer can create a local environment file with:

```bash
cp .env.example .env
```

and then replace placeholder values.

---

# 532. `.env` Security

The actual:

```text
.env
```

file is intentionally ignored by Git.

The `.gitignore` rules include:

```text
.env
.env.*
!.env.example
```

Therefore:

```text
.env.example
```

is tracked, but private environment files are not.

---

# 533. Recommended Local `.env`

A development `.env` should contain values similar to:

```env
APP_ENV=development
ENABLE_DOCS=true

CORS_ORIGINS=
ALLOWED_HOSTS=*

DATABASE_URL=postgresql+psycopg://student_api:YOUR_PASSWORD@localhost:5432/student_result_db

JWT_SECRET_KEY=YOUR_LONG_RANDOM_SECRET
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FLUTTERWAVE_SECRET_KEY=
FLUTTERWAVE_SECRET_HASH=
FLUTTERWAVE_REDIRECT_URL=
```

Real secrets must not be copied into documentation or committed to Git.

---

# 534. Alembic Migration Architecture

Database schema evolution is managed by:

```text
Alembic
```

Migration scripts reside in:

```text
alembic/versions/
```

The migration environment is defined in:

```text
alembic/env.py
```

---

# 535. Centralized Alembic Database URL

`alembic.ini` intentionally contains:

```text
sqlalchemy.url =
```

with no hard-coded database URL.

Instead, `alembic/env.py` performs:

```python
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url,
)
```

Therefore:

```text
FastAPI
+
SQLAlchemy
+
Alembic
```

all obtain the database connection URL from the same centralized Settings object.

This prevents migration and runtime environments from accidentally pointing to different databases.

---

# 536. Alembic Metadata Discovery

`alembic/env.py` imports:

```python
import app.models
```

before assigning:

```text
target_metadata = Base.metadata
```

This ensures all SQLAlchemy model tables are registered in the metadata before Alembic performs autogeneration or comparison.

---

# 537. Alembic Type Comparison

Both online and offline migration modes configure:

```text
compare_type = true
```

This allows Alembic to detect column type changes in addition to table/column additions and removals.

---

# 538. Online Migration Mode

Normal migration execution uses:

```text
run_migrations_online()
```

Alembic builds an Engine from the configured SQLAlchemy URL and uses:

```text
NullPool
```

for the migration connection.

---

# 539. Offline Migration Mode

Alembic also supports:

```text
run_migrations_offline()
```

with:

```text
literal_binds = true
paramstyle = named
```

This allows SQL migration output to be generated without an active live database connection.

---

# 540. Verify Current Migration

Use:

```bash
alembic current
```

The frozen backend's known current head is:

```text
7b933b5b8b78
```

---

# 541. List Migration Heads

Use:

```bash
alembic heads
```

The expected frozen repository state is one migration head:

```text
7b933b5b8b78
```

A single head indicates there are no unresolved migration branches.

---

# 542. Check Model/Migration Drift

Use:

```bash
alembic check
```

Expected output for the frozen backend:

```text
No new upgrade operations detected.
```

This verifies current SQLAlchemy metadata does not require an uncommitted migration.

---

# 543. Apply Database Migrations

For a newly created or outdated database:

```bash
alembic upgrade head
```

This applies all migrations up to the current repository head.

---

# 544. Creating a New Migration

For future model changes:

```bash
alembic revision --autogenerate -m "describe change"
```

After generation, the migration file must be manually reviewed before execution.

Autogenerated migrations should never be applied blindly.

---

# 545. Migration Review Procedure

Before:

```bash
alembic upgrade head
```

review the generated revision for:

```text
Unexpected table deletion
Unexpected column deletion
Incorrect foreign-key actions
Incorrect enum changes
Type conversions
Unique constraints
Indexes
Data-loss risk
```

This review is particularly important in a multi-school SaaS containing production academic records.

---

# 546. Migration Safety Workflow

Recommended workflow:

```text
Change SQLAlchemy model
        ↓
Generate Alembic revision
        ↓
Inspect migration manually
        ↓
Run migration against development database
        ↓
Run automated tests
        ↓
Run alembic check
        ↓
Commit migration
        ↓
Deploy
```

---

# 547. Current Frozen Migration State

The backend freeze established:

```text
Alembic current:
7b933b5b8b78 (head)

Alembic heads:
7b933b5b8b78 (head)

Alembic check:
No new upgrade operations detected.
```

No new database migration is required for the current frozen source code.

---

# 548. Local PostgreSQL Service

Under Ubuntu/WSL, PostgreSQL may be started with:

```bash
sudo service postgresql start
```

If the API reports connection-refused errors, PostgreSQL service status should be checked first.

---

# 549. Local PostgreSQL Connection Test

Because local socket authentication may use peer authentication, the established project workflow uses TCP explicitly:

```bash
PGPASSWORD=YOUR_PASSWORD \
psql -h 127.0.0.1 \
-U student_api \
-d student_result_db
```

This avoids relying on local peer-auth behavior.

---

# 550. PostgreSQL Development Databases

The project maintains separate development and testing databases.

Application development database:

```text
student_result_db
```

Dedicated automated-test database:

```text
student_result_test_db
```

Tests must not run against the normal development or production database.

---

# 551. Test Database URL

The established test database uses a URL of the form:

```text
postgresql+psycopg://student_api:********@127.0.0.1:5432/student_result_test_db
```

The test fixture includes protection against accidentally using a non-test database.

---

# 552. Starting the API Locally

Activate the virtual environment:

```bash
source venv/bin/activate
```

Then run:

```bash
uvicorn app.main:app --reload
```

Alternatively:

```bash
python -m uvicorn app.main:app --reload
```

---

# 553. Local API Address

Default local address:

```text
http://127.0.0.1:8000
```

Useful endpoints include:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/health
http://127.0.0.1:8000/health/database
http://127.0.0.1:8000/docs
```

when documentation is enabled.

---

# 554. Basic Local Health Verification

After startup:

```bash
curl http://127.0.0.1:8000/health
```

Expected:

```json
{
  "status": "healthy"
}
```

Then:

```bash
curl http://127.0.0.1:8000/health/database
```

Expected:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

# 555. Docker Support

The repository contains a production-oriented:

```text
Dockerfile
```

using:

```text
python:3.12-slim
```

as the base image.

---

# 556. Docker Runtime Environment

The image sets:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

This avoids `.pyc` file generation and ensures logs are emitted without Python output buffering.

---

# 557. Docker Working Directory

The container uses:

```text
/app
```

as its working directory.

---

# 558. Docker Dependency Installation

The build process first copies:

```text
requirements.txt
```

then runs:

```bash
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt
```

Copying requirements before application code improves Docker layer caching when source code changes but dependencies do not.

---

# 559. Docker Application Contents

The image copies:

```text
alembic.ini
alembic/
app/
```

into the container.

The current Dockerfile does not copy:

```text
tests/
```

because tests are excluded through `.dockerignore`.

---

# 560. Docker Exposed Port

The image declares:

```text
8000
```

using:

```dockerfile
EXPOSE 8000
```

---

# 561. Docker Startup Command

Container startup runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

This allows the FastAPI process to receive traffic from outside the container.

---

# 562. Build Docker Image

From the repository root:

```bash
docker build -t student-result-management-api .
```

---

# 563. Run Docker Container

Example:

```bash
docker run --rm \
  --env-file .env \
  -p 8000:8000 \
  student-result-management-api
```

This supplies configuration from the local `.env` without baking secrets into the image.

---

# 564. Database Migrations in Deployment

The Docker startup command currently launches Uvicorn directly.

It does not automatically execute:

```bash
alembic upgrade head
```

Therefore migrations should be run explicitly as part of deployment.

A production deployment pipeline should follow:

```text
Build image
      ↓
Configure production environment
      ↓
Run database migrations
      ↓
Start API service
      ↓
Run health checks
```

---

# 565. Example Container Migration Command

Depending on the deployment platform, migrations can be run from the built image with a command equivalent to:

```bash
alembic upgrade head
```

before the long-running Uvicorn process starts.

Migration execution should occur only once per deployment rather than independently from every horizontally scaled application instance.

---

# 566. `.dockerignore`

The repository excludes unnecessary or sensitive content from the Docker build context.

Excluded items include:

```text
.git
.gitignore
.env
.env.*
venv/
.venv/
__pycache__/
*.pyc
.pytest_cache/
.vscode/
.idea/
tests/
ngrok
.DS_Store
```

But:

```text
.env.example
```

is explicitly allowed.

---

# 567. Why `.env` Is Excluded from Docker

The Docker image should never contain real application secrets.

Therefore:

```text
.env
```

is excluded from the build.

Secrets should instead be provided at container runtime through:

```text
environment variables
secret managers
deployment platform configuration
```

---

# 568. Git Ignore Strategy

The repository `.gitignore` excludes:

```text
venv/
.venv/

.env
.env.*

__pycache__/
*.py[cod]

.pytest_cache/

.vscode/
.idea/

.DS_Store
ngrok

.coverage
htmlcov/

*.log
```

while allowing:

```text
.env.example
```

---

# 569. Secret Management Principle

Never commit:

```text
Database passwords
JWT secret
Flutterwave secret key
Flutterwave secret hash
Production redirect secrets
```

The repository should contain only placeholders and configuration names.

---

# 570. Production Environment Example

A production environment may resemble:

```env
APP_ENV=production
ENABLE_DOCS=false

CORS_ORIGINS=https://admin.example.com
ALLOWED_HOSTS=api.example.com

DATABASE_URL=postgresql+psycopg://PRODUCTION_USER:PRODUCTION_PASSWORD@DATABASE_HOST:5432/PRODUCTION_DB

JWT_SECRET_KEY=<LONG_RANDOM_SECRET>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

FLUTTERWAVE_SECRET_KEY=<PRODUCTION_SECRET_KEY>
FLUTTERWAVE_SECRET_HASH=<PRODUCTION_SECRET_HASH>
FLUTTERWAVE_REDIRECT_URL=https://example.com/payment/callback
```

These are illustrative placeholders only.

---

# 571. Production Database Requirement

Production should use a dedicated PostgreSQL database.

It must not reuse:

```text
student_result_db
```

from local development or:

```text
student_result_test_db
```

from automated tests.

---

# 572. Production JWT Requirement

A production JWT secret must differ from:

```text
development
testing
staging
```

environments.

Using the same secret across environments increases the impact of accidental credential exposure.

---

# 573. Production Flutterwave Requirement

Flutterwave credentials must match the intended provider mode.

Development/testing should use provider test credentials.

Production should use production credentials only after deployment configuration, webhook endpoint, and payment flow have been verified.

---

# 574. Production Host Security

Instead of:

```env
ALLOWED_HOSTS=*
```

production should normally use:

```env
ALLOWED_HOSTS=api.example.com
```

or the exact authorized hostnames.

This allows TrustedHostMiddleware to reject unexpected Host headers.

---

# 575. Production CORS Security

For browser-based administrative portals:

```env
CORS_ORIGINS=https://admin.example.com
```

should list only trusted frontend origins.

Avoid:

```text
*
```

when credentials are involved.

Native Android Flutter applications do not normally rely on CORS.

---

# 576. Production API Documentation

A production deployment may use:

```env
ENABLE_DOCS=false
```

to disable:

```text
/docs
/redoc
/openapi.json
```

This is an optional exposure-reduction measure rather than a substitute for authentication or authorization.

---

# 577. Deployment Health Checks

A deployment platform should monitor:

```http
GET /health
```

for application health.

A deeper dependency check can use:

```http
GET /health/database
```

to verify database connectivity.

---

# 578. Database Health Failure Interpretation

If:

```text
/health
```

works but:

```text
/health/database
```

fails, likely areas include:

```text
PostgreSQL unavailable
Invalid DATABASE_URL
Incorrect credentials
Database network restrictions
Database hostname/DNS failure
TLS/connection requirement mismatch
```

---

# 579. Application Startup Failure Interpretation

If the application fails before serving requests, likely configuration causes include:

```text
DATABASE_URL missing
JWT_SECRET_KEY missing
Invalid environment-variable format
Python dependency problems
Import errors
```

`DATABASE_URL` and `JWT_SECRET_KEY` are required Settings fields.

---

# 580. Flutterwave Runtime Failure Interpretation

The FastAPI application can start even with empty Flutterwave credentials because the Flutterwave configuration fields have empty-string defaults.

However, payment operations will fail when:

```text
FLUTTERWAVE_SECRET_KEY
```

or required redirect configuration is missing.

This allows non-payment development to proceed without provider credentials.

---

# 581. Configuration Parsing

Comma-separated host/origin environment values are parsed centrally.

This means deployment configuration should use:

```text
value1,value2,value3
```

rather than JSON arrays.

For example:

```env
ALLOWED_HOSTS=api.example.com,api2.example.com
```

---

# 582. Centralized Configuration Principle

The current architecture follows:

```text
.env / Environment Variables
            ↓
       Settings
       /   |   \
      /    |    \
 FastAPI SQLAlchemy Flutterwave
      \
       Alembic
```

This is preferable to separate modules independently calling:

```text
os.getenv(...)
load_dotenv(...)
```

because it reduces configuration drift.

---

# 583. Current Deployment Artifacts

The frozen backend contains:

```text
.env.example
Dockerfile
.dockerignore
.gitignore
alembic.ini
alembic/env.py
requirements.txt
```

These provide the foundation for reproducible environment configuration and container deployment.

---

# 584. Docker Image Scope

The current Docker image contains the backend application and migration scripts but intentionally excludes:

```text
test suite
virtual environments
IDE files
Git history
local environment secrets
local ngrok binary
```

This keeps the runtime image focused on application execution.

---

# 585. Current Docker Limitation

The repository currently provides a Dockerfile but does not include a Docker Compose configuration in the documented frozen state.

Therefore local PostgreSQL and API orchestration are presently handled separately unless a future Compose configuration is added.

This should not be documented as a missing defect; it is simply not part of the current frozen deployment artifacts.

---

# 586. Production Process Model

The current Docker command runs one Uvicorn process:

```text
uvicorn app.main:app
```

No Gunicorn/process manager configuration is currently included in the repository.

Actual production concurrency should therefore be configured according to the chosen hosting platform.

For container platforms, horizontal scaling may be preferable to embedding multiple process-management layers.

---

# 587. Database Connection Pooling

Application SQLAlchemy Engine uses its normal connection pool together with:

```text
pool_pre_ping = true
```

Alembic deliberately uses:

```text
NullPool
```

because migration commands are short-lived administrative operations.

---

# 588. Environment Setup Workflow

A clean local setup follows:

```text
Clone Repository
      ↓
Create Python virtual environment
      ↓
Install requirements
      ↓
Create PostgreSQL database/user
      ↓
Copy .env.example → .env
      ↓
Configure DATABASE_URL
      ↓
Configure JWT secret
      ↓
alembic upgrade head
      ↓
Start Uvicorn
      ↓
Check /health
      ↓
Check /health/database
```

---

# 589. Example Fresh Installation Commands

From the repository root:

```bash
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

Then:

```bash
cp .env.example .env
```

Edit `.env`, create the PostgreSQL database/user, and run:

```bash
alembic upgrade head
```

Finally:

```bash
uvicorn app.main:app --reload
```

---

# 590. Migration Verification After Setup

After migration:

```bash
alembic current
```

should report the expected head.

Then:

```bash
alembic check
```

should report:

```text
No new upgrade operations detected.
```

This verifies both schema application and metadata synchronization.

---

# 591. Deployment Verification Checklist

After deploying a new environment, verify:

```text
✓ Required environment variables exist
✓ DATABASE_URL points to correct database
✓ JWT secret is production-safe
✓ Flutterwave settings use correct environment
✓ Alembic migration is at head
✓ API process starts
✓ /health succeeds
✓ /health/database succeeds
✓ Authentication works
✓ Tenant isolation works
✓ Payment webhook URL is reachable when required
```

---

# 592. Production Secret Rotation

If:

```text
JWT_SECRET_KEY
```

is rotated, previously issued JWTs signed using the old secret become invalid.

If Flutterwave secrets are rotated, backend environment configuration and provider dashboard configuration must remain synchronized.

Database password rotation likewise requires updating:

```text
DATABASE_URL
```

before old credentials are disabled.

---

# 593. Logging

The current Alembic configuration provides console logging for:

```text
root
SQLAlchemy
Alembic
```

The backend repository currently does not define a larger application-specific structured logging framework.

Such logging may be added later for:

```text
payment events
authentication failures
tenant-security events
publication actions
production exceptions
```

---

# 594. Alembic Logging

Alembic logger level:

```text
INFO
```

SQLAlchemy logger level:

```text
WARNING
```

Root logger:

```text
WARNING
```

This provides useful migration progress without enabling verbose SQL logging by default.

---

# 595. Production Database Backups

The current source files do not implement automated database backup logic.

Backups should therefore be provided by the PostgreSQL hosting/deployment environment.

For a commercial academic SaaS, production infrastructure should support:

```text
regular automated backups
point-in-time recovery where available
retention policies
restore testing
```

These are infrastructure responsibilities rather than current FastAPI features.

---

# 596. Deployment Responsibility Boundary

The backend repository is responsible for:

```text
Application configuration
Database schema migrations
API process
Security/business logic
Health endpoints
Container definition
```

The production infrastructure is responsible for:

```text
Domain/DNS
TLS/HTTPS termination
Database hosting
Database backups
Container orchestration
Monitoring
Log collection
Secret storage
Scaling
Availability
```

---

# 597. HTTPS Requirement

The backend code itself runs HTTP within its local/container environment.

Production traffic should be exposed through:

```text
HTTPS
```

using the hosting platform, reverse proxy, load balancer, or managed ingress.

This is particularly important because requests carry:

```text
JWT access tokens
User credentials
Academic data
Payment-related identifiers
```

---

# 598. Flutter Production Base URL

During local development, Flutter may point to a development API address.

Production must use the deployed HTTPS endpoint, for example:

```text
https://api.example.com
```

The API base URL should be configurable in Flutter rather than hard-coded throughout the application.

---

# 599. Configuration Security Summary

The current configuration architecture provides:

```text
✓ Centralized Settings
✓ .env loading
✓ Required database configuration
✓ Required JWT secret
✓ Configurable token expiration
✓ Configurable CORS
✓ Configurable allowed hosts
✓ Optional API documentation
✓ Flutterwave secret separation
✓ Safe .env.example template
✓ Real .env ignored by Git
✓ Docker exclusion of environment secrets
✓ Unified Alembic/runtime database URL
```

---

# 600. Database and Migration Summary

The database infrastructure provides:

```text
✓ PostgreSQL
✓ psycopg driver
✓ SQLAlchemy ORM
✓ Request-scoped Sessions
✓ pool_pre_ping
✓ Declarative model metadata
✓ Alembic migrations
✓ Online/offline migrations
✓ Type comparison
✓ Centralized DATABASE_URL
✓ Single migration head
✓ Drift checking
```

---

# 601. Deployment Summary

The current deployment foundation can be represented as:

```text
Source Repository
       ↓
Docker Build
       ↓
Python 3.12 Runtime
       ↓
Install requirements
       ↓
Copy FastAPI + Alembic
       ↓
Production Environment Variables
       ↓
Alembic Upgrade
       ↓
Uvicorn
       ↓
FastAPI :8000
       ↓
Production HTTPS / Hosting Layer
```

This provides a clean foundation for deploying the frozen backend before Flutter mobile integration.
# 602. Automated Testing Architecture

The backend includes a dedicated automated regression suite built with:

```text
pytest
FastAPI TestClient
SQLAlchemy
PostgreSQL
```

The test suite validates both ordinary functionality and critical SaaS security guarantees.

Major areas include:

```text
Health and infrastructure
Authentication
Administrator authorization
Tenant isolation
Subscription enforcement
Assessment subscription rules
Attendance subscription rules
Student score subscription rules
Report comment subscription rules
Result publication
Published-result locking
Payment security
```

The frozen backend regression suite contains:

```text
178 automated tests
```

and the verified backend freeze completed with:

```text
178 passed
0 failed
0 errors
```

---

# 603. Dedicated Test Database

Tests use a dedicated PostgreSQL database:

```text
student_result_test_db
```

The test configuration does not use the normal development database.

The test URL follows:

```text
postgresql+psycopg://student_api:********@127.0.0.1:5432/student_result_test_db
```

---

# 604. Test Database Safety Guard

`tests/conftest.py` contains an explicit safeguard:

```python
if "student_result_test_db" not in TEST_DATABASE_URL:
    raise RuntimeError(
        "Tests must only run against student_result_test_db"
    )
```

This prevents the suite from accidentally running destructive cleanup operations against another configured database.

This is especially important because test cleanup truncates application tables.

---

# 605. Environment Override Before Application Import

The test configuration performs:

```python
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
```

before importing:

```text
app.main
SessionLocal
```

This ensures the FastAPI application and SQLAlchemy Engine are initialized against the dedicated test database.

The order is intentional.

Conceptually:

```text
Set TEST DATABASE_URL
        ↓
Import FastAPI application
        ↓
Create SQLAlchemy engine
        ↓
Run tests against test database
```

---

# 606. FastAPI Test Client

A session-scoped fixture provides:

```text
TestClient(app)
```

This allows tests to exercise the API through real HTTP-style requests such as:

```text
GET
POST
PATCH
PUT
DELETE
```

while running inside the test process.

The tests therefore verify routing, dependency injection, authentication, business rules, response status codes, and response bodies together.

---

# 607. Database Session Fixture

Tests also receive a direct SQLAlchemy Session through:

```text
db
```

The fixture:

```text
opens SessionLocal
      ↓
yields Session
      ↓
rolls back any remaining transaction
      ↓
closes Session
```

Direct database access is useful for creating precise preconditions that would be unnecessarily cumbersome through the public API.

---

# 608. Automatic Database Cleanup

An autouse fixture executes after every test.

It truncates:

```text
payment_transactions
published_report_snapshots
result_publications
term_report_comments
student_attendance
student_scores
assessments
teaching_assignments
enrollments
students
teachers
subscriptions
subscription_plans
grading_scales
report_settings
terms
academic_sessions
subjects
classes
users
schools
```

using:

```sql
RESTART IDENTITY CASCADE
```

This gives every test a clean database state and resets generated IDs.

---

# 609. Test Isolation Principle

The cleanup design means:

```text
Test A
   ↓
Creates data
   ↓
Assertions
   ↓
Database cleanup
   ↓
Test B starts clean
```

Tests therefore do not rely on execution order or data accidentally left by previous tests.

---

# 610. Shared Fixture Architecture

`conftest.py` defines reusable fixtures representing the SaaS domain.

Examples include:

```text
Platform Administrator
Inactive Platform Administrator

School One
School Two

School Admin
Second School Admin
Other School Admin

School One Class
School Two Class

School One Subject
School Two Subject

School One Teacher
School Two Teacher

School One Student
School Two Student

Academic Sessions
Terms

Subscription Plan
Active Subscription
Pending Subscription
Cancelled Subscription
Expired Subscription

Assessments
```

These fixtures make tenant-boundary and state-machine tests deterministic.

---

# 611. Two-School Security Test Model

Many security tests deliberately create:

```text
School One
School Two
```

with equivalent academic resources.

For example, both Schools may have:

```text
JSS1
Physics
Teacher T001
First Term
```

The duplicate-looking business values ensure tenant isolation depends on:

```text
school_id
```

rather than globally unique labels.

---

# 612. Automated Test Distribution

The test files contain the following number of test cases:

| Test file                             |   Tests |
| ------------------------------------- | ------: |
| `test_health.py`                      |       3 |
| `test_auth.py`                        |       7 |
| `test_admin_management.py`            |      19 |
| `test_tenant_isolation.py`            |      16 |
| `test_subscription_enforcement.py`    |      20 |
| `test_assessment_subscription.py`     |      15 |
| `test_attendance_subscription.py`     |      16 |
| `test_student_score_subscription.py`  |      15 |
| `test_report_comment_subscription.py` |      15 |
| `test_result_publication.py`          |      19 |
| `test_published_result_locks.py`      |      17 |
| `test_payment_security.py`            |      16 |
| **Total**                             | **178** |

---

# 613. Health Tests

`test_health.py` contains three infrastructure tests.

They verify:

```http
GET /
GET /health
GET /health/database
```

The root contract is checked exactly:

```json
{
  "message": "Student Result Management API is running"
}
```

The application health contract is:

```json
{
  "status": "healthy"
}
```

The database health contract is:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

# 614. Why Exact Health Responses Are Tested

The root and health response bodies are tested exactly rather than only checking HTTP 200.

This protects the published API contract from accidental changes.

During production hardening, this test detected an attempted addition of a `version` field to the root response.

The API was restored to the established contract rather than silently changing a previously tested endpoint.

---

# 615. Authentication Tests

The authentication suite contains:

```text
7 tests
```

It covers:

```text
Successful login
Incorrect password
Unknown User
Inactive User
Protected endpoint without token
Protected endpoint with invalid token
Current authenticated Platform Admin identity
```

---

# 616. Successful Login Test

Valid credentials must produce:

```text
HTTP 200
```

with:

```text
access_token
token_type = bearer
```

The test does not depend on a hard-coded JWT string.

It validates the contract instead.

---

# 617. Invalid Credential Protection

Wrong password and unknown User cases both return:

```text
401 Unauthorized
```

with:

```text
Invalid email or password
```

Returning the same message for both cases avoids revealing whether a particular email address exists.

---

# 618. Inactive User Protection

An inactive User cannot authenticate.

Expected response:

```text
403 Forbidden
User account is inactive
```

This ensures account deactivation takes effect at authentication time.

---

# 619. Missing and Invalid Tokens

Protected resources reject:

```text
Missing Bearer token
Invalid Bearer token
```

with authentication failures.

An invalid token explicitly returns:

```text
401 Unauthorized
Invalid authentication token
```

---

# 620. `/api/users/me` Authentication Test

The suite verifies a Platform Administrator receives:

```text
id
email
role = admin
account_type = platform_admin
school_id = null
is_active = true
```

This confirms the endpoint can be safely used as the Flutter session-bootstrap endpoint.

---

# 621. Administrator Management Tests

Administrator-management coverage contains:

```text
19 tests
```

It verifies both Platform Administrator and School Administrator behavior.

---

# 622. Platform Administrator Creation Tests

The suite verifies:

```text
Platform Admin can create another Platform Admin
School Admin cannot create a Platform Admin
Duplicate admin email is rejected
```

A successfully created Platform Administrator must have:

```text
role = admin
account_type = platform_admin
school_id = null
is_active = true
```

---

# 623. School Administrator Creation Tests

The tests verify:

```text
Platform Admin can create School Admin for selected School
School Admin can create another Admin for own School
School Admin cannot create Admin for another School
Platform Admin must provide school_id
```

This validates both privilege level and tenant ownership.

---

# 624. Administrator Listing Tests

The suite verifies:

```text
Platform Admin can list Platform Admins
School Admin cannot list Platform Admins

Platform Admin can list School Admins across Schools
Platform Admin can filter by School

School Admin sees only administrators belonging to own School
School Admin cannot request another School's administrator list
```

---

# 625. Administrator Deactivation Tests

The suite protects administrative continuity.

Tests include:

```text
Platform Admin cannot deactivate own account
School Admin cannot deactivate own account

Another Platform Admin may be deactivated/reactivated
Another same-School Admin may be deactivated/reactivated

School Admin cannot manage another School's Admin
Last active School Admin cannot be deactivated
```

This reduces the risk of accidentally leaving a School without an administrator.

---

# 626. Tenant Isolation Tests

The tenant-isolation suite contains:

```text
16 tests
```

It uses resources belonging to two different Schools.

---

# 627. Tenant-Scoped List Tests

The suite verifies that list endpoints do not mix tenants.

Examples include:

```text
Classes
Subjects
Teachers
Students
```

For a School One administrator:

```text
School One resource → present
School Two resource → absent
```

---

# 628. Cross-School Direct Read Tests

A School Administrator requesting another tenant's resource receives:

```text
404 Not Found
```

rather than the foreign resource.

This behavior is tested for resources including:

```text
Class
Subject
Teacher
Student
```

---

# 629. Cross-School Modification Tests

The tests attempt to modify resources belonging to another School.

Expected behavior:

```text
404 Not Found
```

and the foreign resource remains inaccessible.

This validates that tenant filtering applies to write operations as well as reads.

---

# 630. Own-Tenant Positive Tests

Tenant isolation does not merely test rejection.

The suite also confirms the same administrator can successfully retrieve:

```text
own Class
own Subject
own Teacher
own Student
```

This distinguishes proper tenant filtering from an endpoint that simply blocks everything.

---

# 631. Subscription Enforcement Tests

The Subscription enforcement suite contains:

```text
20 tests
```

It tests both the central service and the subscription API.

---

# 632. Active Subscription Service Tests

The central function:

```text
require_active_term_subscription(...)
```

is tested against:

```text
active
pending
cancelled
expired
missing
```

subscription states.

Only:

```text
active
```

is accepted.

---

# 633. Exact Tenant Subscription Matching

The suite verifies an active subscription cannot unlock academic operations when:

```text
school_id does not match
```

even if the session and term values otherwise refer to an active Subscription.

---

# 634. Exact Academic Session Matching

The suite also verifies the active Subscription must match the exact:

```text
academic_session_id
```

A Subscription for one Session cannot authorize another Session.

---

# 635. School Subscription Access Tests

School Administrators can:

```text
list own subscriptions
retrieve own subscription
```

but cannot:

```text
read another School's subscription
list every Subscription on the platform
```

Cross-school Subscription retrieval returns:

```text
404 Not Found
```

---

# 636. Platform Subscription Access Tests

Platform Administrators can:

```text
list subscriptions across all Schools
```

while School Administrators are rejected from that platform-level endpoint.

---

# 637. Subscription Status Tests

The tests verify:

```text
School Admin cannot manually activate Subscription

Platform Admin can activate pending Subscription

Same-state update is idempotent

pending → expired is invalid

expired → active is invalid

cancelled → pending is valid
```

These tests enforce the documented Subscription state machine.

---

# 638. Subscription Creation Tests

Coverage includes:

```text
Duplicate School/session/term Subscription rejected
New Subscription starts pending
School cannot subscribe to another School's Academic Session
```

This verifies both uniqueness and tenant isolation during commercial onboarding.

---

# 639. Assessment Subscription Tests

The assessment suite contains:

```text
15 tests
```

It validates commercial entitlement around assessment operations.

---

# 640. Assessment Creation with Active Subscription

An active Subscription for the exact term permits Assessment creation.

The resulting Assessment is checked against:

```text
class_id
subject_id
academic_session_id
term_id
```

rather than merely asserting an HTTP success response.

---

# 641. Assessment Creation Without Valid Subscription

The suite covers non-active states including cases such as:

```text
pending
cancelled
expired
missing
```

The expected commercial failure is:

```text
403 Forbidden
An active subscription is required for this academic term
```

---

# 642. Assessment Update and Delete Enforcement

Subscription enforcement is not limited to Assessment creation.

The suite verifies protected mutation behavior for:

```text
update
delete
```

as well.

This prevents a School from modifying term data after losing commercial entitlement.

---

# 643. Historical Assessment Read Access

The assessment tests deliberately verify that previously created Assessment data remains readable even after the Subscription is no longer active.

This encodes the design principle:

```text
Expired entitlement
      ↓
No new protected writes
      ↓
Historical academic reads remain available
```

Commercial expiration therefore does not erase or hide the School's historical records.

---

# 644. Attendance Subscription Tests

Attendance coverage contains:

```text
16 tests
```

The suite verifies:

```text
Active Subscription permits attendance writes
Inactive Subscription blocks writes
Tenant isolation
Historical reads
Update enforcement
Delete enforcement
```

---

# 645. Attendance Historical-Read Principle

Previously recorded attendance remains readable after Subscription expiration.

The purpose is to separate:

```text
Current commercial entitlement
```

from:

```text
Ownership of historical School records
```

---

# 646. Student Score Subscription Tests

Student Score coverage contains:

```text
15 tests
```

The suite verifies commercial and tenant protections around score records.

---

# 647. Score Write Entitlement

Protected score mutations require an active Subscription for the Assessment's exact:

```text
School
Academic Session
Term
```

This applies to:

```text
create
update
delete
```

---

# 648. Score Historical Retrieval

Student Scores recorded while a Subscription was active remain available through read endpoints even if the Subscription later becomes inactive.

This ensures report/history access is not coupled to current payment status.

---

# 649. Report Comment Subscription Tests

Report Comment coverage contains:

```text
15 tests
```

The suite verifies:

```text
Active Subscription required for writes
Cross-school reads blocked
Cross-school updates blocked
Cross-school deletes blocked
Tenant-safe lists
Historical reads remain available
```

---

# 650. Cross-School Comment Isolation

The tests specifically construct comments for two Schools.

A School Administrator cannot:

```text
retrieve
update
delete
```

another School's comment.

Tenant-scoped list results also exclude the other School's comment.

---

# 651. Result Publication Tests

Result-publication coverage contains:

```text
19 tests
```

This is one of the most important integrity suites in the project.

---

# 652. Publication Precondition Tests

The suite exercises conditions required before a result can become official.

These include:

```text
Correct tenant ownership
Active Subscription
Students enrolled
Assessments available
Student results complete
```

Invalid conditions prevent publication.

---

# 653. Result Completeness Tests

Publication tests prepare the expected scoring structure:

```text
CA1
CA2
CA3
EXAM
```

and verify incomplete results cannot cross the publication boundary.

The publication process therefore depends on result computation rather than merely checking that at least one score exists.

---

# 654. Duplicate Publication Test

Once a class/session/term result is already:

```text
published
```

another normal publication attempt is rejected.

This prevents duplicate simultaneous official publications for the same academic scope.

---

# 655. Publication Tenant Isolation

The result-publication tests verify that a School Administrator cannot publish or retrieve another tenant's result publication.

Tenant validation applies to:

```text
Class
Academic Session
Term
```

and their relationship.

---

# 656. Result Reopen Tests

The suite verifies the controlled transition:

```text
published
      ↓
reopened
```

including Subscription requirements.

An already reopened result cannot be reopened repeatedly as if it were still published.

---

# 657. Snapshot Creation Test

Publication creates:

```text
PublishedReportSnapshot
```

records for enrolled Students.

The stored report is checked for meaningful report data such as:

```text
Student identity
School identity
Term
COMPLETE result status
```

rather than only checking that a JSON object exists.

---

# 658. Snapshot Data Preservation

A published snapshot stores the complete report representation at publication time.

This supports:

```text
historical consistency
stable published reports
separation from live mutable academic data
```

while status remains published.

---

# 659. Republish Snapshot Refresh Test

The suite verifies the correction workflow:

```text
Publish
   ↓
Store snapshot
   ↓
Reopen
   ↓
Modify academic data
   ↓
Republish
```

On republish:

```text
same ResultPublication record is reused
same Student snapshot row is reused
snapshot data is refreshed
```

The tests explicitly ensure the snapshot count remains:

```text
1
```

for that publication/student pair.

---

# 660. Snapshot Versioning Behavior Tested

The tests therefore confirm the current design is:

```text
one snapshot per publication/student
```

not:

```text
one snapshot version per every publication event
```

This agrees with the database uniqueness constraint and documented publication semantics.

---

# 661. Published Result Lock Tests

Published-result locking contains:

```text
17 tests
```

The tests verify that an official publication actually prevents modification of the data used to produce it.

---

# 662. Standard Result Lock Response

Protected mutations expect:

```text
409 Conflict
```

with:

```text
Results for this class and term are published
and cannot be modified. Reopen the results first.
```

The exact conflict behavior is tested.

---

# 663. Enrollment Lock Response

Enrollment changes use a broader class/session lock.

The expected conflict explains:

```text
Published results exist for this class
and academic session.
Enrollment records cannot be modified
until the published results are reopened.
```

---

# 664. Published Academic Data Protected by Tests

The lock suite covers protected data including:

```text
Assessments
Student Scores
Attendance
Term Report Comments
Enrollments
```

The purpose is to prevent the source data of an official report from changing invisibly.

---

# 665. Reopened Results Release Locks

The suite does not only test denial.

It also verifies that after publication status is:

```text
reopened
```

corrections are allowed.

Examples include successful changes to:

```text
Scores
Attendance
Comments
Enrollments
```

where applicable.

This confirms reopening is a genuine controlled editing state.

---

# 666. Enrollment Reopen Tests

The tests explicitly verify reopened results allow:

```text
Enrollment update
Enrollment deletion
```

This confirms the broader session-level enrollment lock is released once the relevant publication is no longer in `published` state.

---

# 667. Payment Security Tests

Payment-security coverage contains:

```text
16 tests
```

The tests use monkeypatching to simulate Flutterwave responses without requiring real payment-network calls.

This makes security scenarios deterministic and repeatable.

---

# 668. Payment Initialization Tests

The suite verifies a School Administrator can initialize payment for their own:

```text
pending Subscription
```

and receives the expected local payment information and checkout link.

---

# 669. Payment Tenant Isolation Tests

The payment suite verifies one School cannot operate on another School's:

```text
Subscription
PaymentTransaction
```

through normal authenticated payment endpoints.

---

# 670. Pending Payment Reuse Tests

The suite covers behavior where a pending local Payment already has a usable checkout link.

The application reuses that payment rather than generating unnecessary duplicate transactions.

---

# 671. Successful Payment Duplicate Protection Tests

Once a Subscription already has a successful payment, initialization of another payment for the same Subscription is rejected.

This guards against accidental duplicate charges.

---

# 672. Payment Verification Tests

Provider verification scenarios validate fields including:

```text
Flutterwave transaction ID
tx_ref
payment status
currency
amount
```

before local success and Subscription activation are accepted.

---

# 673. Underpayment Protection Tests

The payment suite covers the case where Flutterwave returns an amount below the expected local amount.

Such a transaction must not activate the Subscription.

This validates the rule:

```text
verified_amount >= expected_amount
```

---

# 674. Currency Mismatch Protection

A verified provider transaction using the wrong currency is rejected.

A successful provider status alone is therefore insufficient to activate commercial access.

---

# 675. Transaction Reference Protection

A Flutterwave transaction whose provider reference does not equal:

```text
PaymentTransaction.tx_ref
```

is rejected.

This prevents applying a legitimate transaction to the wrong local payment record.

---

# 676. Provider Transaction Replay Protection

The suite verifies a Flutterwave transaction ID cannot be reused for another PaymentTransaction.

This protects against:

```text
One provider payment
      ↓
Multiple Subscription activations
```

---

# 677. Payment Idempotency Tests

Already processed payments can be safely encountered again without duplicating activation.

Idempotency is important because payment systems commonly deliver:

```text
retries
duplicate webhooks
manual verify after webhook
```

---

# 678. Webhook Security Tests

The payment suite also covers webhook-specific security.

Important protections include:

```text
Webhook authentication
Known transaction reference
Supported event
Provider re-verification
Status validation
Currency validation
Amount validation
Transaction replay protection
```

---

# 679. Why Flutterwave Is Mocked in Tests

External Flutterwave calls are replaced with controlled fake responses.

This allows tests to simulate:

```text
Success
Failure
Reference mismatch
Currency mismatch
Underpayment
Reused transaction
```

without:

```text
real money
network dependency
provider instability
live credentials
```

This is the appropriate strategy for backend unit/integration regression tests.

---

# 680. Security Regression Philosophy

The test suite is not limited to happy paths.

For critical resources it deliberately attempts:

```text
Unauthorized access
Wrong role
Cross-school access
Inactive accounts
Invalid Subscription state
Wrong academic term
Published-result mutation
Duplicate resources
Payment replay
Provider-data mismatch
```

These negative tests are essential for a multi-tenant SaaS.

---

# 681. Positive and Negative Pairing

Many security behaviors are tested in pairs.

For example:

```text
School Admin can read own Class
School Admin cannot read other School's Class
```

and:

```text
Active Subscription permits operation
Pending Subscription rejects operation
```

and:

```text
Published result blocks modification
Reopened result permits correction
```

This makes the tests stronger than rejection-only testing.

---

# 682. HTTP Contract Testing

Tests check not only business outcome but HTTP semantics.

Examples include:

```text
200 Successful operation
201 Resource creation
204 Successful deletion

401 Authentication failure
403 Authorization/subscription failure
404 Tenant-hidden resource
409 State/uniqueness conflict
```

This helps keep Flutter error handling predictable.

---

# 683. Exact Error Message Testing

Many tests also assert exact:

```text
response.json()["detail"]
```

values.

Benefits include:

```text
Stable client-facing errors
Regression detection
Clear business-rule contracts
```

The tradeoff is that intentional wording changes require test updates.

---

# 684. Test Data Uses Hashed Passwords

User fixtures store:

```text
password_hash
```

using the application's real:

```text
hash_password(...)
```

function.

The tests therefore exercise the actual password-verification path instead of bypassing security with plaintext test passwords.

---

# 685. Student Test Fixtures Reflect Production Architecture

Student fixtures are deliberately created with:

```text
user_id = None
```

This verifies tests align with the current architecture where Student academic records do not require login Users.

Teacher fixtures, by contrast, create:

```text
User
+
Teacher
```

relationships.

---

# 686. Subscription Fixture States

The test environment provides distinct fixtures for:

```text
active
pending
cancelled
expired
```

subscriptions.

This is important because commercial rules are state-dependent and should not be tested by repeatedly mutating one shared Subscription.

---

# 687. Tenant Fixtures Reuse Business Codes Safely

Examples include both Schools having equivalent values such as:

```text
Class code = JSS1
Subject code = PHY
Teacher employee number = T001
```

This actively validates that uniqueness rules are scoped by School where intended.

---

# 688. Running the Complete Suite

From the activated virtual environment:

```bash
pytest
```

or, for concise output:

```bash
pytest -q
```

The PostgreSQL test database must be available and migrated before execution.

---

# 689. Recommended Pre-Test Database Preparation

Before running the suite on a fresh test environment:

```bash
DATABASE_URL="postgresql+psycopg://student_api:YOUR_PASSWORD@127.0.0.1:5432/student_result_test_db" \
alembic upgrade head
```

The exact environment method may vary, but migrations must be applied to:

```text
student_result_test_db
```

rather than the development database.

---

# 690. Running One Test File

Examples:

```bash
pytest tests/test_auth.py -q
```

```bash
pytest tests/test_tenant_isolation.py -q
```

```bash
pytest tests/test_payment_security.py -q
```

This is useful while developing a specific subsystem.

---

# 691. Running One Individual Test

Pytest supports:

```bash
pytest tests/test_auth.py::test_login_success -q
```

This is useful when diagnosing a single regression.

---

# 692. Current Verified Regression Result

The final backend audit verified:

```text
178 passed
0 failed
0 errors
```

The final full-suite run also emitted deprecation warnings, primarily related to:

```python
datetime.utcnow()
```

These warnings were intentionally not fixed partially during backend freeze because the appropriate solution requires a deliberate timezone-aware database migration.

---

# 693. Warning vs Failure Policy

Deprecation warnings currently do not represent failing business behavior.

The backend freeze therefore distinguishes:

```text
Test failure
→ release blocker
```

from:

```text
Known datetime deprecation warning
→ documented technical debt
```

This prevents an unsafe partial timestamp conversion purely to silence warnings.

---

# 694. Regression Gate for Future Backend Changes

Future backend modifications should not be considered complete until:

```bash
pytest -q
```

passes the full suite.

Recommended gate:

```text
Code change
     ↓
Focused related tests
     ↓
Full 178+ regression suite
     ↓
Alembic current
     ↓
Alembic heads
     ↓
Alembic check
     ↓
Commit
```

As the backend evolves, the number of tests should increase beyond 178 rather than treating 178 as a permanent ceiling.

---

# 695. Migration Regression Rule

Whenever database models change:

```text
Generate migration
      ↓
Review migration
      ↓
Upgrade test database
      ↓
Run entire test suite
      ↓
Run alembic check
```

A migration that applies successfully but breaks tenant/security behavior is not considered safe.

---

# 696. Payment Regression Rule

Any future payment change should rerun at minimum:

```bash
pytest tests/test_payment_security.py -q
pytest tests/test_subscription_enforcement.py -q
```

followed by:

```bash
pytest -q
```

Payment logic should never be validated only through manual checkout.

---

# 697. Result-System Regression Rule

Changes involving:

```text
Assessments
Scores
Attendance
Comments
Results
Report Sheets
Publications
Snapshots
Enrollments
```

should rerun the relevant focused suites plus:

```text
test_result_publication.py
test_published_result_locks.py
```

because these areas are interconnected.

---

# 698. Tenant-Security Regression Rule

Changes to any school-scoped query should rerun:

```bash
pytest tests/test_tenant_isolation.py -q
```

and the resource-specific suite.

Tenant isolation is a system-wide property, not merely a feature of one router.

---

# 699. Authentication Regression Rule

Changes to:

```text
JWT
password hashing
dependencies
User roles
account activation
School activation
```

should rerun:

```bash
pytest tests/test_auth.py -q
pytest tests/test_admin_management.py -q
```

followed by the full suite.

---

# 700. Current Test Coverage Strengths

The suite has particularly strong coverage around:

```text
Authentication boundaries
Administrator privileges
Multi-school tenant isolation
Subscription entitlement
Published-result immutability
Payment verification
Payment replay protection
Historical-read behavior
```

These are the areas where a commercial multi-school result-management platform carries the greatest security and data-integrity risk.

---

# 701. Current Test Coverage Scope

The current suite is primarily:

```text
API integration testing
+
database-backed business-rule testing
+
security regression testing
```

It is not presented as:

```text
browser UI testing
Flutter widget testing
mobile end-to-end testing
load testing
penetration testing
```

Those belong to later stages of the product lifecycle.

---

# 702. Future Flutter Test Layer

When Flutter integration begins, a separate mobile test layer should cover:

```text
JSON deserialization
Authentication token handling
Role-based navigation
API error mapping
Form validation
Subscription/payment states
Result rendering
Report settings
Offline/network failures
```

Those tests complement rather than replace the backend regression suite.

---

# 703. Future End-to-End Testing

Once a deployable mobile application exists, end-to-end scenarios should cover flows such as:

```text
Register School
      ↓
Login
      ↓
Create academic structure
      ↓
Create Student
      ↓
Enroll Student
      ↓
Activate Subscription
      ↓
Create Assessments
      ↓
Enter Scores
      ↓
Publish Result
      ↓
Retrieve Published Report
```

A separate payment test environment should use Flutterwave test mode rather than production transactions.

---

# 704. Quality Gate Summary

The current backend quality gate can be represented as:

```text
Static source review
       ↓
Database migration check
       ↓
Authentication tests
       ↓
Tenant-isolation tests
       ↓
Subscription tests
       ↓
Academic-write tests
       ↓
Publication-integrity tests
       ↓
Payment-security tests
       ↓
Full regression suite
       ↓
178 tests passed
       ↓
Backend freeze
```

---

# 705. Backend Freeze Verification

The regression suite formed part of the final backend freeze process.

The frozen state was verified together with:

```text
Application compilation
Router registration
Alembic single head
Alembic drift check
Authentication review
Tenant-security review
Subscription/payment review
Result/publication review
Deployment configuration review
Full automated regression suite
```

---

# 706. Backend Freeze Commit

The documented frozen backend corresponds to:

```text
074f4df
```

with commit message:

```text
chore: harden production configuration and deployment setup
```

The local `main` branch and `origin/main` were verified synchronized at that commit.

---

# 707. Test and Security Documentation Summary

The backend does not rely only on architectural assumptions such as:

```text
"We filter by school."
"We require subscriptions."
"Published results are locked."
"Payments are verified."
```

Those claims are backed by executable regression tests that intentionally attempt to violate the rules.

The key principle is:

```text
Business Rule
      ↓
Implementation
      ↓
Automated Regression Test
```

This significantly reduces the risk that future development—especially Flutter integration and later backend enhancements—silently breaks the SaaS security model.
# 708. Runtime Dependency Overview

The backend uses a pinned Python dependency set in:

```text
requirements.txt
```

The frozen environment is based on:

```text
Python 3.12
```

as confirmed by the Docker image and local compiled artifacts.

Major application dependencies include:

| Component         | Version |
| ----------------- | ------: |
| FastAPI           | 0.141.1 |
| Starlette         |   1.6.0 |
| Uvicorn           |  0.52.4 |
| SQLAlchemy        |  2.0.52 |
| Alembic           |  1.19.1 |
| Psycopg           |   3.3.5 |
| Pydantic          |  2.13.5 |
| pydantic-settings |  2.15.0 |
| PyJWT             |  2.13.0 |
| pwdlib            |   0.3.1 |
| argon2-cffi       |  25.1.0 |
| pytest            |   9.1.1 |
| httpx             |  0.28.1 |
| httpx2            |  2.12.0 |
| email-validator   |   2.3.0 |

---

# 709. FastAPI Runtime Stack

The runtime request stack can be represented as:

```text
Client
  ↓
Uvicorn
  ↓
FastAPI
  ↓
Starlette
  ↓
Pydantic validation
  ↓
Dependency injection
  ↓
Router
  ↓
Service layer
  ↓
SQLAlchemy
  ↓
psycopg
  ↓
PostgreSQL
```

---

# 710. Authentication Dependency Stack

Authentication uses:

```text
pwdlib
argon2-cffi
PyJWT
```

Responsibilities are separated as follows:

```text
Password input
     ↓
pwdlib / Argon2
     ↓
Password verification
```

and:

```text
Authenticated User
     ↓
PyJWT
     ↓
Signed access token
```

---

# 711. HTTP Client Dependencies

The repository currently contains both:

```text
httpx
httpx2
```

These should not be assumed to be duplicates.

The test/client environment previously required `httpx2` because the installed Starlette TestClient version uses it.

Therefore neither dependency should be removed casually without rerunning the complete regression suite.

---

# 712. Exact Dependency Pinning

Every dependency in `requirements.txt` is pinned with:

```text
==
```

rather than broad ranges.

This provides reproducibility because:

```text
pip install -r requirements.txt
```

installs the exact environment used for the frozen backend.

---

# 713. Dependency Upgrade Policy

Future dependency upgrades should be treated as backend changes.

Recommended process:

```text
Upgrade one logical dependency group
        ↓
Install fresh environment
        ↓
Compile application
        ↓
Run focused tests
        ↓
Run all 178+ tests
        ↓
Run Alembic checks
        ↓
Commit only after successful verification
```

Avoid upgrading the full dependency file blindly.

---

# 714. Repository Root Documentation

The current `README.md` is minimal:

```text
# student-result-management-api

A RESTful API for managing students, classes,
subjects, scores, and academic results.
```

This README predates the full commercial SaaS architecture.

It does not currently describe:

```text
Multi-school tenancy
Authentication
Administrator roles
Subscriptions
Flutterwave payments
Publication
Report snapshots
Docker
Alembic
Testing
Flutter integration
```

---

# 715. README Improvement Recommendation

After the detailed backend documentation is complete, `README.md` should become a short project entry point.

It should contain:

```text
Project summary
Technology stack
Main capabilities
Quick-start instructions
Environment setup
Migration command
Start command
Test command
Link to BACKEND_DOCUMENTATION.md
```

The detailed architecture should remain in the larger documentation rather than duplicating hundreds of sections inside the README.

---

# 716. High-Level Repository Structure

The application structure is:

```text
student-result-management-api/
│
├── app/
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── alembic/
│   ├── versions/
│   ├── env.py
│   └── script.py.mako
│
├── tests/
│
├── docs/
│
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .env.example
└── .gitignore
```

---

# 717. `app/api` Responsibility

The `app/api/` package contains HTTP routing and route-level business validation.

Current router modules include:

```text
academic_sessions
admin_management
assessments
auth
classes
enrollments
grading_scales
payments
report_settings
report_sheets
result_publications
results
roles
schools
student_attendance
student_scores
students
subjects
subscription_plans
subscriptions
teachers
teaching_assignments
term_report_comments
term_results
terms
users
```

---

# 718. `app/models` Responsibility

The `app/models/` package defines persistent SQLAlchemy entities.

It includes:

```text
AcademicSession
Assessment
Class
Enrollment
GradingScale
PaymentTransaction
PublishedReportSnapshot
ReportSettings
ResultPublication
School
Student
StudentAttendance
StudentScore
Subject
Subscription
SubscriptionPlan
Teacher
TeachingAssignment
Term
TermReportComment
User
```

---

# 719. `app/schemas` Responsibility

The `app/schemas/` package defines API contracts using Pydantic.

It separates:

```text
Database representation
```

from:

```text
Client request/response representation
```

This layer is especially important for Flutter integration.

---

# 720. `app/services` Responsibility

Business logic that does not belong directly in routers is placed in:

```text
app/services/
```

Current services include:

```text
flutterwave_service.py
payment_service.py
report_sheet_service.py
result_publication_service.py
result_service.py
subscription_service.py
```

This separation keeps external integration and complex business computation outside the router layer.

---

# 721. Core Infrastructure Package

`app/core/` contains:

```text
config.py
dependencies.py
security.py
```

Responsibilities include:

```text
Environment configuration
JWT processing
Password hashing
Authentication dependency
Role authorization
School activity validation
```

---

# 722. Database Package

`app/database/` contains:

```text
base.py
connection.py
```

It defines:

```text
SQLAlchemy declarative Base
Application Engine
SessionLocal
FastAPI database dependency
```

---

# 723. Alembic Migration History

The repository contains a complete incremental migration history rather than a single generated initial schema.

The history demonstrates evolution including:

```text
Users
Schools
School tenancy
Classes
Subjects
Teachers
Students
Academic Sessions
Terms
Enrollments
Teaching Assignments
Assessments
Scores
Attendance
Comments
Grading
Report settings
Subscriptions
Result publication
Snapshots
Payments
```

---

# 724. Important Migration Evolution

Several migration names show important architectural transitions.

Examples include:

```text
make_student_user_account_optional
scope_class_codes_by_school
scope_subject_names_and_codes_by_school
scope_teacher_employee_numbers_by_school
scope_student_admission_numbers_by_school
scope_academic_sessions_by_school
add_school_tenancy_to_core_academic...
enforce_one_current_academic_session...
add_result_publication
add_published_report_snapshots
create_termly_subscription_tables
add_payment_transactions
```

These migrations document the transition from a simpler result API into a multi-school commercial SaaS.

---

# 725. Migration History Must Be Preserved

Existing migration files should not be rewritten or deleted merely to simplify the directory.

Production databases depend on the migration chain.

Future schema development should add a new migration rather than editing historical revisions that may already have been applied.

---

# 726. Repository Generated Files

The current project structure contains generated files such as:

```text
__pycache__/
*.pyc
.pytest_cache/
```

These are normal local runtime artifacts.

They are already excluded by `.gitignore`.

They should not be manually committed.

---

# 727. Documentation Swap File Warning

The repository listing currently shows:

```text
docs/.BACKEND_DOCUMENTATION.md.swp
```

but does not show:

```text
docs/BACKEND_DOCUMENTATION.md
```

A `.swp` file is normally created by Vim while editing a file.

Before deleting anything, verify whether the documentation is still open in an editor and save it.

Recommended first check:

```bash
ls -la docs
```

If the document is open in Vim:

```text
save and close it normally
```

before removing any swap file.

---

# 728. Safe Documentation Recovery Check

If Vim reports an existing swap file, use:

```bash
vim docs/BACKEND_DOCUMENTATION.md
```

and carefully review the recovery options.

If unsaved content exists, recover and save it before deleting the swap.

The goal is:

```text
docs/BACKEND_DOCUMENTATION.md
```

containing the complete documentation.

---

# 729. Swap File Cleanup

Only after confirming the Markdown document is safely saved should a stale swap file be removed.

Example:

```bash
rm docs/.BACKEND_DOCUMENTATION.md.swp
```

Do not run this if Vim is currently using the file or if the swap contains the only copy of unsaved documentation.

---

# 730. Confirm Documentation File

After saving:

```bash
ls -lh docs/
```

should show:

```text
BACKEND_DOCUMENTATION.md
```

The document should then be committed to Git.

---

# 731. Documentation Commit Recommendation

When the documentation is complete:

```bash
git add docs/BACKEND_DOCUMENTATION.md README.md
git commit -m "docs: add complete backend documentation"
git push origin main
```

Only include `README.md` in the command after it has actually been updated.

---

# 732. Operational Troubleshooting Philosophy

Troubleshooting should begin by identifying which layer is failing.

Use:

```text
Application
Database
Authentication
Authorization
Tenant scope
Subscription
Publication state
Payment provider
Deployment configuration
```

rather than changing code immediately.

---

# 733. API Does Not Start

Symptoms:

```text
Uvicorn exits
Import error
Settings validation error
Connection error
```

Check:

```bash
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Then inspect the first traceback rather than secondary errors.

---

# 734. Missing `DATABASE_URL`

Because `database_url` is required in Settings, absence of:

```env
DATABASE_URL=
```

can prevent application initialization.

Check:

```bash
grep DATABASE_URL .env
```

Do not print real production credentials into shared logs or screenshots.

---

# 735. Missing JWT Secret

`JWT_SECRET_KEY` is also required.

If missing, Settings initialization can fail before the application starts.

Verify the `.env` contains a value.

Do not use the placeholder secret in production.

---

# 736. PostgreSQL Connection Refused

Typical symptom:

```text
connection refused
127.0.0.1:5432
```

Under Ubuntu/WSL:

```bash
sudo service postgresql start
```

Then test:

```bash
sudo service postgresql status
```

---

# 737. PostgreSQL Password Authentication Failure

Example problem:

```text
password authentication failed for user "student_api"
```

Verify:

```text
username
password
database name
hostname
port
```

in `DATABASE_URL`.

Use explicit TCP testing:

```bash
PGPASSWORD=YOUR_PASSWORD \
psql -h 127.0.0.1 \
-U student_api \
-d student_result_db
```

---

# 738. Peer Authentication Failure

A command such as:

```bash
psql -U student_api -d student_result_db
```

may use the local Unix socket and PostgreSQL peer authentication.

For this project, explicit TCP is preferred:

```bash
psql -h 127.0.0.1 ...
```

This uses the password-authentication path expected by the API connection string.

---

# 739. API Healthy but Database Health Fails

If:

```http
GET /health
```

returns 200 while:

```http
GET /health/database
```

fails, FastAPI is running but PostgreSQL connectivity is not.

Investigate:

```text
PostgreSQL service
DATABASE_URL
credentials
database existence
port
host
network rules
```

---

# 740. Alembic Cannot Connect

If:

```bash
alembic current
```

fails with database authentication or connectivity errors, remember Alembic now uses:

```text
settings.database_url
```

from the same `.env` configuration as FastAPI.

Fix the environment rather than editing `alembic.ini` with a second connection URL.

---

# 741. Alembic Import Error

If future refactoring renames configuration exports, ensure:

```text
alembic/env.py
```

still imports valid configuration objects.

The production-hardening audit previously caught this exact class of issue when the old `DATABASE_URL` symbol was removed from `connection.py`.

---

# 742. More Than One Alembic Head

Check:

```bash
alembic heads
```

Expected frozen state:

```text
one head
```

Multiple heads indicate divergent migration branches.

Do not arbitrarily delete migrations.

Resolve the branch with proper Alembic merge/revision practices.

---

# 743. Alembic Detects Unexpected Changes

Run:

```bash
alembic check
```

If it reports new upgrade operations:

```text
Models and migration state are no longer synchronized
```

Review the changed models before generating a migration.

---

# 744. Authentication Returns 401

Investigate:

```text
Missing Authorization header
Malformed Bearer token
Invalid JWT signature
Expired token
Unknown User
```

Expected header:

```http
Authorization: Bearer <token>
```

---

# 745. Authentication Returns 403

Possible causes include:

```text
Inactive User
Inactive School
Wrong role
Missing active Subscription
```

A `403` should not automatically be interpreted as an invalid JWT.

---

# 746. Cross-School Resource Returns 404

This may be intentional.

Tenant isolation deliberately hides many foreign resources using:

```text
404 Not Found
```

Therefore a School Administrator requesting an existing ID from another School should still receive `404`.

---

# 747. Academic Write Returns Subscription 403

Message:

```text
An active subscription is required for this academic term
```

Verify:

```text
School
Academic Session
Term
Subscription status
```

The Subscription must match all three exactly and have:

```text
status = active
```

---

# 748. Academic Write Returns 409 After Publication

Message indicates results are published.

Workflow:

```text
Published
   ↓
Reopen result
   ↓
Correct academic data
   ↓
Republish
```

Do not bypass the publication lock directly at database level in normal operations.

---

# 749. Result Cannot Be Published

Check:

```text
Student Enrollment exists
Assessments exist
CA1 exists
CA2 exists
CA3 exists
EXAM exists
All required scores exist
Subscription is active
Class/session/term belong to School
```

A missing component results in an incomplete result.

---

# 750. Unexpected Class Position

Only Students with complete results participate in ranking.

Ties use competition ranking.

Example:

```text
90 → position 1
90 → position 1
85 → position 3
```

This is intentional.

---

# 751. Published Report Shows Older Data

When status is:

```text
published
```

the report endpoint prefers the stored published snapshot.

If academic data was corrected after reopening, the official snapshot is refreshed only after republishing.

---

# 752. Report Settings Seem Ignored

Check:

```text
school report settings
published snapshot state
```

A historical published snapshot reflects the report representation captured at publication time.

Changing live settings does not necessarily mutate an already published snapshot.

---

# 753. Payment Initialization Fails

Check:

```text
Subscription belongs to School
Subscription is pending
Plan exists
Plan is active where required
No successful payment already exists
Flutterwave secret key configured
Redirect URL configured
```

Provider communication failures can produce:

```text
502
```

rather than ordinary validation errors.

---

# 754. Payment Verification Fails

Provider transaction verification checks:

```text
Transaction ID
tx_ref
successful status
currency
amount
replay protection
```

A successful-looking Flutterwave response is not sufficient if any of these values mismatch.

---

# 755. Payment Webhook Fails

Verify:

```text
FLUTTERWAVE_SECRET_HASH
Webhook provider configuration
Raw request body
Signature/hash headers
Public webhook URL
Transaction reference
Provider transaction ID
```

The webhook intentionally does not require JWT authentication.

---

# 756. Flutterwave Webhook Is Public by Design

The endpoint must be reachable by Flutterwave.

Security comes from:

```text
Webhook secret validation
HMAC/signature verification
Provider transaction re-verification
Local payment lookup
Amount/currency/reference checks
Replay protection
```

Do not add normal User JWT authentication to this endpoint.

---

# 757. Tests Cannot Connect to PostgreSQL

Ensure the test database exists:

```text
student_result_test_db
```

and PostgreSQL is running.

Then migrate the test database before running Pytest.

---

# 758. Test Suite Safety

Never change the test URL to a production database.

The cleanup fixture performs destructive:

```sql
TRUNCATE ... RESTART IDENTITY CASCADE
```

operations.

The built-in name guard provides one layer of protection, but production credentials should never be placed in the test configuration.

---

# 759. Known Technical Debt

The frozen backend intentionally retains some known technical debt.

The main documented items are:

```text
datetime.utcnow() deprecation warnings
Naive database timestamp columns
Legacy Student authorization test route
Minimal README
No application-specific structured logging
No automatic Subscription expiry scheduler
No permanent multi-version report snapshot history
No Docker Compose file
No production monitoring implementation
No rate limiting on public School registration
```

These are not undocumented surprises.

---

# 760. Datetime Technical Debt

Several models and runtime paths still use:

```python
datetime.utcnow()
```

SQLAlchemy timestamp columns are currently predominantly naive rather than:

```text
timezone-aware
```

A partial replacement should be avoided.

---

# 761. Recommended Timestamp Modernization

Future timestamp modernization should be treated as one deliberate migration.

Target:

```text
PostgreSQL timestamptz
+
SQLAlchemy DateTime(timezone=True)
+
timezone-aware UTC Python datetime
```

Workflow:

```text
Audit every timestamp column
      ↓
Design migration
      ↓
Convert existing values safely
      ↓
Update Python defaults
      ↓
Update tests
      ↓
Run complete regression suite
```

---

# 762. Student Authorization Legacy Route

The route:

```http
GET /api/students/test
```

still relies on:

```text
require_student
```

However, current Student creation does not require User/login accounts.

The route should eventually be:

```text
removed
```

or retained only if a future Student portal is deliberately introduced.

---

# 763. School Registration Hardening

Public School registration is intentionally available for SaaS onboarding.

Before broad public launch, additional protections may be considered:

```text
Rate limiting
Email verification
CAPTCHA/anti-bot control
Stronger duplicate-abuse controls
Audit logging
```

These are production-hardening enhancements rather than current API requirements.

---

# 764. Subscription Expiration Automation

The Subscription model supports:

```text
expires_at
status = expired
```

but the reviewed backend does not currently contain a scheduler that automatically marks Subscriptions expired.

Expiration is therefore not documented as automatic.

---

# 765. Snapshot History Limitation

Current snapshot design stores one snapshot per:

```text
publication
+
student
```

After reopen and republish, the existing snapshot is refreshed.

Therefore the current system does not preserve:

```text
Version 1 report
Version 2 report
Version 3 report
```

as independent immutable records.

---

# 766. Future Report Versioning Option

If regulatory/audit requirements later require permanent report history, a future design could introduce:

```text
publication_version
snapshot_version
superseded_at
correction_reason
```

without altering the current frozen behavior retroactively.

---

# 767. Current Logging Limitation

The application does not yet implement comprehensive structured event logging.

Future commercial deployment would benefit from recording events such as:

```text
Login failure
Administrator creation
Administrator deactivation
Subscription activation
Payment verification
Result publication
Result reopening
```

without logging secrets or passwords.

---

# 768. Audit Log Future Enhancement

A future `audit_logs` table could contain:

```text
id
school_id
user_id
action
resource_type
resource_id
metadata
ip_address where appropriate
created_at
```

This should be designed carefully because audit logs themselves contain sensitive operational information.

---

# 769. Mobile Integration Objective

The next product phase is Flutter mobile integration.

The intended architecture is:

```text
Flutter Android Application
          ↓
      HTTPS / JSON
          ↓
       FastAPI
          ↓
      PostgreSQL
```

Payment flow also communicates with Flutterwave through the backend.

---

# 770. Mobile-First Distribution

The first mobile distribution target is:

```text
Android
```

Flutter remains appropriate because the same application architecture can later support:

```text
iOS
Web
```

if desired.

---

# 771. Flutter Should Not Access PostgreSQL Directly

The mobile application must communicate only with FastAPI.

Incorrect:

```text
Flutter
   ↓
PostgreSQL
```

Correct:

```text
Flutter
   ↓
FastAPI
   ↓
PostgreSQL
```

This keeps:

```text
Database credentials
Tenant filtering
Subscription enforcement
Authorization
Publication locks
Payment secrets
```

on the trusted server.

---

# 772. Flutter Should Not Contain Flutterwave Secret Key

The mobile application must never contain:

```text
FLUTTERWAVE_SECRET_KEY
FLUTTERWAVE_SECRET_HASH
JWT_SECRET_KEY
DATABASE_URL
```

These belong exclusively to backend infrastructure.

---

# 773. Flutter Authentication Flow

Recommended flow:

```text
Login Screen
    ↓
POST /api/auth/login
    ↓
Receive access_token
    ↓
Store token securely
    ↓
GET /api/users/me
    ↓
Determine account_type
    ↓
Load appropriate dashboard
```

---

# 774. Secure Token Storage

The JWT should not be stored in:

```text
plain text
debug logs
source code
hard-coded constants
```

Flutter should use an appropriate secure-storage mechanism for Android credentials.

---

# 775. Flutter API Base URL

Define one environment-dependent API base URL.

Example logical values:

```text
Development API
Staging API
Production API
```

Do not scatter hard-coded API addresses throughout widgets.

---

# 776. Suggested Flutter Network Layer

A clean mobile networking architecture can use:

```text
ApiClient
    ↓
Authentication interceptor
    ↓
Domain repositories
    ↓
State management
    ↓
Screens/widgets
```

This keeps HTTP details out of presentation code.

---

# 777. Suggested Flutter Domain Modules

Recommended client modules:

```text
auth
users
schools
admins

academic_sessions
terms
classes
subjects

teachers
students
enrollments
teaching_assignments

assessments
scores
attendance
comments

results
reports
publications

grading
report_settings

subscriptions
payments
```

These mirror the backend domains.

---

# 778. Flutter Model Generation

Flutter response models should be derived from:

```text
Pydantic response schemas
```

rather than SQLAlchemy models.

The API contract—not the internal database structure—is the mobile source of truth.

---

# 779. Nullable Flutter Models

Flutter must respect nullable fields.

For example:

```text
String?
DateTime?
double?
int?
```

should be used where the backend explicitly permits null.

Do not force defaults such as:

```text
null score → 0
```

because an incomplete score and a real zero are different academic meanings.

---

# 780. Flutter Result-State Modeling

The app should preserve backend result states such as:

```text
COMPLETE
INCOMPLETE
published
reopened
```

rather than converting them into simple booleans too early.

This allows the UI to explain the real academic workflow.

---

# 781. Flutter Error Handling

The network layer should distinguish:

```text
400 → invalid business request
401 → login/token issue
403 → permission/subscription issue
404 → unavailable or tenant-hidden resource
409 → conflict/current state prevents operation
422 → input validation
500 → backend/internal issue
502 → external payment-provider issue
```

Screens should show user-friendly messages without hiding the original error category.

---

# 782. Flutter 401 Strategy

For:

```text
401
```

the app should normally consider:

```text
Token missing
Token expired
Token invalid
```

and return to authentication when appropriate.

It should not automatically treat `403` or `404` the same way.

---

# 783. Flutter Subscription UX

Academic write screens should handle:

```text
403
An active subscription is required...
```

by showing a subscription/payment path rather than presenting the problem as a generic system failure.

---

# 784. Flutter Publication Lock UX

When the backend returns a publication-lock:

```text
409
```

the UI should explain:

```text
Results have already been published.
Reopen the results before making corrections.
```

An authorized administrator may then use the reopen workflow.

---

# 785. Flutter Payment Workflow

Recommended flow:

```text
Select Subscription Plan
        ↓
Create Subscription
        ↓
status = pending
        ↓
POST /api/payments/initialize
        ↓
Receive payment_link
        ↓
Open Flutterwave checkout
        ↓
Payment completed
        ↓
Webhook and/or manual verification
        ↓
Backend verifies directly with Flutterwave
        ↓
Payment = successful
Subscription = active
```

---

# 786. Client Does Not Activate Subscription

The Flutter app must never decide:

```text
subscription.status = active
```

after the user merely returns from a payment page.

Only the backend can activate the Subscription after provider verification.

---

# 787. Flutter Payment Success Screen

A client-side checkout-success redirect should be treated as:

```text
payment may have completed
```

not:

```text
payment definitely verified
```

Flutter should query/verify the backend state.

---

# 788. Flutter Result Entry Workflow

A School Administrator workflow may follow:

```text
Choose Session
    ↓
Choose Term
    ↓
Choose Class
    ↓
Choose Subject
    ↓
Load Assessments
    ↓
Load enrolled Students
    ↓
Enter scores
    ↓
Submit
    ↓
Backend validates
```

---

# 789. Flutter Report Workflow

Recommended sequence:

```text
Select Student
    ↓
Select Session
    ↓
Select Term
    ↓
GET report sheet
    ↓
Backend decides:
    published snapshot
    OR
    current live report
    ↓
Flutter renders response
```

Flutter does not need to reproduce result computation logic.

---

# 790. Keep Result Computation on Backend

Do not recalculate official:

```text
Total
Average
Grade
Remark
Position
Result status
```

independently in Flutter.

The backend remains authoritative.

Flutter should display the values returned by the API.

---

# 791. Offline Considerations

The initial Flutter version can remain online-first.

If offline functionality is introduced later, avoid allowing offline data to overwrite server academic records without conflict handling.

Sensitive workflows such as:

```text
Score submission
Publication
Payment
Subscription activation
Administrator management
```

should remain server-confirmed.

---

# 792. Teacher Mobile Experience

The backend already supports Teacher authentication.

A future Teacher interface can be introduced without changing the fundamental User architecture.

Potential future Teacher functions include:

```text
Assigned Classes
Assigned Subjects
Student lists
Score entry
Attendance entry
Comments
```

but these permissions are not currently exposed across the frozen API and should not be assumed by Flutter.

---

# 793. Platform Administrator Mobile Experience

Platform Admin features may include:

```text
View Schools
Manage Platform Admins
Manage School Admins
Manage Subscription Plans
View all Subscriptions
Manage allowed Subscription transitions
```

The Flutter UI should derive authorization from:

```text
account_type = platform_admin
```

rather than displaying these controls to every Admin.

---

# 794. School Administrator Mobile Experience

School Admin is the main operational account.

Suggested dashboard domains:

```text
School
Academics
People
Results
Reports
Subscription
Payments
Settings
```

---

# 795. Role-Based Navigation

After:

```http
GET /api/users/me
```

navigation can be decided from:

```text
account_type
role
```

Example:

```text
platform_admin
    ↓
Platform Dashboard

school_admin
    ↓
School Dashboard

teacher
    ↓
Teacher Dashboard
```

---

# 796. Avoid Trusting Client Role State

Even if Flutter hides a button, security must never depend on the UI.

A modified mobile client could still manually call an endpoint.

Therefore backend dependencies remain authoritative for every protected operation.

---

# 797. Android Emulator Localhost Warning

When Flutter runs on an Android emulator:

```text
127.0.0.1
```

refers to the emulator itself, not necessarily the Windows/WSL host API.

The development base URL must therefore point to an address reachable from the emulator.

The exact address depends on the chosen emulator/network setup.

---

# 798. Physical Android Device Development

A physical device must also reach the backend through a network-accessible development address.

The Uvicorn process may need to listen on:

```text
0.0.0.0
```

instead of only:

```text
127.0.0.1
```

and local firewall/network settings must permit access.

Do not expose development servers publicly without appropriate safeguards.

---

# 799. Production Mobile Networking

Production Flutter releases should call:

```text
HTTPS
```

only.

Cleartext HTTP should not be relied upon for production authentication, academic records, or payment workflows.

---

# 800. Complete SaaS Lifecycle

The full commercial lifecycle is:

```text
School Registration
        ↓
Initial School Admin
        ↓
Login
        ↓
Academic Session
        ↓
Terms
        ↓
Classes
        ↓
Subjects
        ↓
Teachers
        ↓
Students
        ↓
Enrollment
        ↓
Teaching Assignments
        ↓
Subscription Plan Selection
        ↓
Term Subscription
        ↓
Payment Initialization
        ↓
Flutterwave Verification
        ↓
Subscription Active
        ↓
Assessments
        ↓
Scores
        ↓
Attendance
        ↓
Comments
        ↓
Result Computation
        ↓
Grading
        ↓
Class Position
        ↓
Report Preview
        ↓
Publication
        ↓
Published Snapshot
        ↓
Historical Retrieval
```

---

# 801. Tenant Boundary Diagram

```text
                    PLATFORM
                       │
        ┌──────────────┴──────────────┐
        │                             │
     SCHOOL A                      SCHOOL B
        │                             │
 ┌──────┼──────┐               ┌──────┼──────┐
 │      │      │               │      │      │
Users Classes Students        Users Classes Students
 │      │      │               │      │      │
 └──── School A Data           └──── School B Data
```

No school-bound operation should cross the center boundary.

---

# 802. Authentication and Authorization Diagram

```text
Email + Password
       ↓
POST /api/auth/login
       ↓
Password verification
       ↓
User active?
       ↓
School active?
       ↓
Create JWT
       ↓
Bearer Token
       ↓
get_current_user
       ↓
Role Dependency
       ↓
Tenant Validation
       ↓
Business Operation
```

---

# 803. Subscription Gate Diagram

```text
Academic Write Request
        ↓
Authenticated School
        ↓
Academic Session
        ↓
Term
        ↓
Exact Subscription lookup
        ↓
status == active?
      /             \
    YES              NO
     ↓                ↓
Continue          403 Forbidden
```

---

# 804. Publication Workflow Diagram

```text
Complete Academic Data
        ↓
Active Subscription
        ↓
Publication Readiness Check
        ↓
All Students Complete?
      /                \
    YES                 NO
     ↓                   ↓
Create/Reuse          Reject
Publication
     ↓
Generate Reports
     ↓
Store Snapshots
     ↓
status = published
     ↓
Lock Academic Sources
```

---

# 805. Correction Workflow Diagram

```text
Published Result
      ↓
Reopen
      ↓
status = reopened
      ↓
Locks released
      ↓
Correct scores/data
      ↓
Republish
      ↓
Same publication reused
      ↓
Existing snapshot refreshed
      ↓
status = published
```

---

# 806. Payment Security Diagram

```text
Flutter
   ↓
Initialize Payment
   ↓
FastAPI creates tx_ref
   ↓
Flutterwave Checkout
   ↓
Provider reports transaction
   ↓
FastAPI verifies directly
   ↓
Check:
 ID
 Reference
 Status
 Currency
 Amount
 Replay
   ↓
Payment Successful
   ↓
Subscription Active
```

---

# 807. Data Authority Diagram

```text
Flutter
  │
  │ request
  ▼
FastAPI
  │
  ├── authentication
  ├── authorization
  ├── tenant scope
  ├── subscription gate
  ├── validation
  ├── result computation
  ├── publication integrity
  └── payment verification
  │
  ▼
PostgreSQL
```

Flutter is a client.

FastAPI is the trusted business authority.

---

# 808. Security Layers Summary

The commercial SaaS uses multiple defensive layers:

```text
HTTPS at deployment
        ↓
JWT Authentication
        ↓
Active User
        ↓
Active School
        ↓
Role Authorization
        ↓
Tenant Isolation
        ↓
Pydantic Validation
        ↓
Subscription Entitlement
        ↓
Publication Locks
        ↓
Database Constraints
        ↓
Payment Provider Verification
```

---

# 809. Data Integrity Layers

Academic integrity is protected through:

```text
Enrollment validation
Assessment structure
Score bounds
Attendance arithmetic
Grading configuration
Completeness checks
Class ranking logic
Publication readiness
Published-data locks
Report snapshots
```

---

# 810. Commercial Integrity Layers

Commercial access is protected through:

```text
Server-controlled plan price
Server-controlled tx_ref
Pending Subscription requirement
Flutterwave verification
Amount comparison
Currency comparison
Reference comparison
Provider transaction reuse prevention
Atomic Subscription activation
```

---

# 811. Future Feature Candidates

Potential post-MVP enhancements include:

```text
Teacher operational permissions
Student/parent portal
Result PDF export
Email notifications
Push notifications
School analytics
Bulk CSV import
Bulk score entry
Automatic Subscription expiry
Invoice/receipt generation
Payment history exports
Audit logs
Result version history
Multi-factor authentication
Password reset
Email verification
Rate limiting
Background jobs
Object-storage logo uploads
```

These are future features, not current frozen backend behavior.

---

# 812. Student and Parent Portal Future Architecture

If Student access is introduced later, it should use a deliberate authentication model rather than automatically assuming every Student record needs a User.

Possible design:

```text
Student academic record
        ↓
Optional portal identity
        ↓
Read-only own reports/results
```

Parent/guardian access may require a separate relationship model.

---

# 813. Teacher Permissions Future Architecture

Teacher permissions should be based on:

```text
TeachingAssignment
```

rather than giving every Teacher access to all School records.

For example:

```text
Teacher
  ↓
TeachingAssignment
  ↓
Specific Subject
  ↓
Specific Class
  ↓
Specific Academic Session
```

---

# 814. Bulk Operations Future Enhancement

Schools may eventually require bulk operations for:

```text
Student import
Enrollment
Assessment creation
Score entry
Attendance
```

Bulk endpoints must preserve the same:

```text
Tenant checks
Subscription checks
Publication locks
Validation
```

as single-record endpoints.

---

# 815. Background Job Candidates

A future task queue may be useful for:

```text
Email delivery
Push notifications
Report PDF generation
Bulk imports
Subscription expiry
Scheduled reminders
Audit exports
```

These processes are intentionally outside the current synchronous backend.

---

# 816. Observability Future Enhancement

Commercial production should eventually add:

```text
Structured logs
Central log aggregation
Error monitoring
Performance metrics
Database monitoring
Payment-event monitoring
Uptime alerts
```

Health endpoints alone are not a complete observability system.

---

# 817. Backup and Disaster Recovery

Because academic records are important long-lived data, production infrastructure should define:

```text
Backup frequency
Backup retention
Restore testing
Point-in-time recovery
Disaster recovery procedure
```

These belong to operational infrastructure.

---

# 818. Production Deployment Checklist

Before a real production launch:

```text
[ ] Production PostgreSQL configured
[ ] Automated backups configured
[ ] Production DATABASE_URL configured
[ ] Strong JWT secret configured
[ ] Allowed hosts restricted
[ ] CORS origins restricted where needed
[ ] HTTPS enabled
[ ] Flutterwave production credentials configured
[ ] Flutterwave webhook configured
[ ] Alembic at head
[ ] Full test suite passes
[ ] Health checks pass
[ ] Documentation saved and committed
[ ] Production logging/monitoring reviewed
[ ] Android production API URL configured
```

---

# 819. Backend Change Checklist

For every future backend change:

```text
[ ] Understand affected domain
[ ] Preserve tenant isolation
[ ] Preserve role authorization
[ ] Check Subscription implications
[ ] Check publication-lock implications
[ ] Update schemas
[ ] Update tests
[ ] Create migration if database changed
[ ] Inspect migration
[ ] Run focused tests
[ ] Run full tests
[ ] Run alembic check
[ ] Update documentation
[ ] Commit
[ ] Push
```

---

# 820. Flutter Integration Checklist

Before building individual screens:

```text
[ ] Create Flutter project
[ ] Configure environment-specific API URL
[ ] Build shared ApiClient
[ ] Implement Bearer-token interceptor
[ ] Implement secure token storage
[ ] Implement Login API
[ ] Implement /api/users/me bootstrap
[ ] Create role-based navigation
[ ] Define Pydantic-equivalent Dart models
[ ] Implement common API error model
[ ] Add loading/error states
```

Then add domains incrementally.

---

# 821. Recommended Flutter Development Order

A practical implementation sequence is:

```text
1. Flutter project foundation
2. Networking
3. Authentication
4. School Admin dashboard
5. Academic Sessions
6. Terms
7. Classes
8. Subjects
9. Teachers
10. Students
11. Enrollments
12. Teaching Assignments
13. Subscription Plans
14. Subscriptions
15. Payment flow
16. Assessments
17. Scores
18. Attendance
19. Comments
20. Results
21. Report sheets
22. Publication
23. Report settings
24. Platform Admin functionality
```

This follows the dependency order of the backend.

---

# 822. Why Subscription Comes Before Result Entry UI

The backend requires an active Subscription for protected academic writes.

Therefore Flutter should implement:

```text
Subscription status
+
Payment activation
```

before presenting the result-entry workflow as fully operational.

Otherwise users may repeatedly reach valid backend `403` responses without an obvious path to resolve them.

---

# 823. Recommended Mobile MVP

The initial Android MVP can focus on:

```text
Login
School Admin dashboard
Academic setup
Student management
Teacher management
Enrollment
Subscription
Flutterwave payment
Assessment setup
Score entry
Attendance/comments
Result display
Report display
Publication
```

Platform Admin functionality can be included either in the same application through role-based navigation or in a later administrative interface.

---

# 824. API Compatibility Principle

Backend version:

```text
1.0.0
```

should remain stable during initial Flutter integration.

Avoid changing:

```text
Route paths
JSON field names
Nullability
Status semantics
Assessment structure
```

unless the mobile client and backend are intentionally upgraded together.

---

# 825. Backend Freeze Meaning

The backend freeze does not mean:

```text
No future changes are ever allowed
```

It means:

```text
Current backend contract is stable
        ↓
Document it
        ↓
Build Flutter against it
        ↓
Future changes become controlled revisions
```

---

# 826. Frozen Backend Verification State

The documented backend state includes:

```text
API version: 1.0.0
Migration head: 7b933b5b8b78
Regression tests: 178 passed
Git freeze commit: 074f4df
Branch: main
Remote: synchronized
```

---

# 827. Final System Architecture

```text
                 ┌─────────────────────┐
                 │ Flutter Android App │
                 └──────────┬──────────┘
                            │
                          HTTPS
                            │
                 ┌──────────▼──────────┐
                 │    FastAPI 1.0.0    │
                 │                     │
                 │ Authentication      │
                 │ Authorization       │
                 │ Tenant Isolation    │
                 │ Academic Logic      │
                 │ Subscription Logic  │
                 │ Publication Logic   │
                 │ Payment Logic       │
                 └──────┬───────┬──────┘
                        │       │
              SQLAlchemy│       │HTTPS
                        │       │
             ┌──────────▼───┐   │
             │ PostgreSQL   │   │
             └──────────────┘   │
                               │
                        ┌──────▼───────┐
                        │ Flutterwave  │
                        └──────────────┘
```

---

# 828. Product Architecture Summary

The project has evolved into a:

```text
Multi-school
Multi-admin
Subscription-controlled
Result-management SaaS
```

with:

```text
Role-based authentication
Tenant-isolated data
Academic result computation
Publication controls
Immutable-while-published report snapshots
Termly subscriptions
Flutterwave payments
Automated security regression tests
Container deployment support
Mobile-ready REST API
```

---

# 829. Documentation Scope Completed

The backend documentation now covers:

```text
Project purpose
Architecture
Technology stack
Repository structure
Database entities
Relationships
Multi-school tenancy
Authentication
Authorization
Administrator management
Academic configuration
Teachers
Students
Enrollment
Teaching assignments
Assessments
Scores
Attendance
Comments
Grading
Result computation
Class position
Report sheets
Report settings
Publication
Snapshots
Subscription plans
Term subscriptions
Flutterwave payments
Pydantic schemas
API endpoint reference
Environment configuration
PostgreSQL
Alembic
Docker
Testing
Security regression
Troubleshooting
Technical debt
Flutter integration
Operational workflows
Future enhancements
```

---

# 830. Backend Documentation Status

At this point:

```text
Backend implementation      COMPLETE
Backend regression audit    COMPLETE
Backend freeze              COMPLETE
Backend documentation       COMPLETE
Flutter integration         NEXT PHASE
```

---

# 831. Recommended Immediate Actions

Before starting Flutter:

```text
1. Ensure docs/BACKEND_DOCUMENTATION.md is safely saved.
2. Remove stale Vim swap file only after confirming the document.
3. Review the final Markdown document.
4. Update the minimal README.
5. Commit and push the documentation.
6. Create the Flutter project.
7. Begin with authentication and shared networking.
```

---

# 832. Final Backend Statement

The Student Result Management API is now documented as a stable backend contract for the first mobile application release.

The architecture provides a clear separation of responsibility:

```text
Flutter
→ user experience

FastAPI
→ trusted business logic

PostgreSQL
→ persistent data

Flutterwave
→ external payment processing
```

The backend should remain the authoritative source for:

```text
Authentication
Role permissions
School tenancy
Subscriptions
Academic validation
Result computation
Publication state
Reports
Payment verification
```

This separation should be preserved throughout Flutter development.

