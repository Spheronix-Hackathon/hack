import random
import time
import smtplib
from email.message import EmailMessage
import logging
from config.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

otp_store = {}

class VerificationService:
    @staticmethod
    def generate_otp() -> str:
        return str(random.randint(100000, 999999))

    @staticmethod
    async def send_email_otp(email: str) -> bool:
        otp = VerificationService.generate_otp()
        otp_store[email] = {"otp": otp, "expiry": time.time() + 300}
        
        try:
            msg = EmailMessage()
            msg.set_content(f"Your OTP for Spheronix Hackathon Registration is: {otp}\n\nIt is valid for 5 minutes.")
            msg['Subject'] = 'Nodal Officer Registration OTP'
            msg['From'] = settings.mail_from
            msg['To'] = email

            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port)
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email OTP: {e}")
            return False
        
    @staticmethod
    def verify_otp(contact: str, otp: str) -> bool:
        record = otp_store.get(contact)
        if not record:
            return False
        
        if time.time() > record["expiry"]:
            del otp_store[contact]
            return False
            
        if record["otp"] == otp:
            del otp_store[contact]
            return True
            
        return False
