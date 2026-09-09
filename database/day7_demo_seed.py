# day7_demo_seed_final.py
# Inserts demo appointments and billing records relative to TODAY.
# Past appointments are Completed with billing records.
# Future appointments are Scheduled with pending billing.
# Run this on any date and the demo will always show real data.
# python day7_demo_seed_final.py


import mysql.connector
from datetime import date, timedelta


conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Suhani@12345",
    database="caresync"
)
cur = conn.cursor(dictionary=True)
print("Connected to caresync.")


# ── Get doctor1 and patient1 linked IDs ───────────────────────────────────────
cur.execute("SELECT linked_id FROM users WHERE email = 'doctor1@caresync.local'")
row = cur.fetchone()
if not row:
    print("ERROR: doctor1@caresync.local not found. Run day7_users_seed.py first.")
    exit()
DOCTOR_ID = row["linked_id"]


cur.execute("SELECT linked_id FROM users WHERE email = 'patient1@caresync.local'")
row = cur.fetchone()
if not row:
    print("ERROR: patient1@caresync.local not found. Run day7_users_seed.py first.")
    exit()
PATIENT_ID = row["linked_id"]


print(f"Doctor ID  : {DOCTOR_ID}")
print(f"Patient ID : {PATIENT_ID}")


# ── Dates relative to today ───────────────────────────────────────────────────
# This makes the demo work on any date you run it.
TODAY     = date.today()
MINUS_7   = TODAY - timedelta(days=7)   # 1 week ago
MINUS_3   = TODAY - timedelta(days=3)   # 3 days ago
MINUS_1   = TODAY - timedelta(days=1)   # yesterday
PLUS_1    = TODAY + timedelta(days=1)   # tomorrow
PLUS_3    = TODAY + timedelta(days=3)   # 3 days from now
PLUS_7    = TODAY + timedelta(days=7)   # 1 week from now


print(f"Today      : {TODAY}")
print(f"Past dates : {MINUS_7}, {MINUS_3}, {MINUS_1}")
print(f"Future dates: {PLUS_1}, {PLUS_3}, {PLUS_7}")


# ── Appointments ──────────────────────────────────────────────────────────────
# 3 past completed appointments + 3 future scheduled appointments.
# All assigned to doctor1 and patient1 so both dashboards show data.
appointments = [
    # Past appointments - status Completed
    {
        "patient_id":       PATIENT_ID,
        "doctor_id":        DOCTOR_ID,
        "appointment_date": MINUS_7,
        "appointment_time": "09:30:00",
        "status":           "Completed",
        "reason":           "Annual physical examination"
    },
    {
        "patient_id":       PATIENT_ID,
        "doctor_id":        DOCTOR_ID,
        "appointment_date": MINUS_3,
        "appointment_time": "10:00:00",
        "status":           "Completed",
        "reason":           "Follow-up after blood test"
    },
    {
        "patient_id":       PATIENT_ID,
        "doctor_id":        DOCTOR_ID,
        "appointment_date": MINUS_1,
        "appointment_time": "11:00:00",
        "status":           "Completed",
        "reason":           "Fever and fatigue"
    },
    # Future appointments - status Scheduled
    {
        "patient_id":       PATIENT_ID,
        "doctor_id":        DOCTOR_ID,
        "appointment_date": PLUS_1,
        "appointment_time": "09:00:00",
        "status":           "Scheduled",
        "reason":           "Routine check-up"
    },
    {
        "patient_id":       PATIENT_ID,
        "doctor_id":        DOCTOR_ID,
        "appointment_date": PLUS_3,
        "appointment_time": "10:30:00",
        "status":           "Scheduled",
        "reason":           "Diabetes management review"
    },
    {
        "patient_id":       PATIENT_ID,
        "doctor_id":        DOCTOR_ID,
        "appointment_date": PLUS_7,
        "appointment_time": "11:00:00",
        "status":           "Scheduled",
        "reason":           "Post-surgery follow-up"
    },
]


