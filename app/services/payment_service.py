import asyncio
import logging
import re
import secrets
import urllib.parse
from typing import Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.core.time_utils import ist_now, unix_timestamp, utc_now
from app.database.mongodb import async_db, registrations_async_collection
from app.models.schemas import PaymentOrderRequest, PaymentOrderResponse
from app.services.settings_service import get_payment_settings, get_registration_fee
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def build_upi_intent_url(upi_id: str, payee_name: str, amount: float, order_id: str = "") -> str:
    clean_upi_id = (upi_id or "334509931804612@CNRB").strip()
    clean_payee = (payee_name or "Spheronix Hackathon").strip()
    encoded_name = urllib.parse.quote(clean_payee)
    encoded_note = urllib.parse.quote("Hackathon Registration Fee")
    amt_str = f"{float(amount):.2f}"
    return f"upi://pay?pa={clean_upi_id}&pn={encoded_name}&am={amt_str}&cu=INR&tn={encoded_note}"


async def verify_upi_payment(order_id: str, utr_number: str) -> dict:
    clean_order_id = (order_id or "").strip()
    clean_utr = re.sub(r"\D", "", (utr_number or "").strip())

    if not clean_order_id:
        raise HTTPException(status_code=400, detail="Order ID is required for payment verification.")

    if len(clean_utr) != 12:
        raise HTTPException(
            status_code=400,
            detail="UTR Number must be exactly 12 numeric digits. Please check your payment receipt.",
        )

    existing_doc = await registrations_async_collection.find_one(
        {"rzp_order_id": clean_order_id},
        {"_id": 1, "payment": 1, "registrationCompleted": 1},
    )

    if not existing_doc:
        raise HTTPException(status_code=404, detail="Payment order not found. Please initiate the payment again.")

    # Check if this UTR is already associated with another completed registration (Section 21)
    duplicate_utr = await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "rzp_order_id": {"$ne": clean_order_id},
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

    # Update payment document with successful UPI verification
    await registrations_async_collection.update_one(
        {"rzp_order_id": clean_order_id},
        {
            "$set": {
                "payment": {
                    "gateway": "upi",
                    "transaction_id": clean_utr,
                    "status": "success",
                    "utr_number": clean_utr,
                    "timestamp": utc_now(),
                },
                "verifiedAt": utc_now(),
                "updatedAt": utc_now(),
            }
        },
    )

    return {
        "status": "success",
        "message": "UPI payment verified successfully.",
        "order_id": clean_order_id,
        "transaction_id": clean_utr,
        "rzp_order_id": clean_order_id,
        "rzp_payment_id": clean_utr,
    }


async def verify_razorpay_payment(razorpay_order_id: str, razorpay_payment_id: str, razorpay_signature: str) -> dict:
    """Backwards-compatible verification handler for legacy or mock requests."""
    return await verify_upi_payment(razorpay_order_id, razorpay_payment_id or "UPI_TXN_VERIFIED")


