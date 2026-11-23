import psycopg

#set up and prepares postgreSQL database schema and seed data for the ClinicFlow application. It defines the structure of the database tables, including clinics, doctors, patients, and appointments, along with their relationships and constraints. 
#The code also includes logic to initialize the database by creating tables if they do not exist and populating them with initial data if they are empty.

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS btree_gist;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'appointment_status') THEN
        CREATE TYPE appointment_status AS ENUM (
            'BOOKED',
            'CHECKED_IN',
            'COMPLETED',
            'CANCELLED',
            'NO_SHOW'
        );
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS clinics (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code text NOT NULL UNIQUE CHECK (code ~ '^[A-Z]{3}-[0-9]{2}$'),
    name text NOT NULL,
    city text NOT NULL,
    timezone text NOT NULL DEFAULT 'Asia/Kolkata'
);

CREATE TABLE IF NOT EXISTS doctors (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics (id),
    code text NOT NULL,
    full_name text NOT NULL,
    specialty text NOT NULL,
    UNIQUE (clinic_id, code)
);

CREATE TABLE IF NOT EXISTS patients (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics (id),
    patient_ref text NOT NULL,
    full_name text NOT NULL,
    phone text NOT NULL,
    date_of_birth date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (clinic_id, patient_ref)
);

CREATE TABLE IF NOT EXISTS appointments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id uuid NOT NULL REFERENCES clinics (id),
    doctor_id uuid NOT NULL REFERENCES doctors (id),
    patient_id uuid NOT NULL REFERENCES patients (id),
    scheduled_at timestamptz NOT NULL,
    duration_min int NOT NULL DEFAULT 15 CHECK (duration_min BETWEEN 5 AND 240),
    slot_end timestamptz NOT NULL,
    status appointment_status NOT NULL DEFAULT 'BOOKED',
    reschedule_count int NOT NULL DEFAULT 0,
    cancel_reason text,
    notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CHECK (slot_end > scheduled_at),
    CONSTRAINT no_double_booking EXCLUDE USING gist (
        doctor_id WITH =,
        tstzrange(scheduled_at, slot_end) WITH &&
    ) WHERE (status IN ('BOOKED', 'CHECKED_IN'))
);

CREATE INDEX IF NOT EXISTS ix_appt_clinic_time ON appointments (clinic_id, scheduled_at);
CREATE INDEX IF NOT EXISTS ix_appt_patient ON appointments (patient_id, scheduled_at);
"""

SEED_SQL = """
INSERT INTO clinics (code, name, city) VALUES
    ('BLR-01', 'Bengaluru Central Clinic', 'Bengaluru'),
    ('MYS-01', 'Mysuru City Clinic', 'Mysuru'),
    ('COK-01', 'Kochi Harbour Clinic', 'Kochi')
ON CONFLICT (code) DO NOTHING;

INSERT INTO doctors (clinic_id, code, full_name, specialty)
SELECT c.id, d.code, d.full_name, d.specialty
FROM clinics c
JOIN (VALUES
    ('BLR-01', 'DR-014', 'Dr R. Iyer', 'GENERAL'),
    ('BLR-01', 'DR-015', 'Dr S. Nair', 'GENERAL'),
    ('MYS-01', 'DR-021', 'Dr A. Rao', 'PAEDIATRICS'),
    ('MYS-01', 'DR-022', 'Dr K. Thomas', 'GENERAL'),
    ('COK-01', 'DR-031', 'Dr M. Shetty', 'DERMATOLOGY'),
    ('COK-01', 'DR-032', 'Dr L. Varghese', 'ENT')
) AS d(clinic_code, code, full_name, specialty) ON d.clinic_code = c.code
ON CONFLICT (clinic_id, code) DO NOTHING;
"""


def init_db(conn: psycopg.Connection) -> None:
    """Create tables on first start; add starting clinics/doctors if none exist. Safe to call every start."""
    with conn.transaction():
        exists = conn.execute("SELECT to_regclass('public.appointments')").fetchone()[0]
        if exists is None:
            conn.execute(SCHEMA_SQL)
        clinic_count = conn.execute("SELECT count(*) FROM clinics").fetchone()[0]
        if clinic_count == 0:
            conn.execute(SEED_SQL)