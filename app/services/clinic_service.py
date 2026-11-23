from uuid import UUID
import psycopg
from app.errors import NotFoundError
from app.repositories import clinic_repo


def list_clinics(conn: psycopg.Connection) -> list[dict]:
    return clinic_repo.list_clinics(conn)


def get_clinic(conn: psycopg.Connection, clinic_id: UUID) -> dict:
    clinic = clinic_repo.get_clinic_by_id(conn, clinic_id)
    if clinic is None:
        raise NotFoundError(f"Clinic '{clinic_id}' not found.", code="CLINIC_NOT_FOUND")
    return clinic


def list_doctors(conn: psycopg.Connection, clinic_id: UUID | None = None) -> list[dict]:
    if clinic_id is not None:
        get_clinic(conn, clinic_id)
    return clinic_repo.list_doctors(conn, clinic_id=clinic_id)


def get_doctor(conn: psycopg.Connection, doctor_id: UUID) -> dict:
    doctor = clinic_repo.get_doctor_by_id(conn, doctor_id)
    if doctor is None:
        raise NotFoundError(f"Doctor '{doctor_id}' not found.", code="DOCTOR_NOT_FOUND")
    return doctor