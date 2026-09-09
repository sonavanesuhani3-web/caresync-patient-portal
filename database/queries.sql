USE caresync;

-- Task 9: Doctor Appointment Summary Query
SELECT 
    d.full_name AS doctor_name,
    COUNT(a.appointment_id) AS total_appointments
FROM doctor d
LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
GROUP BY d.doctor_id, d.full_name
ORDER BY total_appointments DESC;

-- Task 10: Create SQL View for Doctor Appointment Summary
CREATE OR REPLACE VIEW vw_doctor_appointment_summary AS
SELECT 
    d.full_name AS doctor_name,
    COUNT(a.appointment_id) AS total_appointments
FROM doctor d
LEFT JOIN appointment a ON d.doctor_id = a.doctor_id
GROUP BY d.doctor_id, d.full_name
ORDER BY total_appointments DESC;