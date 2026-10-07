from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
import base64
import json
import uuid
from datetime import datetime
from app.routers.dashboard import get_current_user
from app.services.auth_service import AuthService
from app.database.mongodb import users_collection, nodal_registrations_collection, submissions_collection

router = APIRouter(prefix="/api/payment", tags=["Payment"])

@router.post("/submit")
async def final_submit(
    paymentProof: UploadFile = File(...), 
    parsedData: str = Form(...),
    totalAmount: float = Form(...),
    eligibleRecords: int = Form(...),
    originalFilename: str = Form(...),
    user_id: str = Depends(get_current_user)
):
    # Check if user exists
    user     = await AuthService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Validate image file
    if not paymentProof.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Payment proof must be an image file.")
        
    content = await paymentProof.read()
    if len(content) > 30 * 1024:
        raise HTTPException(status_code=400, detail="Payment proof exceeds the 30 KB size limit.")
        
    # Convert image to base64 for easy DB storage (since it's max 30KB, this is very efficient)
    b64_image = base64.b64encode(content).decode('utf-8')
    mime_type = paymentProof.content_type
    image_data_uri = f"data:{mime_type};base64,{b64_image}"
    
    try:
        json_data = json.loads(parsedData)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON data.")

    # Fetch nodal registration to get collegeCode and submitter details
    nodal = await nodal_registrations_collection.find_one({
        "$or": [{"principalId": user_id}, {"nodalOfficerId": user_id}]
    })
    
    college_code = "UNKNOWN"
    submitter_role = "Admin"
    submitter_name = "Admin"
    
    if nodal:
        college_code = nodal.get("collegeCode", "UNKNOWN")
        if user_id == nodal.get("principalId"):
            submitter_role = "Principal"
            submitter_name = nodal.get("principalName", "Unknown")
        else:
            submitter_role = "Nodal Officer"
            submitter_name = nodal.get("nodalOfficerName", "Unknown")

    timestamp_str = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_str = uuid.uuid4().hex[:6].upper()
    submission_id = f"SUB-{timestamp_str}-{random_str}"

    submission_data = {
        "submissionId": submission_id,
        "userId": user_id,
        "collegeCode": college_code,
        "submitterRole": submitter_role,
        "submitterName": submitter_name,
        "status": "Submitted",
        "csvData": json_data,
        "paymentProof": image_data_uri,
        "totalAmount": totalAmount,
        "eligibleRecords": eligibleRecords,
        "originalFilename": originalFilename,
        "paymentTimestamp": datetime.utcnow()
    }
    
    # Insert new submission
    await submissions_collection.insert_one(submission_data)
    
    return {"message": "Application submitted successfully."}
