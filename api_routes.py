from flask import Blueprint, request, jsonify, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, date, time
import logging

from app import db
from models import *
from auth import request_otp, verify_otp, login_with_email, login_with_abha, get_current_user, update_user_profile
from hmis_integration import search_doctors, share_profile_with_hmis, get_doctor_availability
from ai_services import transcribe_audio, analyze_symptoms, summarize_records
from notification_service import create_notification, get_user_notifications
from utils import allowed_file, save_uploaded_file, generate_qr_code

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# Authentication endpoints
@api_bp.route('/auth/request-otp', methods=['POST'])
def api_request_otp():
    """Request OTP for mobile number"""
    data = request.get_json()
    mobile_number = data.get('mobile_number')
    
    if not mobile_number:
        return jsonify({"success": False, "message": "Mobile number is required"}), 400
    
    result = request_otp(mobile_number)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/auth/verify-otp', methods=['POST'])
def api_verify_otp():
    """Verify OTP and login"""
    data = request.get_json()
    mobile_number = data.get('mobile_number')
    otp_code = data.get('otp_code')
    
    if not mobile_number or not otp_code:
        return jsonify({"success": False, "message": "Mobile number and OTP are required"}), 400
    
    result = verify_otp(mobile_number, otp_code)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/auth/login-email', methods=['POST'])
def api_login_email():
    """Login with email and password"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400
    
    result = login_with_email(email, password)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/auth/login-abha', methods=['POST'])
def api_login_abha():
    """Login with ABHA ID"""
    data = request.get_json()
    abha_id = data.get('abha_id')
    
    if not abha_id:
        return jsonify({"success": False, "message": "ABHA ID is required"}), 400
    
    result = login_with_abha(abha_id)
    return jsonify(result), 200 if result['success'] else 400

# Profile management
@api_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get user profile"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "abha_id": user.abha_id,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "gender": user.gender,
            "address": user.address,
            "emergency_contact": user.emergency_contact,
            "profile_image": user.profile_image
        }
    })

@api_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    data = request.get_json()
    result = update_user_profile(data)
    return jsonify(result), 200 if result['success'] else 400

@api_bp.route('/profile/qr-code', methods=['GET'])
@jwt_required()
def get_profile_qr():
    """Generate QR code for user profile"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    qr_data = {
        "user_id": user.id,
        "name": user.name,
        "mobile": user.mobile_number,
        "emergency_contact": user.emergency_contact
    }
    
    qr_code_url = generate_qr_code(qr_data)
    
    return jsonify({
        "success": True,
        "qr_code_url": qr_code_url,
        "profile_data": qr_data
    })

