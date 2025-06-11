# PHR Healthcare API

A comprehensive Personal Health Records (PHR) backend API system built with Flask and PostgreSQL, featuring HMIS integration and AI-powered health services.

## Features

- **Multi-factor Authentication**: OTP, Email, and ABHA ID login
- **Doctor Management**: Search, booking, and availability management
- **AI-Powered Health Services**: Symptom analysis, voice transcription, and medical record summarization using Google Gemini
- **Document Management**: Secure upload, storage, and HMIS integration
- **Medicine Tracking**: Smart reminders and prescription management
- **Lab Services**: Test booking and result management
- **Emergency Services**: Ambulance booking and emergency notifications
- **Care Packages**: Health monitoring and wellness programs
- **Peer Support**: Anonymous chat for mental health support

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Google Gemini API Key (for AI features)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd phr-healthcare-api
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Initialize the database**
```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE phr_healthcare_db;"

# Run DDL scripts
psql -U postgres -d phr_healthcare_db -f database_schema.sql
```

5. **Start the application**
```bash
python main.py
```

The API will be available at `http://localhost:5000`

## API Documentation

Interactive Swagger documentation is available at: `http://localhost:5000/api/docs`

### Authentication

All protected endpoints require JWT authentication. Obtain a token using one of these methods:

1. **Mobile OTP Authentication**
```bash
# Request OTP
curl -X POST http://localhost:5000/api/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "9876543210"}'

# Verify OTP
curl -X POST http://localhost:5000/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"mobile_number": "9876543210", "otp_code": "123456"}'
```

2. **Email Authentication**
```bash
curl -X POST http://localhost:5000/api/auth/login-email \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

3. **ABHA ID Authentication**
```bash
curl -X POST http://localhost:5000/api/auth/login-abha \
  -H "Content-Type: application/json" \
  -d '{"abha_id": "12-3456-7890-1234"}'
```

### Using JWT Token

Include the token in the Authorization header:
```bash
curl -X GET http://localhost:5000/api/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Core API Endpoints

### Authentication
- `POST /api/auth/request-otp` - Request OTP for mobile number
- `POST /api/auth/verify-otp` - Verify OTP and login
- `POST /api/auth/login-email` - Login with email/password
- `POST /api/auth/login-abha` - Login with ABHA ID

### Profile Management
- `GET /api/profile` - Get user profile
- `PUT /api/profile` - Update user profile
- `GET /api/profile/qr-code` - Generate QR code for profile
- `POST /api/profile/share` - Share profile with hospital

### Doctor & Appointments
- `GET /api/doctors` - List doctors with filtering
- `GET /api/doctors/{id}/availability` - Get doctor availability
- `POST /api/appointments` - Book appointment
- `GET /api/appointments` - Get user appointments

### Symptom Checker
- `GET /api/symptoms` - List available symptoms
- `POST /api/symptom-assessment` - Create symptom assessment
- `POST /api/symptom-assessment/audio` - Upload audio for analysis

### Document Management
- `POST /api/documents` - Upload document
- `GET /api/documents` - List user documents
- `GET /api/documents/{id}/download` - Download document
- `POST /api/records/summarize` - AI-powered record summary

### Medicine Management
- `POST /api/prescriptions/upload` - Upload prescription image
- `POST /api/medicine-tracker` - Add medicine to tracker
- `GET /api/medicine-tracker` - Get medicine tracker

### Lab Services
- `GET /api/lab-tests` - List available lab tests
- `POST /api/lab-bookings` - Book lab tests

### Care & Support
- `GET /api/care-packages` - List care packages
- `POST /api/care-packages/{id}/apply` - Apply for care package
- `GET /api/ambulance-services` - List ambulance services
- `POST /api/ambulance/book` - Book ambulance
- `POST /api/peer-support/messages` - Send peer support message
- `GET /api/peer-support/messages` - Get peer support messages

### Notifications
- `GET /api/notifications` - Get user notifications

## HMIS Integration

The system integrates with Hospital Management Information Systems (HMIS) through standardized APIs:

### Assumed HMIS API Specifications

#### Doctor Search
```
GET /doctors/search
Parameters:
  - specialty: string (optional)
  - name: string (optional)
Response:
{
  "doctors": [
    {
      "id": "string",
      "name": "string",
      "specialty": "string",
      "qualification": "string",
      "experience_years": number,
      "hospital_name": "string",
      "consultation_fee": number,
      "rating": number,
      "profile_image": "string"
    }
  ]
}
```

