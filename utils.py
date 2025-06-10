import os
import uuid
import json
import qrcode
from io import BytesIO
import base64
from werkzeug.utils import secure_filename
from PIL import Image
import logging

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp3', 'wav', 'ogg', 'm4a'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, filename):
    """Save uploaded file to the uploads directory"""
    try:
        upload_folder = os.environ.get("UPLOAD_FOLDER", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        logger.info(f"File saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise

def generate_qr_code(data):
    """Generate QR code for the given data"""
    try:
        # Convert data to JSON string
        qr_data = json.dumps(data) if isinstance(data, dict) else str(data)
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        img_buffer = BytesIO()
        qr_image.save(img_buffer, format='PNG')
        img_str = base64.b64encode(img_buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        return None

def validate_mobile_number(mobile_number):
    """Validate mobile number format"""
    import re
    
    # Remove any non-digit characters
    cleaned_number = re.sub(r'\D', '', mobile_number)
    
    # Check if it's a valid Indian mobile number (10 digits starting with 6-9)
    if len(cleaned_number) == 10 and cleaned_number[0] in '6789':
        return True
    
    # Check if it's a valid international number (with country code)
    if len(cleaned_number) >= 10 and len(cleaned_number) <= 15:
        return True
    
    return False

def validate_email(email):
    """Validate email format"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def generate_unique_filename(original_filename):
    """Generate unique filename while preserving extension"""
    name, ext = os.path.splitext(original_filename)
    unique_name = f"{uuid.uuid4()}_{secure_filename(name)}{ext}"
    return unique_name

def compress_image(image_path, max_size=(800, 800), quality=85):
    """Compress image file"""
    try:
        with Image.open(image_path) as img:
            # Convert RGBA to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with compression
            img.save(image_path, 'JPEG', quality=quality, optimize=True)
            
        logger.info(f"Image compressed: {image_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error compressing image {image_path}: {str(e)}")
        return False

def calculate_age(birth_date):
    """Calculate age from birth date"""
    try:
        from datetime import date
        
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        
        today = date.today()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        
        return age
        
    except Exception as e:
        logger.error(f"Error calculating age: {str(e)}")
        return None

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def sanitize_filename(filename):
    """Sanitize filename for safe storage"""
    import re
    
    # Remove any path components
    filename = os.path.basename(filename)
    
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext

def generate_otp_code(length=6):
    """Generate numeric OTP code"""
    import random
    import string
    
    return ''.join(random.choices(string.digits, k=length))

def hash_sensitive_data(data):
    """Hash sensitive data for logging/storage"""
    import hashlib
    
    return hashlib.sha256(str(data).encode()).hexdigest()[:8]

def validate_date_format(date_string, format_string='%Y-%m-%d'):
    """Validate date string format"""
    try:
        from datetime import datetime
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False

def get_file_extension(filename):
    """Get file extension in lowercase"""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

def is_image_file(filename):
    """Check if file is an image"""
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    return get_file_extension(filename) in image_extensions

def is_audio_file(filename):
    """Check if file is an audio file"""
    audio_extensions = {'mp3', 'wav', 'ogg', 'm4a', 'aac', 'flac'}
    return get_file_extension(filename) in audio_extensions

def is_document_file(filename):
    """Check if file is a document"""
    document_extensions = {'pdf', 'doc', 'docx', 'txt', 'rtf'}
    return get_file_extension(filename) in document_extensions

def create_response(success=True, message="", data=None, status_code=200):
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message
    }
    
    if data:
        response.update(data)
    
    return response, status_code

def log_api_request(endpoint, user_id=None, ip_address=None, user_agent=None):
    """Log API request for monitoring"""
    try:
        log_data = {
            "endpoint": endpoint,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"API Request: {json.dumps(log_data)}")
        
    except Exception as e:
        logger.error(f"Error logging API request: {str(e)}")

def mask_sensitive_info(text, patterns=None):
    """Mask sensitive information in text"""
    import re
    
    if patterns is None:
        patterns = [
            (r'\b\d{10}\b', 'XXXXXXXXXX'),  # Phone numbers
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'email@masked.com'),  # Emails
            (r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b', 'XXXX XXXX XXXX XXXX'),  # Credit card numbers
        ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    
    return text
