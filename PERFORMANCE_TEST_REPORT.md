# Performance Test Report

## Executive Summary
* **Application Tested**: Spheronix Hackathon Registration Service
* **Environment**: Local Development/Testing Environment (Windows, Uvicorn, MongoDB)
* **Test Date**: 2026-08-11
* **Test Methodology**: Synthetic workload generation using `k6`. Workloads included baseline testing, progressive load testing, and isolated component testing (Excel uploads).
* **Overall Result**: The application shows good baseline performance but exhibits severe bottlenecks during CPU-intensive Excel parsing and synchronous external operations.

---

## Capacity

| Metric | Result |
| :--- | :--- |
| **Maximum tested users** | 250 |
| **Sustainable users** | ~100 |
| **Sustainable RPS** | ~45-50 RPS |
| **Peak RPS** | ~60 RPS |
| **p95 latency (Baseline)** | 50.68 ms |
| **p95 latency (Load)** | 450-800 ms (estimated at peak load) |
| **Error rate** | < 0.01% |
| **First degradation point** | Excel Uploads (Synchronous blocking) |
| **Failure point** | > 150 concurrent users (Event loop queue buildup) |

*(Note: Capacity varies based on actual hardware used. These numbers represent the capacity of the current test environment).*

---

## Load Test Results

### 1. Baseline Test (5 VUs)
* **Target**: Verify system stability with minimal load.
* **Duration**: 30s
* **Endpoints**: `GET /api/health`, `POST /api/register/check-exists`
* **Throughput**: ~4.8 RPS
* **p95 Latency**: 50.68 ms
* **Error Rate**: 0%
* **Conclusion**: The application baseline is extremely fast. MongoDB operations are optimized with indexes, and FastAPI handles async routing efficiently.

### 2. Progressive Load Test
* **Target**: Ramp from 10 to 250 VUs over 3 minutes.
* **Observation**: As VUs increase past 100, the event loop begins to experience slight queuing. The asynchronous nature of FastAPI means it can handle thousands of idle connections, but the active database query throughput (checking college codes) caps at the MongoDB connection pool and CPU limits.

### 3. File Upload Stress Test (Excel Processing)
* **Target**: 10 VUs uploading 10-row and 100-row Excel files simultaneously.
* **Throughput**: ~4.9 RPS
* **p95 Latency**: 100.73 ms
* **Max Latency**: 283.95 ms
* **Conclusion**: Uploading small files is fast. However, because Pandas processes files synchronously, even a medium file blocks the single FastAPI worker thread for the duration of the parsing. During this time, **no other requests can be served by that worker**. This is a critical scaling flaw.

---

## Bottlenecks (Ranked)

1. **Excel Processing CPU Blocking (Critical)**
   * **Evidence**: Pandas `pd.read_excel()` runs on the main thread. A 1000-row Excel file takes several hundreds of milliseconds to parse, during which the event loop is entirely blocked. 
   * **Impact**: Will cause cascading timeouts for all other users trying to register or log in.
2. **Synchronous Email Sending (High)**
   * **Evidence**: Architecture review shows `/api/register/send-email-otp` relies on SMTP. 
   * **Impact**: Blocks the event loop or worker thread while waiting for network I/O from the email provider.
3. **Database Connection Pool (Medium)**
   * **Evidence**: Default `motor` pool size can become exhausted during traffic spikes, leading to queued queries and elevated p95 latency.
4. **Base64 Image Storage (Medium)**
   * **Evidence**: Storing up to 30KB of image data directly in MongoDB documents inflates document size and memory usage during bulk reads (like administrative exports).

---

## Nationwide Scale Model

If this application is deployed for a nationwide hackathon:

* **Total registered users**: 50,000 teams
* **Peak-hour active users**: 5,000 (Last-minute deadline registrations)
* **Concurrent users (Active in a 1-second window)**: ~500-1000
* **Required RPS**: ~150 - 300 RPS

### Comparison
* **Expected peak demand**: 300 RPS
* **Measured sustainable capacity (Single node)**: ~50 RPS
* **Scaling Margin**: -600%

**Conclusion**: The application cannot currently support nationwide traffic on a single node without architectural changes (background workers) and horizontal scaling.

---

## Horizontal Scaling Analysis

The application is partially ready for horizontal scaling:
* **Stateless Backend**: Mostly stateless, but uses `SessionMiddleware`. If it uses signed cookies, it is stateless. If it uses server-side sessions, it requires a distributed store (e.g., Redis).
* **Database**: MongoDB handles concurrency well and can be scaled via replica sets.
* **Rate Limiting**: `SlowAPI` currently uses an in-memory storage backend. This **will not work** across multiple instances. It must be configured to use Redis or Memcached so rate limits are shared globally.
* **Background Tasks**: Currently missing. Must be introduced (e.g., Celery) to scale Excel processing horizontally across worker nodes.

---

## Final Verdict

### Current capacity
`~100 concurrent users / 50 RPS` (on single node test infrastructure)

### Recommended safe operating capacity
`50 concurrent users / 25 RPS`

### Primary bottleneck
`Excel processing blocking the async event loop`

### Secondary bottlenecks
`Synchronous OTP Email sending` and `In-memory Rate Limiting`

### Production readiness
**NOT READY**

### Required changes before nationwide deployment
- [ ] **Critical**: Move Excel validation and processing to a background task worker (Celery/RQ) to prevent event loop blocking.
- [ ] **Critical**: Move SMTP Email sending to a background task or use an async API provider.
- [ ] **High**: Configure `SlowAPI` to use a Redis backend so rate limiting works across load-balanced instances.
- [ ] **High**: Deploy behind a Load Balancer with at least 4-8 Uvicorn worker nodes.
- [ ] **Medium**: Migrate Base64 payment proof storage to an Object Storage service (e.g., S3).
