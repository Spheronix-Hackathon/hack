# Performance Architecture Analysis

## 1. Application Architecture Overview
The application is a Python-based web service built on **FastAPI** with an asynchronous **MongoDB** backend (Motor driver). It runs behind **Uvicorn** and is designed to handle hackathon registrations, file uploads (Excel/CSV), payment proof submissions, and administrative tasks.

### Key Technologies:
* **Framework**: FastAPI (Asynchronous ASGI framework)
* **Server**: Uvicorn + Gunicorn (typically used in production)
* **Database**: MongoDB (motor for async operations)
* **Data Validation**: Pydantic & Custom `ExcelValidator`
* **Rate Limiting**: SlowAPI (in-memory rate limiter based on limits)
* **Authentication**: JWT based authentication (PyJWT), OTP via Email (using external SMTP, likely Authlib/Email-validator involved)
* **File Processing**: Pandas, openpyxl, python-multipart for Excel/CSV parsing and validation.

## 2. Request Flow
1. **Client** (Browser/API) sends an HTTP Request.
2. **Reverse Proxy** (e.g., Nginx) forwards the request to the application. The app trusts `127.0.0.1` via `ProxyHeadersMiddleware`.
3. **Middlewares**:
   - `ProxyHeadersMiddleware`: Resolves client IP.
   - `CORSMiddleware`: Handles cross-origin requests.
   - `SessionMiddleware`: Manages sessions.
   - `SlowAPI Rate Limiter`: Checks if the client has exceeded request limits.
4. **Router/Controller**: Routes request to specific endpoint (e.g., `/api/register/submit`, `/api/dashboard/upload-data`).
5. **Service Layer**: Handles business logic, OTP verification, Excel validation (`ExcelValidator.validate()`).
6. **Database Layer**: Asynchronous MongoDB operations via `motor` (`async_client`).
7. **Response**: JSON payloads or redirect responses returned to the client.

## 3. Critical User Journeys (CUJ)
1. **Nodal Officer Registration (Write-Heavy & External Dependency)**:
   - Request OTP (`/api/register/send-email-otp`) -> Requires external SMTP/Email service.
   - Verify OTP & Submit Registration (`/api/register/submit`) -> Creates unique indexes in MongoDB.
2. **Authentication (Read-Heavy)**:
   - Login flow creating JWT tokens and fetching user session data (`/api/dashboard/me`).
3. **Excel File Upload & Validation (CPU & Memory Intensive)**:
   - Upload Excel/CSV (`/api/dashboard/upload-data`).
   - Parse using Pandas (high memory usage for large files).
   - Validation logic loops through rows checking for duplicates, regex matches, and team constraints.
4. **Final Payment Proof Submission (I/O Heavy)**:
   - Base64 encoding of image (limited to 30KB).
   - Storing image data URI directly in MongoDB (`/api/payment/submit`).

## 4. Database Dependencies
* **Collections**: `nodal_registrations`, `users`, `settings`, `submissions`, `contacts`.
* **Indexes**: Extensive unique indexes on `nodal_registrations` (collegeCode, principalEmail, nodalOfficerEmail, etc.). 
* **Write Pattern**: High write contention on `nodal_registrations` due to unique indexes during bulk registrations.
* **Read Pattern**: Dashboard data fetching and pre-validation checks (`/api/register/check-exists`).

## 5. External Dependencies
* **Email Provider**: Used for OTP sending. If the SMTP server is slow, it will block or slow down the OTP endpoints, causing thread exhaustion or timeout buildup.
* **MongoDB**: External database connection. The application uses a single async client pool.

## 6. Suspected Bottlenecks
1. **Excel Processing (`upload-data` endpoint)**:
   - Pandas reads the entire file into memory (`io.BytesIO(content)`).
   - Synchronous processing within an async endpoint. Although it's bound by Python's GIL, this operation can block the event loop for large files, degrading concurrent request performance.
2. **OTP Sending (`send-email-otp` endpoint)**:
   - If the email service is synchronous or slow, this will become an immediate bottleneck under high registration load.
3. **Base64 Image Storage**:
   - Storing base64 encoded images directly in MongoDB documents (even if limited to 30KB) can lead to large document sizes, impacting read/write latency and memory if queried frequently.
4. **MongoDB Connection Pool**:
   - High concurrency might exhaust the default connection pool if not tuned for Motor.

## 7. Components Requiring Special Load Testing
* `/api/dashboard/upload-data`: Needs testing with various file sizes (10, 100, 1000 rows) to monitor CPU and event loop blocking.
* `/api/register/send-email-otp`: Needs to simulate high concurrency to verify SMTP handling.
* `/api/register/submit`: Needs concurrent testing to monitor MongoDB index contention and write performance.

## 8. Recommended Test Strategy
1. **Baseline Testing**: Identify minimal latency on all endpoints with 1-10 users.
2. **Isolate Excel Processing**: Run a specialized load test only for Excel uploads to measure CPU bound event loop latency.
3. **Database Contention Test**: Simulate simultaneous registrations attempting to register the same college/email to test index enforcement and database locking.
4. **End-to-End CUJ Test**: Simulate a complete user journey (Register -> OTP -> Upload Excel -> Submit Payment) with realistic think times.
5. **Spike Testing**: Simulate a sudden surge of registrations (e.g., deadline day).
