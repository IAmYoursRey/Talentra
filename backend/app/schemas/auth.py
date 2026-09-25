from pydantic import BaseModel, Field
from ..domain.enums import UserRole

class LoginRequest(BaseModel):
    identifier: str = Field(..., min_length=3, max_length=30)
    password: str = Field(..., min_length=1)

class DemoLoginRequest(BaseModel):
    role: UserRole

class SchoolBrief(BaseModel):
    id: str
    name: str

class UserResponse(BaseModel):
    id: str
    displayName: str
    role: UserRole
    email: str
    school: SchoolBrief
    maskedIdentifier: str
    className: str | None = None
    title: str | None = None
    requiresCredentialUpdate: bool = False

class LoginResponse(BaseModel):
    user: UserResponse
    redirectTo: str

class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "Sesi berhasil diakhiri."

class CsrfResponse(BaseModel):
    csrfToken: str

class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str = Field(..., min_length=8)

class ChangePasswordResponse(BaseModel):
    success: bool
    message: str

class ErrorDetail(BaseModel):
    code: str
    message: str
    requestId: str

class ErrorEnvelope(BaseModel):
    error: ErrorDetail