async def create_order(request: PaymentOrderRequest) -> PaymentOrderResponse:
    normalized_email = str(request.email).lower()
    selected_task = (request.projectSelected or "").strip()

    # 1. Check for completed registrations with this email or mobile
    completed_conflict = await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "$or": [
                {"email": normalized_email},
                {"leader.email": normalized_email},
                {"team_members.email": normalized_email},
                {"mobile": request.mobile},
                {"leader.phone": request.mobile},
                {"team_members.mobile": request.mobile},
            ],
        },
        {"_id": 1, "email": 1, "mobile": 1, "leader": 1, "team_members": 1},
    )
    if completed_conflict:
        is_email_match = (
            completed_conflict.get("email") == normalized_email
            or (completed_conflict.get("leader", {}).get("email") == normalized_email)
            or any(m.get("email") == normalized_email for m in completed_conflict.get("team_members", []))
        )
        if is_email_match:
            raise HTTPException(status_code=409, detail="This email is already registered for the hackathon")
        else:
            raise HTTPException(status_code=409, detail="This mobile number is already registered for the hackathon")

    # 2. Clean up incomplete drafts ONLY if they belong to a DIFFERENT email and collide with this mobile
    if request.mobile:
        await registrations_async_collection.delete_many({
            "registrationCompleted": False,
            "email": {"$ne": normalized_email},
            "mobile": request.mobile,
        })

    base_amount = await get_registration_fee()
    if request.participationMode == "team":
        total_members = 1 + request.teamMembersCount
        amount = float(base_amount * total_members)
    else:
        total_members = 1
        amount = float(base_amount)

    total_members = 1 + request.teamMembersCount if request.participationMode == "team" else 1
    update_filter = {"email": normalized_email}

    # Check if this order was already created and completed
    existing_doc = await registrations_async_collection.find_one(
        update_filter,
    )
    is_already_paid = existing_doc and str(existing_doc.get("payment", {}).get("status") or "").lower() in [
        "success",
        "paid",
        "captured",
    ]

    saved_order_id = existing_doc.get("order_id") or existing_doc.get("rzp_order_id") if existing_doc else None
    order_id = saved_order_id or f"SPX_UPI_{unix_timestamp()}_{secrets.token_hex(3).upper()}"

    payment_settings = await get_payment_settings()
    upi_id = payment_settings.get("upiId") or "334509931804612@CNRB"
    upi_payee_name = payment_settings.get("upiPayeeName") or "SPHERONIX TECHNOLOGY PVT. LTD."
    bank_name = payment_settings.get("bankName") or "CANARA BANK"
    account_number = payment_settings.get("accountNumber") or "120036804612"
    ifsc_code = payment_settings.get("ifscCode") or "CNRB0000659"
    account_holder_name = payment_settings.get("accountHolderName") or "SPHERONIX TECHNOLOGY PVT. LTD."

    upi_intent_url = build_upi_intent_url(upi_id, upi_payee_name, amount, order_id)

    if is_already_paid:
        return PaymentOrderResponse(
            orderId=order_id,
            amount=amount,
            currency="INR",
            paymentGateway="upi",
            upiId=upi_id,
            upiPayeeName=upi_payee_name,
            bankName=bank_name,
            accountNumber=account_number,
            ifscCode=ifsc_code,
            accountHolderName=account_holder_name,
            upiIntentUrl=upi_intent_url,
            qrCodeData=upi_intent_url,
            totalMembers=total_members,
            feePerMember=base_amount,
            paymentSessionId="",
            environment="PRODUCTION",
            mockMode=True,
            mockPaymentId=existing_doc.get("payment", {}).get("transaction_id") or "already_paid",
            message="Payment already completed",
        )

    # Resolve college name
    final_college = None
    if request.collegeName:
        c_clean = request.collegeName.strip()
        if c_clean.lower() != "other":
            final_college = c_clean

    final_year = None
    if request.currentYear:
        if request.currentYear.strip().lower() == "other" and request.otherCurrentYear:
            final_year = request.otherCurrentYear.strip()
        else:
            final_year = request.currentYear.strip()

    update_data: dict = {
        "registrationCompleted": False,
        "email": normalized_email,
        "fullName": request.fullName,
        "participationMode": request.participationMode,
        "mobile": request.mobile,
        "totalMembers": total_members,
        "project_selected": selected_task or (existing_doc.get("project_selected") if existing_doc else None),
        "task_selected": selected_task or (existing_doc.get("task_selected") if existing_doc else None),
        "rzp_order_id": order_id,
        "order_id": order_id,
        "updatedAt": ist_now(),
        "payment": {
            "gateway": "upi",
            "status": "created",
            "transaction_id": None,
            "amount": amount,
            "currency": "INR",
            "timestamp": ist_now(),
        },
        "payment_status": "pending",
    }

    if final_college:
        update_data["collegeName"] = final_college
    if request.otherCollegeName:
        update_data["otherCollegeName"] = request.otherCollegeName.strip()
    if request.branch:
        update_data["branch"] = request.branch.strip()
    if request.city:
        update_data["city"] = request.city.strip()
    if request.rollNumber and request.rollNumber.strip():
        update_data["rollNumber"] = request.rollNumber.strip()
    if final_year:
        update_data["currentYear"] = final_year
    if request.otherCurrentYear:
        update_data["otherCurrentYear"] = request.otherCurrentYear.strip()
    if request.registrationDate:
        update_data["registrationDate"] = request.registrationDate.strip()

    if request.teamName and request.teamName.strip():
        update_data["team_name"] = request.teamName.strip()
    if request.teamMembers:
        update_data["team_members"] = request.teamMembers

    # Update leader subdocument
    effective_college = update_data.get("collegeName") or (existing_doc.get("leader", {}).get("college") if existing_doc else None) or (existing_doc.get("collegeName") if existing_doc else None)
    effective_branch = update_data.get("branch") or (existing_doc.get("leader", {}).get("branch") if existing_doc else None) or (existing_doc.get("branch") if existing_doc else None)
    effective_city = update_data.get("city") or (existing_doc.get("leader", {}).get("city") if existing_doc else None) or (existing_doc.get("city") if existing_doc else None)
    effective_roll = update_data.get("rollNumber") or (existing_doc.get("leader", {}).get("rollNumber") if existing_doc else None) or (existing_doc.get("rollNumber") if existing_doc else None)
    effective_year = update_data.get("currentYear") or (existing_doc.get("leader", {}).get("currentYear") if existing_doc else None) or (existing_doc.get("currentYear") if existing_doc else None)

    leader_updates = {
        "leader.name": request.fullName,
        "leader.email": normalized_email,
        "leader.phone": request.mobile,
        "leader.mobile": request.mobile,
    }
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

    try:
        await registrations_async_collection.update_one(
            update_filter,
            {
                "$set": update_data,
                "$setOnInsert": {
                    "createdAt": ist_now(),
                    "registeredAt": ist_now(),
                    "is_reviewed": False,
                    "is_selected": False,
                    "Reviewedby": None,
                    "user_feedback": None,
                    "password": "",
                    "feedback": "",
                    "github_link": "",
                },
            },
            upsert=True,
        )

        return PaymentOrderResponse(
            orderId=order_id,
            amount=amount,
            currency="INR",
            paymentGateway="upi",
            upiId=upi_id,
            upiPayeeName=upi_payee_name,
            bankName=bank_name,
            accountNumber=account_number,
            ifscCode=ifsc_code,
            accountHolderName=account_holder_name,
            upiIntentUrl=upi_intent_url,
            qrCodeData=upi_intent_url,
            totalMembers=total_members,
            feePerMember=base_amount,
            paymentSessionId="",
            environment="PRODUCTION",
            mockMode=False,
            mockPaymentId=None,
            message="UPI Payment order created successfully. Scan the QR code or use UPI App to pay.",
        )
    except DuplicateKeyError as exc:
        logger.exception("Mongo duplicate key error while creating payment order")
        raise HTTPException(status_code=409, detail="A unique constraint error occurred. Please try again.")
    except Exception as exc:
        logger.exception(f"Payment order creation failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Unable to generate payment order at this moment. Please try again.",
        )
