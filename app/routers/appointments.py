from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
import psycopg
from app.db import get_db
from app.schemas import (
    AppointmentCancel,
    AppointmentCreate,
    AppointmentReschedule,
    AppointmentResponse,
    AppointmentStatus,
    AppointmentStatusUpdate,
)
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(
    payload: AppointmentCreate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    return appointment_service.book_appointment(
        conn,
        clinic_id=payload.clinic_id,
        doctor_id=payload.doctor_id,
        patient_id=payload.patient_id,
        scheduled_at=payload.scheduled_at,
        duration_min=payload.duration_min,
        notes=payload.notes,
    )


@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    clinic_id: UUID | None = Query(default=None),
    doctor_id: UUID | None = Query(default=None),
    patient_id: UUID | None = Query(default=None),
    status_filter: AppointmentStatus | None = Query(default=None, alias="status"),
    conn: psycopg.Connection = Depends(get_db),
) -> list[dict]:
    return appointment_service.list_appointments(
        conn,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        patient_id=patient_id,
        status=status_filter,
    )


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: UUID,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    return appointment_service.get_appointment(conn, appointment_id)


@router.patch("/{appointment_id}/reschedule", response_model=AppointmentResponse)
def reschedule_appointment(
    appointment_id: UUID,
    payload: AppointmentReschedule,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    return appointment_service.reschedule_appointment(
        conn,
        appointment_id=appointment_id,
        scheduled_at=payload.scheduled_at,
        duration_min=payload.duration_min,
    )


@router.post("/{appointment_id}/cancel", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: UUID,
    payload: AppointmentCancel | None = None,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    reason = payload.reason if payload is not None else None
    return appointment_service.cancel_appointment(
        conn,
        appointment_id=appointment_id,
        reason=reason,
    )


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: UUID,
    payload: AppointmentStatusUpdate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    return appointment_service.update_appointment_status(
        conn,
        appointment_id=appointment_id,
        target_status=payload.status,
    )