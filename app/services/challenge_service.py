import random
from typing import Any

from fastapi import HTTPException

from app.core.time_utils import utc_now
from app.database.mongodb import (
    hackathon_challenges_async_collection,
    registrations_async_collection,
    teams_async_collection,
)


def normalize_challenge_category(cat: Any) -> str:
    if not cat:
        return "N/A"
    raw = str(cat).strip()
    low = raw.lower()
    if "full stack" in low or "fullstack" in low:
        return "Full Stack Application"
    if "bug" in low:
        return "Bug Hunt"
    if "native" in low or "windows" in low:
        return "Native Apps (Windows)"
    if "ideathon" in low:
        return "Ideathon"
    return raw


def serialize_assigned_challenge(document: dict[str, Any] | None) -> dict[str, str] | None:
    if not document:
        return None

    title = str(document.get("title") or "").strip()
    description = str(document.get("description") or "").strip()
    if not title or not description:
        return None

    return {
        "category": str(document.get("category") or "").strip(),
        "title": title,
        "description": description,
    }


async def assign_random_challenge(
    task_category: str,
    team_id: str | None = None,
    registration_id: str | None = None,
) -> dict[str, str]:
    normalized_category = (task_category or "").strip()
    if not normalized_category:
        raise HTTPException(status_code=400, detail="Task category is required for challenge assignment")

    # If category is Ideathon, do NOT fetch from database questions.
    # Set main task and assigned challenge directly to Ideathon prototype.
    if normalized_category.lower() == "ideathon":
        selected_challenge = {
            "category": "Ideathon",
            "title": "Ideathon",
            "description": "Design and develop an innovative prototype solution. Present your problem statement, system architecture, and prototype demonstration.",
            "requirements": "Problem Statement, Innovation Pitch, System Architecture, Prototype Demo / GitHub Repository",
            "projectUrl": "",
        }
    else:
        # 1. Fetch available questions for other categories from global data
        from app.database.mongodb import global_data_async_collection
        low_cat = normalized_category.lower()
        if "bug" in low_cat:
            cat_query = {"name": {"$regex": r"bug", "$options": "i"}}
        elif "native" in low_cat or "windows" in low_cat:
            cat_query = {"name": {"$regex": r"native", "$options": "i"}}
        elif "full stack" in low_cat or "fullstack" in low_cat:
            cat_query = {"name": {"$regex": r"full\s*stack", "$options": "i"}}
        else:
            cat_query = {"name": normalized_category}

        global_doc = await global_data_async_collection.find_one(cat_query)
        if not global_doc or not global_doc.get("questions"):
            selected_challenge = {
                "category": normalized_category,
                "title": f"{normalized_category} - Open Innovation Challenge",
                "description": f"Present and pitch your innovative project or idea under {normalized_category}.",
                "requirements": "Problem Statement, Solution Pitch, Architecture & Roadmap, Prototype Demo",
                "projectUrl": "",
            }
        else:
            available_questions = global_doc["questions"]
            selected_question = random.choice(available_questions)

            if isinstance(selected_question, dict):
                selected_challenge = {
                    "category": normalized_category,
                    "title": selected_question.get("name", "") or selected_question.get("title", ""),
                    "description": selected_question.get("description", ""),
                    "requirements": selected_question.get("requirements", ""),
                    "projectUrl": selected_question.get("projectUrl", ""),
                }
            else:
                # Legacy support for older string-based questions
                selected_challenge = {
                    "category": normalized_category,
                    "title": str(selected_question),
                    "description": f"Detailed problem statement for {selected_question}",
                    "requirements": "",
                    "projectUrl": "",
                }

    if not selected_challenge or not selected_challenge.get("title"):
        raise HTTPException(status_code=500, detail="Selected hackathon challenge is invalid")

    if team_id:
        await teams_async_collection.update_one(
            {"teamId": team_id},
            {
                "$set": {
                    "assignedChallenge": selected_challenge,
                    "updatedAt": utc_now(),
                }
            },
        )

    if registration_id:
        await registrations_async_collection.update_one(
            {"$or": [{"order_id": registration_id}, {"rzp_order_id": registration_id}]},
            {
                "$set": {
                    "assigned_challenge": selected_challenge,
                    "updatedAt": utc_now(),
                }
            },
        )

    return selected_challenge


async def get_registration_summary(registration_id: str) -> dict[str, Any]:
    registration = await registrations_async_collection.find_one(
        {"$or": [{"order_id": registration_id}, {"rzp_order_id": registration_id}]},
        {"_id": 0}
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    payment = registration.get("payment", {})
    payment_status = str(payment.get("status") or "").lower()

    # Allow summary only if registration is completed
    if not registration.get("registrationCompleted"):
        raise HTTPException(status_code=404, detail="Registration not yet finalized")

    leader = registration.get("leader", {})
    team_members = registration.get("team_members", [])

    return {
        "registrationId": str(registration.get("rzp_order_id") or ""),
        "transactionId": payment.get("transaction_id"),
        "fullName": str(leader.get("name") or registration.get("fullName") or ""),
        "email": str(leader.get("email") or registration.get("email") or "").lower(),
        "participantId": leader.get("participant_id") or registration.get("participant_id"),
        "teamId": registration.get("team_id"),
        "teamName": registration.get("team_name"),
        "taskSelected": normalize_challenge_category(registration.get("project_selected") or registration.get("task_selected")),
        "assignedChallenge": None, # Hide from user
        "paymentStatus": payment.get("status"),
        "teamMemberEmails": [
            str(member.get("email") or "").lower()
            for member in team_members
            if member.get("email")
        ],
        "teamMemberNames": [
            str(member.get("name") or member.get("fullName") or "").strip()
            for member in team_members
            if (member.get("name") or member.get("fullName"))
        ],
        "is_reviewed": bool(registration.get("is_reviewed", False)),
        "is_selected": bool(registration.get("is_selected", False)),
        # Fix L-01: Renamed from Reviewedby to reviewed_by for consistent snake_case
        "reviewed_by": registration.get("Reviewedby"),
        "user_feedback": registration.get("user_feedback"),
        "payment_receipt_url": registration.get("payment_receipt_url") or payment.get("receipt_url"),
        "payment_receipt_name": registration.get("payment_receipt_name") or payment.get("payment_receipt_name") or payment.get("receipt_name"),
        "payment_receipt_base64": registration.get("payment_receipt_base64") or payment.get("payment_receipt_base64") or registration.get("receipt_base64") or payment.get("receipt_base64"),
        "receipt_base64": registration.get("payment_receipt_base64") or payment.get("payment_receipt_base64") or registration.get("receipt_base64") or payment.get("receipt_base64"),
    }