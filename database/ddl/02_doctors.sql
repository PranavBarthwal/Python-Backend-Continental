-- Doctors table DDL
-- Healthcare provider information and availability management

-- Drop table if exists
DROP TABLE IF EXISTS doctors CASCADE;

-- Create doctors table
CREATE TABLE doctors (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    qualification VARCHAR(200),
    experience_years INTEGER DEFAULT 0,
    consultation_fee DECIMAL(10,2) DEFAULT 0.00,
    hospital_name VARCHAR(200),
    hospital_address TEXT,
    profile_image VARCHAR(255),
    rating DECIMAL(3,2) DEFAULT 0.00,
    total_reviews INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    hmis_id VARCHAR(50),
    license_number VARCHAR(50),
    contact_number VARCHAR(15),
    email VARCHAR(120),
    languages_spoken TEXT[],
    available_days TEXT[],
    available_hours JSONB,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_doctors_specialty ON doctors(specialty);
CREATE INDEX idx_doctors_hospital_name ON doctors(hospital_name);
CREATE INDEX idx_doctors_is_available ON doctors(is_available);
CREATE INDEX idx_doctors_rating ON doctors(rating);
CREATE INDEX idx_doctors_consultation_fee ON doctors(consultation_fee);
CREATE INDEX idx_doctors_hmis_id ON doctors(hmis_id) WHERE hmis_id IS NOT NULL;
CREATE INDEX idx_doctors_is_deleted ON doctors(is_deleted);
CREATE INDEX idx_doctors_created_at ON doctors(created_at);

-- Create trigger for updated_at
CREATE TRIGGER update_doctors_updated_at BEFORE UPDATE ON doctors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add constraints
ALTER TABLE doctors ADD CONSTRAINT chk_doctors_rating CHECK (rating >= 0 AND rating <= 5);
ALTER TABLE doctors ADD CONSTRAINT chk_doctors_consultation_fee CHECK (consultation_fee >= 0);
ALTER TABLE doctors ADD CONSTRAINT chk_doctors_experience_years CHECK (experience_years >= 0);