from datetime import datetime
from uuid import UUID

import psycopg

from app.errors import ConflictError, NotFoundError, RuleViolationError
from app.repositories import appointment_repo
from app.schemas import AppointmentStatus
from app.services import clinic_service, patient_service

ClinicId = str
DoctorId = str
PatientId = str

_ALLOWED_TRANSITIONS: dict[AppointmentStatus, set[AppointmentStatus]] = {
    AppointmentStatus.BOOKED: {
        AppointmentStatus.CHECKED_IN,
        AppointmentStatus.CANCELLED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.CHECKED_IN: {
        AppointmentStatus.COMPLETED,
        AppointmentStatus.NO_SHOW,
    },
    AppointmentStatus.COMPLETED: set(),
    AppointmentStatus.CANCELLED: set(),
    AppointmentStatus.NO_SHOW: set(),
}


def _concurrent_update_error() -> ConflictError:
    """Raised when another request changed the appointment between our read and our write."""
    return ConflictError(
        "Appointment was changed by another request; reload and try again.",
        code="CONCURRENT_UPDATE",
    )


def book_appointment(
    conn: psycopg.Connection,
    *,
    clinic_id: ClinicId,
    doctor_id: DoctorId,
    patient_id: PatientId,
    scheduled_at: datetime,
    duration_min: int,
    notes: str | None = None,
) -> dict:
    clinic_service.get_clinic(conn, clinic_id)
    doctor = clinic_service.get_doctor(conn, doctor_id)
    patient = patient_service.get_patient(conn, patient_id)

    if doctor["clinic_id"] != clinic_id:
        raise RuleViolationError(
            "Doctor does not belong to the specified clinic.",
            code="DOCTOR_CLINIC_MISMATCH",
        )

    if patient["clinic_id"] != clinic_id:
        raise RuleViolationError(
            "Patient is not registered under the specified clinic.",
            code="PATIENT_CLINIC_MISMATCH",
        )

    # Double-booking is blocked by the database exclusion constraint (23P01 -> 409).
    return appointment_repo.create_appointment(
        conn,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        scheduled_at=scheduled_at,
        duration_min=duration_min,
        notes=notes,
    )


def get_appointment(conn: psycopg.Connection, appointment_id: UUID) -> dict:
    appointment = appointment_repo.get_appointment_by_id(conn, appointment_id)
    if appointment is None:
        raise NotFoundError(
            f"Appointment '{appointment_id}' not found.",
            code="APPOINTMENT_NOT_FOUND",
        )
    return appointment


def list_appointments(
    conn: psycopg.Connection,
    *,
    clinic_id: ClinicId | None = None,
    doctor_id: DoctorId | None = None,
    patient_id: PatientId | None = None,
    status: AppointmentStatus | None = None,
) -> list[dict]:
    if clinic_id is not None:
        clinic_service.get_clinic(conn, clinic_id)
    if doctor_id is not None:
        clinic_service.get_doctor(conn, doctor_id)
    if patient_id is not None:
        patient_service.get_patient(conn, patient_id)

    return appointment_repo.list_appointments(
        conn,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        status=status.value if status is not None else None,
    )


def reschedule_appointment(
    conn: psycopg.Connection,
    *,
    appointment_id: UUID,
    scheduled_at: datetime,
    duration_min: int | None = None,
) -> dict:
    existing = get_appointment(conn, appointment_id)
    current_status = AppointmentStatus(existing["status"])

    if current_status != AppointmentStatus.BOOKED:
        raise RuleViolationError(
            f"Cannot reschedule an appointment in '{current_status.value}' status.",
            code="INVALID_RESCHEDULE_STATE",
        )

    next_duration = duration_min if duration_min is not None else existing["duration_min"]

    # The repository adds 1 to reschedule_count in SQL and only updates
    # if the status is still the one we read (WHERE id=%s AND status=%s).
    updated = appointment_repo.update_appointment_schedule(
        conn,
        appointment_id=appointment_id,
        expected_status=current_status.value,
        scheduled_at=scheduled_at,
        duration_min=next_duration,
    )
    if updated is None:
        raise _concurrent_update_error()
    return updated


def cancel_appointment(
    conn: psycopg.Connection,
    *,
    appointment_id: UUID,
    reason: str | None = None,
) -> dict:
    existing = get_appointment(conn, appointment_id)
    current_status = AppointmentStatus(existing["status"])

    if AppointmentStatus.CANCELLED not in _ALLOWED_TRANSITIONS[current_status]:
        raise RuleViolationError(
            f"Cannot cancel an appointment in '{current_status.value}' status.",
            code="INVALID_STATUS_TRANSITION",
        )

    updated = appointment_repo.update_appointment_status(
        conn,
        appointment_id=appointment_id,
        expected_status=current_status.value,
        status=AppointmentStatus.CANCELLED.value,
        cancel_reason=reason,
    )
    if updated is None:
        raise _concurrent_update_error()
    return updated


def update_appointment_status(
    conn: psycopg.Connection,
    *,
    appointment_id: UUID,
    target_status: AppointmentStatus,
) -> dict:
    if target_status == AppointmentStatus.BOOKED:
        raise RuleViolationError(
            "Cannot transition an appointment back to 'BOOKED'.",
            code="INVALID_STATUS_TRANSITION",
        )

    existing = get_appointment(conn, appointment_id)
    current_status = AppointmentStatus(existing["status"])

    if current_status == target_status:
        return existing  # already in that status: nothing to do

    if target_status not in _ALLOWED_TRANSITIONS[current_status]:
        raise RuleViolationError(
            f"Cannot transition appointment from '{current_status.value}' to '{target_status.value}'.",
            code="INVALID_STATUS_TRANSITION",
        )

    updated = appointment_repo.update_appointment_status(
        conn,
        appointment_id=appointment_id,
        expected_status=current_status.value,
        status=target_status.value,
        cancel_reason=None,
    )
    if updated is None:
        raise _concurrent_update_error()
    return updated