import psycopg

#set up and prepares postgreSQL database schema and seed data for the ClinicFlow application. It defines the structure of the database tables, including clinics, doctors, patients, and appointments, along with their relationships and constraints. 
#The code also includes logic to initialize the database by creating tables if they do not exist and populating them with initial data if they are empty.

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE SEQUENCE IF NOT EXISTS clinic_id_seq;
CREATE SEQUENCE IF NOT EXISTS doctor_id_seq;
CREATE SEQUENCE IF NOT EXISTS patient_id_seq;

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
    id text PRIMARY KEY DEFAULT ('cl' || lpad(nextval('clinic_id_seq')::text, 2, '0')),
    code text NOT NULL UNIQUE CHECK (code ~ '^[A-Z]{3}-[0-9]{2}$'),
    name text NOT NULL,
    city text NOT NULL,
    timezone text NOT NULL DEFAULT 'Asia/Kolkata'
);

CREATE TABLE IF NOT EXISTS doctors (
    id text PRIMARY KEY DEFAULT ('dr' || lpad(nextval('doctor_id_seq')::text, 2, '0')),
    clinic_id text NOT NULL REFERENCES clinics (id),
    code text NOT NULL,
    full_name text NOT NULL,
    specialty text NOT NULL,
    UNIQUE (clinic_id, code)
);

CREATE TABLE IF NOT EXISTS patients (
    id text PRIMARY KEY DEFAULT ('pt' || lpad(nextval('patient_id_seq')::text, 2, '0')),
    clinic_id text NOT NULL REFERENCES clinics (id),
    patient_ref text NOT NULL,
    full_name text NOT NULL,
    phone text NOT NULL,
    date_of_birth date NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (clinic_id, patient_ref)
);

