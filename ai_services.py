import os
import logging
from datetime import datetime
import json
import time
import functools

# Import Google Gemini client
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
except ImportError:
    genai = None
    HarmCategory = None
    HarmBlockThreshold = None
    logging.warning("Google Generative AI library not installed. AI features will be limited.")

logger = logging.getLogger(__name__)

# Configure Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "gemini_api_key")
GEMINI_REQUEST_TIMEOUT = int(os.environ.get("GEMINI_REQUEST_TIMEOUT", "60"))

if genai and GEMINI_API_KEY != "gemini_api_key":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Google Gemini AI configured successfully")
    except Exception as e:
        logger.error(f"Failed to configure Google Gemini AI: {str(e)}")
        genai = None

def retry_on_failure(max_retries=3, delay=1):
    """Decorator for retrying AI operations with exponential backoff"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (2 ** attempt)
                        logger.warning(f"AI operation failed (attempt {attempt + 1}/{max_retries}): {str(e)}. Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"AI operation failed after {max_retries} attempts: {str(e)}")
            
            # Return fallback response on final failure
            return {
                "success": False,
                "message": f"AI service unavailable after {max_retries} attempts: {str(last_exception)}",
                "fallback": True
            }
        return wrapper
    return decorator

def log_ai_operation(operation_name):
    """Decorator for logging AI operations"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            logger.info(f"Starting AI operation: {operation_name}")
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"AI operation {operation_name} completed successfully in {duration:.2f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"AI operation {operation_name} failed after {duration:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator

def get_gemini_model(model_name='gemini-1.5-flash'):
    """Get configured Gemini model with safety settings"""
    if not genai:
        raise Exception("Google Generative AI not available")
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    } if HarmCategory and HarmBlockThreshold else None
    
    return genai.GenerativeModel(
        model_name=model_name,
        safety_settings=safety_settings
    )

@retry_on_failure(max_retries=3)
@log_ai_operation("audio_transcription")
def transcribe_audio(audio_file_path):
    """
    Transcribe audio file using Google Gemini API with robust error handling
    """
    if not genai:
        logger.error("Google Generative AI not available for audio transcription")
        return {
            "success": False,
            "message": "AI transcription service not available",
            "fallback": True
        }
    
    if not os.path.exists(audio_file_path):
        logger.error(f"Audio file not found: {audio_file_path}")
        return {
            "success": False,
            "message": "Audio file not found"
        }
    
    try:
        # Check file size and format
        file_size = os.path.getsize(audio_file_path)
        max_size = int(os.environ.get("AUDIO_RECORDING_MAX_SIZE", "50000000"))  # 50MB default
        
        if file_size > max_size:
            logger.error(f"Audio file too large: {file_size} bytes (max: {max_size})")
            return {
                "success": False,
                "message": "Audio file too large for processing"
            }
        
        # Upload audio file to Gemini
        logger.info(f"Uploading audio file: {audio_file_path} ({file_size} bytes)")
        audio_file = genai.upload_file(audio_file_path)
        
        # Use Gemini to transcribe the audio
        model = get_gemini_model()
        prompt = """
        Please transcribe this audio recording accurately. The audio contains a patient describing their symptoms.
        Provide only the transcription of what was said, without any additional commentary or interpretation.
        If the audio is unclear or inaudible, indicate that clearly.
        """
        
        response = model.generate_content([prompt, audio_file])
        
        if not response or not response.text:
            logger.error("Empty response from Gemini API during transcription")
            return {
                "success": False,
                "message": "No transcription generated"
            }
        
        transcription = response.text.strip()
        logger.info(f"Audio transcription completed: {len(transcription)} characters")
        
        return {
            "success": True,
            "transcription": transcription,
            "file_size": file_size,
            "processing_time": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error transcribing audio {audio_file_path}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"Transcription failed: {str(e)}"
        }

