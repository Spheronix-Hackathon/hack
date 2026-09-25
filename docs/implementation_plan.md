# Implementation Plan - UTR + Payment Receipt OCR Verification

Implement and fix the Payment UTR + Payment Receipt OCR verification flow for the Spheronix Hackathon Registration project, strictly adhering to the **Zero Database Changes** rule (no schema changes, no index changes, no migrations, no modifications to existing records).

---

## User Review Required

> [!IMPORTANT]
> **Zero Database Changes Adherence**:
> - Existing collections, documents, records, fields, types, and indexes will remain **100% READ-ONLY**.
> - Startup migrations and `$unset` routines in `app/database/mongodb.py` will be safely deactivated so that starting or running the application never mutates existing database records or indexes.
> - Fee calculation will use `DEFAULT_REGISTRATION_FEE=1` (₹1 per participant) calculated securely on the server.

---

## Proposed Changes

### Configuration & Settings

#### [MODIFY] [.env](file:///d:/hackathon%20registration/hackathon%20registration/.env)
- Update `DEFAULT_REGISTRATION_FEE=1` (from 399).

#### [MODIFY] [config/settings.py](file:///d:/hackathon%20registration/hackathon%20registration/config/settings.py)
- Change default `default_registration_fee` to `1.0`.

#### [MODIFY] [app/services/settings_service.py](file:///d:/hackathon%20registration/hackathon%20registration/app/services/settings_service.py)
- Ensure fallback registration fee defaults to `1.0` if not set in DB settings.

---

### Database Layer (Safety & Preservation)

#### [MODIFY] [app/database/mongodb.py](file:///d:/hackathon%20registration/hackathon%20registration/app/database/mongodb.py)
- Deactivate startup migrations, bulk updates, `$unset` operations, and index modifications in `initialize_async_collections()`.
- Preserve existing collections and indexes as strictly read-only.

---

### Backend Services & API Routers

#### [MODIFY] [app/services/payment_service.py](file:///d:/hackathon%20registration/hackathon%20registration/app/services/payment_service.py)
- Validate 12-digit numeric UTR strictly (`^\d{12}$`).
- Check for duplicate UTR among completed registrations using existing collections (read-only query).
- Recalculate total fee server-side (`participant_count * fee_per_member`), never trusting browser-supplied totals.
- Support OCR mismatch detection if receipt is provided during verification/submission.

#### [MODIFY] [app/services/registration_service.py](file:///d:/hackathon%20registration/hackathon%20registration/app/services/registration_service.py)
- Implement `resolve_receipt_storage` helper to safely populate `payment_receipt_url`, `payment_receipt_base64`, and `payment_receipt_name` for new registrations using existing fields without touching existing records.
- Enforce backend validation of 12-digit UTR and server-side fee calculation.

#### [MODIFY] [app/routers/students.py](file:///d:/hackathon%20registration/hackathon%20registration/app/routers/students.py)
- In `/api/all-users-json`, ensure `paymentReceiptUrl`, `paymentReceiptBase64`, and `paymentReceiptName` are included in the output.
- Dynamic fee calculation in draft autosave instead of hardcoded 399.

---

### Frontend (OCR Flow, UI, & Bug Fixes)

#### [MODIFY] [static/index.html](file:///d:/hackathon%20registration/hackathon%20registration/static/index.html)
- Include Tesseract.js: `<script src="https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js"></script>`.
- Place Receipt Upload dropzone alongside UTR input in Step 4 so the user can enter UTR and upload receipt in the payment flow.
- Add OCR status indicator, Match badge (`✓ Uploaded & Verified | UTR: <number>`), Mismatch warning alert box, and the Auto-correct button (`Re-enter UTR (<detected_utr>)`).

#### [MODIFY] [static/js/script.js](file:///d:/hackathon%20registration/hackathon%20registration/static/js/script.js)
- Declare `summaryReceiptLink` and `summaryReceiptRow` at the top level to resolve `ReferenceError: summaryReceiptLink is not defined`.
- Implement Tesseract.js OCR scanning on receipt upload (PNG, JPG, JPEG, WEBP).
- Implement robust UTR extraction using regex tailored to receipt patterns (`UTR`, `UPI Ref`, `Reference No`, `Txn ID`, `RRN`, etc.) and normalization to 12 digits.
- Compare entered UTR with detected UTR:
  - **MATCH**: Show `✓ Uploaded & Verified | UTR: <number>`, allow continuation.
  - **MISMATCH**: Show `⚠ UTR Mismatch`, display both entered and receipt UTRs, highlight receipt dropzone in red, provide `[ Re-enter UTR (<detected_utr>) ]` button, and BLOCK submission.
  - **OCR_UNABLE_TO_DETECT**: Display clear message for manual verification flow without false mismatch alert.
- Auto-correct button handler: copies detected UTR to UTR input, revalidates, and sets UI to match state.
- Dynamic fee calculation in frontend using server settings (₹1 per member).
- Ensure submit button state is always restored from `Submitting...` upon error or failure.

#### [MODIFY] [static/css/style.css](file:///d:/hackathon%20registration/hackathon%20registration/static/css/style.css)
- Add styles for OCR scanning spinner/progress, verified match badge, mismatch alert container, and the re-enter action button.

---

## Verification Plan

### Automated / Programmatic Tests
- Run Python test script verifying:
  1. UTR validation (12 digits pass, 11/13/letters fail).
  2. Fee calculation (1 participant -> ₹1, 2 participants -> ₹2, etc.).
  3. Tampered amount rejection by backend.
  4. Server-side receipt file upload validation.
  5. Database structure integrity verification (confirming zero existing records modified, zero schema changes, zero index modifications).

### Manual / Browser Verification
- Open the application in browser:
  1. Authenticate / enter student details.
  2. Select 1 participant -> verify fee shows ₹1. Select 2 participants -> verify fee shows ₹2.
  3. Enter UTR: `487499545986` and upload receipt containing `487499545984`.
  4. Verify Mismatch alert displays both numbers, highlights receipt in red, and blocks submit.
  5. Click `Re-enter UTR (487499545984)` -> verify input updates and UI shows verified match.
  6. Verify submit works and button does not get stuck.
