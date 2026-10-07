from app.database.mongodb import nodal_registrations_collection
from app.models.schemas import NodalRegistrationRequest
from pymongo.errors import DuplicateKeyError
import logging

logger = logging.getLogger(__name__)

class NodalRegistrationService:
    @staticmethod
    async def register_nodal_officer(data: NodalRegistrationRequest) -> dict:
        college_code_upper = data.collegeCode.strip().upper()
        
        # Explicitly check cross-field uniqueness before insert
        if await nodal_registrations_collection.find_one({"collegeCode": college_code_upper}):
            return {"success": False, "message": "This College Code already exists."}
            
        emails_to_check = [data.principalEmail, data.nodalOfficerEmail]
        if await nodal_registrations_collection.find_one({"$or": [{"principalEmail": {"$in": emails_to_check}}, {"nodalOfficerEmail": {"$in": emails_to_check}}]}):
            return {"success": False, "message": "One of the provided Email Addresses already exists in another registration."}
            
        mobiles_to_check = [data.principalMobile, data.nodalOfficerMobile]
        if await nodal_registrations_collection.find_one({"$or": [{"principalMobile": {"$in": mobiles_to_check}}, {"nodalOfficerMobile": {"$in": mobiles_to_check}}]}):
            return {"success": False, "message": "One of the provided Mobile Numbers already exists in another registration."}

        doc = data.model_dump()
        doc["collegeCode"] = college_code_upper
        try:
            result = await nodal_registrations_collection.insert_one(doc)
            return {"success": True, "id": str(result.inserted_id)}
        except DuplicateKeyError as e:
            msg = "Registration already exists"
            if "collegeCode" in str(e):
                msg = "This College Code already exists."
            elif "principalName" in str(e):
                msg = "A registration with this Principal Name already exists."
            elif "principalEmail" in str(e):
                msg = "A registration with this Principal Gmail Address already exists."
            elif "principalMobile" in str(e):
                msg = "A registration with this Principal Mobile Number already exists."
            elif "nodalOfficerName" in str(e):
                msg = "A registration with this Nodal Officer Name already exists."
            elif "nodalOfficerEmail" in str(e):
                msg = "A registration with this Nodal Officer Gmail Address already exists."
            elif "nodalOfficerMobile" in str(e):
                msg = "A registration with this Nodal Officer Mobile Number already exists."
            return {"success": False, "message": msg}
        except Exception as e:
            logger.error(f"Error registering nodal officer: {e}")
            return {"success": False, "message": "Internal server error during registration"}
            
    @staticmethod
    async def check_field_exists(field: str, value: str) -> bool:
        if field == "collegeCode":
            value = value.strip().upper()
            query = {field: value}
        elif field in ["principalEmail", "nodalOfficerEmail"]:
            query = {"$or": [{"principalEmail": value}, {"nodalOfficerEmail": value}]}
        elif field in ["principalMobile", "nodalOfficerMobile"]:
            query = {"$or": [{"principalMobile": value}, {"nodalOfficerMobile": value}]}
        else:
            query = {field: value}
            
        doc = await nodal_registrations_collection.find_one(query)
        return bool(doc)
