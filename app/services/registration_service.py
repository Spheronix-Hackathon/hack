import asyncio
import logging
import secrets
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.core.time_utils import ist_now, utc_now
from app.database.mongodb import registrations_async_collection, teams_async_collection, users_async_collection
from app.models.schemas import StudentRegister, StudentResponse
from app.services.challenge_service import assign_random_challenge
from app.services.receipt_service import build_receipt_download_url, build_receipt_pdf, format_datetime_ist
from app.services.supabase_service import upload_receipt_to_supabase
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

MIN_TEAM_TOTAL_MEMBERS = 2
MAX_TEAM_TOTAL_MEMBERS = 5
MAX_TEAM_MEMBERS_EXCLUDING_LEADER = 4
from app.services.settings_service import get_registration_fee


def numeric_6() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"


async def generate_unique_individual_id() -> str:
    # Fix H-04: Use collision-resistant hex string instead of infinite DB busy-wait loop
    return f"SPX_HACK2026_INDV_{secrets.token_hex(4).upper()}"


async def generate_unique_team_id() -> str:
    # Fix H-04: Use collision-resistant hex string instead of infinite DB busy-wait loop
    return f"SPX_HACK2026_TEAM_{secrets.token_hex(4).upper()}"


def build_team_member_participant_id(team_id: str, member_index: int) -> str:
    return f"{team_id}_{member_index:02d}"


def normalize_challenge_category(cat: Optional[str]) -> str:
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


def normalize_https_receipt_url(url: Optional[str]) -> Optional[str]:
    if not url or not str(url).strip():
        return None
    cleaned = str(url).strip()
    if cleaned.startswith("data:"):
        return cleaned
    if cleaned.startswith("/"):
        return f"https://puhackathon.spheronixtechnology.com{cleaned}"
    if cleaned.startswith("http://localhost:8000"):
        return cleaned.replace("http://localhost:8000", "https://puhackathon.spheronixtechnology.com")
    if cleaned.startswith("http://127.0.0.1:8000"):
        return cleaned.replace("http://127.0.0.1:8000", "https://puhackathon.spheronixtechnology.com")
    if cleaned.startswith("http://"):
        return "https://" + cleaned[7:]
    if not cleaned.startswith("https://"):
        return f"https://{cleaned}"
    return cleaned