@api_bp.route('/profile/share', methods=['POST'])
@jwt_required()
def share_profile():
    """Share profile with hospital HMIS"""
    data = request.get_json()
    hospital_id = data.get('hospital_id')
    
    if not hospital_id:
        return jsonify({"success": False, "message": "Hospital ID is required"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    result = share_profile_with_hmis(user.id, hospital_id)
    return jsonify(result), 200 if result['success'] else 400

# Doctor and appointment management
@api_bp.route('/doctors', methods=['GET'])
@jwt_required()
def get_doctors():
    """Get list of doctors with optional filtering"""
    specialty = request.args.get('specialty')
    name_search = request.args.get('name')
    
    query = Doctor.query.filter_by(is_active=True)
    
    if specialty:
        query = query.filter(Doctor.specialty.ilike(f'%{specialty}%'))
    
    if name_search:
        query = query.filter(Doctor.name.ilike(f'%{name_search}%'))
    
    doctors = query.all()
    
    # Also search HMIS for additional doctors
    hmis_doctors = search_doctors(specialty, name_search)
    
    doctors_list = []
    for doctor in doctors:
        doctors_list.append({
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "qualification": doctor.qualification,
            "experience_years": doctor.experience_years,
            "hospital_name": doctor.hospital_name,
            "consultation_fee": float(doctor.consultation_fee) if doctor.consultation_fee else None,
            "rating": float(doctor.rating) if doctor.rating else None,
            "profile_image": doctor.profile_image,
            "source": "local"
        })
    
    # Add HMIS doctors
    doctors_list.extend(hmis_doctors)
    
    return jsonify({
        "success": True,
        "doctors": doctors_list
    })

@api_bp.route('/doctors/<doctor_id>/availability', methods=['GET'])
@jwt_required()
def get_doctor_availability_api(doctor_id):
    """Get doctor availability"""
    date_str = request.args.get('date')
    
    if not date_str:
        return jsonify({"success": False, "message": "Date is required"}), 400
    
    try:
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Check local doctor first
    doctor = Doctor.query.get(doctor_id)
    if doctor:
        availability = doctor.availability or {}
        day_name = appointment_date.strftime('%A').lower()
        available_slots = availability.get(day_name, [])
    else:
        # Check HMIS
        availability_result = get_doctor_availability(doctor_id, appointment_date)
        if availability_result['success']:
            available_slots = availability_result['slots']
        else:
            return jsonify(availability_result), 400
    
    # Filter out booked slots
    booked_appointments = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=appointment_date
    ).all()
    
    booked_times = [apt.appointment_time.strftime('%H:%M') for apt in booked_appointments]
    available_slots = [slot for slot in available_slots if slot not in booked_times]
    
    return jsonify({
        "success": True,
        "date": date_str,
        "available_slots": available_slots
    })

@api_bp.route('/appointments', methods=['POST'])
@jwt_required()
def book_appointment():
    """Book an appointment"""
    data = request.get_json()
    doctor_id = data.get('doctor_id')
    appointment_date_str = data.get('appointment_date')
    appointment_time_str = data.get('appointment_time')
    symptoms = data.get('symptoms', '')
    consultation_type = data.get('consultation_type', 'in-person')
    
    if not all([doctor_id, appointment_date_str, appointment_time_str]):
        return jsonify({"success": False, "message": "Doctor ID, date, and time are required"}), 400
    
    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
        appointment_time = datetime.strptime(appointment_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date or time format"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Check if slot is available
    existing_appointment = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time
    ).first()
    
    if existing_appointment:
        return jsonify({"success": False, "message": "Time slot is already booked"}), 400
    
    # Create appointment
    appointment = Appointment(
        user_id=user.id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        symptoms=symptoms,
        consultation_type=consultation_type
    )
    
    db.session.add(appointment)
    db.session.commit()
    
    # Create notification
    create_notification(
        user.id,
        "Appointment Booked",
        f"Your appointment has been booked for {appointment_date_str} at {appointment_time_str}",
        "appointment"
    )
    
    return jsonify({
        "success": True,
        "message": "Appointment booked successfully",
        "appointment_id": appointment.id
    })

@api_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    """Get user appointments"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    status = request.args.get('status')
    
    query = Appointment.query.filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    
    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    
    appointments_list = []
    for appointment in appointments:
        doctor = Doctor.query.get(appointment.doctor_id)
        appointments_list.append({
            "id": appointment.id,
            "doctor_name": doctor.name if doctor else "Unknown Doctor",
            "doctor_specialty": doctor.specialty if doctor else None,
            "appointment_date": appointment.appointment_date.isoformat(),
            "appointment_time": appointment.appointment_time.strftime('%H:%M'),
            "status": appointment.status,
            "symptoms": appointment.symptoms,
            "consultation_type": appointment.consultation_type,
            "amount": float(appointment.amount) if appointment.amount else None
        })
    
    return jsonify({
        "success": True,
        "appointments": appointments_list
    })

# Symptom checker
@api_bp.route('/symptoms', methods=['GET'])
@jwt_required()
def get_symptoms():
    """Get list of symptoms"""
    category = request.args.get('category')
    
    query = Symptom.query
    if category:
        query = query.filter_by(category=category)
    
    symptoms = query.all()
    
    symptoms_list = []
    for symptom in symptoms:
        symptoms_list.append({
            "id": symptom.id,
            "name": symptom.name,
            "description": symptom.description,
            "category": symptom.category,
            "severity_levels": symptom.severity_levels,
            "associated_specialties": symptom.associated_specialties
        })
    
    return jsonify({
        "success": True,
        "symptoms": symptoms_list
    })

@api_bp.route('/symptom-assessment', methods=['POST'])
@jwt_required()
def create_symptom_assessment():
    """Create symptom assessment"""
    data = request.get_json()
    symptoms = data.get('symptoms', [])
    questionnaire_responses = data.get('questionnaire_responses', {})
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Analyze symptoms using AI
    ai_analysis = analyze_symptoms(symptoms, questionnaire_responses)
    
    assessment = SymptomAssessment(
        user_id=user.id,
        symptoms=symptoms,
        questionnaire_responses=questionnaire_responses,
        ai_analysis=ai_analysis,
        recommended_specialty=ai_analysis.get('recommended_specialty'),
        severity_score=ai_analysis.get('severity_score')
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "assessment_id": assessment.id,
        "ai_analysis": ai_analysis,
        "recommended_specialty": assessment.recommended_specialty,
        "severity_score": assessment.severity_score
    })

@api_bp.route('/symptom-assessment/audio', methods=['POST'])
@jwt_required()
def upload_symptom_audio():
    """Upload and analyze audio for symptom assessment"""
    if 'audio' not in request.files:
        return jsonify({"success": False, "message": "No audio file provided"}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({"success": False, "message": "No audio file selected"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Save audio file
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    file_path = save_uploaded_file(file, filename)
    
    # Transcribe audio using Google Gemini
    transcription_result = transcribe_audio(file_path)
    
    if not transcription_result['success']:
        return jsonify(transcription_result), 400
    
    transcription = transcription_result['transcription']
    
    # Analyze transcribed symptoms
    ai_analysis = analyze_symptoms([], {}, transcription)
    
    assessment = SymptomAssessment(
        user_id=user.id,
        symptoms=ai_analysis.get('identified_symptoms', []),
        audio_recording_path=file_path,
        transcription=transcription,
        ai_analysis=ai_analysis,
        recommended_specialty=ai_analysis.get('recommended_specialty'),
        severity_score=ai_analysis.get('severity_score')
    )
    
    db.session.add(assessment)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "assessment_id": assessment.id,
        "transcription": transcription,
        "ai_analysis": ai_analysis,
        "recommended_specialty": assessment.recommended_specialty
    })

# Document management
@api_bp.route('/documents', methods=['POST'])
@jwt_required()
def upload_document():
    """Upload a document"""
    if 'file' not in request.files:
        return jsonify({"success": False, "message": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    document_type = request.form.get('document_type', 'general')
    title = request.form.get('title', file.filename)
    
    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "File type not allowed"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Save file
    filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
    file_path = save_uploaded_file(file, filename)
    
    # Create document record
    document = Document(
        user_id=user.id,
        document_type=document_type,
        title=title,
        file_path=file_path,
        file_type=file.filename.rsplit('.', 1)[1].lower(),
        file_size=len(file.read()),
        uploaded_by='patient'
    )
    
    file.seek(0)  # Reset file pointer after reading for size
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Document uploaded successfully",
        "document_id": document.id
    })

@api_bp.route('/documents', methods=['GET'])
@jwt_required()
def get_documents():
    """Get user documents"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    document_type = request.args.get('type')
    
    query = Document.query.filter_by(user_id=user.id)
    if document_type:
        query = query.filter_by(document_type=document_type)
    
    documents = query.order_by(Document.created_at.desc()).all()
    
    documents_list = []
    for doc in documents:
        documents_list.append({
            "id": doc.id,
            "title": doc.title,
            "document_type": doc.document_type,
            "file_type": doc.file_type,
            "file_size": doc.file_size,
            "uploaded_by": doc.uploaded_by,
            "created_at": doc.created_at.isoformat(),
            "download_url": f"/api/documents/{doc.id}/download"
        })
    
    return jsonify({
        "success": True,
        "documents": documents_list
    })

@api_bp.route('/documents/<document_id>/download', methods=['GET'])
@jwt_required()
def download_document(document_id):
    """Download a document"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    document = Document.query.filter_by(id=document_id, user_id=user.id).first()
    if not document:
        return jsonify({"success": False, "message": "Document not found"}), 404
    
    return send_from_directory(
        os.path.dirname(document.file_path),
        os.path.basename(document.file_path),
        as_attachment=True
    )

# Record summarization
@api_bp.route('/records/summarize', methods=['POST'])
@jwt_required()
def summarize_user_records():
    """Summarize user records using AI"""
    data = request.get_json()
    summary_type = data.get('summary_type', 'all_records')  # all_records or selected_records
    document_ids = data.get('document_ids', [])
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    if summary_type == 'selected_records' and not document_ids:
        return jsonify({"success": False, "message": "Document IDs required for selected records"}), 400
    
    # Get documents to summarize
    if summary_type == 'all_records':
        documents = Document.query.filter_by(user_id=user.id).all()
    else:
        documents = Document.query.filter(
            Document.user_id == user.id,
            Document.id.in_(document_ids)
        ).all()
    
    if not documents:
        return jsonify({"success": False, "message": "No documents found"}), 404
    
    # Generate summary using AI
    summary_result = summarize_records(documents)
    
    if not summary_result['success']:
        return jsonify(summary_result), 400
    
    # Save summary
    record_summary = RecordSummary(
        user_id=user.id,
        summary_type=summary_type,
        document_ids=document_ids if summary_type == 'selected_records' else None,
        summary_text=summary_result['summary'],
        ai_insights=summary_result.get('insights')
    )
    
    db.session.add(record_summary)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "summary_id": record_summary.id,
        "summary": summary_result['summary'],
        "insights": summary_result.get('insights')
    })

# Medicine and prescription management
@api_bp.route('/prescriptions', methods=['POST'])
@jwt_required()
def upload_prescription():
    """Upload prescription image"""
    if 'prescription_image' not in request.files:
        return jsonify({"success": False, "message": "No prescription image provided"}), 400
    
    file = request.files['prescription_image']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Save prescription image
    filename = secure_filename(f"prescription_{uuid.uuid4()}_{file.filename}")
    file_path = save_uploaded_file(file, filename)
    
    # Create prescription record
    prescription = Prescription(
        user_id=user.id,
        medicines=[],  # Will be populated after OCR processing
        prescription_image_path=file_path
    )
    
    db.session.add(prescription)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Prescription uploaded successfully",
        "prescription_id": prescription.id
    })

@api_bp.route('/medicine-tracker', methods=['POST'])
@jwt_required()
def add_medicine_tracker():
    """Add medicine to tracker"""
    data = request.get_json()
    medicine_name = data.get('medicine_name')
    dosage = data.get('dosage')
    frequency = data.get('frequency')
    timing = data.get('timing', [])
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not all([medicine_name, dosage, frequency, timing, start_date_str]):
        return jsonify({"success": False, "message": "Required fields missing"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else None
    except ValueError:
        return jsonify({"success": False, "message": "Invalid date format"}), 400
    
    medicine_tracker = MedicineTracker(
        user_id=user.id,
        medicine_name=medicine_name,
        dosage=dosage,
        frequency=frequency,
        timing=timing,
        start_date=start_date,
        end_date=end_date
    )
    
    db.session.add(medicine_tracker)
    db.session.commit()
    
    # Create notifications for medicine reminders
    for time_slot in timing:
        create_notification(
            user.id,
            "Medicine Reminder",
            f"Time to take {medicine_name} - {dosage}",
            "medicine_reminder",
            metadata={"medicine_tracker_id": medicine_tracker.id, "time_slot": time_slot}
        )
    
    return jsonify({
        "success": True,
        "message": "Medicine added to tracker",
        "tracker_id": medicine_tracker.id
    })

@api_bp.route('/medicine-tracker', methods=['GET'])
@jwt_required()
def get_medicine_tracker():
    """Get medicine tracker list"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    trackers = MedicineTracker.query.filter_by(
        user_id=user.id,
        is_active=True
    ).all()
    
    tracker_list = []
    for tracker in trackers:
        tracker_list.append({
            "id": tracker.id,
            "medicine_name": tracker.medicine_name,
            "dosage": tracker.dosage,
            "frequency": tracker.frequency,
            "timing": tracker.timing,
            "start_date": tracker.start_date.isoformat(),
            "end_date": tracker.end_date.isoformat() if tracker.end_date else None,
            "is_active": tracker.is_active
        })
    
    return jsonify({
        "success": True,
        "medicine_trackers": tracker_list
    })

