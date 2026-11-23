from uuid import UUID
from fastapi import APIRouter, Depends, Query
import psycopg
from app.db import get_db
from app.schemas import ClinicResponse, DoctorResponse
from app.services import clinic_service

router = APIRouter(tags=["Clinics & Doctors"])


@router.get("/clinics", response_model=list[ClinicResponse])
def list_clinics(conn: psycopg.Connection = Depends(get_db)) -> list[dict]:
    return clinic_service.list_clinics(conn)


@router.get("/clinics/{clinic_id}", response_model=ClinicResponse)
def get_clinic(clinic_id: UUID, conn: psycopg.Connection = Depends(get_db)) -> dict:
    return clinic_service.get_clinic(conn, clinic_id)


@router.get("/doctors", response_model=list[DoctorResponse])
def list_doctors(
    clinic_id: UUID | None = Query(default=None),
    conn: psycopg.Connection = Depends(get_db),
) -> list[dict]:
    return clinic_service.list_doctors(conn, clinic_id=clinic_id)


@router.get("/clinics/{clinic_id}/doctors", response_model=list[DoctorResponse])
def list_clinic_doctors(clinic_id: UUID, conn: psycopg.Connection = Depends(get_db)) -> list[dict]:
    return clinic_service.list_doctors(conn, clinic_id=clinic_id)