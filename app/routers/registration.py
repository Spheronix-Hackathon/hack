from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.models.schemas import NodalRegistrationRequest, OtpSendRequest
from app.services.verification_service import VerificationService, otp_store
from app.services.nodal_registration_service import NodalRegistrationService

router = APIRouter(prefix="/api/register", tags=["Registration"])

@router.post("/send-email-otp")
async def send_email_otp(req: OtpSendRequest):
    # Prevent sending OTP if email is already registered
    is_principal = await NodalRegistrationService.check_field_exists("principalEmail", req.contact)
    is_nodal = await NodalRegistrationService.check_field_exists("nodalOfficerEmail", req.contact)
    if is_principal or is_nodal:
        raise HTTPException(status_code=400, detail="This Email Address is already registered.")

    success = await VerificationService.send_email_otp(req.contact)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send OTP")
    return {"message": "OTP sent successfully"}

class CheckExistsRequest(BaseModel):
    field: str
    value: str

@router.post("/check-exists")
async def check_exists(req: CheckExistsRequest):
    allowed_fields = [
        "collegeCode", "principalName", "principalEmail", "principalMobile",
        "nodalOfficerName", "nodalOfficerEmail", "nodalOfficerMobile"
    ]
    if req.field not in allowed_fields:
        raise HTTPException(status_code=400, detail="Invalid field for existence check")
        
    exists = await NodalRegistrationService.check_field_exists(req.field, req.value)
    return {"exists": exists}

@router.post("/submit")
async def submit_registration(data: NodalRegistrationRequest):
    # Verify OTPs
    if not VerificationService.verify_otp(data.principalEmail, data.emailOtp):
        raise HTTPException(status_code=400, detail="Invalid or expired Email OTP")

    # Store registration
    result = await NodalRegistrationService.register_nodal_officer(data)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
        
    return {"message": "Registration successful", "id": result["id"]}
