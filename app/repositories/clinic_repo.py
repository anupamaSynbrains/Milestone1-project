import psycopg
from psycopg.rows import dict_row


ClinicId = str
DoctorId = str


def list_clinics(conn: psycopg.Connection) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        rows = cur.execute(
            """
            SELECT id, code, name, city, timezone
            FROM clinics
            ORDER BY code
            """
        ).fetchall()
    return list(rows)


def get_clinic_by_id(conn: psycopg.Connection, clinic_id: ClinicId) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            SELECT id, code, name, city, timezone
            FROM clinics
            WHERE id = %s
            """,
            (clinic_id,),
        ).fetchone()


def get_clinic_by_code(conn: psycopg.Connection, code: str) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            SELECT id, code, name, city, timezone
            FROM clinics
            WHERE code = %s
            """,
            (code,),
        ).fetchone()


def list_doctors(conn: psycopg.Connection, clinic_id: ClinicId | None = None) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        if clinic_id is not None:
            rows = cur.execute(
                """
                SELECT id, clinic_id, code, full_name, specialty
                FROM doctors
                WHERE clinic_id = %s
                ORDER BY code
                """,
                (clinic_id,),
            ).fetchall()
        else:
            rows = cur.execute(
                """
                SELECT id, clinic_id, code, full_name, specialty
                FROM doctors
                ORDER BY code
                """
            ).fetchall()
    return list(rows)


def get_doctor_by_id(conn: psycopg.Connection, doctor_id: DoctorId) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            SELECT id, clinic_id, code, full_name, specialty
            FROM doctors
            WHERE id = %s
            """,
            (doctor_id,),
        ).fetchone()