import logging
import re

from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from fastapi.responses import Response
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

from app.core.rate_limit import limiter
from app.core.time_utils import ist_now

from app.database.mongodb import colleges_async_collection, registrations_async_collection
from app.models.schemas import (
    DuplicateCheck,
    RegistrationSummaryResponse,
    StudentDraft,
    StudentRegister,
    StudentResponse,
)
from app.services.challenge_service import get_registration_summary

from app.services.receipt_service import build_receipt_pdf, verify_receipt_token
from app.services.registration_service import register_student as register_student_service
from app.services.settings_service import get_registration_fee
from config.settings import get_settings

router = APIRouter(tags=["students"])
settings = get_settings()

# Simple email regex for path-parameter validation (B-02)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# Fix C-03: Admin API key dependency
async def require_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")):
    """Protect admin-only endpoints with a shared API key header.
    Set ADMIN_API_KEY in .env to enable. Generate a strong random key with:
        python -c "import secrets; print(secrets.token_urlsafe(32))"
    """
    if not settings.admin_api_key or settings.admin_api_key == "change-this-admin-key":
        raise HTTPException(
            status_code=503,
            detail="Admin API key is not configured on this server. Set ADMIN_API_KEY in .env.",
        )
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid or missing X-Admin-Key header.",
        )


async def resolve_college_name(student: StudentRegister) -> str:
    selected_college = (student.collegeName or "").strip()
    if not selected_college:
        raise HTTPException(status_code=400, detail="College selection is required")

    if selected_college.lower() == "other":
        raise HTTPException(status_code=400, detail="Please select your college from the list. 'Other' option is not available.")

    existing = await colleges_async_collection.find_one(
        {"name_lc": selected_college.lower(), "is_other": False},
        {"_id": 0, "name": 1},
    )
    if not existing:
        raise HTTPException(status_code=400, detail="Invalid college selected. Please select your college from the list.")
    return str(existing.get("name", selected_college)).strip()


@router.get("/api/check-email/{email}")
@limiter.limit("20/minute")
async def check_email_exists(request: Request, email: str):
    # Fix B-02: Validate email format before querying DB
    if not _EMAIL_RE.match(email):
        return {"exists": False}

    normalized_email = email.lower()
    existing = await registrations_async_collection.find_one(
        {
            "$or": [
                {"email": normalized_email},
                {"leader.email": normalized_email},
                {"team_members.email": normalized_email},
            ],
        },
        {"_id": 1, "registrationCompleted": 1, "payment.status": 1, "rzp_order_id": 1, "fullName": 1, "mobile": 1, "collegeName": 1, "branch": 1, "rollNumber": 1},
    )

    if not existing:
        return {"exists": False}

    payment_status = str(existing.get("payment", {}).get("status") or "").lower()
    is_completed = bool(existing.get("registrationCompleted", False))
    return {
        "exists": is_completed,
        "hasRecord": True,
        "hasDraft": not is_completed,
        "registrationCompleted": is_completed,
        "paymentStatus": payment_status,
        "hasPaid": payment_status in ["success", "paid", "captured"],
        "registrationId": existing.get("rzp_order_id"),
    }


