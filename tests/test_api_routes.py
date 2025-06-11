import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from app import create_app, db
from models import User, Doctor, Appointment, Symptom, Document


class TestAPIRoutes(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def _create_test_data(self):
        """Create test data for tests"""
        # Create test user
        self.test_user = User(
            name='Test User',
            mobile_number='9876543210',
            email='test@example.com',
            is_verified=True
        )
        db.session.add(self.test_user)
        
        # Create test doctor
        self.test_doctor = Doctor(
            name='Dr. Test',
            specialty='Cardiology',
            qualification='MBBS, MD',
            experience_years=10,
            consultation_fee=500,
            hospital_name='Test Hospital'
        )
        db.session.add(self.test_doctor)
        
        # Create test symptoms
        symptoms = ['Fever', 'Cough', 'Headache', 'Fatigue']
        for symptom_name in symptoms:
            symptom = Symptom(name=symptom_name, category='General')
            db.session.add(symptom)
        
        db.session.commit()
    
    def _get_auth_token(self):
        """Get authentication token for tests"""
        mobile = '9876543210'
        self.client.post('/api/auth/request-otp', json={'mobile_number': mobile})
        
        with self.app.app_context():
            from models import OTPCode
            otp_record = OTPCode.query.filter_by(mobile_number=mobile).first()
            otp_code = otp_record.otp_code
        
        login_response = self.client.post('/api/auth/verify-otp', 
                                        json={'mobile_number': mobile, 'otp_code': otp_code})
        return json.loads(login_response.data)['token']
    
    def test_get_doctors(self):
        """Test getting list of doctors"""
        token = self._get_auth_token()
        response = self.client.get('/api/doctors', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('doctors', data)
        self.assertGreater(len(data['doctors']), 0)
    
    def test_get_doctors_with_specialty_filter(self):
        """Test getting doctors filtered by specialty"""
        token = self._get_auth_token()
        response = self.client.get('/api/doctors?specialty=Cardiology', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['doctors'][0]['specialty'], 'Cardiology')
    
    def test_get_doctor_availability(self):
        """Test getting doctor availability"""
        token = self._get_auth_token()
        response = self.client.get(f'/api/doctors/{self.test_doctor.id}/availability?date=2024-12-20', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('available_slots', data)
    
    def test_book_appointment(self):
        """Test booking appointment"""
        token = self._get_auth_token()
        appointment_data = {
            'doctor_id': str(self.test_doctor.id),
            'appointment_date': '2024-12-20',
            'appointment_time': '10:00',
            'symptoms': 'Chest pain and breathing difficulty'
        }
        
        response = self.client.post('/api/appointments', 
                                  json=appointment_data,
                                  headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('appointment_id', data)
    
    def test_get_appointments(self):
        """Test getting user appointments"""
        token = self._get_auth_token()
        
        # First book an appointment
        appointment_data = {
            'doctor_id': str(self.test_doctor.id),
            'appointment_date': '2024-12-20',
            'appointment_time': '10:00',
            'symptoms': 'Regular checkup'
        }
        self.client.post('/api/appointments', 
                        json=appointment_data,
                        headers={'Authorization': f'Bearer {token}'})
        
        # Then get appointments
        response = self.client.get('/api/appointments', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('appointments', data)
        self.assertGreater(len(data['appointments']), 0)
    
    def test_get_symptoms(self):
        """Test getting list of symptoms"""
        token = self._get_auth_token()
        response = self.client.get('/api/symptoms', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('symptoms', data)
        self.assertGreater(len(data['symptoms']), 0)
    
    @patch('ai_services.analyze_symptoms')
    def test_create_symptom_assessment(self, mock_analyze):
        """Test creating symptom assessment"""
        mock_analyze.return_value = {
            'success': True,
            'recommended_specialty': 'Cardiology',
            'severity_score': 7,
            'insights': 'Possible cardiac issue'
        }
        
        token = self._get_auth_token()
        assessment_data = {
            'symptoms': ['Chest pain', 'Shortness of breath'],
            'severity': 7,
            'duration': '2 days',
            'additional_info': 'Pain worsens with activity'
        }
        
        response = self.client.post('/api/symptom-assessment', 
                                  json=assessment_data,
                                  headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('assessment_id', data)
        self.assertIn('ai_analysis', data)
    
    def test_upload_document(self):
        """Test document upload"""
        token = self._get_auth_token()
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(b'Test document content')
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as test_file:
                response = self.client.post('/api/documents',
                                          data={
                                              'file': (test_file, 'test_document.pdf'),
                                              'document_type': 'lab_report',
                                              'title': 'Test Lab Report'
                                          },
                                          headers={'Authorization': f'Bearer {token}'})
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIn('document_id', data)
        finally:
            os.unlink(tmp_file_path)
    
    def test_get_documents(self):
        """Test getting user documents"""
        token = self._get_auth_token()
        
        # First upload a document
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(b'Test document content')
            tmp_file_path = tmp_file.name
        
        try:
            with open(tmp_file_path, 'rb') as test_file:
                self.client.post('/api/documents',
                               data={
                                   'file': (test_file, 'test_document.pdf'),
                                   'document_type': 'lab_report',
                                   'title': 'Test Lab Report'
                               },
                               headers={'Authorization': f'Bearer {token}'})
            
            # Then get documents
            response = self.client.get('/api/documents', 
                                     headers={'Authorization': f'Bearer {token}'})
            data = json.loads(response.data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTrue(data['success'])
            self.assertIn('documents', data)
        finally:
            os.unlink(tmp_file_path)
    
    def test_get_lab_tests(self):
        """Test getting available lab tests"""
        token = self._get_auth_token()
        response = self.client.get('/api/lab-tests', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('lab_tests', data)
    
    def test_book_lab_tests(self):
        """Test booking lab tests"""
        token = self._get_auth_token()
        booking_data = {
            'test_ids': ['test_1', 'test_2'],
            'preferred_date': '2024-12-20',
            'preferred_time': '09:00',
            'lab_location': 'Main Lab'
        }
        
        response = self.client.post('/api/lab-bookings', 
                                  json=booking_data,
                                  headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('booking_id', data)
    
    def test_get_care_packages(self):
        """Test getting care packages"""
        token = self._get_auth_token()
        response = self.client.get('/api/care-packages', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('packages', data)
    
    def test_get_ambulance_services(self):
        """Test getting ambulance services"""
        token = self._get_auth_token()
        response = self.client.get('/api/ambulance-services', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('services', data)
    
    def test_book_ambulance(self):
        """Test booking ambulance service"""
        token = self._get_auth_token()
        booking_data = {
            'service_type': 'emergency',
            'pickup_location': '123 Main St',
            'destination': 'City Hospital',
            'emergency_type': 'chest_pain',
            'contact_number': '9876543210'
        }
        
        response = self.client.post('/api/ambulance/book', 
                                  json=booking_data,
                                  headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('booking_id', data)
    
    def test_send_peer_support_message(self):
        """Test sending peer support message"""
        token = self._get_auth_token()
        message_data = {
            'message': 'Hello, I need some support',
            'category': 'anxiety'
        }
        
        response = self.client.post('/api/peer-support/messages', 
                                  json=message_data,
                                  headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('message_id', data)
    
    def test_get_notifications(self):
        """Test getting user notifications"""
        token = self._get_auth_token()
        response = self.client.get('/api/notifications', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('notifications', data)
    
    def test_unauthorized_access(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get('/api/profile')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
    
    def test_invalid_token(self):
        """Test accessing protected endpoint with invalid token"""
        response = self.client.get('/api/profile', 
                                 headers={'Authorization': 'Bearer invalid_token'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])


if __name__ == '__main__':
    unittest.main()