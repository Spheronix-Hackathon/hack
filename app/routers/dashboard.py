from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
import csv
from io import StringIO
from typing import Optional
import pandas as pd
import io
from app.services.auth_service import AuthService
from app.database.mongodb import settings_collection, users_collection, nodal_registrations_collection, submissions_collection

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = authorization.split(" ")[1]
    payload = AuthService.decode_jwt_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["userId"]

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user)):
    user = await users_collection.find_one({"userId": user_id}, {"_id": 0})
    if user:
        return user
        
    nodal = await nodal_registrations_collection.find_one({"principalId": user_id}, {"_id": 0})
    if nodal:
        nodal["userId"] = nodal["principalId"]
        nodal["role"] = "principal"
        return nodal
        
    nodal = await nodal_registrations_collection.find_one({"nodalOfficerId": user_id}, {"_id": 0})
    if nodal:
        nodal["userId"] = nodal["nodalOfficerId"]
        nodal["role"] = "nodal_officer"
        return nodal
        
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/sample-excel")
async def get_sample_excel():
    from fastapi.responses import FileResponse
    import os
    
    file_path = "static/Hackathon Students Sample Data.xlsx"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample file not found on server")
        
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="Hackathon_Students_Sample_Data.xlsx"
    )

@router.post("/upload-data")
async def upload_data(file: UploadFile = File(...), user_id: str = Depends(get_current_user)):
    filename = file.filename.lower()
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(status_code=400, detail="Only CSV, XLSX, and XLS files are allowed.")
    
    content = await file.read()
    try:
        if filename.endswith(".csv"):
            try:
                decoded_content = content.decode('utf-8')
            except UnicodeDecodeError:
                raise HTTPException(status_code=400, detail="Invalid file encoding. Please upload a UTF-8 CSV.")
                
            csv_reader = csv.reader(StringIO(decoded_content))
            rows = list(csv_reader)
        else:
            # Excel files
            df = pd.read_excel(io.BytesIO(content))
            df = df.fillna("")
            headers = df.columns.tolist()
            rows = [headers] + df.values.tolist()
            rows = [[str(val) for val in row] for row in rows]
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing file: {str(e)}")
    
    if len(rows) < 2:
        raise HTTPException(status_code=400, detail="File is empty or missing data rows.")
        
    headers = rows[0]
    json_data = []
    eligible_count = 0
    
    for row in rows[1:]: # Skip header
        if not any(row): # Skip entirely empty rows
            continue
            
        row_dict = {}
        has_data = False
        for i, val in enumerate(row):
            col_name = headers[i] if i < len(headers) else f"Col_{i}"
            row_dict[col_name] = str(val).strip()
            if i >= 1 and str(val).strip(): # Check if there is data in columns from 2nd col onwards
                has_data = True
                
        if has_data:
            eligible_count += 1
                
        json_data.append(row_dict)
        
    from app.services.excel_validator import ExcelValidator
    validation_result = ExcelValidator.validate(json_data)
    
    if not validation_result["success"]:
        # Return 200 with the validation payload so frontend can display the table
        return validation_result
        
    # Validation passed, use the normalized data (or original data as per validator)
    # The validator sets it to `normalized_data` but we can just use json_data to keep it identical to before
    
    # Fetch admin setting for registrationAmount and upiId
    admin_settings = await settings_collection.find_one({})
    # Default to 0 if not found
    amount_per_record = admin_settings.get("registrationAmount", 0) if admin_settings else 0
    upi_id = admin_settings.get("upiId", "admin@upi") if admin_settings else "admin@upi"
    
    bank_details = {
        "bankName": admin_settings.get("bankName", "") if admin_settings else "",
        "accountNumber": admin_settings.get("accountNumber", "") if admin_settings else "",
        "ifscCode": admin_settings.get("ifscCode", "") if admin_settings else "",
        "accountHolderName": admin_settings.get("accountHolderName", "") if admin_settings else ""
    }
    
    # We only count valid eligible rows. Since validation passed, all rows are valid.
    eligible_count = validation_result["summary"]["valid_rows"]
    total_amount = eligible_count * float(amount_per_record)
    
    return {
        "success": True,
        "eligibleRecords": eligible_count,
        "amountPerRecord": amount_per_record,
        "totalAmount": total_amount,
        "upiId": upi_id,
        "bankDetails": bank_details,
        "parsedData": validation_result["normalized_data"],
        "summary": validation_result["summary"]
    }

@router.get("/submissions")
async def get_submissions(user_id: str = Depends(get_current_user)):
    user = await users_collection.find_one({"userId": user_id})
    if user and (user.get("role") == "admin" or user_id.lower() == "admin"):
        query = {}
    else:
        nodal = await nodal_registrations_collection.find_one({
            "$or": [{"principalId": user_id}, {"nodalOfficerId": user_id}]
        })
        if nodal:
            college_code = nodal.get("collegeCode")
            query = {
                "$or": [
                    {"collegeCode": college_code},
                    {"userId": {"$in": [nodal.get("principalId"), nodal.get("nodalOfficerId")]}}
                ]
            }
        else:
            query = {"userId": user_id}

    cursor = submissions_collection.find(
        query,
        {"_id": 0, "csvData": 0, "paymentProof": 0} # Exclude large fields for listing
    ).sort("paymentTimestamp", -1)
    
    submissions = await cursor.to_list(length=100)
    return {"submissions": submissions}

@router.get("/submissions/{submission_id}")
async def get_submission(submission_id: str, user_id: str = Depends(get_current_user)):
    user = await users_collection.find_one({"userId": user_id})
    if user and (user.get("role") == "admin" or user_id.lower() == "admin"):
        query = {"submissionId": submission_id}
    else:
        nodal = await nodal_registrations_collection.find_one({
            "$or": [{"principalId": user_id}, {"nodalOfficerId": user_id}]
        })
        if nodal:
            college_code = nodal.get("collegeCode")
            query = {
                "submissionId": submission_id,
                "$or": [
                    {"collegeCode": college_code},
                    {"userId": {"$in": [nodal.get("principalId"), nodal.get("nodalOfficerId")]}}
                ]
            }
        else:
            query = {"submissionId": submission_id, "userId": user_id}

    submission = await submissions_collection.find_one(
        query,
        {"_id": 0}
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission
