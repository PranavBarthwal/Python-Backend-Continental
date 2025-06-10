import os
import random
import string
from datetime import datetime, timedelta
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app import db
from models import User, OTP
import logging

logger = logging.getLogger(__name__)

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def send_otp_sms(mobile_number, otp_code):
    """
    Send OTP via SMS - In production, integrate with SMS service provider
    For now, we'll just log the OTP (in production, this should be removed)
    """
    logger.info(f"OTP for {mobile_number}: {otp_code}")
    # In production, integrate with SMS service like Twilio, AWS SNS, etc.
    # Example: twilio_client.messages.create(to=mobile_number, body=f"Your OTP is: {otp_code}")
    return True

def request_otp(mobile_number):
    """Generate and send OTP for mobile number"""
    try:
        # Generate OTP
        otp_code = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)  # OTP expires in 10 minutes
        
        # Save OTP to database
        otp_record = OTP(
            mobile_number=mobile_number,
            otp_code=otp_code,
            expires_at=expires_at
        )
        db.session.add(otp_record)
        db.session.commit()
        
        # Send OTP via SMS
        if send_otp_sms(mobile_number, otp_code):
            return {"success": True, "message": "OTP sent successfully"}
        else:
            return {"success": False, "message": "Failed to send OTP"}
            
    except Exception as e:
        logger.error(f"Error requesting OTP: {str(e)}")
        db.session.rollback()
        return {"success": False, "message": "Failed to generate OTP"}

def verify_otp(mobile_number, otp_code):
    """Verify OTP and return user token"""
    try:
        # Find valid OTP
        otp_record = OTP.query.filter_by(
            mobile_number=mobile_number,
            otp_code=otp_code,
            is_used=False
        ).filter(
            OTP.expires_at > datetime.utcnow()
        ).first()
        
        if not otp_record:
            return {"success": False, "message": "Invalid or expired OTP"}
        
        # Mark OTP as used
        otp_record.is_used = True
        
        # Find or create user
        user = User.query.filter_by(mobile_number=mobile_number).first()
        if not user:
            user = User(
                mobile_number=mobile_number,
                name=f"User_{mobile_number[-4:]}",  # Temporary name
                is_verified=True
            )
            db.session.add(user)
        else:
            user.is_verified = True
        
        db.session.commit()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return {
            "success": True,
            "message": "OTP verified successfully",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "mobile_number": user.mobile_number,
                "email": user.email,
                "is_verified": user.is_verified
            }
        }
        
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        db.session.rollback()
        return {"success": False, "message": "Failed to verify OTP"}

def login_with_email(email, password):
    """Login with email and password"""
    try:
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            return {"success": False, "message": "Invalid email or password"}
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return {
            "success": True,
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "mobile_number": user.mobile_number,
                "email": user.email,
                "is_verified": user.is_verified
            }
        }
        
    except Exception as e:
        logger.error(f"Error during email login: {str(e)}")
        return {"success": False, "message": "Login failed"}

def login_with_abha(abha_id):
    """Login with ABHA ID"""
    try:
        user = User.query.filter_by(abha_id=abha_id).first()
        
        if not user:
            # In production, integrate with ABHA authentication system
            # For now, create a basic user record
            user = User(
                abha_id=abha_id,
                name=f"ABHA_User_{abha_id[-4:]}",
                mobile_number="",  # This should be fetched from ABHA system
                is_verified=True
            )
            db.session.add(user)
            db.session.commit()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        return {
            "success": True,
            "message": "ABHA login successful",
            "access_token": access_token,
            "user": {
                "id": user.id,
                "name": user.name,
                "mobile_number": user.mobile_number,
                "email": user.email,
                "abha_id": user.abha_id,
                "is_verified": user.is_verified
            }
        }
        
    except Exception as e:
        logger.error(f"Error during ABHA login: {str(e)}")
        db.session.rollback()
        return {"success": False, "message": "ABHA login failed"}

def get_current_user():
    """Get current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        return user
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        return None

def update_user_profile(user_data):
    """Update user profile information"""
    try:
        user = get_current_user()
        if not user:
            return {"success": False, "message": "User not authenticated"}
        
        # Update user fields
        if 'name' in user_data:
            user.name = user_data['name']
        if 'email' in user_data:
            user.email = user_data['email']
        if 'date_of_birth' in user_data:
            user.date_of_birth = datetime.strptime(user_data['date_of_birth'], '%Y-%m-%d').date()
        if 'gender' in user_data:
            user.gender = user_data['gender']
        if 'address' in user_data:
            user.address = user_data['address']
        if 'emergency_contact' in user_data:
            user.emergency_contact = user_data['emergency_contact']
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "name": user.name,
                "mobile_number": user.mobile_number,
                "email": user.email,
                "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
                "gender": user.gender,
                "address": user.address,
                "emergency_contact": user.emergency_contact
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        db.session.rollback()
        return {"success": False, "message": "Failed to update profile"}
