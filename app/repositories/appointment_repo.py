from datetime import datetime
from uuid import UUID
import psycopg
from psycopg.rows import dict_row

_APPOINTMENT_COLUMNS = """
    id,
    clinic_id,
    doctor_id,
    patient_id,
    scheduled_at,
    duration_min,
    slot_end,
    status,
    reschedule_count,
    cancel_reason,
    notes,
    created_at,
    updated_at
"""


def create_appointment(
    conn: psycopg.Connection,
    *,
    clinic_id: UUID,
    doctor_id: UUID,
    patient_id: UUID,
    scheduled_at: datetime,
    duration_min: int,
    notes: str | None = None,
) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        row = cur.execute(
            f"""
            INSERT INTO appointments (
                clinic_id,
                doctor_id,
                patient_id,
                scheduled_at,
                duration_min,
                slot_end,
                notes
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s + make_interval(mins => %s),
                %s
            )
            RETURNING {_APPOINTMENT_COLUMNS}
            """,
            (
                clinic_id,
                doctor_id,
                patient_id,
                scheduled_at,
                duration_min,
                scheduled_at,
                duration_min,
                notes,
            ),
        ).fetchone()
    return dict(row)


def get_appointment_by_id(conn: psycopg.Connection, appointment_id: UUID) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            f"""
            SELECT {_APPOINTMENT_COLUMNS}
            FROM appointments
            WHERE id = %s
            """,
            (appointment_id,),
        ).fetchone()


def list_appointments(
    conn: psycopg.Connection,
    *,
    clinic_id: UUID | None = None,
    doctor_id: UUID | None = None,
    patient_id: UUID | None = None,
    status: str | None = None,
) -> list[dict]:
    clauses: list[str] = []
    params: list[object] = []

    if clinic_id is not None:
        clauses.append("clinic_id = %s")
        params.append(clinic_id)
    if doctor_id is not None:
        clauses.append("doctor_id = %s")
        params.append(doctor_id)
    if patient_id is not None:
        clauses.append("patient_id = %s")
        params.append(patient_id)
    if status is not None:
        clauses.append("status = %s")
        params.append(status)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            f"""
            SELECT {_APPOINTMENT_COLUMNS}
            FROM appointments
            {where_sql}
            ORDER BY scheduled_at ASC
            """,
            tuple(params),
        ).fetchall()
    return list(rows)


def update_appointment_schedule(
    conn: psycopg.Connection,
    *,
    appointment_id: UUID,
    scheduled_at: datetime,
    duration_min: int,
    reschedule_count: int,
) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        row = cur.execute(
            f"""
            UPDATE appointments
            SET
                scheduled_at = %s,
                duration_min = %s,
                slot_end = %s + make_interval(mins => %s),
                reschedule_count = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING {_APPOINTMENT_COLUMNS}
            """,
            (
                scheduled_at,
                duration_min,
                scheduled_at,
                duration_min,
                reschedule_count,
                appointment_id,
            ),
        ).fetchone()
    return dict(row) if row is not None else None


def update_appointment_status(
    conn: psycopg.Connection,
    *,
    appointment_id: UUID,
    status: str,
    cancel_reason: str | None = None,
) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        row = cur.execute(
            f"""
            UPDATE appointments
            SET
                status = %s,
                cancel_reason = %s,
                updated_at = now()
            WHERE id = %s
            RETURNING {_APPOINTMENT_COLUMNS}
            """,
            (status, cancel_reason, appointment_id),
        ).fetchone()
    return dict(row) if row is not None else None