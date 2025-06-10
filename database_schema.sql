-- PHR Healthcare Database Schema
-- PostgreSQL DDL for creating all required tables
-- Note: No foreign key constraints as per requirements

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS record_summaries CASCADE;
DROP TABLE IF EXISTS ambulance_bookings CASCADE;
DROP TABLE IF EXISTS ambulance_services CASCADE;
DROP TABLE IF EXISTS chat_messages CASCADE;
DROP TABLE IF EXISTS user_care_packages CASCADE;
DROP TABLE IF EXISTS care_packages CASCADE;
DROP TABLE IF EXISTS notifications CASCADE;
DROP TABLE IF EXISTS lab_bookings CASCADE;
DROP TABLE IF EXISTS lab_tests CASCADE;
DROP TABLE IF EXISTS medicine_tracker CASCADE;
DROP TABLE IF EXISTS prescriptions CASCADE;
DROP TABLE IF EXISTS medicines CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP TABLE IF EXISTS symptom_assessments CASCADE;
DROP TABLE IF EXISTS symptoms CASCADE;
DROP TABLE IF EXISTS appointments CASCADE;
DROP TABLE IF EXISTS doctors CASCADE;
DROP TABLE IF EXISTS otp_codes CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL,
    mobile_number VARCHAR(15) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE,
    abha_id VARCHAR(50) UNIQUE,
    password_hash VARCHAR(256),
    is_verified BOOLEAN DEFAULT FALSE,
    profile_image VARCHAR(255),
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    emergency_contact VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create OTP codes table
CREATE TABLE otp_codes (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    mobile_number VARCHAR(15) NOT NULL,
    otp_code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Doctors table
CREATE TABLE doctors (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    qualification VARCHAR(200),
    experience_years INTEGER,
    hospital_id VARCHAR(50),
    hospital_name VARCHAR(200),
    availability JSONB,
    consultation_fee DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    profile_image VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Appointments table
CREATE TABLE appointments (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(36) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    symptoms TEXT,
    notes TEXT,
    consultation_type VARCHAR(20) DEFAULT 'in-person' CHECK (consultation_type IN ('in-person', 'video', 'audio')),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Symptoms table
CREATE TABLE symptoms (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    severity_levels JSONB,
    associated_specialties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Symptom Assessments table
CREATE TABLE symptom_assessments (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    symptoms JSONB NOT NULL,
    questionnaire_responses JSONB,
    audio_recording_path VARCHAR(255),
    transcription TEXT,
    ai_analysis JSONB,
    recommended_specialty VARCHAR(100),
    severity_score INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Documents table
CREATE TABLE documents (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_type VARCHAR(10) NOT NULL,
    file_size INTEGER,
    uploaded_by VARCHAR(50),
    upload_source VARCHAR(100),
    tags JSONB,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Medicines table
CREATE TABLE medicines (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    dosage VARCHAR(100),
    manufacturer VARCHAR(100),
    description TEXT,
    price DECIMAL(10, 2),
    is_prescription_required BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Prescriptions table
CREATE TABLE prescriptions (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(36),
    appointment_id VARCHAR(36),
    medicines JSONB NOT NULL,
    instructions TEXT,
    prescription_image_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Medicine Tracker table
CREATE TABLE medicine_tracker (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    prescription_id VARCHAR(36),
    medicine_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    timing JSONB NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Lab Tests table
CREATE TABLE lab_tests (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    normal_range VARCHAR(100),
    price DECIMAL(10, 2),
    preparation_instructions TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Lab Bookings table
CREATE TABLE lab_bookings (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(36),
    tests JSONB NOT NULL,
    scheduled_date TIMESTAMP,
    status VARCHAR(20) DEFAULT 'requested' CHECK (status IN ('requested', 'scheduled', 'completed', 'cancelled')),
    total_amount DECIMAL(10, 2),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    results_available BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Notifications table
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    scheduled_for TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Care Packages table
CREATE TABLE care_packages (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    features JSONB,
    price DECIMAL(10, 2),
    duration_months INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create User Care Packages table
CREATE TABLE user_care_packages (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    care_package_id VARCHAR(36) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'cancelled')),
    payment_status VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Chat Messages table
CREATE TABLE chat_messages (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    sender_id VARCHAR(36) NOT NULL,
    receiver_id VARCHAR(36),
    room_id VARCHAR(50),
    message TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text' CHECK (message_type IN ('text', 'image', 'file')),
    is_anonymous BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Ambulance Services table
CREATE TABLE ambulance_services (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    service_name VARCHAR(200) NOT NULL,
    phone_number VARCHAR(15) NOT NULL,
    service_type VARCHAR(50) NOT NULL CHECK (service_type IN ('emergency', 'non_emergency')),
    coverage_area VARCHAR(200),
    base_price DECIMAL(10, 2),
    per_km_rate DECIMAL(10, 2),
    rating DECIMAL(3, 2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Ambulance Bookings table
CREATE TABLE ambulance_bookings (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    ambulance_service_id VARCHAR(36) NOT NULL,
    pickup_location VARCHAR(500) NOT NULL,
    destination VARCHAR(500) NOT NULL,
    emergency_level VARCHAR(20) NOT NULL CHECK (emergency_level IN ('high', 'medium', 'low')),
    patient_condition TEXT,
    requested_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'requested' CHECK (status IN ('requested', 'assigned', 'in_transit', 'completed', 'cancelled')),
    estimated_amount DECIMAL(10, 2),
    actual_amount DECIMAL(10, 2),
    driver_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Record Summaries table
CREATE TABLE record_summaries (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    summary_type VARCHAR(20) NOT NULL CHECK (summary_type IN ('all_records', 'selected_records')),
    document_ids JSONB,
    summary_text TEXT NOT NULL,
    ai_insights JSONB,
    generated_by VARCHAR(50) DEFAULT 'gemini_ai',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_users_mobile_number ON users(mobile_number);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_abha_id ON users(abha_id);
CREATE INDEX idx_otp_codes_mobile_number ON otp_codes(mobile_number);
CREATE INDEX idx_otp_codes_expires_at ON otp_codes(expires_at);
CREATE INDEX idx_doctors_specialty ON doctors(specialty);
CREATE INDEX idx_doctors_hospital_id ON doctors(hospital_id);
CREATE INDEX idx_appointments_user_id ON appointments(user_id);
CREATE INDEX idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_symptom_assessments_user_id ON symptom_assessments(user_id);
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_prescriptions_user_id ON prescriptions(user_id);
CREATE INDEX idx_medicine_tracker_user_id ON medicine_tracker(user_id);
CREATE INDEX idx_medicine_tracker_active ON medicine_tracker(is_active);
CREATE INDEX idx_lab_bookings_user_id ON lab_bookings(user_id);
CREATE INDEX idx_lab_bookings_status ON lab_bookings(status);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(notification_type);
CREATE INDEX idx_notifications_read ON notifications(is_read);
CREATE INDEX idx_user_care_packages_user_id ON user_care_packages(user_id);
CREATE INDEX idx_chat_messages_sender_id ON chat_messages(sender_id);
CREATE INDEX idx_chat_messages_room_id ON chat_messages(room_id);
CREATE INDEX idx_ambulance_bookings_user_id ON ambulance_bookings(user_id);
CREATE INDEX idx_record_summaries_user_id ON record_summaries(user_id);

-- Insert sample data for testing (basic reference data)

-- Insert sample symptoms
INSERT INTO symptoms (name, description, category, severity_levels, associated_specialties) VALUES
('Fever', 'Elevated body temperature', 'General', '["mild", "moderate", "high"]', '["General Medicine", "Internal Medicine"]'),
('Headache', 'Pain in the head or neck area', 'Neurological', '["mild", "moderate", "severe"]', '["Neurology", "General Medicine"]'),
('Cough', 'Sudden expulsion of air from the lungs', 'Respiratory', '["dry", "wet", "persistent"]', '["Pulmonology", "General Medicine"]'),
('Chest Pain', 'Pain in the chest area', 'Cardiac', '["mild", "moderate", "severe", "crushing"]', '["Cardiology", "Emergency Medicine"]'),
('Shortness of Breath', 'Difficulty breathing', 'Respiratory', '["mild", "moderate", "severe"]', '["Pulmonology", "Cardiology"]'),
('Nausea', 'Feeling of sickness', 'Gastrointestinal', '["mild", "moderate", "severe"]', '["Gastroenterology", "General Medicine"]'),
('Fatigue', 'Extreme tiredness', 'General', '["mild", "moderate", "severe"]', '["General Medicine", "Internal Medicine"]'),
('Dizziness', 'Feeling of lightheadedness', 'Neurological', '["mild", "moderate", "severe"]', '["Neurology", "ENT"]');

-- Insert sample doctors
INSERT INTO doctors (name, specialty, qualification, experience_years, hospital_name, consultation_fee, rating, is_active) VALUES
('Dr. Rajesh Kumar', 'General Medicine', 'MBBS, MD', 15, 'City General Hospital', 500.00, 4.5, true),
('Dr. Priya Sharma', 'Cardiology', 'MBBS, MD, DM Cardiology', 12, 'Heart Care Center', 800.00, 4.8, true),
('Dr. Amit Singh', 'Neurology', 'MBBS, MD Neurology', 10, 'Neuro Specialty Hospital', 700.00, 4.6, true),
('Dr. Sneha Patel', 'Gynecology', 'MBBS, MS Gynecology', 8, 'Women''s Health Clinic', 600.00, 4.7, true),
('Dr. Vikram Joshi', 'Orthopedics', 'MBBS, MS Orthopedics', 18, 'Bone & Joint Hospital', 650.00, 4.4, true),
('Dr. Kavita Reddy', 'Pediatrics', 'MBBS, MD Pediatrics', 14, 'Children''s Hospital', 550.00, 4.9, true),
('Dr. Suresh Gupta', 'Dermatology', 'MBBS, MD Dermatology', 11, 'Skin Care Clinic', 450.00, 4.3, true),
('Dr. Meera Iyer', 'Psychiatry', 'MBBS, MD Psychiatry', 9, 'Mental Health Center', 750.00, 4.6, true);

-- Update doctor availability (sample availability for all doctors)
UPDATE doctors SET availability = '{
    "monday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
    "tuesday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
    "wednesday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
    "thursday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
    "friday": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
    "saturday": ["09:00", "10:00", "11:00"],
    "sunday": []
}';

-- Insert sample lab tests
INSERT INTO lab_tests (name, description, category, normal_range, price, preparation_instructions) VALUES
('Complete Blood Count (CBC)', 'Comprehensive blood analysis', 'Hematology', 'WBC: 4000-11000/μL, RBC: 4.5-5.5 million/μL', 300.00, 'No special preparation required'),
('Lipid Profile', 'Cholesterol and triglyceride levels', 'Cardiology', 'Total Cholesterol: <200 mg/dL', 400.00, 'Fasting for 12 hours required'),
('Blood Glucose (Fasting)', 'Blood sugar level after fasting', 'Diabetes', '70-100 mg/dL', 150.00, 'Fasting for 8-12 hours required'),
('Thyroid Function Test', 'TSH, T3, T4 levels', 'Endocrinology', 'TSH: 0.4-4.0 mIU/L', 500.00, 'No special preparation required'),
('Liver Function Test', 'Liver enzyme levels', 'Gastroenterology', 'ALT: 7-56 U/L, AST: 10-40 U/L', 450.00, 'No special preparation required'),
('Kidney Function Test', 'Creatinine and BUN levels', 'Nephrology', 'Creatinine: 0.6-1.2 mg/dL', 350.00, 'No special preparation required'),
('Vitamin D', 'Vitamin D level', 'General', '30-100 ng/mL', 600.00, 'No special preparation required'),
('HbA1c', 'Average blood sugar over 3 months', 'Diabetes', '<5.7%', 400.00, 'No special preparation required');

-- Insert sample medicines
INSERT INTO medicines (name, generic_name, dosage, manufacturer, price, is_prescription_required) VALUES
('Paracetamol 500mg', 'Paracetamol', '500mg', 'Generic Pharma', 25.00, false),
('Amoxicillin 250mg', 'Amoxicillin', '250mg', 'Antibiotic Inc', 120.00, true),
('Atorvastatin 10mg', 'Atorvastatin', '10mg', 'Cardio Pharma', 85.00, true),
('Metformin 500mg', 'Metformin', '500mg', 'Diabetes Care', 45.00, true),
('Omeprazole 20mg', 'Omeprazole', '20mg', 'Gastro Med', 60.00, true),
('Aspirin 75mg', 'Aspirin', '75mg', 'Heart Care', 30.00, false),
('Lisinopril 5mg', 'Lisinopril', '5mg', 'BP Control', 95.00, true),
('Cetirizine 10mg', 'Cetirizine', '10mg', 'Allergy Relief', 40.00, false);

-- Insert sample care packages
INSERT INTO care_packages (name, description, category, features, price, duration_months) VALUES
('Diabetes Care Package', 'Comprehensive diabetes management program', 'Diabetes', '["Regular glucose monitoring", "Diet consultation", "Exercise plan", "Medicine reminders"]', 2500.00, 12),
('Heart Health Package', 'Cardiovascular health monitoring and care', 'Cardiology', '["ECG monitoring", "Blood pressure tracking", "Cardiology consultations", "Emergency support"]', 3500.00, 12),
('Senior Citizen Care', 'Complete healthcare for elderly patients', 'Geriatric', '["Regular health checkups", "Medicine management", "Emergency response", "Health tracking"]', 4000.00, 12),
('Maternity Care Package', 'Complete pregnancy and postnatal care', 'Maternity', '["Regular checkups", "Nutritional guidance", "Exercise plan", "Emergency support"]', 15000.00, 10),
('Mental Health Support', 'Comprehensive mental health care program', 'Mental Health', '["Counseling sessions", "Therapy support", "Peer group access", "Crisis intervention"]', 2000.00, 6);

-- Insert sample ambulance services
INSERT INTO ambulance_services (service_name, phone_number, service_type, coverage_area, base_price, per_km_rate, rating) VALUES
('City Emergency Ambulance', '108', 'emergency', 'City Wide', 500.00, 15.00, 4.5),
('Private Ambulance Service', '+919876543210', 'non_emergency', 'Metropolitan Area', 800.00, 20.00, 4.2),
('24x7 Medical Transport', '+919876543211', 'emergency', 'State Wide', 600.00, 18.00, 4.7),
('Comfort Medical Transport', '+919876543212', 'non_emergency', 'City Wide', 1000.00, 25.00, 4.8);

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update the updated_at column
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON doctors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments to tables for documentation
COMMENT ON TABLE users IS 'Main user table storing patient information';
COMMENT ON TABLE doctors IS 'Doctor information with specialties and availability';
COMMENT ON TABLE appointments IS 'Patient appointments with doctors';
COMMENT ON TABLE symptoms IS 'Master list of medical symptoms';
COMMENT ON TABLE symptom_assessments IS 'Patient symptom assessments with AI analysis';
COMMENT ON TABLE documents IS 'Medical documents and files uploaded by patients or hospitals';
COMMENT ON TABLE prescriptions IS 'Digital prescriptions from doctors';
COMMENT ON TABLE medicine_tracker IS 'Medicine reminder and tracking system';
COMMENT ON TABLE lab_tests IS 'Available laboratory tests';
COMMENT ON TABLE lab_bookings IS 'Patient lab test bookings';
COMMENT ON TABLE notifications IS 'System notifications for users';
COMMENT ON TABLE care_packages IS 'Healthcare packages available for subscription';
COMMENT ON TABLE chat_messages IS 'Peer support chat messages';
COMMENT ON TABLE ambulance_services IS 'Available ambulance services';
COMMENT ON TABLE record_summaries IS 'AI-generated summaries of patient records';

-- Grant necessary permissions (adjust as needed for your environment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

-- Database setup complete
SELECT 'PHR Healthcare Database Schema created successfully!' as message;
