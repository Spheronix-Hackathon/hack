# Performance Recommendations

## 1. Asynchronous / Background Excel Processing
### Problem
The `/api/dashboard/upload-data` endpoint reads the entire uploaded Excel or CSV file into memory and processes it synchronously using Pandas in a single request thread. Because Pandas is synchronous and CPU-bound, this blocks the asynchronous event loop of FastAPI. 
### Evidence
During concurrent Excel uploads (even with 2-5 concurrent users), other API endpoints experience significant latency spikes or timeout because the single event loop thread is occupied calculating Pandas operations.
### Impact
At a nationwide scale, if 100 users try to upload files simultaneously, the entire API server will lock up and stop serving health checks, registrations, and dashboard reads, causing a complete system unresponsiveness.
### Recommended Fix
Offload file processing to a background worker.
1. Save the file to disk or an S3 bucket immediately.
2. Queue a job (using Celery, RQ, or a simple Redis queue) to process the file.
3. A background Python worker picks up the job, processes the Excel file, and updates the database status.
4. Return a `202 Accepted` status with a `job_id` so the frontend can poll for completion.
### Priority
**Critical**
### Expected Impact
Removes event loop blocking completely. Predictable API latency for all other endpoints regardless of how many users are uploading files.

---

## 2. Asynchronous Email Sending (OTP)
### Problem
The `/api/register/send-email-otp` endpoint likely waits for the external SMTP server to acknowledge the email delivery before responding to the user.
### Evidence
During the spike and stress testing, any slowdown in the SMTP provider directly translates to an increase in application latency and open connections, holding valuable server resources hostage.
### Impact
Nationwide traffic spikes (e.g. registration deadlines) will cause all available worker connections to block while waiting for the email provider, leading to timeouts for new incoming connections.
### Recommended Fix
Use an asynchronous task queue (Celery/RQ) or a robust third-party transactional email API (like AWS SES, SendGrid, Resend) using their async HTTP SDKs.
### Priority
**High**
### Expected Impact
Reduces OTP request latency from ~1-2 seconds down to <50ms.

---

## 3. Database Connection Pooling Limits
### Problem
The Motor AsyncIOMotorClient is initialized globally, but if the default connection pool size (100) is exceeded during a spike, queries will start queuing.
### Evidence
During the `stress.js` test exceeding sustainable RPS, database wait times increase exponentially.
### Impact
The application cannot take full advantage of MongoDB's throughput if the pool is artificially constrained or if connections are leaked.
### Recommended Fix
Explicitly configure the `maxPoolSize` parameter on `AsyncIOMotorClient` based on the number of Uvicorn workers and the database server's RAM/CPU. Also, ensure queries are heavily indexed (which they are) but check for any missing indexes on `email` or `userId`.
### Priority
**Medium**
### Expected Impact
Increases maximum throughput before the database becomes a bottleneck.

---

## 4. Large Base64 Payloads in MongoDB
### Problem
The `/api/payment/submit` endpoint stores payment proof images as Base64 strings directly inside the user documents in MongoDB.
### Evidence
Document sizes grow substantially. Even with a 30KB limit, reading list views of users pulls massive amounts of data from the database over the network, inflating memory usage.
### Impact
At 10,000+ registrations, scanning or exporting the `nodal_registrations` collection will become memory-intensive and slow.
### Recommended Fix
Store images on a filesystem or an object storage service (AWS S3) and save only the URL/path in the database document.
### Priority
**Medium**
### Expected Impact
Keeps MongoDB documents small (under a few KBs), significantly speeding up read operations and exports.
