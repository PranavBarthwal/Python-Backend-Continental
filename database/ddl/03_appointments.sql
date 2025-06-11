-- Appointments table DDL
-- Patient appointment scheduling and management

-- Drop table if exists
DROP TABLE IF EXISTS appointments CASCADE;

-- Create appointments table
CREATE TABLE appointments (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    user_id VARCHAR(36) NOT NULL,
    doctor_id VARCHAR(36) NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
    symptoms TEXT,
    notes TEXT,
    consultation_fee DECIMAL(10,2),
    booking_source VARCHAR(20) DEFAULT 'phr_app' CHECK (booking_source IN ('phr_app', 'hmis', 'phone', 'walk_in')),
    hmis_appointment_id VARCHAR(50),
    confirmation_number VARCHAR(50),
    prescription_id VARCHAR(36),
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_appointments_user_id ON appointments(user_id);
CREATE INDEX idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_booking_source ON appointments(booking_source);
CREATE INDEX idx_appointments_hmis_id ON appointments(hmis_appointment_id) WHERE hmis_appointment_id IS NOT NULL;
CREATE INDEX idx_appointments_is_deleted ON appointments(is_deleted);
CREATE INDEX idx_appointments_created_at ON appointments(created_at);

-- Create trigger for updated_at
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add unique constraint for preventing double booking
CREATE UNIQUE INDEX idx_appointments_unique_slot ON appointments(doctor_id, appointment_date, appointment_time) 
WHERE is_deleted = FALSE AND status != 'cancelled';