def analyze_symptoms(symptoms_list, questionnaire_responses=None, transcription=None):
    """
    Analyze symptoms using Google Gemini AI
    Returns recommended specialty, severity score, and insights
    """
    try:
        if not genai:
            # Fallback analysis without AI
            return {
                "recommended_specialty": "General Medicine",
                "severity_score": 5,
                "identified_symptoms": symptoms_list,
                "insights": "AI analysis not available. Please consult with a healthcare provider.",
                "ai_confidence": 0.0
            }
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare the prompt
        prompt = f"""
        You are a medical AI assistant helping to analyze patient symptoms. Based on the following information, provide a medical analysis:

        Symptoms reported: {symptoms_list}
        """
        
        if questionnaire_responses:
            prompt += f"\nQuestionnaire responses: {json.dumps(questionnaire_responses, indent=2)}"
        
        if transcription:
            prompt += f"\nPatient voice description: {transcription}"
        
        prompt += """

        Please provide a JSON response with the following structure:
        {
            "recommended_specialty": "Most appropriate medical specialty",
            "severity_score": "Number from 1-10 (1=minor, 10=emergency)",
            "identified_symptoms": ["list", "of", "symptoms", "identified"],
            "insights": "Brief analysis and recommendations",
            "urgency_level": "low/medium/high/emergency",
            "ai_confidence": "Confidence score 0.0-1.0",
            "differential_diagnosis": ["possible", "conditions"],
            "recommended_actions": ["immediate", "actions", "to", "take"]
        }

        IMPORTANT: This is for informational purposes only and should not replace professional medical advice.
        """
        
        response = model.generate_content(prompt)
        
        # Parse the AI response
        try:
            ai_analysis = json.loads(response.text)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            ai_analysis = {
                "recommended_specialty": "General Medicine",
                "severity_score": 5,
                "identified_symptoms": symptoms_list,
                "insights": response.text,
                "urgency_level": "medium",
                "ai_confidence": 0.7,
                "differential_diagnosis": [],
                "recommended_actions": ["Consult with a healthcare provider"]
            }
        
        return ai_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing symptoms: {str(e)}")
        # Return fallback analysis
        return {
            "recommended_specialty": "General Medicine",
            "severity_score": 5,
            "identified_symptoms": symptoms_list,
            "insights": f"Analysis error occurred: {str(e)}. Please consult with a healthcare provider.",
            "urgency_level": "medium",
            "ai_confidence": 0.0,
            "differential_diagnosis": [],
            "recommended_actions": ["Consult with a healthcare provider immediately"]
        }

def summarize_records(documents):
    """
    Summarize medical records using Google Gemini AI
    """
    try:
        if not genai:
            return {
                "success": False,
                "message": "Google Generative AI not available"
            }
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare document information for analysis
        documents_info = []
        for doc in documents:
            doc_info = {
                "title": doc.title,
                "type": doc.document_type,
                "date": doc.created_at.isoformat(),
                "file_type": doc.file_type
            }
            documents_info.append(doc_info)
        
        prompt = f"""
        You are a medical AI assistant tasked with summarizing a patient's medical records. 
        Based on the following document information, provide a comprehensive medical summary:

        Patient Documents:
        {json.dumps(documents_info, indent=2)}

        Please provide a JSON response with the following structure:
        {{
            "summary": "Comprehensive medical summary covering key findings, treatments, and health status",
            "insights": {{
                "key_diagnoses": ["list", "of", "main", "diagnoses"],
                "treatments": ["list", "of", "treatments", "received"],
                "medications": ["list", "of", "medications"],
                "test_results": ["summary", "of", "test", "results"],
                "health_trends": "Overall health trend analysis",
                "recommendations": ["list", "of", "recommendations"],
                "risk_factors": ["identified", "risk", "factors"],
                "follow_up_needed": ["areas", "requiring", "follow", "up"]
            }},
            "timeline": "Chronological overview of medical events",
            "red_flags": ["any", "concerning", "findings"],
            "ai_confidence": "Confidence score 0.0-1.0"
        }}

        Note: This summary is for informational purposes and should be reviewed by healthcare professionals.
        """
        
        response = model.generate_content(prompt)
        
        try:
            result = json.loads(response.text)
            return {
                "success": True,
                "summary": result.get("summary", "Summary generation completed"),
                "insights": result.get("insights", {}),
                "timeline": result.get("timeline", ""),
                "red_flags": result.get("red_flags", []),
                "ai_confidence": result.get("ai_confidence", 0.7)
            }
        except json.JSONDecodeError:
            return {
                "success": True,
                "summary": response.text,
                "insights": {},
                "timeline": "",
                "red_flags": [],
                "ai_confidence": 0.5
            }
        
    except Exception as e:
        logger.error(f"Error summarizing records: {str(e)}")
        return {
            "success": False,
            "message": f"Record summarization failed: {str(e)}"
        }

