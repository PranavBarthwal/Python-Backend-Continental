from flask import Blueprint, render_template, jsonify
from flask_swagger_ui import get_swaggerui_blueprint
import json

swagger_bp = Blueprint('swagger', __name__)

# Swagger UI configuration
SWAGGER_URL = '/api/docs'
API_URL = '/api/swagger.json'

# Create Swagger UI blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "PHR Healthcare API",
        'layout': "BaseLayout",
        'deepLinking': True,
        'displayRequestDuration': True,
        'defaultModelsExpandDepth': 2,
        'defaultModelExpandDepth': 2,
        'docExpansion': 'none',
        'filter': True,
        'showExtensions': True,
        'showCommonExtensions': True,
        'supportedSubmitMethods': ['get', 'post', 'put', 'delete', 'patch'],
        'validatorUrl': None
    }
)

# Register the Swagger UI blueprint
swagger_bp.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@swagger_bp.route('/api/swagger.json')
def swagger_json():
    """Return Swagger JSON specification"""
    swagger_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "PHR Healthcare API",
            "description": "Comprehensive Personal Health Records (PHR) API system with HMIS integration and AI-powered features",
            "version": "1.0.0",
            "contact": {
                "name": "PHR API Support",
                "email": "support@phr-healthcare.com"
            }
        },
        "servers": [
            {
                "url": "/api",
                "description": "PHR API Server"
            }
        ],
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter JWT token obtained from authentication endpoints"
                }
            },
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "mobile_number": {"type": "string"},
                        "email": {"type": "string"},
                        "abha_id": {"type": "string"},
                        "date_of_birth": {"type": "string", "format": "date"},
                        "gender": {"type": "string"},
                        "address": {"type": "string"},
                        "emergency_contact": {"type": "string"},
                        "is_verified": {"type": "boolean"}
                    }
                },
                "Doctor": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "specialty": {"type": "string"},
                        "qualification": {"type": "string"},
                        "experience_years": {"type": "integer"},
                        "hospital_name": {"type": "string"},
                        "consultation_fee": {"type": "number"},
                        "rating": {"type": "number"},
                        "profile_image": {"type": "string"}
                    }
                },
                "Appointment": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "doctor_id": {"type": "string"},
                        "appointment_date": {"type": "string", "format": "date"},
                        "appointment_time": {"type": "string", "format": "time"},
                        "status": {"type": "string", "enum": ["scheduled", "completed", "cancelled"]},
                        "symptoms": {"type": "string"},
                        "consultation_type": {"type": "string", "enum": ["in-person", "video", "audio"]}
                    }
                },
                "Document": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "document_type": {"type": "string"},
                        "file_type": {"type": "string"},
                        "file_size": {"type": "integer"},
                        "uploaded_by": {"type": "string"},
                        "created_at": {"type": "string", "format": "date-time"}
                    }
                },
                "SuccessResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "message": {"type": "string"}
                    }
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean", "example": False},
                        "message": {"type": "string"}
                    }
                }
            }
        },
        "security": [],
        "paths": {
            "/auth/request-otp": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Request OTP for mobile number",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "mobile_number": {"type": "string", "example": "9876543210"}
                                    },
                                    "required": ["mobile_number"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "OTP sent successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/auth/verify-otp": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Verify OTP and login",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "mobile_number": {"type": "string", "example": "9876543210"},
                                        "otp_code": {"type": "string", "example": "123456"}
                                    },
                                    "required": ["mobile_number", "otp_code"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "OTP verified successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "access_token": {"type": "string"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/auth/login-email": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Login with email and password",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "example": "user@example.com"},
                                        "password": {"type": "string", "example": "password123"}
                                    },
                                    "required": ["email", "password"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "access_token": {"type": "string"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/auth/login-abha": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Login with ABHA ID",
                    "security": [],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "abha_id": {"type": "string", "example": "12-3456-7890-1234"}
                                    },
                                    "required": ["abha_id"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "ABHA login successful",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "access_token": {"type": "string"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/profile": {
                "get": {
                    "tags": ["Profile"],
                    "summary": "Get user profile",
                    "security": [{"bearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "User profile retrieved",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "user": {"$ref": "#/components/schemas/User"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "put": {
                    "tags": ["Profile"],
                    "summary": "Update user profile",
                    "security": [{"bearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/User"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Profile updated successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/profile/qr-code": {
                "get": {
                    "tags": ["Profile"],
                    "summary": "Generate QR code for user profile",
                    "responses": {
                        "200": {
                            "description": "QR code generated",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "qr_code_url": {"type": "string"},
                                            "profile_data": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/profile/share": {
                "post": {
                    "tags": ["Profile"],
                    "summary": "Share profile with hospital HMIS",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "hospital_id": {"type": "string"}
                                    },
                                    "required": ["hospital_id"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Profile shared successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/doctors": {
                "get": {
                    "tags": ["Doctors"],
                    "summary": "Get list of doctors",
                    "parameters": [
                        {
                            "name": "specialty",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Filter by specialty"
                        },
                        {
                            "name": "name",
                            "in": "query",
                            "schema": {"type": "string"},
                            "description": "Search by doctor name"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of doctors",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "doctors": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Doctor"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/doctors/{doctor_id}/availability": {
                "get": {
                    "tags": ["Doctors"],
                    "summary": "Get doctor availability",
                    "parameters": [
                        {
                            "name": "doctor_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "date",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "date"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Doctor availability",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "date": {"type": "string"},
                                            "available_slots": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/appointments": {
                "post": {
                    "tags": ["Appointments"],
                    "summary": "Book an appointment",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "doctor_id": {"type": "string"},
                                        "appointment_date": {"type": "string", "format": "date"},
                                        "appointment_time": {"type": "string", "format": "time"},
                                        "symptoms": {"type": "string"},
                                        "consultation_type": {"type": "string", "enum": ["in-person", "video", "audio"]}
                                    },
                                    "required": ["doctor_id", "appointment_date", "appointment_time"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Appointment booked successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "message": {"type": "string"},
                                            "appointment_id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "get": {
                    "tags": ["Appointments"],
                    "summary": "Get user appointments",
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["scheduled", "completed", "cancelled"]}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of appointments",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "appointments": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Appointment"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/symptoms": {
                "get": {
                    "tags": ["Symptom Checker"],
                    "summary": "Get list of symptoms",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of symptoms",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "symptoms": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/symptom-assessment": {
                "post": {
                    "tags": ["Symptom Checker"],
                    "summary": "Create symptom assessment",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "symptoms": {"type": "array", "items": {"type": "string"}},
                                        "questionnaire_responses": {"type": "object"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Assessment created",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "assessment_id": {"type": "string"},
                                            "ai_analysis": {"type": "object"},
                                            "recommended_specialty": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/symptom-assessment/audio": {
                "post": {
                    "tags": ["Symptom Checker"],
                    "summary": "Upload audio for symptom assessment",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "audio": {"type": "string", "format": "binary"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Audio processed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "transcription": {"type": "string"},
                                            "ai_analysis": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/documents": {
                "post": {
                    "tags": ["Document Management"],
                    "summary": "Upload a document",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {"type": "string", "format": "binary"},
                                        "document_type": {"type": "string"},
                                        "title": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Document uploaded",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                },
                "get": {
                    "tags": ["Document Management"],
                    "summary": "Get user documents",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of documents",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "documents": {
                                                "type": "array",
                                                "items": {"$ref": "#/components/schemas/Document"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/records/summarize": {
                "post": {
                    "tags": ["AI Services"],
                    "summary": "Summarize medical records using AI",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "summary_type": {"type": "string", "enum": ["all_records", "selected_records"]},
                                        "document_ids": {"type": "array", "items": {"type": "string"}}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Records summarized",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "summary": {"type": "string"},
                                            "insights": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/medicine-tracker": {
                "post": {
                    "tags": ["Medicine Management"],
                    "summary": "Add medicine to tracker",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "medicine_name": {"type": "string"},
                                        "dosage": {"type": "string"},
                                        "frequency": {"type": "string"},
                                        "timing": {"type": "array"},
                                        "start_date": {"type": "string", "format": "date"},
                                        "end_date": {"type": "string", "format": "date"}
                                    },
                                    "required": ["medicine_name", "dosage", "frequency", "timing", "start_date"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Medicine added to tracker",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                },
                "get": {
                    "tags": ["Medicine Management"],
                    "summary": "Get medicine tracker list",
                    "responses": {
                        "200": {
                            "description": "Medicine tracker list",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "medicine_trackers": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/lab-tests": {
                "get": {
                    "tags": ["Lab Tests"],
                    "summary": "Get available lab tests",
                    "parameters": [
                        {
                            "name": "category",
                            "in": "query",
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of lab tests",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "lab_tests": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/lab-bookings": {
                "post": {
                    "tags": ["Lab Tests"],
                    "summary": "Book lab tests",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "test_ids": {"type": "array", "items": {"type": "string"}},
                                        "doctor_id": {"type": "string"}
                                    },
                                    "required": ["test_ids"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Lab tests booked",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/notifications": {
                "get": {
                    "tags": ["Notifications"],
                    "summary": "Get user notifications",
                    "responses": {
                        "200": {
                            "description": "List of notifications",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "notifications": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/care-packages": {
                "get": {
                    "tags": ["Care Packages"],
                    "summary": "Get available care packages",
                    "responses": {
                        "200": {
                            "description": "List of care packages",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "care_packages": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/ambulance-services": {
                "get": {
                    "tags": ["Ambulance Services"],
                    "summary": "Get available ambulance services",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["emergency", "non_emergency"]}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of ambulance services",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "ambulance_services": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/ambulance-bookings": {
                "post": {
                    "tags": ["Ambulance Services"],
                    "summary": "Book ambulance service",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "ambulance_service_id": {"type": "string"},
                                        "pickup_location": {"type": "string"},
                                        "destination": {"type": "string"},
                                        "emergency_level": {"type": "string", "enum": ["high", "medium", "low"]},
                                        "patient_condition": {"type": "string"}
                                    },
                                    "required": ["ambulance_service_id", "pickup_location", "destination"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Ambulance booking requested",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/chat/peer-support": {
                "post": {
                    "tags": ["Mental Health"],
                    "summary": "Send message in peer support chat",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string"}
                                    },
                                    "required": ["message"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Message sent",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/SuccessResponse"}
                                }
                            }
                        }
                    }
                },
                "get": {
                    "tags": ["Mental Health"],
                    "summary": "Get peer support chat messages",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 50}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Chat messages",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "success": {"type": "boolean"},
                                            "messages": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    return jsonify(swagger_spec)

@swagger_bp.route('/')
def swagger_ui():
    """Render custom Swagger UI"""
    return render_template('swagger.html')