@router.post("/api/save-draft")
@router.post("/api/draft")
@limiter.limit("60/minute")
async def save_registration_draft(request: Request, draft: StudentDraft):
    normalized_email = str(draft.email).strip().lower()
    if not normalized_email:
        raise HTTPException(status_code=400, detail="Email is required to save progress.")

    # Resolve college name
    final_college = None
    if draft.collegeName and draft.collegeName.strip():
        c_clean = draft.collegeName.strip()
        if c_clean.lower() != "other":
            final_college = c_clean

    # Resolve current year
    final_year = None
    if draft.currentYear and draft.currentYear.strip():
        y_clean = draft.currentYear.strip()
        if y_clean.lower() == "other" and draft.otherCurrentYear and draft.otherCurrentYear.strip():
            final_year = draft.otherCurrentYear.strip()
        elif y_clean:
            final_year = y_clean
    elif draft.otherCurrentYear and draft.otherCurrentYear.strip():
        final_year = draft.otherCurrentYear.strip()

    existing = await registrations_async_collection.find_one({"email": normalized_email})

    now_ist = ist_now()
    update_data: dict = {
        "email": normalized_email,
        "registrationCompleted": False if not (existing and existing.get("registrationCompleted")) else existing.get("registrationCompleted"),
        "updatedAt": now_ist,
        "payment_status": existing.get("payment_status", "pending") if existing else "pending",
    }

    if draft.fullName and draft.fullName.strip():
        update_data["fullName"] = draft.fullName.strip()
    if draft.mobile and draft.mobile.strip():
        clean_mob = re.sub(r"\D", "", draft.mobile.strip())
        if clean_mob:
            update_data["mobile"] = clean_mob
    if draft.branch and draft.branch.strip():
        update_data["branch"] = draft.branch.strip()
    if final_college:
        update_data["collegeName"] = final_college
    if draft.otherCollegeName and draft.otherCollegeName.strip():
        update_data["otherCollegeName"] = draft.otherCollegeName.strip()
    if draft.city and draft.city.strip():
        update_data["city"] = draft.city.strip()
    if draft.rollNumber and draft.rollNumber.strip():
        update_data["rollNumber"] = draft.rollNumber.strip()
    if final_year:
        update_data["currentYear"] = final_year
    if draft.otherCurrentYear and draft.otherCurrentYear.strip():
        update_data["otherCurrentYear"] = draft.otherCurrentYear.strip()
    if draft.projectSelected and draft.projectSelected.strip():
        update_data["project_selected"] = draft.projectSelected.strip()
        update_data["task_selected"] = draft.projectSelected.strip()
    if draft.participationMode and draft.participationMode.strip():
        update_data["participationMode"] = draft.participationMode.strip()
    if draft.registrationDate and draft.registrationDate.strip():
        update_data["registrationDate"] = draft.registrationDate.strip()
    if draft.teamName and draft.teamName.strip():
        update_data["team_name"] = draft.teamName.strip()
    if draft.teamMembers is not None:
        update_data["team_members"] = draft.teamMembers
        update_data["total_members"] = 1 + len(draft.teamMembers)

    # Clean up incomplete drafts ONLY if they belong to a DIFFERENT email and collide with this mobile or rollNumber
    if "mobile" in update_data:
        await registrations_async_collection.delete_many({
            "registrationCompleted": False,
            "email": {"$ne": normalized_email},
            "mobile": update_data["mobile"],
        })
    if "rollNumber" in update_data:
        await registrations_async_collection.delete_many({
            "registrationCompleted": False,
            "email": {"$ne": normalized_email},
            "rollNumber": update_data["rollNumber"],
        })

    # Prepare leader fields so Admin Dashboard displays student info under pending
    effective_name = update_data.get("fullName") or (existing.get("leader", {}).get("name") if existing else None) or (existing.get("fullName") if existing else "")
    effective_phone = update_data.get("mobile") or (existing.get("leader", {}).get("phone") if existing else None) or (existing.get("mobile") if existing else "")
    effective_college = update_data.get("collegeName") or (existing.get("leader", {}).get("college") if existing else None) or (existing.get("collegeName") if existing else "")
    effective_branch = update_data.get("branch") or (existing.get("leader", {}).get("branch") if existing else None) or (existing.get("branch") if existing else "")
    effective_city = update_data.get("city") or (existing.get("leader", {}).get("city") if existing else None) or (existing.get("city") if existing else "")
    effective_roll = update_data.get("rollNumber") or (existing.get("leader", {}).get("rollNumber") if existing else None) or (existing.get("rollNumber") if existing else "")
    effective_year = update_data.get("currentYear") or (existing.get("leader", {}).get("currentYear") if existing else None) or (existing.get("currentYear") if existing else "")

    leader_updates = {
        "leader.email": normalized_email,
    }
    if effective_name:
        leader_updates["leader.name"] = effective_name
    if effective_phone:
        leader_updates["leader.phone"] = effective_phone
        leader_updates["leader.mobile"] = effective_phone
    if effective_college:
        leader_updates["leader.college"] = effective_college
    if effective_branch:
        leader_updates["leader.branch"] = effective_branch
    if effective_city:
        leader_updates["leader.city"] = effective_city
    if effective_roll:
        leader_updates["leader.rollNumber"] = effective_roll
    if effective_year:
        leader_updates["leader.currentYear"] = effective_year

    update_data.update(leader_updates)

    existing_payment = existing.get("payment") if existing else None
    if not existing_payment or not existing_payment.get("status"):
        base_reg_fee = await get_registration_fee()
        member_cnt = (1 + len(draft.teamMembers or [])) if draft.participationMode == "team" else 1
        update_data["payment"] = {
            "gateway": "upi",
            "status": "pending",
            "transaction_id": None,
            "amount": float(base_reg_fee * member_cnt),
            "currency": "INR",
            "timestamp": now_ist,
        }

    if draft.orderId and draft.orderId.strip():
        update_data["order_id"] = draft.orderId.strip()
        update_data["rzp_order_id"] = draft.orderId.strip()

    insert_defaults = {
        "createdAt": now_ist,
        "registeredAt": now_ist,
        "is_reviewed": False,
        "is_selected": False,
        "Reviewedby": None,
        "user_feedback": None,
        "password": "",
        "feedback": "",
        "github_link": "",
    }

    try:
        await registrations_async_collection.update_one(
            {"email": normalized_email},
            {
                "$set": update_data,
                "$setOnInsert": insert_defaults,
            },
            upsert=True,
        )
        logger.info(f"[AUTOSAVE SUCCESS] Draft saved to MongoDB for {normalized_email}")
    except DuplicateKeyError as dke:
        logger.warning(f"Duplicate key conflict for {normalized_email}: {dke}. Retrying without mobile/rollNumber...")
        update_data.pop("mobile", None)
        update_data.pop("rollNumber", None)
        update_data.pop("leader.phone", None)
        update_data.pop("leader.mobile", None)
        update_data.pop("leader.rollNumber", None)
        await registrations_async_collection.update_one(
            {"email": normalized_email},
            {
                "$set": update_data,
                "$setOnInsert": insert_defaults,
            },
            upsert=True,
        )
        logger.info(f"[AUTOSAVE SUCCESS - RETRY] Draft saved without conflicting unique keys for {normalized_email}")
    except Exception as exc:
        logger.error(f"Error saving draft for {normalized_email}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to auto-save draft: {str(exc)}")

    return {
        "status": "success",
        "message": "Registration draft auto-saved in database successfully.",
        "email": normalized_email,
    }


