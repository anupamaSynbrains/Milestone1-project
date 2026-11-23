from datetime import date
import psycopg
from psycopg.rows import dict_row


ClinicId = str
PatientId = str


def create_patient(
    conn: psycopg.Connection,
    *,
    clinic_id: ClinicId,
    patient_ref: str,
    full_name: str,
    phone: str,
    date_of_birth: date,
) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        row = cur.execute(
            """
            INSERT INTO patients (clinic_id, patient_ref, full_name, phone, date_of_birth)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, clinic_id, patient_ref, full_name, phone, date_of_birth, created_at
            """,
            (clinic_id, patient_ref, full_name, phone, date_of_birth),
        ).fetchone()
    return dict(row)


def get_patient_by_id(conn: psycopg.Connection, patient_id: PatientId) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            SELECT id, clinic_id, patient_ref, full_name, phone, date_of_birth, created_at
            FROM patients
            WHERE id = %s
            """,
            (patient_id,),
        ).fetchone()


def get_patient_by_ref(
    conn: psycopg.Connection,
    clinic_id: ClinicId,
    patient_ref: str,
) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            SELECT id, clinic_id, patient_ref, full_name, phone, date_of_birth, created_at
            FROM patients
            WHERE clinic_id = %s AND patient_ref = %s
            """,
            (clinic_id, patient_ref),
        ).fetchone()


def list_patients(conn: psycopg.Connection, clinic_id: ClinicId | None = None) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        if clinic_id is not None:
            rows = cur.execute(
                """
                SELECT id, clinic_id, patient_ref, full_name, phone, date_of_birth, created_at
                FROM patients
                WHERE clinic_id = %s
                ORDER BY created_at DESC, full_name
                """,
                (clinic_id,),
            ).fetchall()
        else:
            rows = cur.execute(
                """
                SELECT id, clinic_id, patient_ref, full_name, phone, date_of_birth, created_at
                FROM patients
                ORDER BY created_at DESC, full_name
                """
            ).fetchall()
    return list(rows)