print()
print("Inserting appointments...")


inserted_ids = []


for appt in appointments:
    cur.execute("""
        INSERT INTO appointment
            (patient_id, doctor_id, appointment_date, appointment_time, status, reason)
        VALUES
            (%s, %s, %s, %s, %s, %s)
    """, (
        appt["patient_id"],
        appt["doctor_id"],
        appt["appointment_date"],
        appt["appointment_time"],
        appt["status"],
        appt["reason"]
    ))
    conn.commit()
    new_id = cur.lastrowid
    inserted_ids.append({"id": new_id, "status": appt["status"], "date": appt["appointment_date"]})
    print(f"  ID {new_id}  |  {appt['appointment_date']}  |  {appt['status']}  |  {appt['reason']}")


# ── Billing records ───────────────────────────────────────────────────────────
# Billing records for past completed appointments - Paid or Partially Paid.
# Billing records for future appointments - Pending.
print()
print("Inserting billing records...")


billing_map = [
    # Past completed - Paid
    {
        "appointment_id": inserted_ids[0]["id"],
        "patient_id":     PATIENT_ID,
        "bill_date":      MINUS_7,
        "total_amount":   1500.00,
        "amount_paid":    1500.00,
        "discount":       0.00,
        "status":         "Paid"
    },
    # Past completed - Partially Paid
    {
        "appointment_id": inserted_ids[1]["id"],
        "patient_id":     PATIENT_ID,
        "bill_date":      MINUS_3,
        "total_amount":   2200.00,
        "amount_paid":    1000.00,
        "discount":       200.00,
        "status":         "Partially Paid"
    },
    # Past completed - Paid
    {
        "appointment_id": inserted_ids[2]["id"],
        "patient_id":     PATIENT_ID,
        "bill_date":      MINUS_1,
        "total_amount":   800.00,
        "amount_paid":    800.00,
        "discount":       0.00,
        "status":         "Paid"
    },
    # Future scheduled - Pending
    {
        "appointment_id": inserted_ids[3]["id"],
        "patient_id":     PATIENT_ID,
        "bill_date":      PLUS_1,
        "total_amount":   1200.00,
        "amount_paid":    0.00,
        "discount":       0.00,
        "status":         "Pending"
    },
    # Future scheduled - Pending
    {
        "appointment_id": inserted_ids[4]["id"],
        "patient_id":     PATIENT_ID,
        "bill_date":      PLUS_3,
        "total_amount":   3500.00,
        "amount_paid":    0.00,
        "discount":       500.00,
        "status":         "Pending"
    },
    # Future scheduled - Pending
    {
        "appointment_id": inserted_ids[5]["id"],
        "patient_id":     PATIENT_ID,
        "bill_date":      PLUS_7,
        "total_amount":   1800.00,
        "amount_paid":    0.00,
        "discount":       0.00,
        "status":         "Pending"
    },
]


for bill in billing_map:
    cur.execute("""
        INSERT INTO billing
            (appointment_id, patient_id, bill_date,
             total_amount, amount_paid, discount, status)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s)
    """, (
        bill["appointment_id"],
        bill["patient_id"],
        bill["bill_date"],
        bill["total_amount"],
        bill["amount_paid"],
        bill["discount"],
        bill["status"]
    ))
    conn.commit()
    print(f"  Bill for appointment {bill['appointment_id']}  |  {bill['bill_date']}  |  Rs {bill['total_amount']}  |  {bill['status']}")


cur.close()
conn.close()


print()
print("Demo data inserted successfully.")
print()
print("Doctor dashboard  : login as doctor1@caresync.local  /  Doctor@1234")
print("                    Shows past and upcoming appointments.")
print()
print("Patient dashboard : login as patient1@caresync.local  /  Patient@1234")
print("                    Shows appointments and billing records.")
