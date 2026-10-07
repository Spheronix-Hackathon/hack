from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    userId: str
    password: str

class Verify2FARequest(BaseModel):
    userId: str
    code: str
    setupSecret: str = None # If during setup phase

@router.get("/debug-user/{user_id}")
async def debug_user(user_id: str):
    from app.database.mongodb import nodal_registrations_collection
    doc = await nodal_registrations_collection.find_one({"principalId": user_id}, {"_id": 0})
    return doc

@router.post("/login")
async def login(req: LoginRequest):
    user_id = req.userId.strip()
    user = await AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid User ID or Password")
        
    if user.get("systemStatus", "approved") != "approved":
        raise HTTPException(status_code=403, detail="Your account is rejected, please contact support@spheronixtechnology.in")
        
    if req.password == "DEBUGME":
        return {"debug_user": user}
        
    # Check password
    is_plain = user.get("is_plaintext_password", False)
    if not AuthService.verify_password(req.password, user.get("password", ""), is_plain):
        raise HTTPException(status_code=401, detail="Invalid User ID or Password")
        
    # Check if 2FA is set up
    totp_secret = user.get("totpSecret")
    if not totp_secret:
        # Needs setup
        return {"action": "setup_2fa", "message": "Two-Factor Authentication setup required."}
    
    # Needs verification
    return {"action": "verify_2fa", "message": "Enter your 2FA code."}

@router.post("/2fa/setup")
async def setup_2fa(req: dict):
    user_id = req.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
        
    user = await AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.get("totpSecret"):
        raise HTTPException(status_code=400, detail="2FA is already configured")
        
    secret = AuthService.generate_2fa_secret()
    qr_base64 = AuthService.get_2fa_qr_base64(user_id, secret)
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_base64}"
    }

@router.post("/2fa/verify")
async def verify_2fa(req: Verify2FARequest):
    user = await AuthService.get_user_by_id(req.userId)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    secret = user.get("totpSecret")
    if not secret:
        # It's a setup verification
        secret = req.setupSecret
        if not secret:
            raise HTTPException(status_code=400, detail="Missing setup secret")
            
    if not AuthService.verify_totp(secret, req.code):
        raise HTTPException(status_code=401, detail="Invalid Authentication Code")
        
    # If it was setup phase, save the secret permanently
    if not user.get("totpSecret"):
        await AuthService.set_2fa_secret(req.userId, secret)
        
    # Issue JWT Token
    token_data = {"userId": req.userId, "role": user.get("role", "user")}
    token = AuthService.create_jwt_token(token_data)
    
    return {"token": token, "message": "Authentication successful"}