# Lab tests
@api_bp.route('/lab-tests', methods=['GET'])
@jwt_required()
def get_lab_tests():
    """Get available lab tests"""
    category = request.args.get('category')
    
    query = LabTest.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    
    tests = query.all()
    
    tests_list = []
    for test in tests:
        tests_list.append({
            "id": test.id,
            "name": test.name,
            "description": test.description,
            "category": test.category,
            "normal_range": test.normal_range,
            "price": float(test.price) if test.price else None,
            "preparation_instructions": test.preparation_instructions
        })
    
    return jsonify({
        "success": True,
        "lab_tests": tests_list
    })

@api_bp.route('/lab-bookings', methods=['POST'])
@jwt_required()
def book_lab_tests():
    """Book lab tests"""
    data = request.get_json()
    test_ids = data.get('test_ids', [])
    doctor_id = data.get('doctor_id')
    
    if not test_ids:
        return jsonify({"success": False, "message": "At least one test must be selected"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    # Calculate total amount
    tests = LabTest.query.filter(LabTest.id.in_(test_ids)).all()
    total_amount = sum(float(test.price) for test in tests if test.price)
    
    lab_booking = LabBooking(
        user_id=user.id,
        doctor_id=doctor_id,
        tests=test_ids,
        total_amount=total_amount
    )
    
    db.session.add(lab_booking)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Lab tests booked successfully",
        "booking_id": lab_booking.id,
        "total_amount": float(total_amount)
    })