def resolve_receipt_storage(student: StudentRegister, existing_doc: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Safely resolve payment receipt storage for new registrations using existing fields:
    - payment_receipt_base64
    - payment_receipt_url
    - payment_receipt_name
    Guarantees no modifications or rewrites to existing database records.
    """
    existing_b64 = None
    existing_url = None
    existing_name = None
    if existing_doc:
        existing_b64 = existing_doc.get("payment_receipt_base64") or existing_doc.get("receipt_base64")
        existing_url = existing_doc.get("payment_receipt_url") or existing_doc.get("receipt_url")
        existing_name = existing_doc.get("payment_receipt_name") or existing_doc.get("receipt_name")

    receipt_b64 = (
        student.payment_receipt_base64
        or student.receipt_base64
        or (student.payment_receipt_url if (student.payment_receipt_url or "").startswith("data:") else None)
        or existing_b64
        or None
    )

    raw_url = (
        (student.payment_receipt_url if not (student.payment_receipt_url or "").startswith("data:") else None)
        or (existing_url if not (existing_url or "").startswith("data:") else None)
        or None
    )
    receipt_url = normalize_https_receipt_url(raw_url)

    # When a storage URL (e.g. Supabase) is present, strictly omit base64 from MongoDB
    receipt_b64 = None if receipt_url else (
        student.payment_receipt_base64
        or student.receipt_base64
        or (student.payment_receipt_url if (student.payment_receipt_url or "").startswith("data:") else None)
        or existing_b64
        or None
    )

    receipt_name = (
        student.payment_receipt_name
        or existing_name
        or ("payment_receipt" if receipt_b64 or receipt_url else None)
    )

    return {
        "payment_receipt_base64": receipt_b64,
        "payment_receipt_url": receipt_url,
        "payment_receipt_name": receipt_name,
    }


def _build_email_bodies(
    participant_name: str,
    recipient_email: str,
    mobile_number: str,
    college_name: str,
    task_selected: str,
    participation_mode: str,
    role_text: str,
    participant_id: str,
    team_name: Optional[str],
    team_id: Optional[str],
    team_members: List[Dict[str, Any]],
    transaction_id: str,
    amount: float,
    currency: str,
    payment_status: str,
    paid_date: str,
    receipt_url: str,
    roll_number: Optional[str] = None,
) -> tuple[str, str]:
    is_team = bool((participation_mode or "").lower() == "team" or team_name or team_id)
    mode_display = "Team" if is_team else "Individual"
    if is_team and role_text:
        mode_display = f"Team ({role_text.title()})"

    team_info_plain = ""
    team_info_html = ""
    if is_team:
        team_info_plain = f"Team Name: {team_name or 'N/A'}\nTeam ID: {team_id or 'N/A'}\n"
        team_info_html = f"""
            <tr><td style="color:#4b5563;font-weight:600;padding:6px 0;">Team Name:</td><td style="color:#111827;padding:6px 0;font-weight:600;">{team_name or 'N/A'}</td></tr>
            <tr><td style="color:#4b5563;font-weight:600;padding:6px 0;">Team ID:</td><td style="color:#111827;padding:6px 0;font-family:monospace;font-weight:600;">{team_id or 'N/A'}</td></tr>
        """

    team_members_plain = ""
    team_members_html = ""
    if is_team and team_members:
        team_members_plain = "\n--- Team Members Details ---\n"
        for idx, m in enumerate(team_members, 1):
            m_name = m.get("name", "")
            m_email = m.get("email", "")
            m_mobile = m.get("mobile") or m.get("phone", "")
            m_role = (m.get("role") or ("Team Leader" if idx == 1 else "Team Member")).title()
            team_members_plain += (
                f"\nMember {idx}:\n"
                f"Name: {m_name}\n"
                f"Role: {m_role}\n"
                f"Email-ID: {m_email}\n"
                f"Mobile Number: {m_mobile}\n"
                f"College Name: {college_name}\n"
            )

        member_rows = ""
        for idx, m in enumerate(team_members, 1):
            m_name = m.get("name", "")
            m_email = m.get("email", "")
            m_mobile = m.get("mobile") or m.get("phone", "")
            m_role = (m.get("role") or ("Team Leader" if idx == 1 else "Team Member")).title()
            badge_color = "#173f97" if "leader" in m_role.lower() else "#4b5563"
            member_rows += f"""
                <tr style="border-bottom:1px solid #e5e7eb;">
                    <td style="padding:8px 10px;color:#111827;font-weight:600;">{m_name}</td>
                    <td style="padding:8px 10px;"><span style="background:#eef2ff;color:{badge_color};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;">{m_role}</span></td>
                    <td style="padding:8px 10px;color:#4b5563;">{m_email}</td>
                    <td style="padding:8px 10px;color:#4b5563;">{m_mobile}</td>
                    <td style="padding:8px 10px;color:#4b5563;">{college_name}</td>
                </tr>
            """

        team_members_html = f"""
            <div style="margin-top:20px;margin-bottom:18px;">
                <div style="font-size:14px;font-weight:700;color:#1f2937;margin-bottom:8px;">Team Members ({len(team_members)} members)</div>
                <table width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-size:13px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
                    <thead>
                        <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                            <th style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">Name</th>
                            <th style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">Role</th>
                            <th style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">Email-ID</th>
                            <th style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">Mobile Number</th>
                            <th style="padding:8px 10px;border-bottom:1px solid #e5e7eb;">College Name</th>
                        </tr>
                    </thead>
                    <tbody>
                        {member_rows}
                    </tbody>
                </table>
            </div>
        """

    plain_body = (
        f"Dear {participant_name},\n\n"
        "Thank you for completing your registration for the Spheronix Hackathon 2026.\n"
        "Your payment has been successfully processed, and your participation is now officially confirmed.\n\n"
        "--- Registration Details ---\n"
        f"Name: {participant_name}\n"
        f"Email-ID: {recipient_email}\n"
        f"Mobile Number: {mobile_number}\n"
        f"College Name: {college_name}\n"
        f"Challenge Category: {task_selected}\n"
        f"Participant Mode: {mode_display}\n"
        f"{team_info_plain}"
        f"Amount Paid: {currency} {amount:.2f}\n"
        f"Date: {paid_date}\n"
        f"Transaction ID: {transaction_id}\n"
        f"{team_members_plain}\n"
        "A formal PDF payment receipt is attached to this email for your records.\n"
        f"You may also securely download it here: {receipt_url}\n\n"
        "If you have any questions, please contact our support team at spheronixhackathon@gmail.com.\n\n"
        "Best regards,\n"
        "Spheronix Hackathon Team\n"
        "Bangalore, India\n"
        "This is an automated transactional email."
    )

    html_body = f"""
        <html>
            <body style="margin:0;padding:0;background:#eef2ff;font-family:'Segoe UI',Arial,sans-serif;">
                <span style="display:none;visibility:hidden;opacity:0;color:transparent;height:0;width:0;overflow:hidden;">
                    Registration confirmed for Spheronix Hackathon 2026. Your details and payment receipt are attached.
                </span>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef2ff;padding:24px 12px;">
                    <tr>
                        <td align="center">
                            <table role="presentation" width="640" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #dbe3ff;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
                                <tr>
                                    <td style="background:#173f97;color:#ffffff;padding:22px 24px;">
                                        <div style="font-size:22px;font-weight:700;letter-spacing:-0.3px;">Spheronix Hackathon 2026</div>
                                        <div style="font-size:13px;opacity:0.9;margin-top:4px;">Official Registration Confirmation</div>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="padding:24px;">
                                        <p style="margin:0 0 12px 0;font-size:15px;color:#111827;">Dear <strong>{participant_name}</strong>,</p>
                                        <p style="margin:0 0 18px 0;font-size:14px;line-height:1.6;color:#374151;">
                                            Thank you for completing your registration for the <strong>Spheronix Hackathon 2026</strong>. Your payment has been successfully processed, and your participation is now officially confirmed.
                                        </p>

                                        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8faff;border:1px solid #d9e4ff;border-radius:10px;margin-bottom:18px;">
                                            <tr>
                                                <td style="padding:18px 20px;">
                                                    <table width="100%" cellspacing="0" cellpadding="0" style="font-size:14px;line-height:1.6;border-collapse:collapse;">
                                                        <tr>
                                                            <td style="width:165px;color:#4b5563;font-weight:600;padding:6px 0;">Name:</td>
                                                            <td style="color:#111827;font-weight:600;padding:6px 0;">{participant_name}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Email-ID:</td>
                                                            <td style="color:#111827;padding:6px 0;">{recipient_email}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Mobile Number:</td>
                                                            <td style="color:#111827;padding:6px 0;">{mobile_number}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">College Name:</td>
                                                            <td style="color:#111827;padding:6px 0;">{college_name}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Challenge Category:</td>
                                                            <td style="color:#111827;font-weight:600;padding:6px 0;">{task_selected}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Participant Mode:</td>
                                                            <td style="color:#111827;padding:6px 0;"><span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600;">{mode_display}</span></td>
                                                        </tr>
                                                        {team_info_html}
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Amount Paid:</td>
                                                            <td style="color:#16a34a;font-weight:700;padding:6px 0;">{currency} {amount:.2f}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Date:</td>
                                                            <td style="color:#111827;padding:6px 0;">{paid_date}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="color:#4b5563;font-weight:600;padding:6px 0;">Transaction ID:</td>
                                                            <td style="color:#111827;font-family:monospace;padding:6px 0;">{transaction_id}</td>
                                                        </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>

                                        {team_members_html}

                                        <p style="margin:18px 0 12px 0;font-size:14px;color:#4b5563;">
                                            A formal PDF payment receipt is attached to this email for your records.
                                        </p>
                                        <div style="margin:14px 0 20px 0;">
                                            <a href="{receipt_url}" style="display:inline-block;background:#173f97;color:#ffffff;text-decoration:none;font-size:14px;font-weight:600;padding:11px 18px;border-radius:8px;">
                                                Download Payment Receipt
                                            </a>
                                        </div>

                                        <hr style="border:none;border-top:1px solid #e5e7eb;margin:22px 0;"/>
                                        <p style="margin:0;font-size:13px;line-height:1.6;color:#6b7280;">
                                            If you have any questions, please contact our support team at <a href="mailto:spheronixhackathon@gmail.com" style="color:#173f97;text-decoration:none;font-weight:600;">spheronixhackathon@gmail.com</a>.<br/><br/>
                                            Best regards,<br/>
                                            <strong style="color:#1f2937;">Spheronix Hackathon Team</strong><br/>
                                            Bangalore, India
                                        </p>
                                    </td>
                                </tr>
                                <tr>
                                    <td style="background:#f8fafc;border-top:1px solid #e5e7eb;padding:12px 24px;font-size:12px;color:#6b7280;text-align:center;">
                                        This is an automated transactional email regarding your Spheronix Hackathon registration.
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
    """

    return plain_body, html_body


def send_participant_confirmation_email(
    recipient_email: str,
    participant_name: str,
    role_text: str,
    participant_id: str,
    team_name: Optional[str],
    team_id: Optional[str],
    registration_doc: Dict[str, Any],
    mobile_number: Optional[str] = None,
) -> None:
    mail_from = settings.mail_from or settings.smtp_user
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password or not mail_from:
        return

    payment = registration_doc.get("payment", {})
    amount = float(payment.get("amount") or 0)
    currency = payment.get("currency") or "INR"
    payment_status = str(payment.get("status") or "success").upper()
    transaction_id = payment.get("transaction_id") or "N/A"
    task_selected = normalize_challenge_category(
        registration_doc.get("project_selected")
        or (registration_doc.get("assigned_challenge") or {}).get("category")
        or registration_doc.get("task_selected")
    )

    paid_ts = payment.get("timestamp") or registration_doc.get("registeredAt") or utc_now()
    paid_date = format_datetime_ist(paid_ts)

    # Extract college name & roll number
    leader_info = registration_doc.get("leader", {})
    college_name = leader_info.get("college") or registration_doc.get("collegeName") or "N/A"
    roll_number = leader_info.get("rollNumber") or registration_doc.get("rollNumber") or ""

    # Extract mobile number if not passed directly
    if not mobile_number:
        if str(recipient_email).lower() == str(leader_info.get("email", "")).lower():
            mobile_number = leader_info.get("phone") or leader_info.get("mobile") or ""
        else:
            for m in registration_doc.get("team_members", []):
                if str(m.get("email", "")).lower() == str(recipient_email).lower():
                    mobile_number = m.get("mobile") or m.get("phone") or ""
                    break
    mobile_number = mobile_number or leader_info.get("phone") or "N/A"

    # Build all team members list for team registration
    participation_mode = registration_doc.get("participationMode", "individual")
    team_members_list = []
    if participation_mode == "team" or team_name or team_id:
        if leader_info.get("name"):
            team_members_list.append({
                "name": leader_info.get("name"),
                "email": leader_info.get("email"),
                "mobile": leader_info.get("phone") or leader_info.get("mobile"),
                "college": leader_info.get("college") or college_name,
                "role": "Team Leader",
            })
        for m in registration_doc.get("team_members", []):
            team_members_list.append({
                "name": m.get("name"),
                "email": m.get("email"),
                "mobile": m.get("mobile") or m.get("phone"),
                "college": m.get("college") or college_name,
                "role": "Team Member",
            })

    receipt_url = build_receipt_download_url(registration_doc.get("rzp_order_id", ""), recipient_email)
    plain_body, html_body = _build_email_bodies(
        participant_name=participant_name,
        recipient_email=recipient_email,
        mobile_number=mobile_number,
        college_name=college_name,
        task_selected=task_selected,
        participation_mode=participation_mode,
        role_text=role_text,
        participant_id=participant_id,
        team_name=team_name,
        team_id=team_id,
        team_members=team_members_list,
        transaction_id=transaction_id,
        amount=amount,
        currency=currency,
        payment_status=payment_status,
        paid_date=paid_date,
        receipt_url=receipt_url,
        roll_number=roll_number,
    )

    sender_name = "Spheronix Hackathon"
    from_address = mail_from
    envelope_from = mail_from

    smtp_domain = settings.smtp_user.split("@", 1)[1].strip().lower() if "@" in settings.smtp_user else ""
    from_domain = mail_from.split("@", 1)[1].strip().lower() if "@" in mail_from else ""

    if smtp_domain and from_domain and smtp_domain != from_domain:
        # Align visible sender with SMTP identity to improve DMARC/SPF alignment.
        from_address = settings.smtp_user
        envelope_from = settings.smtp_user
        logger.warning(
            "MAIL_FROM domain (%s) differs from SMTP_USER domain (%s). Using SMTP_USER for sender alignment.",
            from_domain,
            smtp_domain,
        )

    sender_domain = "localhost"
    if "@" in from_address:
        sender_domain = from_address.split("@", 1)[1].strip() or sender_domain

    msg = MIMEMultipart("mixed")
    msg["From"] = formataddr((sender_name, from_address))
    msg["To"] = recipient_email
    msg["Subject"] = "Spheronix Hackathon Registration Confirmed"
    msg["Date"] = formatdate(localtime=True)
    msg["Reply-To"] = from_address

    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain_body, "plain"))
    alt.attach(MIMEText(html_body, "html"))
    msg.attach(alt)

    receipt_bytes = build_receipt_pdf(registration_doc, recipient_email)
    attachment = MIMEApplication(receipt_bytes, _subtype="pdf")
    attachment.add_header("Content-Disposition", "attachment", filename="Spheronix_Payment_Receipt.pdf")
    msg.attach(attachment)

    if settings.smtp_port == 465:
        # Fix P-05: Explicitly create default SSL context for certificate validation
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=25, context=ssl.create_default_context()) as server:
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(envelope_from, [recipient_email], msg.as_string())
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=25) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(envelope_from, [recipient_email], msg.as_string())



async def send_confirmation_email_async(**kwargs: Any) -> None:
    await asyncio.to_thread(send_participant_confirmation_email, **kwargs)


async def _duplicate_exists(query: Dict[str, Any], rzp_order_id: str) -> bool:
    existing = await registrations_async_collection.find_one(
        {
            "registrationCompleted": True,
            "rzp_order_id": {"$ne": rzp_order_id},
            "$or": [query],
        },
        {"_id": 1},
    )
    return existing is not None


def _resolve_verified_payment_amount(
    expected_amount: float,
    payment_state: Dict[str, Any],
    submitted_amount: Optional[float],
) -> tuple[float, str]:
    if submitted_amount is not None:
        try:
            submitted_value = float(submitted_amount)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid payment amount submitted")
        if abs(submitted_value - expected_amount) > 0.01:
            raise HTTPException(status_code=400, detail=f"Invalid payment amount. Expected INR {expected_amount:.2f}")

    recorded_amount = payment_state.get("amount")
    if recorded_amount is None:
        final_amount = expected_amount
    else:
        try:
            final_amount = float(recorded_amount)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid recorded payment amount")

        if abs(final_amount - expected_amount) > 0.01:
            raise HTTPException(status_code=400, detail=f"Payment amount mismatch. Expected INR {expected_amount:.2f}")

    currency = str(payment_state.get("currency") or "INR")
    return final_amount, currency


def _resolve_selected_task(student: StudentRegister, existing_for_order: Dict[str, Any] | None) -> str:
    submitted_task = (student.projectSelected or "").strip()
    if submitted_task:
        return submitted_task

    stored_task = ""
    if existing_for_order:
        stored_task = str(
            existing_for_order.get("task_selected") or existing_for_order.get("project_selected") or ""
        ).strip()

    if stored_task:
        return stored_task

    raise HTTPException(status_code=400, detail="Task category is required for challenge assignment")


def _validate_no_local_duplicates(student: StudentRegister, member_dicts: List[Dict[str, Any]]) -> None:
    emails = {str(student.email).lower()}
    mobiles = {student.mobile}
    rolls = {student.rollNumber.lower()}

    for member in member_dicts:
        email = str(member["email"]).lower()
        mobile = member["mobile"]
        roll = member["rollNumber"].lower()

        if email in emails:
            raise HTTPException(status_code=400, detail="Duplicate email inside team members")
        if mobile in mobiles:
            raise HTTPException(status_code=400, detail="Duplicate mobile inside team members")
        if roll in rolls:
            raise HTTPException(status_code=400, detail="Duplicate roll number inside team members")

        emails.add(email)
        mobiles.add(mobile)
        rolls.add(roll)


async def _validate_global_duplicates(student: StudentRegister, member_dicts: List[Dict[str, Any]]) -> None:
    checks = [
        {"email": str(student.email)},
        {"leader.email": str(student.email)},
        {"team_members.email": str(student.email)},
        {"mobile": student.mobile},
        {"leader.phone": student.mobile},
        {"team_members.mobile": student.mobile},
        {"rollNumber": student.rollNumber},
        {"leader.rollNumber": student.rollNumber},
        {"team_members.rollNumber": student.rollNumber},
    ]

    for member in member_dicts:
        checks.extend(
            [
                {"team_members.email": str(member["email"])},
                {"team_members.mobile": member["mobile"]},
                {"team_members.rollNumber": member["rollNumber"]},
                {"email": str(member["email"])},
                {"leader.email": str(member["email"])},
                {"mobile": member["mobile"]},
                {"leader.phone": member["mobile"]},
                {"rollNumber": member["rollNumber"]},
                {"leader.rollNumber": member["rollNumber"]},
            ]
        )

    for query in checks:
        if await _duplicate_exists(query, student.rzp_order_id or ""):
            raise HTTPException(status_code=400, detail="Duplicate registration data detected.")


def _build_idempotent_response(existing_for_order: Dict[str, Any]) -> StudentResponse:
    participation_mode = str(existing_for_order.get("participationMode") or "individual").lower()
    leader = existing_for_order.get("leader") or {}
    team_members = existing_for_order.get("team_members") or []
    payment = existing_for_order.get("payment") or {}

    registration_id = str(existing_for_order.get("rzp_order_id") or "")
    participant_id = str(
        existing_for_order.get("participant_id")
        or leader.get("participant_id")
        or ""
    )
    participant_id = participant_id or None

    task_selected = str(
        existing_for_order.get("task_selected")
        or existing_for_order.get("project_selected")
        or ""
    ) or None
    transaction_id = str(payment.get("transaction_id") or "") or None
    payment_status = str(
        existing_for_order.get("payment_status")
        or payment.get("status")
        or "success"
    )

    if participation_mode == "team":
        team_member_ids = [
            str(member.get("participant_id"))
            for member in team_members
            if member.get("participant_id")
        ]
        team_member_emails = [
            str(member.get("email")).lower()
            for member in team_members
            if member.get("email")
        ]
        return StudentResponse(
            registrationId=registration_id,
            fullName=str(leader.get("name") or ""),
            email=str(leader.get("email") or "").lower(),
            participantId=participant_id,
            teamLeaderId=participant_id,
            teamMemberIds=team_member_ids,
            teamId=str(existing_for_order.get("team_id") or "") or None,
            transactionId=transaction_id,
            paymentStatus=payment_status,
            taskSelected=task_selected,
            assignedChallenge=None,  # Hide from user
            message="Team registration already completed for this payment order.",
            teamMemberEmails=team_member_emails,
            teamMemberNames=[member.get("name") for member in team_members if member.get("name")],
        )

    return StudentResponse(
        registrationId=registration_id,
        fullName=str(leader.get("name") or ""),
        email=str(leader.get("email") or "").lower(),
        participantId=participant_id,
        teamId=None,
        transactionId=transaction_id,
        paymentStatus=payment_status,
        taskSelected=task_selected,
        assignedChallenge=None,  # Hide from user
        message="Individual registration already completed for this payment order.",
    )


async def register_student(student: StudentRegister, rzp_payment_id: str | None, payment_status: str) -> StudentResponse:
    registration_time = ist_now()
    normalized_payment_status = (payment_status or "success").lower()
    if normalized_payment_status != "success":
        raise HTTPException(status_code=400, detail="Payment is not successful.")

    existing_for_order = await registrations_async_collection.find_one({"rzp_order_id": student.rzp_order_id})
    if existing_for_order and existing_for_order.get("registrationCompleted"):
        return _build_idempotent_response(existing_for_order)
    payment_state = existing_for_order.get("payment", {}) if existing_for_order else {}
    selected_task = _resolve_selected_task(student, existing_for_order)

    # Intercept payment receipt and upload to Supabase Storage
    base64_receipt = (
        student.payment_receipt_base64
        or student.receipt_base64
        or (student.payment_receipt_url if (student.payment_receipt_url or "").startswith("data:") else None)
    )
    final_receipt_url = student.payment_receipt_url if not (student.payment_receipt_url or "").startswith("data:") else None

    if base64_receipt:
        import time
        import re
        timestamp = int(time.time())
        order_key = student.order_id or student.rzp_order_id or "order"
        safe_name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", student.payment_receipt_name or "receipt.png")
        filename = f"{order_key}_{timestamp}_{safe_name}"

        supabase_url = await upload_receipt_to_supabase(base64_receipt, filename)
        if supabase_url:
            final_receipt_url = supabase_url
            student.payment_receipt_url = supabase_url
            student.payment_receipt_base64 = None
            student.receipt_base64 = None
        else:
            raise HTTPException(status_code=500, detail="Failed to upload payment receipt to storage. Please try again.")

    if not final_receipt_url and existing_for_order:
        existing_url = existing_for_order.get("payment_receipt_url") or existing_for_order.get("receipt_url")
        if existing_url and not existing_url.startswith("data:"):
            final_receipt_url = existing_url

    receipt_name = student.payment_receipt_name or (existing_for_order.get("payment_receipt_name") if existing_for_order else None) or "receipt.png"

    receipt_fields = {
        "payment_receipt_base64": None,
        "payment_receipt_name": receipt_name,
        "payment_receipt_url": final_receipt_url,
    }

    if student.participationMode == "team":
        member_models = student.teamMembers or []
        member_count = len(member_models)
        total_members = 1 + member_count

        if total_members < MIN_TEAM_TOTAL_MEMBERS:
            raise HTTPException(status_code=400, detail="Team must have at least 2 members including leader")
        if total_members > MAX_TEAM_TOTAL_MEMBERS:
            raise HTTPException(status_code=400, detail="Team cannot exceed 5 members including leader")
        if member_count > MAX_TEAM_MEMBERS_EXCLUDING_LEADER:
            raise HTTPException(status_code=400, detail="Maximum 4 team members allowed excluding leader")

        fee_per_member = await get_registration_fee()
        expected_amount = float(fee_per_member * total_members)
        paid_amount, paid_currency = _resolve_verified_payment_amount(
            expected_amount=expected_amount,
            payment_state=payment_state,
            submitted_amount=student.payment_amount,
        )

        team_name = (student.teamName or "").strip()
        if not team_name:
            raise HTTPException(status_code=400, detail="Team name is required for team registration")

        member_dicts = [member.model_dump() for member in member_models]
        _validate_no_local_duplicates(student, member_dicts)
        await _validate_global_duplicates(student, member_dicts)

        team_id = await generate_unique_team_id()
        leader_id = build_team_member_participant_id(team_id, 1)
        assigned_challenge = await assign_random_challenge(
            selected_task,
            team_id=team_id,
            registration_id=student.rzp_order_id,
        )

        enriched_members: List[Dict[str, Any]] = []
        for idx, member in enumerate(member_dicts, start=2):
            enriched_member = {
                "name": member["fullName"],
                "email": str(member["email"]).lower(),
                "mobile": member["mobile"],
                "phone": member["mobile"],
                "rollNumber": member["rollNumber"],
                "githubProfile": member["githubProfile"],
                "branch": student.branch,
                "participant_id": build_team_member_participant_id(team_id, idx),
            }
            enriched_members.append(enriched_member)

        registration_doc: Dict[str, Any] = {
            "order_id": student.order_id or student.rzp_order_id,
            "rzp_order_id": student.order_id or student.rzp_order_id,
            "registrationCompleted": True,
            "participationMode": "team",
            "team_id": team_id,
            "team_name": team_name,
            "project_selected": normalize_challenge_category(selected_task),
            "task_selected": normalize_challenge_category(selected_task),
            "assigned_challenge": assigned_challenge,
            "total_members": total_members,
            "payment_status": "success",
            "currentYear": student.currentYear,
            "leader": {
                "participant_id": leader_id,
                "name": student.fullName,
                "email": str(student.email).lower(),
                "phone": student.mobile,
                "college": student.collegeName,
                "branch": student.branch,
                "city": student.city,
                "rollNumber": student.rollNumber,
                "currentYear": student.currentYear,
                "githubProfile": student.githubProfile,
            },
            "team_members": enriched_members,
            **receipt_fields,
            "payment": {
                "transaction_id": rzp_payment_id,
                "order_id": student.order_id or student.rzp_order_id,
                "gateway": student.payment_gateway or "upi",
                "amount": paid_amount,
                "currency": paid_currency,
                "status": "success",
                "timestamp": registration_time,
            },
            "updatedAt": registration_time,
        }
        
        insert_only_fields = {
            "createdAt": registration_time,
            "registeredAt": registration_time,
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
                {"rzp_order_id": student.rzp_order_id},
                {
                    "$set": registration_doc,
                    "$setOnInsert": insert_only_fields,
                },
                upsert=True,
            )

            logger.info(
                "[MONGODB SAVED] Team Registration for '%s' (Order: %s) saved to 'registrations' collection. Receipt URL: %s",
                student.fullName,
                student.rzp_order_id,
                student.payment_receipt_url,
            )

            await teams_async_collection.update_one(
                {"teamId": team_id},
                {
                    "$set": {
                        "teamId": team_id,
                        "teamName": team_name,
                        "leaderEmail": str(student.email).lower(),
                        "leaderId": leader_id,
                        "collegeName": student.collegeName,
                        "branch": student.branch,
                        "projectSelected": selected_task,
                        "taskSelected": assigned_challenge["title"],
                        "assignedChallenge": assigned_challenge,
                        "paymentStatus": "success",
                        "payment": registration_doc["payment"],
                        "registrationId": student.rzp_order_id,
                        "members": [
                            {
                                "participant_id": leader_id,
                                "name": student.fullName,
                                "email": str(student.email).lower(),
                                "mobile": student.mobile,
                                "role": "leader",
                            }
                        ]
                        + [
                            {
                                "participant_id": member["participant_id"],
                                "name": member["name"],
                                "email": member["email"],
                                "mobile": member["mobile"],
                                "role": "member",
                            }
                            for member in enriched_members
                        ],
                        "totalMembers": total_members,
                        "updatedAt": registration_time,
                    },
                    "$setOnInsert": {"createdAt": registration_time},
                },
                upsert=True,
            )
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail="Duplicate registration conflict. Please retry.")

        await users_async_collection.update_one(
            {"email": str(student.email).lower()},
            {
                "$set": {"name": student.fullName, "googleId": None, "updatedAt": registration_time},
                "$setOnInsert": {"createdAt": registration_time},
            },
            upsert=True,
        )

        # Team leader + each member receive their own ID and receipt email individually.
        try:
            # Fix M-03: Send emails in the background to avoid blocking API response
            async def send_all_team_emails():
                try:
                    await asyncio.gather(
                        send_confirmation_email_async(
                            recipient_email=str(student.email).lower(),
                            participant_name=student.fullName,
                            role_text="team leader",
                            participant_id=leader_id,
                            team_name=team_name,
                            team_id=team_id,
                            registration_doc=registration_doc,
                            mobile_number=student.mobile,
                        ),
                        *[
                            send_confirmation_email_async(
                                recipient_email=member["email"],
                                participant_name=member["name"],
                                role_text="team member",
                                participant_id=member["participant_id"],
                                team_name=team_name,
                                team_id=team_id,
                                registration_doc=registration_doc,
                                mobile_number=member.get("mobile", ""),
                            )
                            for member in enriched_members
                        ],
                    )
                except Exception as email_err:
                    logger.warning("Failed to send team confirmation emails: %s", email_err)
            
            asyncio.create_task(send_all_team_emails())
        except Exception as e:
            logger.warning("Failed to schedule team emails: %s", e)

        return StudentResponse(
            registrationId=student.rzp_order_id or "",
            fullName=student.fullName,
            email=str(student.email).lower(),
            participantId=leader_id,
            teamLeaderId=leader_id,
            teamMemberIds=[member["participant_id"] for member in enriched_members],
            teamId=team_id,
            transactionId=rzp_payment_id,
            paymentStatus="success",
            taskSelected=selected_task,
            assignedChallenge=None, # Hide from user
            message=(
                "Team registration successful. Team ID, challenge details, and receipts have been emailed to the leader and members."
            ),
            teamMemberEmails=[member["email"] for member in enriched_members],
            teamMemberNames=[member["name"] for member in enriched_members],
        )

    await _validate_global_duplicates(student, [])

    fee_per_member = await get_registration_fee()
    expected_amount = float(fee_per_member)
    paid_amount, paid_currency = _resolve_verified_payment_amount(
        expected_amount=expected_amount,
        payment_state=payment_state,
        submitted_amount=student.payment_amount,
    )

    individual_id = await generate_unique_individual_id()
    assigned_challenge = await assign_random_challenge(selected_task, registration_id=student.rzp_order_id)
    registration_doc = {
        "order_id": student.order_id or student.rzp_order_id,
        "rzp_order_id": student.order_id or student.rzp_order_id,
        "registrationCompleted": True,
        "participationMode": "individual",
        "participant_id": individual_id,
        "team_id": None,
        "team_name": None,
        "project_selected": normalize_challenge_category(selected_task),
        "task_selected": normalize_challenge_category(selected_task),
        "assigned_challenge": assigned_challenge,
        "total_members": 1,
        "payment_status": "success",
        "currentYear": student.currentYear,
        "leader": {
            "participant_id": individual_id,
            "name": student.fullName,
            "email": str(student.email).lower(),
            "phone": student.mobile,
            "college": student.collegeName,
            "branch": student.branch,
            "city": student.city,
            "rollNumber": student.rollNumber,
            "currentYear": student.currentYear,
            "githubProfile": student.githubProfile,
        },
        "team_members": [],
        **receipt_fields,
        "payment": {
            "transaction_id": rzp_payment_id,
            "order_id": student.order_id or student.rzp_order_id,
            "gateway": student.payment_gateway or "upi",
            "amount": paid_amount,
            "currency": paid_currency,
            "status": "success",
            "timestamp": registration_time,
        },
        "updatedAt": registration_time,
    }
    
    insert_only_fields = {
        "createdAt": registration_time,
        "registeredAt": registration_time,
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
            {"rzp_order_id": student.rzp_order_id},
            {
                "$set": registration_doc,
                "$setOnInsert": insert_only_fields,
            },
            upsert=True,
        )

        logger.info(
            "[MONGODB SAVED] Individual Registration for '%s' (Order: %s) saved to 'registrations' collection. Receipt URL: %s",
            student.fullName,
            student.rzp_order_id,
            student.payment_receipt_url,
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Duplicate registration conflict. Please retry.")

    await users_async_collection.update_one(
        {"email": str(student.email).lower()},
        {
            "$set": {"name": student.fullName, "googleId": None, "updatedAt": registration_time},
            "$setOnInsert": {"createdAt": registration_time},
        },
        upsert=True,
    )

    try:
        # Fix M-03: Send emails in the background to avoid blocking API response
        async def send_individual_email():
            try:
                await send_confirmation_email_async(
                    recipient_email=str(student.email).lower(),
                    participant_name=student.fullName,
                    role_text="individual",
                    participant_id=individual_id,
                    team_name=None,
                    team_id=None,
                    registration_doc=registration_doc,
                    mobile_number=student.mobile,
                )
            except Exception as email_err:
                logger.warning("Failed to send individual confirmation email: %s", email_err)
        
        asyncio.create_task(send_individual_email())
    except Exception as e:
        logger.warning("Failed to schedule individual email: %s", e)

    return StudentResponse(
        registrationId=student.rzp_order_id or "",
        fullName=student.fullName,
        email=str(student.email).lower(),
        participantId=individual_id,
        teamId=None,
        transactionId=rzp_payment_id,
        paymentStatus="success",
        taskSelected=selected_task,
        assignedChallenge=None, # Hide from user
        message="Individual registration successful. Your registration details and receipt have been emailed.",
    )



