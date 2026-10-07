from typing import Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo

class InstitutionType(str, Enum):
    AUTONOMOUS = "Autonomous"
    NON_AUTONOMOUS = "Non-Autonomous"

class CategoryType(str, Enum):
    BTECH = "B.Tech"
    MTECH = "M.Tech"
    DEGREE = "Degree"
    MBA = "MBA"
    MCA = "MCA"
    PHARMACY = "Pharmacy"
    DIPLOMA = "Diploma / Polytechnic"
    OTHERS = "Others"

class NodalRegistrationRequest(BaseModel):
    state: str = Field(..., min_length=2)
    district: str = Field(..., min_length=2)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    collegeName: str = Field(..., min_length=2)
    collegeCode: str = Field(..., min_length=2)
    affiliatedTo: str = Field(..., min_length=2)
    institutionType: InstitutionType
    category: CategoryType
    specifyCategory: Optional[str] = None
    
    principalName: str = Field(..., min_length=2)
    principalEmail: EmailStr
    principalMobile: str = Field(..., pattern=r"^\d{10}$")
    
    nodalOfficerName: str = Field(..., min_length=2)
    nodalOfficerEmail: EmailStr
    nodalOfficerMobile: str = Field(..., pattern=r"^\d{10}$")
    
    emailOtp: str = Field(..., min_length=6, max_length=6)

    @field_validator("collegeName", "collegeCode")
    @classmethod
    def to_uppercase(cls, v: str) -> str:
        return v.strip().upper() if v else v

    @field_validator("specifyCategory")
    @classmethod
    def validate_specify_category(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        if info.data.get("category") == CategoryType.OTHERS:
            if not v or not v.strip():
                raise ValueError("Specify Category is required when Others is selected")
            return v.strip().upper()
        return v

class OtpSendRequest(BaseModel):
    contact: str # Can be email or mobile

class OtpVerifyRequest(BaseModel):
    contact: str
    otp: str = Field(..., min_length=6, max_length=6)
