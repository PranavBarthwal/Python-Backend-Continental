import unittest
import json
from unittest.mock import patch, MagicMock
from app import create_app, db
from models import User, OTPCode
import auth


class TestAuthenticationAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        
        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_generate_otp(self):
        """Test OTP generation"""
        otp = auth.generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
    
    def test_request_otp_valid_mobile(self):
        """Test OTP request with valid mobile number"""
        response = self.client.post('/api/auth/request-otp', 
                                  json={'mobile_number': '9876543210'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('message', data)
    
    def test_request_otp_invalid_mobile(self):
        """Test OTP request with invalid mobile number"""
        response = self.client.post('/api/auth/request-otp', 
                                  json={'mobile_number': '123'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
    
    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        mobile = '9876543210'
        
        # First request OTP
        self.client.post('/api/auth/request-otp', json={'mobile_number': mobile})
        
        # Get the OTP from database
        with self.app.app_context():
            otp_record = OTPCode.query.filter_by(mobile_number=mobile).first()
            otp_code = otp_record.otp_code
        
        # Verify OTP
        response = self.client.post('/api/auth/verify-otp', 
                                  json={'mobile_number': mobile, 'otp_code': otp_code})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
    
    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code"""
        mobile = '9876543210'
        
        # First request OTP
        self.client.post('/api/auth/request-otp', json={'mobile_number': mobile})
        
        # Try to verify with wrong OTP
        response = self.client.post('/api/auth/verify-otp', 
                                  json={'mobile_number': mobile, 'otp_code': '000000'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertFalse(data['success'])
    
    def test_email_login_success(self):
        """Test successful email login"""
        with self.app.app_context():
            # Create test user
            user = User(
                name='Test User',
                mobile_number='9876543210',
                email='test@example.com',
                is_verified=True
            )
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
        
        response = self.client.post('/api/auth/login-email', 
                                  json={'email': 'test@example.com', 'password': 'password123'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
    
    def test_email_login_invalid_credentials(self):
        """Test email login with invalid credentials"""
        response = self.client.post('/api/auth/login-email', 
                                  json={'email': 'wrong@example.com', 'password': 'wrongpass'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
    
    def test_abha_login_success(self):
        """Test successful ABHA login"""
        with self.app.app_context():
            # Create test user with ABHA ID
            user = User(
                name='Test User',
                mobile_number='9876543210',
                abha_id='12-3456-7890-1234',
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()
        
        response = self.client.post('/api/auth/login-abha', 
                                  json={'abha_id': '12-3456-7890-1234'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
    
    def test_abha_login_not_found(self):
        """Test ABHA login with non-existent ABHA ID"""
        response = self.client.post('/api/auth/login-abha', 
                                  json={'abha_id': '99-9999-9999-9999'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 404)
        self.assertFalse(data['success'])
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get('/api/profile')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 401)
        self.assertFalse(data['success'])
    
    def test_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid token"""
        # First get a token
        mobile = '9876543210'
        self.client.post('/api/auth/request-otp', json={'mobile_number': mobile})
        
        with self.app.app_context():
            otp_record = OTPCode.query.filter_by(mobile_number=mobile).first()
            otp_code = otp_record.otp_code
        
        login_response = self.client.post('/api/auth/verify-otp', 
                                        json={'mobile_number': mobile, 'otp_code': otp_code})
        token = json.loads(login_response.data)['token']
        
        # Use token to access protected endpoint
        response = self.client.get('/api/profile', 
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_profile_update(self):
        """Test profile update functionality"""
        # Get authenticated
        mobile = '9876543210'
        self.client.post('/api/auth/request-otp', json={'mobile_number': mobile})
        
        with self.app.app_context():
            otp_record = OTPCode.query.filter_by(mobile_number=mobile).first()
            otp_code = otp_record.otp_code
        
        login_response = self.client.post('/api/auth/verify-otp', 
                                        json={'mobile_number': mobile, 'otp_code': otp_code})
        token = json.loads(login_response.data)['token']
        
        # Update profile
        update_data = {
            'name': 'Updated Name',
            'email': 'updated@example.com',
            'gender': 'male'
        }
        
        response = self.client.put('/api/profile', 
                                 json=update_data,
                                 headers={'Authorization': f'Bearer {token}'})
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])


if __name__ == '__main__':
    unittest.main()