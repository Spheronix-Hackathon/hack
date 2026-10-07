import pyotp
import jwt
import base64
from datetime import datetime, timedelta
from passlib.context import CryptContext
from qrcode import make as make_qr
from io import BytesIO
from app.database.mongodb import users_collection, nodal_registrations_collection
from config.settings import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use a default secret if not set
JWT_SECRET = getattr(settings, "jwt_secret", "spheronix-hackathon-super-secret-key")
JWT_ALGORITHM = "HS256"

class AuthService:
    @staticmethod
    def verify_password(plain_password, db_password, is_plaintext=False):
        plain_password = plain_password.strip()
        if is_plaintext:
            return plain_password == db_password
        try:
            return pwd_context.verify(plain_password, db_password)
        except Exception as e1:
            try:
                import bcrypt
                # bcrypt library throws Invalid Salt for $2a$, so we map it to $2b$ which is compatible
                fixed_hash = db_password.replace('$2a$', '$2b$').encode('utf-8')
                return bcrypt.checkpw(plain_password.encode('utf-8'), fixed_hash)
            except Exception as e2:
                import logging
                logging.error(f"Passlib error: {e1}, Bcrypt error: {e2}")
                return False

    @staticmethod
    async def get_user_by_id(user_id: str):
        # Case-insensitive query for userId
        query_pattern = {"$regex": f"^{user_id}$", "$options": "i"}
        
        user = await users_collection.find_one({"userId": query_pattern})
        if user:
            pwd = user.get("password", "")
            user["is_plaintext_password"] = user.get("is_plaintext_password", not str(pwd).startswith("$2"))
            user["systemStatus"] = user.get("systemStatus", "approved")  # Default to approved for regular users
            return user
            
        nodal = await nodal_registrations_collection.find_one({"principalId": query_pattern})
        if nodal:
            pwd = nodal.get("principalPassword", nodal.get("password", ""))
            return {
                "userId": nodal["principalId"],
                "password": pwd,
                "role": "principal",
                "is_plaintext_password": not pwd.startswith("$2"),
                "totpSecret": nodal.get("principalTotpSecret", nodal.get("totpSecret")),
                "systemStatus": nodal.get("systemStatus", "pending")
            }
            
        nodal = await nodal_registrations_collection.find_one({"nodalOfficerId": query_pattern})
        if nodal:
            pwd = nodal.get("nodalOfficerPassword", nodal.get("password", ""))
            return {
                "userId": nodal["nodalOfficerId"],
                "password": pwd,
                "role": "nodal_officer",
                "is_plaintext_password": not pwd.startswith("$2"),
                "totpSecret": nodal.get("nodalOfficerTotpSecret", nodal.get("totpSecret")),
                "systemStatus": nodal.get("systemStatus", "pending")
            }
            
        return None

    @staticmethod
    def create_jwt_token(data: dict, expires_delta: timedelta = timedelta(hours=8)):
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_jwt_token(token: str):
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None

    @staticmethod
    def generate_2fa_secret():
        return pyotp.random_base32()

    @staticmethod
    def get_2fa_qr_base64(user_id: str, secret: str):
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=user_id, issuer_name="Spheronix Hackathon")
        img = make_qr(uri)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()

    @staticmethod
    def verify_totp(secret: str, code: str):
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    @staticmethod
    async def set_2fa_secret(user_id: str, secret: str):
        result = await users_collection.update_one({"userId": user_id}, {"$set": {"totpSecret": secret}})
        if result.modified_count == 0:
            res = await nodal_registrations_collection.update_one({"principalId": user_id}, {"$set": {"principalTotpSecret": secret}})
            if res.modified_count == 0:
                await nodal_registrations_collection.update_one({"nodalOfficerId": user_id}, {"$set": {"nodalOfficerTotpSecret": secret}})