CREATE TABLE IF NOT EXISTS appointments (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id text NOT NULL REFERENCES clinics (id),
    doctor_id text NOT NULL REFERENCES doctors (id),
    patient_id text NOT NULL REFERENCES patients (id),
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

MIGRATE_UUID_IDS_SQL = """
CREATE SEQUENCE IF NOT EXISTS clinic_id_seq;
CREATE SEQUENCE IF NOT EXISTS doctor_id_seq;
CREATE SEQUENCE IF NOT EXISTS patient_id_seq;

CREATE TEMP TABLE clinic_id_map ON COMMIT DROP AS
SELECT id AS old_id,
       'cl' || lpad(row_number() OVER (
           ORDER BY CASE code
               WHEN 'BLR-01' THEN 1
               WHEN 'MYS-01' THEN 2
               WHEN 'COK-01' THEN 3
               ELSE 4
           END, code
       )::text, 2, '0') AS new_id
FROM clinics;

CREATE TEMP TABLE doctor_id_map ON COMMIT DROP AS
SELECT id AS old_id,
       'dr' || lpad(row_number() OVER (ORDER BY code, id)::text, 2, '0') AS new_id
FROM doctors;

CREATE TEMP TABLE patient_id_map ON COMMIT DROP AS
SELECT id AS old_id,
       'pt' || lpad(row_number() OVER (ORDER BY created_at, id)::text, 2, '0') AS new_id
FROM patients;

ALTER TABLE doctors DROP CONSTRAINT IF EXISTS doctors_clinic_id_fkey;
ALTER TABLE patients DROP CONSTRAINT IF EXISTS patients_clinic_id_fkey;
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_clinic_id_fkey;
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_doctor_id_fkey;
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS appointments_patient_id_fkey;
ALTER TABLE appointments DROP CONSTRAINT IF EXISTS no_double_booking;

ALTER TABLE clinics ALTER COLUMN id DROP DEFAULT;
ALTER TABLE doctors ALTER COLUMN id DROP DEFAULT;
ALTER TABLE patients ALTER COLUMN id DROP DEFAULT;

ALTER TABLE clinics ALTER COLUMN id TYPE text USING id::text;
ALTER TABLE doctors ALTER COLUMN id TYPE text USING id::text;
ALTER TABLE doctors ALTER COLUMN clinic_id TYPE text USING clinic_id::text;
ALTER TABLE patients ALTER COLUMN id TYPE text USING id::text;
ALTER TABLE patients ALTER COLUMN clinic_id TYPE text USING clinic_id::text;
ALTER TABLE appointments ALTER COLUMN clinic_id TYPE text USING clinic_id::text;
ALTER TABLE appointments ALTER COLUMN doctor_id TYPE text USING doctor_id::text;
ALTER TABLE appointments ALTER COLUMN patient_id TYPE text USING patient_id::text;

UPDATE doctors d SET clinic_id = m.new_id
FROM clinic_id_map m WHERE d.clinic_id = m.old_id::text;
UPDATE patients p SET clinic_id = m.new_id
FROM clinic_id_map m WHERE p.clinic_id = m.old_id::text;
UPDATE appointments a SET clinic_id = m.new_id
FROM clinic_id_map m WHERE a.clinic_id = m.old_id::text;
UPDATE appointments a SET doctor_id = m.new_id
FROM doctor_id_map m WHERE a.doctor_id = m.old_id::text;
UPDATE appointments a SET patient_id = m.new_id
FROM patient_id_map m WHERE a.patient_id = m.old_id::text;

UPDATE clinics c SET id = m.new_id
FROM clinic_id_map m WHERE c.id = m.old_id::text;
UPDATE doctors d SET id = m.new_id
FROM doctor_id_map m WHERE d.id = m.old_id::text;
UPDATE patients p SET id = m.new_id
FROM patient_id_map m WHERE p.id = m.old_id::text;

ALTER TABLE clinics ALTER COLUMN id SET DEFAULT ('cl' || lpad(nextval('clinic_id_seq')::text, 2, '0'));
ALTER TABLE doctors ALTER COLUMN id SET DEFAULT ('dr' || lpad(nextval('doctor_id_seq')::text, 2, '0'));
ALTER TABLE patients ALTER COLUMN id SET DEFAULT ('pt' || lpad(nextval('patient_id_seq')::text, 2, '0'));

ALTER TABLE doctors ADD CONSTRAINT doctors_clinic_id_fkey
    FOREIGN KEY (clinic_id) REFERENCES clinics (id);
ALTER TABLE patients ADD CONSTRAINT patients_clinic_id_fkey
    FOREIGN KEY (clinic_id) REFERENCES clinics (id);
ALTER TABLE appointments ADD CONSTRAINT appointments_clinic_id_fkey
    FOREIGN KEY (clinic_id) REFERENCES clinics (id);
ALTER TABLE appointments ADD CONSTRAINT appointments_doctor_id_fkey
    FOREIGN KEY (doctor_id) REFERENCES doctors (id);
ALTER TABLE appointments ADD CONSTRAINT appointments_patient_id_fkey
    FOREIGN KEY (patient_id) REFERENCES patients (id);
ALTER TABLE appointments ADD CONSTRAINT no_double_booking EXCLUDE USING gist (
    doctor_id WITH =,
    tstzrange(scheduled_at, slot_end) WITH &&
) WHERE (status IN ('BOOKED', 'CHECKED_IN'));

"""

SYNC_ID_SEQUENCES_SQL = """
SELECT setval('clinic_id_seq', GREATEST(COALESCE(
    (SELECT max(substring(id FROM 3)::bigint) FROM clinics WHERE id ~ '^cl[0-9]+$'), 0
) + 1, 1), false);
SELECT setval('doctor_id_seq', GREATEST(COALESCE(
    (SELECT max(substring(id FROM 3)::bigint) FROM doctors WHERE id ~ '^dr[0-9]+$'), 0
) + 1, 1), false);
SELECT setval('patient_id_seq', GREATEST(COALESCE(
    (SELECT max(substring(id FROM 3)::bigint) FROM patients WHERE id ~ '^pt[0-9]+$'), 0
) + 1, 1), false);
"""

SEED_SQL = """
INSERT INTO clinics (id, code, name, city) VALUES
    ('cl01', 'BLR-01', 'Bengaluru Central Clinic', 'Bengaluru'),
    ('cl02', 'MYS-01', 'Mysuru City Clinic', 'Mysuru'),
    ('cl03', 'COK-01', 'Kochi Harbour Clinic', 'Kochi')
ON CONFLICT (code) DO NOTHING;

INSERT INTO doctors (id, clinic_id, code, full_name, specialty)
SELECT d.id, c.id, d.code, d.full_name, d.specialty
FROM clinics c
JOIN (VALUES
    ('cl01', 'dr01', 'DR-014', 'Dr R. Iyer', 'GENERAL'),
    ('cl01', 'dr02', 'DR-015', 'Dr S. Nair', 'GENERAL'),
    ('cl02', 'dr03', 'DR-021', 'Dr A. Rao', 'PAEDIATRICS'),
    ('cl02', 'dr04', 'DR-022', 'Dr K. Thomas', 'GENERAL'),
    ('cl03', 'dr05', 'DR-031', 'Dr M. Shetty', 'DERMATOLOGY'),
    ('cl03', 'dr06', 'DR-032', 'Dr L. Varghese', 'ENT')
) AS d(clinic_id, id, code, full_name, specialty) ON d.clinic_id = c.id
ON CONFLICT (clinic_id, code) DO NOTHING;
"""


def init_db(conn: psycopg.Connection) -> None:
    """Create tables and seed data on first start; migrate UUID entity IDs if needed."""
    with conn.transaction():
        sync_sequences = False
        exists = conn.execute("SELECT to_regclass('public.appointments')").fetchone()[0]
        if exists is None:
            conn.execute(SCHEMA_SQL)
        else:
            id_type = conn.execute(
                """
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'clinics'
                  AND column_name = 'id'
                """
            ).fetchone()
            if id_type is not None and id_type[0] == "uuid":
                conn.execute(MIGRATE_UUID_IDS_SQL)
                sync_sequences = True
        clinic_count = conn.execute("SELECT count(*) FROM clinics").fetchone()[0]
        if clinic_count == 0:
            conn.execute(SEED_SQL)
            sync_sequences = True
        if sync_sequences:
            conn.execute(SYNC_ID_SEQUENCES_SQL)