#### Doctor Availability
```
GET /doctors/{id}/availability
Parameters:
  - date: string (YYYY-MM-DD)
Response:
{
  "available_slots": ["09:00", "10:00", "11:00", "14:00"]
}
```

#### Appointment Booking
```
POST /appointments/book
Body:
{
  "patient_id": "string",
  "patient_name": "string",
  "patient_mobile": "string",
  "doctor_id": "string",
  "appointment_date": "string",
  "appointment_time": "string",
  "symptoms": "string",
  "booked_via": "phr_app"
}
Response:
{
  "appointment_id": "string",
  "confirmation_number": "string"
}
```

#### Profile Sharing
```
POST /patients/share-profile
Body:
{
  "patient_id": "string",
  "name": "string",
  "mobile_number": "string",
  "email": "string",
  "date_of_birth": "string",
  "gender": "string",
  "address": "string",
  "emergency_contact": "string",
  "hospital_id": "string",
  "shared_at": "string"
}
Response:
{
  "share_token": "string"
}
```

#### Document Upload (from HMIS to PHR)
```
POST /phr/documents/upload
Body:
{
  "patient_id": "string",
  "document_type": "string",
  "title": "string",
  "file_content": "string (base64)",
  "file_type": "string",
  "hospital_id": "string",
  "doctor_name": "string"
}
```

### HMIS Configuration

Configure HMIS integration in your `.env` file:
```
HMIS_BASE_URL=https://your-hmis-api.com
HMIS_API_KEY=your_hmis_api_key
```

## Database Schema

The system uses PostgreSQL with the following key tables:

- **users** - User profiles and authentication
- **otp_codes** - OTP verification codes
- **doctors** - Doctor information and availability
- **appointments** - Appointment bookings
- **symptoms** - Symptom catalog
- **symptom_assessments** - AI-powered symptom analysis
- **documents** - Document storage metadata
- **prescriptions** - Prescription management
- **medicine_tracker** - Medicine reminders
- **lab_tests** - Available lab tests
- **lab_bookings** - Lab test bookings
- **notifications** - User notifications
- **care_packages** - Health care packages
- **ambulance_services** - Emergency services
- **chat_messages** - Peer support chat

All tables include:
- `id` (UUID primary key)
- `created_at` (timestamp)
- `updated_at` (timestamp, where applicable)
- `is_deleted` (soft delete flag, where applicable)

See `database_schema.sql` for complete DDL.

## AI Services

### Google Gemini Integration

The system uses Google Gemini for:
- Audio transcription for symptom reporting
- Symptom analysis and recommendations
- Medical record summarization
- Prescription image analysis

Configure Gemini API:
```
GEMINI_API_KEY=your_gemini_api_key
```

### Error Handling

All AI services include robust error handling:
- Automatic fallback responses when AI is unavailable
- Comprehensive logging of all failures
- Graceful degradation of features

## Testing

Run the test suite:
```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_auth.py
```

## Deployment

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Application Configuration
SESSION_SECRET=your_super_secret_session_key_here
JWT_SECRET_KEY=your_jwt_secret_key_here
FLASK_ENV=production
FLASK_DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key

# HMIS Integration
HMIS_BASE_URL=https://your-hmis-api.com
HMIS_API_KEY=your_hmis_api_key

# SMS Service (for OTP)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800
```

### Production Deployment

1. **Using Gunicorn** (recommended)
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

2. **Using Docker**
```bash
docker build -t phr-api .
docker run -p 5000:5000 --env-file .env phr-api
```

3. **Using systemd**
Create `/etc/systemd/system/phr-api.service`:
```ini
[Unit]
Description=PHR Healthcare API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/phr-api
Environment=PATH=/path/to/phr-api/venv/bin
ExecStart=/path/to/phr-api/venv/bin/gunicorn --bind 0.0.0.0:5000 main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

## Security Considerations

- All sensitive data is encrypted at rest
- JWT tokens include expiration and refresh mechanisms
- File uploads are validated and sanitized
- SQL injection protection through SQLAlchemy ORM
- CORS configuration for web client integration
- Rate limiting on authentication endpoints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@phr-healthcare.com
- Documentation: [API Docs](http://localhost:5000/api/docs)

## Changelog

### Version 1.0.0
- Initial release with complete PHR functionality
- HMIS integration capabilities
- AI-powered health services
- Comprehensive API documentation