def analyze_prescription_image(image_path):
    """
    Analyze prescription image to extract medicine information using Google Gemini Vision
    """
    try:
        if not genai:
            return {
                "success": False,
                "message": "Google Generative AI not available"
            }
        
        # Upload image to Gemini
        image_file = genai.upload_file(image_path)
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = """
        Analyze this prescription image and extract the following information in JSON format:
        {
            "medicines": [
                {
                    "name": "Medicine name",
                    "dosage": "Dosage information",
                    "frequency": "How often to take",
                    "duration": "How long to take",
                    "instructions": "Special instructions"
                }
            ],
            "doctor_name": "Prescribing doctor's name",
            "date": "Prescription date",
            "patient_name": "Patient name if visible",
            "additional_instructions": "Any additional notes"
        }
        
        If any information is not clearly visible, mark it as "Not clear" or "Not visible".
        """
        
        response = model.generate_content([prompt, image_file])
        
        try:
            prescription_data = json.loads(response.text)
            return {
                "success": True,
                "prescription_data": prescription_data
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Could not parse prescription data",
                "raw_response": response.text
            }
        
    except Exception as e:
        logger.error(f"Error analyzing prescription image: {str(e)}")
        return {
            "success": False,
            "message": f"Prescription analysis failed: {str(e)}"
        }

def generate_health_insights(user_data, recent_documents, symptoms_history):
    """
    Generate personalized health insights based on user data and history
    """
    try:
        if not genai:
            return {
                "success": False,
                "message": "Google Generative AI not available"
            }
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are a health insights AI assistant. Based on the following patient information, 
        provide personalized health insights and recommendations:

        Patient Profile:
        - Age: {user_data.get('age', 'Not specified')}
        - Gender: {user_data.get('gender', 'Not specified')}
        - Medical History: {json.dumps(recent_documents, indent=2)}
        - Recent Symptoms: {json.dumps(symptoms_history, indent=2)}

        Please provide a JSON response with:
        {{
            "health_score": "Overall health score 1-100",
            "insights": {{
                "positive_trends": ["list", "of", "positive", "health", "trends"],
                "areas_of_concern": ["list", "of", "areas", "needing", "attention"],
                "lifestyle_recommendations": ["personalized", "lifestyle", "advice"],
                "preventive_measures": ["preventive", "health", "measures"],
                "monitoring_suggestions": ["what", "to", "monitor"]
            }},
            "risk_assessment": {{
                "low_risk": ["conditions", "with", "low", "risk"],
                "moderate_risk": ["conditions", "with", "moderate", "risk"],
                "high_risk": ["conditions", "with", "high", "risk"]
            }},
            "next_steps": ["recommended", "next", "actions"],
            "ai_confidence": "Confidence score 0.0-1.0"
        }}

        Focus on actionable insights and general wellness advice.
        """
        
        response = model.generate_content(prompt)
        
        try:
            insights = json.loads(response.text)
            return {
                "success": True,
                "insights": insights
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Could not parse health insights",
                "raw_response": response.text
            }
        
    except Exception as e:
        logger.error(f"Error generating health insights: {str(e)}")
        return {
            "success": False,
            "message": f"Health insights generation failed: {str(e)}"
        }
