from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.time_utils import ist_now


class ParticipationMode(str, Enum):
    INDIVIDUAL = "individual"
    TEAM = "team"


class TeamRole(str, Enum):
    LEADER = "leader"
    MEMBER = "member"


# Public models for API


class AssignedChallenge(BaseModel):
    category: str
    title: str
    description: str


class TeamMember(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    mobile: str = Field(..., pattern=r"^\d{10}$")
    rollNumber: str = Field(..., min_length=2, max_length=60)
    githubProfile: Optional[str] = None
    collegeName: Optional[str] = None
    branch: Optional[str] = None
    projectSelected: Optional[str] = None
    role: TeamRole = TeamRole.MEMBER

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Branch cannot be empty")
        return value

    @field_validator("projectSelected")
    @classmethod
    def validate_project_selected(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not value.strip():
            raise ValueError("Project category cannot be empty")
        return value


class StudentRegister(BaseModel):
    fullName: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    mobile: str = Field(..., pattern=r"^\d{10}$")
    branch: str = Field(..., min_length=2, max_length=80)
    otherBranchName: Optional[str] = None
    collegeName: str = Field(..., min_length=2, max_length=180)
    otherCollegeName: Optional[str] = Field(default=None, min_length=2, max_length=180)
    city: str = Field(..., min_length=2, max_length=80)
    rollNumber: str = Field(..., min_length=2, max_length=60)
    currentYear: Optional[str] = Field(default=None, max_length=60)
    githubProfile: Optional[str] = None
    projectSelected: str = Field(..., min_length=2, max_length=120)
    otherProjectSelected: Optional[str] = None
    participationMode: ParticipationMode
    registrationDate: datetime = Field(default_factory=ist_now)
    teamId: Optional[str] = None
    teamName: Optional[str] = None
    isTeamLeader: bool = False
    teamMembers: Optional[List[TeamMember]] = None
    
    # Payment fields (UPI & fallback)
    payment_gateway: Optional[str] = "upi"
    payment_utr: Optional[str] = None
    detected_receipt_utr: Optional[str] = None
    rzp_payment_id: Optional[str] = None  # Transaction ID / UTR
    rzp_order_id: Optional[str] = None    # Order ID
    order_id: Optional[str] = None
    utr_number: Optional[str] = None
    transaction_id: Optional[str] = None
    payment_amount: Optional[float] = None
    payment_currency: Optional[str] = "INR"
    payment_receipt_url: Optional[str] = None
    payment_receipt_name: Optional[str] = None
    payment_receipt_base64: Optional[str] = None
    receipt_base64: Optional[str] = None

    @field_validator("branch")
    @classmethod
    def validate_branch(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Branch cannot be empty")
        return value

    @field_validator("projectSelected")
    @classmethod
    def validate_project_selected(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Project category cannot be empty")
        return value

    @field_validator("collegeName")
    @classmethod
    def normalize_college_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("otherCollegeName")
    @classmethod
    def normalize_other_college_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        cleaned = value.strip().lower()
        return cleaned or None

    @field_validator("teamMembers")
    @classmethod
    def validate_team_members(cls, value: Optional[List[TeamMember]]) -> Optional[List[TeamMember]]:
        if value is None:
            return value
        if len(value) > 4:
            raise ValueError("Maximum 4 team members allowed")
        return value

    @model_validator(mode="after")
    def sync_payment_fields(self) -> "StudentRegister":
        # Ensure order_id and rzp_order_id are in sync
        effective_order = self.order_id or self.rzp_order_id
        if effective_order:
            self.order_id = effective_order
            self.rzp_order_id = effective_order

        # Ensure transaction_id, utr_number, payment_utr, and rzp_payment_id are in sync
        effective_txn = self.payment_utr or self.utr_number or self.transaction_id or self.rzp_payment_id
        if effective_txn:
            self.transaction_id = effective_txn
            self.utr_number = effective_txn
            self.payment_utr = effective_txn
            self.rzp_payment_id = effective_txn
        return self


class StudentDraft(BaseModel):
    email: str
    fullName: Optional[str] = None
    mobile: Optional[str] = None
    branch: Optional[str] = None
    otherBranchName: Optional[str] = None
    collegeName: Optional[str] = None
    otherCollegeName: Optional[str] = None
    city: Optional[str] = None
    rollNumber: Optional[str] = None
    currentYear: Optional[str] = None
    otherCurrentYear: Optional[str] = None
    projectSelected: Optional[str] = None
    otherProjectSelected: Optional[str] = None
    participationMode: Optional[str] = "individual"
    registrationDate: Optional[str] = None
    teamName: Optional[str] = None
    teamMembers: Optional[List[Dict[str, Any]]] = None
    orderId: Optional[str] = None


class PaymentOrderRequest(BaseModel):
    participationMode: ParticipationMode
    teamMembersCount: int = Field(default=0, ge=0, le=4)
    email: EmailStr
    fullName: str
    mobile: str = Field(..., pattern=r"^\d{10}$")
    projectSelected: Optional[str] = None
    branch: Optional[str] = None
    collegeName: Optional[str] = None
    otherCollegeName: Optional[str] = None
    city: Optional[str] = None
    rollNumber: Optional[str] = None
    currentYear: Optional[str] = None
    otherCurrentYear: Optional[str] = None
    registrationDate: Optional[str] = None
    teamName: Optional[str] = None
    teamMembers: Optional[List[Dict[str, Any]]] = None

    @field_validator("projectSelected")
    @classmethod
    def validate_payment_project_selected(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            return None
        return normalized

    @model_validator(mode="after")
    def validate_team_size(self) -> "PaymentOrderRequest":
        if self.participationMode == ParticipationMode.TEAM:
            total = 1 + self.teamMembersCount
            if total < 2:
                raise ValueError("Team must have at least 2 members including the leader. Please add at least 1 team member.")
            if total > 5:
                raise ValueError("Team cannot exceed 5 members including the leader.")
        return self


class PaymentOrderResponse(BaseModel):
    orderId: str
    amount: float
    currency: str = "INR"
    paymentGateway: str = "upi"
    upiId: str = ""
    upiPayeeName: str = "Spheronix Hackathon"
    bankName: str = "CANARA BANK"
    accountNumber: str = "120036804612"
    ifscCode: str = "CNRB0000659"
    accountHolderName: str = "SPHERONIX TECHNOLOGY PVT. LTD."
    upiIntentUrl: str = ""
    qrCodeData: str = ""
    totalMembers: int = 1
    feePerMember: float = 1.0
    paymentSessionId: str = ""
    environment: str = "PRODUCTION"
    mockMode: bool = False
    mockPaymentId: Optional[str] = None
    message: Optional[str] = None


class PaymentVerification(BaseModel):
    order_id: Optional[str] = None
    utr_number: Optional[str] = None
    transaction_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_signature: Optional[str] = None

    @property
    def effective_order_id(self) -> str:
        return (self.order_id or self.razorpay_order_id or "").strip()

    @property
    def effective_transaction_id(self) -> str:
        return (self.utr_number or self.transaction_id or self.razorpay_payment_id or "").strip()


class StudentResponse(BaseModel):
    registrationId: str
    fullName: str
    email: str
    participantId: Optional[str] = None
    teamLeaderId: Optional[str] = None
    teamMemberIds: Optional[List[str]] = None
    teamId: Optional[str] = None
    transactionId: Optional[str] = None
    paymentStatus: Optional[str] = None
    taskSelected: Optional[str] = None
    assignedChallenge: Optional[AssignedChallenge] = None
    message: str
    teamMemberEmails: Optional[List[str]] = None
    teamMemberNames: Optional[List[str]] = None


class RegistrationSummaryResponse(BaseModel):
    registrationId: str
    fullName: str
    email: str
    participantId: Optional[str] = None
    teamId: Optional[str] = None
    teamName: Optional[str] = None
    transactionId: Optional[str] = None
    paymentStatus: Optional[str] = None
    taskSelected: Optional[str] = None
    assignedChallenge: Optional[AssignedChallenge] = None
    teamMemberEmails: Optional[List[str]] = None
    teamMemberNames: Optional[List[str]] = None
    is_reviewed: bool = False
    is_selected: bool = False
    reviewed_by: Optional[str] = None
    user_feedback: Optional[str] = None
    payment_receipt_url: Optional[str] = None
    payment_receipt_name: Optional[str] = None
    payment_receipt_base64: Optional[str] = None
    receipt_base64: Optional[str] = None


class CollegeCreate(BaseModel):
    name: str
    city: Optional[str] = ""
    state: Optional[str] = ""


class CollegeResponse(BaseModel):
    name: str
    city: str
    state: str


class DuplicateCheck(BaseModel):
    email: Optional[str] = None
    rollNumber: Optional[str] = None
    githubProfile: Optional[str] = None
    mobile: Optional[str] = None


class LeaderDetailsResponse(BaseModel):
    teamId: str
    leaderEmail: str
    collegeName: str
    branch: str
    projectSelected: str
    taskSelected: Optional[str] = None
    assignedChallenge: Optional[AssignedChallenge] = None