# Notifications
@api_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get user notifications"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    notifications = get_user_notifications(user.id)
    return jsonify({
        "success": True,
        "notifications": notifications
    })

# Care packages
@api_bp.route('/care-packages', methods=['GET'])
@jwt_required()
def get_care_packages():
    """Get available care packages"""
    packages = CarePackage.query.filter_by(is_active=True).all()
    
    packages_list = []
    for package in packages:
        packages_list.append({
            "id": package.id,
            "name": package.name,
            "description": package.description,
            "category": package.category,
            "features": package.features,
            "price": float(package.price) if package.price else None,
            "duration_months": package.duration_months
        })
    
    return jsonify({
        "success": True,
        "care_packages": packages_list
    })

@api_bp.route('/care-packages/<package_id>/apply', methods=['POST'])
@jwt_required()
def apply_care_package(package_id):
    """Apply for a care package"""
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    package = CarePackage.query.get(package_id)
    if not package:
        return jsonify({"success": False, "message": "Care package not found"}), 404
    
    # Check if user already has this package
    existing = UserCarePackage.query.filter_by(
        user_id=user.id,
        care_package_id=package_id,
        status='active'
    ).first()
    
    if existing:
        return jsonify({"success": False, "message": "You already have this care package"}), 400
    
    user_package = UserCarePackage(
        user_id=user.id,
        care_package_id=package_id,
        start_date=datetime.utcnow().date()
    )
    
    db.session.add(user_package)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Care package applied successfully",
        "user_package_id": user_package.id
    })

