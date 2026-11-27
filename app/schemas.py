from datetime import date, datetime
from enum import Enum
from typing import Annotated
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator

ClinicId = Annotated[str, Field(pattern=r"^cl[0-9]+$")]
DoctorId = Annotated[str, Field(pattern=r"^dr[0-9]+$")]
PatientId = Annotated[str, Field(pattern=r"^pt[0-9]+$")]

#validates the data for the API endpoints and defines the data models used in the application.
#shapes the outgoing responses for the API endpoints and ensures that the data returned to the client is in the expected format.
#requests models only accept fields that are relevant to the specific operation being performed, while response models include all fields that are returned to the client.

# --- Appointment Status Enum ---
class AppointmentStatus(str, Enum):
    BOOKED = "BOOKED"
    CHECKED_IN = "CHECKED_IN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


# --- Clinics & Doctors ---

class ClinicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: ClinicId
    code: str
    name: str
    city: str
    timezone: str


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: DoctorId
    clinic_id: ClinicId
    code: str
    full_name: str
    specialty: str


# --- Patients ---

class PatientCreate(BaseModel):
    clinic_id: ClinicId
    patient_ref: str = Field(min_length=1, max_length=64)
    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=5, max_length=32)
    date_of_birth: date

    @field_validator("date_of_birth")
    @classmethod
    def check_date_of_birth(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PatientId
    clinic_id: ClinicId
    patient_ref: str
    full_name: str
    phone: str
    date_of_birth: date
    created_at: datetime

class PatientDetailResponse(PatientResponse):
    appointments: list[AppointmentResponse] = Field(default_factory=list)


# --- Appointments ---

class AppointmentCreate(BaseModel):
    clinic_id: ClinicId
    doctor_id: DoctorId
    patient_id: PatientId
    scheduled_at: datetime
    duration_min: int = Field(default=15, ge=5, le=240)
    notes: str | None = Field(default=None, max_length=1000)


class AppointmentReschedule(BaseModel):
    scheduled_at: datetime
    duration_min: int | None = Field(default=None, ge=5, le=240)


class AppointmentCancel(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clinic_id: ClinicId
    doctor_id: DoctorId
    patient_id: PatientId
    scheduled_at: datetime
    duration_min: int
    slot_end: datetime
    status: AppointmentStatus
    reschedule_count: int
    cancel_reason: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime