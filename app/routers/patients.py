from fastapi import APIRouter, Depends, Query, status
import psycopg
from app.db import get_db
from app.schemas import PatientCreate,ClinicId,PatientId, PatientDetailResponse, PatientResponse
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
def create_patient(
    payload: PatientCreate,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    return patient_service.create_patient(
        conn,
        clinic_id=payload.clinic_id,
        patient_ref=payload.patient_ref,
        full_name=payload.full_name,
        phone=payload.phone,
        date_of_birth=payload.date_of_birth,
    )


@router.get("", response_model=list[PatientResponse])
def list_patients(
    clinic_id: ClinicId | None = Query(default=None),
    conn: psycopg.Connection = Depends(get_db),
) -> list[dict]:
    return patient_service.list_patients(conn, clinic_id=clinic_id)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
def get_patient(
    patient_id: UUID,
    conn: psycopg.Connection = Depends(get_db),
) -> dict:
    return patient_service.get_patient_with_appointments(conn, patient_id)