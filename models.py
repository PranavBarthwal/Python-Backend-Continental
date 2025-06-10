from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    abha_id = db.Column(db.String(50), unique=True, nullable=True)
    password_hash = db.Column(db.String(256))
    is_verified = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(255), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class OTP(db.Model):
    __tablename__ = 'otp_codes'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    mobile_number = db.Column(db.String(15), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Doctor(db.Model):
    __tablename__ = 'doctors'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(200), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    hospital_id = db.Column(db.String(50), nullable=True)
    hospital_name = db.Column(db.String(200), nullable=True)
    availability = db.Column(db.JSON, nullable=True)
    consultation_fee = db.Column(db.Numeric(10, 2), nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Appointment(db.Model):
    __tablename__ = 'appointments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    doctor_id = db.Column(db.String(36), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled
    symptoms = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    consultation_type = db.Column(db.String(20), default='in-person')  # in-person, video, audio
    payment_status = db.Column(db.String(20), default='pending')
    amount = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Symptom(db.Model):
    __tablename__ = 'symptoms'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    severity_levels = db.Column(db.JSON, nullable=True)
    associated_specialties = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SymptomAssessment(db.Model):
    __tablename__ = 'symptom_assessments'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    symptoms = db.Column(db.JSON, nullable=False)
    questionnaire_responses = db.Column(db.JSON, nullable=True)
    audio_recording_path = db.Column(db.String(255), nullable=True)
    transcription = db.Column(db.Text, nullable=True)
    ai_analysis = db.Column(db.JSON, nullable=True)
    recommended_specialty = db.Column(db.String(100), nullable=True)
    severity_score = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # prescription, test_result, handout, etc.
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # pdf, jpg, png
    file_size = db.Column(db.Integer, nullable=True)
    uploaded_by = db.Column(db.String(50), nullable=True)  # patient, doctor, hospital
    upload_source = db.Column(db.String(100), nullable=True)  # hmis_id or manual
    tags = db.Column(db.JSON, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    __tablename__ = 'medicines'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200), nullable=True)
    dosage = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    is_prescription_required = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    doctor_id = db.Column(db.String(36), nullable=True)
    appointment_id = db.Column(db.String(36), nullable=True)
    medicines = db.Column(db.JSON, nullable=False)  # List of medicines with dosage instructions
    instructions = db.Column(db.Text, nullable=True)
    prescription_image_path = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MedicineTracker(db.Model):
    __tablename__ = 'medicine_tracker'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    prescription_id = db.Column(db.String(36), nullable=True)
    medicine_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)  # daily, twice_daily, etc.
    timing = db.Column(db.JSON, nullable=False)  # [{"time": "08:00", "relation": "before_breakfast"}]
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LabTest(db.Model):
    __tablename__ = 'lab_tests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    normal_range = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    preparation_instructions = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LabBooking(db.Model):
    __tablename__ = 'lab_bookings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    doctor_id = db.Column(db.String(36), nullable=True)
    tests = db.Column(db.JSON, nullable=False)  # List of test IDs
    scheduled_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='requested')  # requested, scheduled, completed, cancelled
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    payment_status = db.Column(db.String(20), default='pending')
    results_available = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # medicine_reminder, appointment, etc.
    is_read = db.Column(db.Boolean, default=False)
    scheduled_for = db.Column(db.DateTime, nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class CarePackage(db.Model):
    __tablename__ = 'care_packages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False)  # diabetes, hypertension, etc.
    features = db.Column(db.JSON, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    duration_months = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserCarePackage(db.Model):
    __tablename__ = 'user_care_packages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    care_package_id = db.Column(db.String(36), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default='active')  # active, expired, cancelled
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.String(36), nullable=False)
    receiver_id = db.Column(db.String(36), nullable=True)  # Null for group/anonymous chat
    room_id = db.Column(db.String(50), nullable=True)  # For group chats like peer support
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')  # text, image, file
    is_anonymous = db.Column(db.Boolean, default=False)
    metadata = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AmbulanceService(db.Model):
    __tablename__ = 'ambulance_services'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    service_name = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # emergency, non_emergency
    coverage_area = db.Column(db.String(200), nullable=True)
    base_price = db.Column(db.Numeric(10, 2), nullable=True)
    per_km_rate = db.Column(db.Numeric(10, 2), nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AmbulanceBooking(db.Model):
    __tablename__ = 'ambulance_bookings'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    ambulance_service_id = db.Column(db.String(36), nullable=False)
    pickup_location = db.Column(db.String(500), nullable=False)
    destination = db.Column(db.String(500), nullable=False)
    emergency_level = db.Column(db.String(20), nullable=False)  # high, medium, low
    patient_condition = db.Column(db.Text, nullable=True)
    requested_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='requested')  # requested, assigned, in_transit, completed, cancelled
    estimated_amount = db.Column(db.Numeric(10, 2), nullable=True)
    actual_amount = db.Column(db.Numeric(10, 2), nullable=True)
    driver_details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RecordSummary(db.Model):
    __tablename__ = 'record_summaries'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False)
    summary_type = db.Column(db.String(20), nullable=False)  # all_records, selected_records
    document_ids = db.Column(db.JSON, nullable=True)  # For selected records
    summary_text = db.Column(db.Text, nullable=False)
    ai_insights = db.Column(db.JSON, nullable=True)
    generated_by = db.Column(db.String(50), default='gemini_ai')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
