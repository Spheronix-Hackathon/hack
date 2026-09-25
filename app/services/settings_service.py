from typing import Any, Dict
from app.database.mongodb import async_db, global_async_db, async_client
from config.settings import get_settings

def extract_field(doc: dict, *keys: str, default: str = "") -> str:
    if not doc:
        return default
    for k in keys:
        val = doc.get(k)
        if val is not None and str(val).strip():
            return str(val).strip()
    return default

async def get_raw_settings_doc() -> dict:
    """Fetch the latest settings document across all database locations."""
    # 1. Primary: spheronix_db.settings
    doc = await async_db["settings"].find_one(sort=[("updatedAt", -1), ("_id", -1)])
    if doc:
        return doc

    # 2. Secondary: global_async_db.settings
    try:
        doc = await global_async_db["settings"].find_one(sort=[("updatedAt", -1), ("_id", -1)])
        if doc:
            return doc
    except Exception:
        pass

    # 3. Tertiary: admin database settings
    try:
        doc = await async_client["admin"]["settings"].find_one(sort=[("updatedAt", -1), ("_id", -1)])
        if doc:
            return doc
    except Exception:
        pass

    return {}

async def get_payment_settings() -> Dict[str, Any]:
    """Retrieve up-to-date payment configuration from the latest admin settings document."""
    current_settings = get_settings()
    db_settings = await get_raw_settings_doc()

    # Extract Registration Fee / Amount
    reg_amount = float(current_settings.default_registration_fee or 1.0)
    for k in ("registrationAmount", "registration_amount", "registrationFee", "registration_fee", "amount", "fee", "price"):
        if k in db_settings:
            try:
                reg_amount = float(db_settings[k])
                break
            except (ValueError, TypeError):
                pass

    # Extract UPI ID (Ensure no placeholder)
    raw_upi = extract_field(
        db_settings,
        "upiId", "upi_id", "upi", "vpa", "upi_address",
        default=current_settings.upi_id or "334509931804612@CNRB",
    )
    if not raw_upi or "spheronixhackathon@" in raw_upi.lower() or "example@" in raw_upi.lower() or raw_upi.lower() == "spheronixhackathon@upi":
        raw_upi = (current_settings.upi_id or "").strip() or "334509931804612@CNRB"

    upi_payee = extract_field(
        db_settings,
        "upiPayeeName", "upi_payee_name", "payeeName", "payee_name", "accountHolderName",
        default=current_settings.upi_payee_name or "SPHERONIX TECHNOLOGY PVT. LTD.",
    )
    bank_name = extract_field(
        db_settings,
        "bankName", "bank_name", "bank",
        default="CANARA BANK",
    )
    account_number = extract_field(
        db_settings,
        "accountNumber", "account_number", "accountNo", "account_no", "accNumber",
        default="120036804612",
    )
    ifsc_code = extract_field(
        db_settings,
        "ifscCode", "ifsc_code", "ifsc", "IFSC",
        default="CNRB0000659",
    )
    account_holder_name = extract_field(
        db_settings,
        "accountHolderName", "account_holder_name", "holderName", "accountName", "account_name",
        default="SPHERONIX TECHNOLOGY PVT. LTD.",
    )

    return {
        "registrationAmount": reg_amount,
        "upiId": raw_upi,
        "upiPayeeName": upi_payee,
        "bankName": bank_name,
        "accountNumber": account_number,
        "ifscCode": ifsc_code,
        "accountHolderName": account_holder_name,
    }

async def get_registration_fee() -> float:
    settings_dict = await get_payment_settings()
    return float(settings_dict.get("registrationAmount", 1.0))
