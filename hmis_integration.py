import requests
import logging
from datetime import datetime, date
import os

logger = logging.getLogger(__name__)

# HMIS integration configuration
HMIS_BASE_URL = os.environ.get("HMIS_BASE_URL", "https://api.hmis-example.com")
HMIS_API_KEY = os.environ.get("HMIS_API_KEY", "hmis_api_key")

def search_doctors(specialty=None, name_search=None):
    """
    Search for doctors in HMIS system
    Returns list of doctors matching the criteria
    """
    try:
        url = f"{HMIS_BASE_URL}/doctors/search"
        headers = {
            "Authorization": f"Bearer {HMIS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {}
        if specialty:
            params['specialty'] = specialty
        if name_search:
            params['name'] = name_search
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            hmis_doctors = response.json().get('doctors', [])
            
            # Transform HMIS doctor data to our format
            doctors_list = []
            for doctor in hmis_doctors:
                doctors_list.append({
                    "id": f"hmis_{doctor.get('id')}",
                    "name": doctor.get('name'),
                    "specialty": doctor.get('specialty'),
                    "qualification": doctor.get('qualification'),
                    "experience_years": doctor.get('experience_years'),
                    "hospital_name": doctor.get('hospital_name'),
                    "consultation_fee": doctor.get('consultation_fee'),
                    "rating": doctor.get('rating'),
                    "profile_image": doctor.get('profile_image'),
                    "source": "hmis",
                    "hmis_id": doctor.get('id')
                })
            
            return doctors_list
        else:
            logger.error(f"HMIS doctor search failed: {response.status_code} - {response.text}")
            return []
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to HMIS for doctor search: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in HMIS doctor search: {str(e)}")
        return []

def get_doctor_availability(doctor_id, appointment_date):
    """
    Get doctor availability from HMIS system
    Returns available time slots for the given date
    """
    try:
        # Remove 'hmis_' prefix if present
        hmis_doctor_id = doctor_id.replace('hmis_', '') if doctor_id.startswith('hmis_') else doctor_id
        
        url = f"{HMIS_BASE_URL}/doctors/{hmis_doctor_id}/availability"
        headers = {
            "Authorization": f"Bearer {HMIS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        params = {
            "date": appointment_date.isoformat() if isinstance(appointment_date, date) else appointment_date
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "slots": data.get('available_slots', [])
            }
        else:
            logger.error(f"HMIS availability check failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": "Failed to fetch availability from HMIS"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to HMIS for availability: {str(e)}")
        return {
            "success": False,
            "message": "Connection error to HMIS system"
        }
    except Exception as e:
        logger.error(f"Unexpected error in HMIS availability check: {str(e)}")
        return {
            "success": False,
            "message": "Unexpected error occurred"
        }

def share_profile_with_hmis(user_id, hospital_id):
    """
    Share user profile with HMIS system
    This allows hospitals to access patient information
    """
    try:
        from models import User
        from app import db
        
        user = User.query.get(user_id)
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        url = f"{HMIS_BASE_URL}/patients/share-profile"
        headers = {
            "Authorization": f"Bearer {HMIS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        profile_data = {
            "patient_id": user.id,
            "name": user.name,
            "mobile_number": user.mobile_number,
            "email": user.email,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "gender": user.gender,
            "address": user.address,
            "emergency_contact": user.emergency_contact,
            "hospital_id": hospital_id,
            "shared_at": datetime.utcnow().isoformat()
        }
        
        response = requests.post(url, headers=headers, json=profile_data, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Profile shared successfully with hospital",
                "share_token": response.json().get('share_token')
            }
        else:
            logger.error(f"HMIS profile sharing failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": "Failed to share profile with hospital"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to HMIS for profile sharing: {str(e)}")
        return {
            "success": False,
            "message": "Connection error to HMIS system"
        }
    except Exception as e:
        logger.error(f"Unexpected error in HMIS profile sharing: {str(e)}")
        return {
            "success": False,
            "message": "Unexpected error occurred"
        }

def book_appointment_with_hmis(user_id, doctor_id, appointment_date, appointment_time, symptoms):
    """
    Book appointment directly with HMIS system
    Used when the doctor is from HMIS
    """
    try:
        from models import User
        
        user = User.query.get(user_id)
        if not user:
            return {
                "success": False,
                "message": "User not found"
            }
        
        # Remove 'hmis_' prefix if present
        hmis_doctor_id = doctor_id.replace('hmis_', '') if doctor_id.startswith('hmis_') else doctor_id
        
        url = f"{HMIS_BASE_URL}/appointments/book"
        headers = {
            "Authorization": f"Bearer {HMIS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        appointment_data = {
            "patient_id": user.id,
            "patient_name": user.name,
            "patient_mobile": user.mobile_number,
            "doctor_id": hmis_doctor_id,
            "appointment_date": appointment_date.isoformat() if hasattr(appointment_date, 'isoformat') else appointment_date,
            "appointment_time": appointment_time.strftime('%H:%M') if hasattr(appointment_time, 'strftime') else appointment_time,
            "symptoms": symptoms,
            "booked_via": "phr_app"
        }
        
        response = requests.post(url, headers=headers, json=appointment_data, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "message": "Appointment booked successfully",
                "hmis_appointment_id": data.get('appointment_id'),
                "confirmation_number": data.get('confirmation_number')
            }
        else:
            logger.error(f"HMIS appointment booking failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "message": "Failed to book appointment with hospital"
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to HMIS for appointment booking: {str(e)}")
        return {
            "success": False,
            "message": "Connection error to HMIS system"
        }
    except Exception as e:
        logger.error(f"Unexpected error in HMIS appointment booking: {str(e)}")
        return {
            "success": False,
            "message": "Unexpected error occurred"
        }

def receive_document_from_hmis(document_data):
    """
    Receive and process documents uploaded by HMIS
    This endpoint will be called by HMIS systems to upload patient documents
    """
    try:
        from models import Document, User
        from app import db
        import uuid
        
        patient_id = document_data.get('patient_id')
        document_type = document_data.get('document_type')
        title = document_data.get('title')
        file_content = document_data.get('file_content')  # Base64 encoded
        file_type = document_data.get('file_type')
        hospital_id = document_data.get('hospital_id')
        doctor_name = document_data.get('doctor_name')
        
        # Verify patient exists
        user = User.query.get(patient_id)
        if not user:
            return {
                "success": False,
                "message": "Patient not found"
            }
        
        # Save the document
        import base64
        file_data = base64.b64decode(file_content)
        filename = f"hmis_{uuid.uuid4()}.{file_type}"
        file_path = os.path.join(os.environ.get("UPLOAD_FOLDER", "uploads"), filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        # Create document record
        document = Document(
            user_id=patient_id,
            document_type=document_type,
            title=title,
            file_path=file_path,
            file_type=file_type,
            file_size=len(file_data),
            uploaded_by='hospital',
            upload_source=hospital_id,
            tags=[doctor_name] if doctor_name else []
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Create notification for patient
        from notification_service import create_notification
        create_notification(
            patient_id,
            "New Document Uploaded",
            f"A new {document_type} has been uploaded by {doctor_name or 'Hospital'}",
            "document_upload"
        )
        
        return {
            "success": True,
            "message": "Document uploaded successfully",
            "document_id": document.id
        }
        
    except Exception as e:
        logger.error(f"Error processing HMIS document upload: {str(e)}")
        return {
            "success": False,
            "message": "Failed to process document upload"
        }

def get_hospital_list():
    """
    Get list of hospitals from HMIS
    """
    try:
        url = f"{HMIS_BASE_URL}/hospitals"
        headers = {
            "Authorization": f"Bearer {HMIS_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return {
                "success": True,
                "hospitals": response.json().get('hospitals', [])
            }
        else:
            logger.error(f"HMIS hospital list failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "hospitals": []
            }
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to HMIS for hospital list: {str(e)}")
        return {
            "success": False,
            "hospitals": []
        }
    except Exception as e:
        logger.error(f"Unexpected error in HMIS hospital list: {str(e)}")
        return {
            "success": False,
            "hospitals": []
        }