# Ambulance services
@api_bp.route('/ambulance-services', methods=['GET'])
@jwt_required()
def get_ambulance_services():
    """Get available ambulance services"""
    service_type = request.args.get('type')
    
    query = AmbulanceService.query.filter_by(is_active=True)
    if service_type:
        query = query.filter_by(service_type=service_type)
    
    services = query.all()
    
    services_list = []
    for service in services:
        services_list.append({
            "id": service.id,
            "service_name": service.service_name,
            "phone_number": service.phone_number,
            "service_type": service.service_type,
            "coverage_area": service.coverage_area,
            "base_price": float(service.base_price) if service.base_price else None,
            "per_km_rate": float(service.per_km_rate) if service.per_km_rate else None,
            "rating": float(service.rating) if service.rating else None
        })
    
    return jsonify({
        "success": True,
        "ambulance_services": services_list
    })

@api_bp.route('/ambulance-bookings', methods=['POST'])
@jwt_required()
def book_ambulance():
    """Book ambulance service"""
    data = request.get_json()
    service_id = data.get('ambulance_service_id')
    pickup_location = data.get('pickup_location')
    destination = data.get('destination')
    emergency_level = data.get('emergency_level', 'medium')
    patient_condition = data.get('patient_condition')
    
    if not all([service_id, pickup_location, destination]):
        return jsonify({"success": False, "message": "Required fields missing"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    booking = AmbulanceBooking(
        user_id=user.id,
        ambulance_service_id=service_id,
        pickup_location=pickup_location,
        destination=destination,
        emergency_level=emergency_level,
        patient_condition=patient_condition
    )
    
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Ambulance booking requested",
        "booking_id": booking.id
    })

# Chat functionality
@api_bp.route('/chat/peer-support', methods=['POST'])
@jwt_required()
def send_peer_support_message():
    """Send message in peer support chat"""
    data = request.get_json()
    message = data.get('message')
    
    if not message:
        return jsonify({"success": False, "message": "Message is required"}), 400
    
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    
    chat_message = ChatMessage(
        sender_id=user.id,
        room_id='peer_support',
        message=message,
        is_anonymous=True
    )
    
    db.session.add(chat_message)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message_id": chat_message.id
    })

@api_bp.route('/chat/peer-support', methods=['GET'])
@jwt_required()
def get_peer_support_messages():
    """Get peer support chat messages"""
    limit = request.args.get('limit', 50, type=int)
    
    messages = ChatMessage.query.filter_by(
        room_id='peer_support'
    ).order_by(
        ChatMessage.created_at.desc()
    ).limit(limit).all()
    
    messages_list = []
    for msg in messages:
        messages_list.append({
            "id": msg.id,
            "message": msg.message,
            "sender": "Anonymous" if msg.is_anonymous else "User",
            "created_at": msg.created_at.isoformat()
        })
    
    return jsonify({
        "success": True,
        "messages": list(reversed(messages_list))  # Reverse to show oldest first
    })