@router.get("/api/draft/{email}")
@limiter.limit("30/minute")
async def get_registration_draft(request: Request, email: str):
    if not _EMAIL_RE.match(email):
        return {"hasDraft": False}

    normalized_email = email.lower().strip()
    doc = await registrations_async_collection.find_one(
        {"email": normalized_email},
        {"_id": 0},
    )
    if not doc:
        return {"hasDraft": False}

    return {
        "hasDraft": True,
        "registrationCompleted": doc.get("registrationCompleted", False),
        "draft": {
            "fullName": doc.get("fullName") or (doc.get("leader", {}) or {}).get("name") or "",
            "email": normalized_email,
            "mobile": doc.get("mobile") or (doc.get("leader", {}) or {}).get("phone") or "",
            "branch": doc.get("branch") or (doc.get("leader", {}) or {}).get("branch") or "",
            "collegeName": doc.get("collegeName") or (doc.get("leader", {}) or {}).get("college") or "",
            "otherCollegeName": doc.get("otherCollegeName") or "",
            "city": doc.get("city") or (doc.get("leader", {}) or {}).get("city") or "",
            "rollNumber": doc.get("rollNumber") or (doc.get("leader", {}) or {}).get("rollNumber") or "",
            "currentYear": doc.get("currentYear") or (doc.get("leader", {}) or {}).get("currentYear") or "",
            "otherCurrentYear": doc.get("otherCurrentYear") or "",
            "projectSelected": doc.get("project_selected") or doc.get("task_selected") or "",
            "participationMode": doc.get("participationMode") or "individual",
            "registrationDate": doc.get("registrationDate") or "",
            "teamName": doc.get("team_name") or "",
            "teamMembers": doc.get("team_members") or [],
            "orderId": doc.get("order_id") or doc.get("rzp_order_id") or "",
            "paymentStatus": (doc.get("payment") or {}).get("status") or doc.get("payment_status") or "pending",
        },
    }


@router.get("/api/check-roll-number/{roll_number}")
@limiter.limit("20/minute")
async def check_roll_number_exists(request: Request, roll_number: str):
    existing = await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"rollNumber": roll_number},
                {"leader.rollNumber": roll_number},
                {"team_members.rollNumber": roll_number},
            ],
        },
        {"_id": 1},
    )
    if existing:
        return {"exists": True, "message": "Already exists."}
    return {"exists": False}


