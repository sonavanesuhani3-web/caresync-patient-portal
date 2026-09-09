# day6_seed.py
# CareSync Day 6 Data Seeder
#
# Adds two new tables:
#   doctor_rating  -- patient satisfaction scores per doctor per month
#   monthly_summary -- pre-aggregated monthly stats for the dashboard
#
# Safe to run on an existing caresync database.
# Does NOT touch doctor, patient, appointment, or billing tables.

import mysql.connector
import random
from datetime import date, timedelta
from faker import Faker

fake = Faker('en_IN')

conn = mysql.connector.connect(
    host='localhost',
    port=3306,
    user='root',
    password='Suhani@12345',     # change to your MySQL password
    database='caresync'
)
cur = conn.cursor()
print('Connected.')

# ── TABLE 1: doctor_rating ───────────────────────────────────────────────
# Stores patient satisfaction ratings (1 to 5) for each doctor.
# One rating per completed appointment.
cur.execute('''
    CREATE TABLE IF NOT EXISTS doctor_rating (
        rating_id     INT          NOT NULL AUTO_INCREMENT,
        doctor_id     INT          NOT NULL,
        appointment_id INT         NOT NULL,
        rating        TINYINT      NOT NULL,
        rating_date   DATE         NOT NULL,
        comments      TEXT,
        PRIMARY KEY (rating_id),
        UNIQUE KEY uq_rating_appt (appointment_id),
        CONSTRAINT fk_rating_doctor
            FOREIGN KEY (doctor_id) REFERENCES doctor (doctor_id)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        CONSTRAINT fk_rating_appt
            FOREIGN KEY (appointment_id) REFERENCES appointment (appointment_id)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        INDEX idx_rating_doctor (doctor_id, rating_date)
    )
''')
conn.commit()
print('Table doctor_rating ready.')

# ── TABLE 2: monthly_summary ─────────────────────────────────────────────
# Pre-aggregated monthly performance data.
# Used for fast dashboard queries without re-aggregating millions of rows.
cur.execute('''
    CREATE TABLE IF NOT EXISTS monthly_summary (
        summary_id          INT            NOT NULL AUTO_INCREMENT,
        summary_month       CHAR(7)        NOT NULL,
        total_appointments  INT            NOT NULL DEFAULT 0,
        total_completed     INT            NOT NULL DEFAULT 0,
        total_cancelled     INT            NOT NULL DEFAULT 0,
        total_billed        DECIMAL(12,2)  NOT NULL DEFAULT 0.00,
        total_collected     DECIMAL(12,2)  NOT NULL DEFAULT 0.00,
        total_rejected      INT            NOT NULL DEFAULT 0,
        new_patients        INT            NOT NULL DEFAULT 0,
        PRIMARY KEY (summary_id),
        UNIQUE KEY uq_month (summary_month)
    )
''')
conn.commit()
print('Table monthly_summary ready.')

# ── POPULATE doctor_rating ────────────────────────────────────────────────
# Fetch completed appointments that do not yet have a rating.
cur.execute('''
    SELECT a.appointment_id, a.doctor_id, a.appointment_date
    FROM appointment a
    LEFT JOIN doctor_rating dr ON dr.appointment_id = a.appointment_id
    WHERE a.status = 'Completed'
      AND dr.rating_id IS NULL
    LIMIT 2500
''')
appointments = cur.fetchall()
print(f'Inserting ratings for {len(appointments)} appointments...')

# Rating distribution: mostly positive (hospital is doing well)
# Weights: 1=5%, 2=8%, 3=17%, 4=35%, 5=35%
RATING_VALUES   = [1, 2, 3, 4, 5]
RATING_WEIGHTS  = [5, 8, 17, 35, 35]

RATING_COMMENTS = {
    5: ['Excellent care, very satisfied.', 'Doctor was thorough and kind.',
        'Best experience at this hospital.', 'Highly recommend this doctor.'],
    4: ['Good service overall.', 'Doctor explained everything clearly.',
        'Wait time was long but treatment was good.'],
    3: ['Average experience.', 'Could improve communication.',
        'Treatment was fine but rushed.'],
    2: ['Long wait time and felt ignored.', 'Doctor seemed distracted.',
        'Would prefer more explanation of diagnosis.'],
    1: ['Very dissatisfied with the visit.', 'Did not feel heard.',
        'Needs significant improvement.'],
}

for (appt_id, doc_id, appt_date) in appointments:
    rating      = random.choices(RATING_VALUES, weights=RATING_WEIGHTS)[0]
    comment     = random.choice(RATING_COMMENTS[rating])
    # Rating submitted 1 to 3 days after the appointment
    rating_date = appt_date + timedelta(days=random.randint(1, 3))

    cur.execute(
        '''
        INSERT IGNORE INTO doctor_rating
            (doctor_id, appointment_id, rating, rating_date, comments)
        VALUES (%s, %s, %s, %s, %s)
        ''',
        (doc_id, appt_id, rating, rating_date, comment)
    )

conn.commit()
print(f'  Done. Ratings inserted.')

# ── POPULATE monthly_summary ─────────────────────────────────────────────
print('Building monthly summary...')

cur.execute('''
    INSERT INTO monthly_summary
        (summary_month, total_appointments, total_completed,
         total_cancelled, total_billed, total_collected,
         total_rejected, new_patients)
    SELECT
        DATE_FORMAT(a.appointment_date, '%Y-%m') AS summary_month,
        COUNT(a.appointment_id)                  AS total_appointments,
        SUM(a.status = 'Completed')              AS total_completed,
        SUM(a.status = 'Cancelled')              AS total_cancelled,
        COALESCE(SUM(b.total_amount),  0)        AS total_billed,
        COALESCE(SUM(b.amount_paid),   0)        AS total_collected,
        COALESCE(SUM(b.status = 'Rejected'), 0)  AS total_rejected,
        COUNT(DISTINCT CASE
            WHEN a.appointment_date = (
                SELECT MIN(a2.appointment_date)
                FROM appointment a2
                WHERE a2.patient_id = a.patient_id
            ) THEN a.patient_id END
        )                                        AS new_patients
    FROM appointment a
    LEFT JOIN billing b ON b.appointment_id = a.appointment_id
    GROUP BY summary_month
    ON DUPLICATE KEY UPDATE
        total_appointments = VALUES(total_appointments),
        total_completed    = VALUES(total_completed),
        total_cancelled    = VALUES(total_cancelled),
        total_billed       = VALUES(total_billed),
        total_collected    = VALUES(total_collected),
        total_rejected     = VALUES(total_rejected),
        new_patients       = VALUES(new_patients)
''')
conn.commit()
print('  Monthly summary built.')

# ── VERIFY ───────────────────────────────────────────────────────────────
print()
print('=== ROW COUNTS ===')
for t in ['doctor_rating', 'monthly_summary']:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    print(f'  {t:<20}: {cur.fetchone()[0]} rows')

cur.close()
conn.close()
print()
print('Day 6 seeder complete. Ready for SQL exercises.')
