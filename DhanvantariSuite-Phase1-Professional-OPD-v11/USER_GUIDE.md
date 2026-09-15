# Dhanvantari Clinic ERP — User Guide

Welcome to the Dhanvantari Clinic ERP. This guide will help you navigate the system based on your assigned role.

## 1. Getting Started
- Open your browser and navigate to the application URL (e.g., http://127.0.0.1:8000/ui/).
- Log in using your assigned credentials.

## 2. Roles & Capabilities
- **Admin**: You have access to all system settings, user management, and overall clinic reports.
- **Receptionist**: You manage the front desk. Your primary tasks are Patient Registration, Appointment Booking, and Check-in.
- **Doctor**: You manage the clinical workflow. You can view your assigned patients, record vitals, and generate prescriptions.
- **Doctor_All**: You have super-user clinical access. You can view and manage patients across all doctors in the clinic.

## 3. Patient Registration & Appointments (Receptionist)
1. Navigate to the **Patients** tab.
2. Search for existing patients by Mobile Number or Patient ID to avoid duplicates.
3. If new, click **New Patient** and fill in the required details.
4. To book an appointment, select the patient and click **Book Appointment**. Choose the appropriate doctor and time slot.
5. When the patient arrives, click **Check-In** to move them into the doctor's active queue.

## 4. Consultancy (Doctor / Doctor_All)
1. Navigate to the **Dashboard** or **Queue**.
2. **Doctor**: You will see patients checked in for you.
3. **Doctor_All**: You can see all patients across the clinic.
4. Click on a patient to start the consultation.
5. Record symptoms, diagnoses, and any required medicines.
6. Click **Complete Consultation** to generate the prescription.

## 5. Billing & Invoicing
1. Invoices are automatically generated upon consultation completion.
2. Navigate to the **Billing** section.
3. Search for the patient's invoice.
4. Record the payment received (Partial or Paid).
5. Only authorized roles (configured by Admin) can collect payments.