@router.get("/api/check-github/{github_profile:path}")
@limiter.limit("20/minute")
async def check_github_exists(request: Request, github_profile: str):
    existing = await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"githubProfile": github_profile},
                {"leader.githubProfile": github_profile},
                {"team_members.githubProfile": github_profile},
            ],
        },
        {"_id": 1},
    )
    if existing:
        return {"exists": True, "message": "Already exists."}
    return {"exists": False}


@router.post("/api/check-duplicate")
@limiter.limit("10/minute")
async def check_duplicate(request: Request, data: DuplicateCheck):
    checks = []
    normalized_email = data.email.lower() if data.email else None

    if normalized_email and await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"email": normalized_email},
                {"leader.email": normalized_email},
                {"team_members.email": normalized_email},
            ],
        },
        {"_id": 1},
    ):
        checks.append({"field": "email", "exists": True, "message": "This email is already registered."})

    if data.rollNumber and await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"rollNumber": data.rollNumber},
                {"leader.rollNumber": data.rollNumber},
                {"team_members.rollNumber": data.rollNumber},
            ],
        },
        {"_id": 1},
    ):
        checks.append({"field": "rollNumber", "exists": True, "message": "Already exists."})

    if data.githubProfile and await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"githubProfile": data.githubProfile},
                {"leader.githubProfile": data.githubProfile},
                {"team_members.githubProfile": data.githubProfile},
            ],
        },
        {"_id": 1},
    ):
        checks.append({"field": "githubProfile", "exists": True, "message": "Already exists."})

    if data.mobile and await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"mobile": data.mobile},
                {"leader.phone": data.mobile},
                {"team_members.mobile": data.mobile},
            ],
        },
        {"_id": 1},
    ):
        checks.append({"field": "mobile", "exists": True, "message": "This mobile number is already registered."})

    return {"hasDuplicate": len(checks) > 0, "duplicates": checks}


@router.post("/api/register", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def register_student(student: StudentRegister):
    resolved_college_name = await resolve_college_name(student)
    student = student.model_copy(update={"collegeName": resolved_college_name})

    effective_order_id = student.order_id or student.rzp_order_id
    if not effective_order_id:
        raise HTTPException(status_code=400, detail="Payment details are missing. Please complete the payment first.")

    db_registration = await registrations_async_collection.find_one(
        {"$or": [{"order_id": effective_order_id}, {"rzp_order_id": effective_order_id}]},
        {"_id": 0, "payment": 1, "payment_receipt_base64": 1, "receipt_base64": 1, "payment_receipt_url": 1}
    )
    if not db_registration or not db_registration.get("payment"):
        raise HTTPException(status_code=400, detail="Payment not found for the given order.")

    payment_data = db_registration.get("payment", {})
    payment_status = str(payment_data.get("status", "")).lower()
    if payment_status not in ["success", "paid", "captured"]:
        raise HTTPException(status_code=400, detail=f"Payment is not successful. Current status: {payment_status}")

    # Enforce mandatory payment receipt upload
    receipt = (
        student.payment_receipt_base64
        or student.receipt_base64
        or student.payment_receipt_url
        or db_registration.get("payment_receipt_base64")
        or db_registration.get("receipt_base64")
        or db_registration.get("payment_receipt_url")
    )
    if not receipt:
        raise HTTPException(
            status_code=400,
            detail="Payment receipt / screenshot is mandatory. Please upload your payment slip before completing registration.",
        )

    rzp_payment_id = payment_data.get("transaction_id") or student.rzp_payment_id
    clean_utr = re.sub(r"\D", "", str(rzp_payment_id or ""))
    if len(clean_utr) != 12:
        raise HTTPException(
            status_code=400,
            detail="UTR Number must be exactly 12 numeric digits. Please check your payment receipt.",
        )

    # If OCR detected a valid 12-digit UTR from receipt, enforce match on server
    if student.detected_receipt_utr:
        clean_detected = re.sub(r"\D", "", str(student.detected_receipt_utr))
        if len(clean_detected) == 12 and clean_detected != clean_utr:
            raise HTTPException(
                status_code=400,
                detail=f"Submitted UTR ({clean_utr}) does not match the UTR detected on your payment receipt ({clean_detected}).",
            )

    # Check duplicate UTR against completed registrations
    duplicate_utr = await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "rzp_order_id": {"$ne": effective_order_id},
            "$or": [
                {"payment.transaction_id": clean_utr},
                {"payment.utr_number": clean_utr},
                {"rzp_payment_id": clean_utr},
                {"transaction_id": clean_utr},
            ],
        },
        {"_id": 1},
    )
    if duplicate_utr:
        raise HTTPException(
            status_code=400,
            detail="This UTR / Transaction ID has already been used for another confirmed registration.",
        )

    return await register_student_service(student, clean_utr, payment_status)


