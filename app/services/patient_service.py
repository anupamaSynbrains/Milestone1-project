from datetime import date
from uuid import UUID
import psycopg
from app.errors import ConflictError, NotFoundError
from app.repositories import patient_repo
from app.services import clinic_service


def create_patient(
    conn: psycopg.Connection,
    *,
    clinic_id: UUID,
    patient_ref: str,
    full_name: str,
    phone: str,
    date_of_birth: date,
) -> dict:
    clinic_service.get_clinic(conn, clinic_id)

    existing = patient_repo.get_patient_by_ref(conn, clinic_id, patient_ref)
    if existing is not None:
        raise ConflictError(
            f"Patient with ref '{patient_ref}' already exists in this clinic.",
            code="DUPLICATE_PATIENT_REF",
        )

    return patient_repo.create_patient(
        conn,
        clinic_id=clinic_id,
        patient_ref=patient_ref,
        full_name=full_name,
        phone=phone,
        date_of_birth=date_of_birth,
    )


def get_patient(conn: psycopg.Connection, patient_id: UUID) -> dict:
    patient = patient_repo.get_patient_by_id(conn, patient_id)
    if patient is None:
        raise NotFoundError(f"Patient '{patient_id}' not found.", code="PATIENT_NOT_FOUND")
    return patient


def list_patients(conn: psycopg.Connection, clinic_id: UUID | None = None) -> list[dict]:
    if clinic_id is not None:
        clinic_service.get_clinic(conn, clinic_id)
    return patient_repo.list_patients(conn, clinic_id=clinic_id)