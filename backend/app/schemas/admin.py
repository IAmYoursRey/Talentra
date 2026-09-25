from typing import Optional, List
from pydantic import BaseModel, Field


class CreateStudentRequest(BaseModel):
    displayName: str = Field(..., min_length=2, max_length=255)
    nisn: str = Field(..., min_length=10, max_length=10)
    gradeLevel: str | int = Field(...)
    classId: Optional[str] = None


class CreateTeacherRequest(BaseModel):
    displayName: str = Field(..., min_length=2, max_length=255)
    identifier: str = Field(..., min_length=16, max_length=18)
    title: Optional[str] = Field(None, max_length=128)


class UpdateUserRequest(BaseModel):
    displayName: Optional[str] = Field(None, min_length=2, max_length=255)
    gradeLevel: Optional[str | int] = None
    title: Optional[str] = Field(None, max_length=128)


class CreateClassRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    gradeLevel: str | int = Field(...)
    academicYear: str = Field(..., min_length=4, max_length=16)


class UpdateClassRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=64)
    gradeLevel: Optional[str | int] = None
    academicYear: Optional[str] = Field(None, min_length=4, max_length=16)


class EnrollStudentRequest(BaseModel):
    studentId: str = Field(..., min_length=1)


class AssignTeacherRequest(BaseModel):
    teacherId: str = Field(..., min_length=1)
    assignmentType: str = Field("portfolio_validator", max_length=32)