@router.get("/api/registration/{registration_id}/summary", response_model=RegistrationSummaryResponse)
async def registration_summary(registration_id: str):
    return await get_registration_summary(registration_id)


# Fix C-03: Protect /api/all-users-json with admin authentication
@router.get("/api/all-users-json", dependencies=[Depends(require_admin_key)])
async def get_all_users_json():
    """
    Export all registrations as a flat JSON list.
    Requires X-Admin-Key header matching ADMIN_API_KEY env variable.
    """
    cursor = registrations_async_collection.find({"registrationCompleted": True})
    registrations = await cursor.to_list(length=1000)

    flattened_users = []
    for reg in registrations:
        # Participation Mode
        mode = reg.get("participationMode", "individual")

        # Base data from registration
        common_data = {
            "registrationId": reg.get("rzp_order_id"),
            "participationMode": mode,
            "teamId": reg.get("team_id"),
            "teamName": reg.get("team_name"),
            "projectSelected": reg.get("project_selected"),
            "is_reviewed": reg.get("is_reviewed", False),
            "is_selected": reg.get("is_selected", False),
            "reviewed_by": reg.get("Reviewedby"),  # renamed field (L-01)
            "user_feedback": reg.get("user_feedback"),
            "registeredAt": reg.get("registeredAt"),
            "paymentStatus": reg.get("payment_status"),
            "paymentReceiptUrl": reg.get("payment_receipt_url") or (reg.get("payment", {}) or {}).get("receipt_url"),
            "paymentReceiptBase64": reg.get("payment_receipt_base64") or reg.get("receipt_base64") or (reg.get("payment", {}) or {}).get("payment_receipt_base64"),
            "paymentReceiptName": reg.get("payment_receipt_name") or (reg.get("payment", {}) or {}).get("payment_receipt_name"),
        }

        # Leader data
        leader = reg.get("leader", {})
        leader_entry = {
            **common_data,
            "role": "leader" if mode == "team" else "individual",
            "participantId": leader.get("participant_id"),
            "fullName": leader.get("name"),
            "email": leader.get("email"),
            "mobile": leader.get("phone"),
            "collegeName": leader.get("college"),
            "branch": leader.get("branch"),
            "city": leader.get("city"),
            "rollNumber": leader.get("rollNumber"),
            "githubProfile": leader.get("githubProfile"),
        }
        flattened_users.append(leader_entry)

        # Team members data
        for member in reg.get("team_members", []):
            member_entry = {
                **common_data,
                "role": "member",
                "participantId": member.get("participant_id"),
                "fullName": member.get("name"),
                "email": member.get("email"),
                "mobile": member.get("mobile"),
                "collegeName": leader.get("college"),  # members share leader's college in current schema
                "branch": member.get("branch") or leader.get("branch"),
                "city": leader.get("city"),
                "rollNumber": member.get("rollNumber"),
                "githubProfile": member.get("githubProfile"),
            }
            flattened_users.append(member_entry)

    return flattened_users


@router.get("/api/receipt/{registration_id}")
async def download_receipt(registration_id: str, email: str, token: str):
    if not verify_receipt_token(token=token, registration_id=registration_id, email=email):
        raise HTTPException(status_code=403, detail="Invalid receipt token")

    registration = await registrations_async_collection.find_one(
        {"$or": [{"order_id": registration_id}, {"rzp_order_id": registration_id}]}
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    leader_email = str(registration.get("leader", {}).get("email", "")).lower()
    member_emails = {str(item.get("email", "")).lower() for item in registration.get("team_members", [])}
    requested_email = email.lower()
    if requested_email != leader_email and requested_email not in member_emails:
        raise HTTPException(status_code=403, detail="Email is not authorized for this receipt")

    pdf_data = build_receipt_pdf(registration, requested_email)
    return Response(
        content=pdf_data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="Spheronix_Receipt_{registration_id}.pdf"',
            "Cache-Control": "no-store",
        },
    )