import json
import os
import requests
import time
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import google.generativeai as genai
from model_config import get_model_with_retry
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"))

class VideoCallInput(BaseModel):
    patient_info: dict = Field(..., description="Patient information")
    emergency_type: str = Field(..., description="Type of emergency")
    ai_doctor_script: str = Field(..., description="AI-generated doctor script")

class VideoCallTool(BaseTool):
    name: str = "Emergency Video Call Coordinator"
    description: str = "Initiate emergency video calls with doctors using free video calling services"
    args_schema: Type[BaseModel] = VideoCallInput

    def _run(self, patient_info: dict, emergency_type: str, ai_doctor_script: str) -> str:
        try:
            print("📹 EMERGENCY VIDEO CALL TOOL ACTIVATED")
            
            # Check if this is a genuine emergency that requires AI virtual doctor
            is_emergency = self._verify_emergency_status(patient_info, emergency_type)
            
            if not is_emergency:
                return json.dumps({
                    "video_call_created": False,
                    "ai_virtual_doctor_activated": False,
                    "message": "No emergency detected. AI Virtual Doctor is only available for genuine emergencies.",
                    "recommended_action": "Continue with normal consultation workflow"
                })
            
            print("🚨 EMERGENCY CONFIRMED - ACTIVATING AI VIRTUAL DOCTOR")
            
            # Generate dynamic video call setup
            video_call_setup = self._generate_video_call_setup(patient_info, emergency_type, ai_doctor_script)
            
            # Create video call link using free service
            video_call_link = self._create_video_call_link(patient_info, emergency_type)
            
            # Generate doctor briefing
            doctor_briefing = self._generate_doctor_briefing(patient_info, emergency_type, ai_doctor_script)
            
            # Send real-time notifications to available doctors
            doctor_notifications = self._notify_available_doctors(patient_info, emergency_type, video_call_link)
            
            # Create real-time monitoring session
            monitoring_session = self._create_monitoring_session(patient_info, emergency_type)
            
            result = {
                "video_call_created": True,
                "ai_virtual_doctor_activated": True,
                "emergency_confirmed": True,
                "video_call_link": video_call_link,
                "doctor_briefing": doctor_briefing,
                "setup_instructions": video_call_setup,
                "doctor_notifications": doctor_notifications,
                "monitoring_session": monitoring_session,
                "emergency_type": emergency_type,
                "patient_name": patient_info.get('name', 'Unknown'),
                "timestamp": datetime.now().isoformat(),
                "real_time_status": "ACTIVE"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            print(f"❌ Error in video call setup: {e}")
            return json.dumps({
                "video_call_created": False,
                "error": str(e),
                "message": "Video call setup failed. Please use phone consultation."
            })

    def _generate_video_call_setup(self, patient_info: dict, emergency_type: str, ai_doctor_script: str) -> dict:
        """Generate dynamic video call setup instructions"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are an emergency medical coordinator setting up a video consultation.
            
            PATIENT INFO: {json.dumps(patient_info, indent=2)}
            EMERGENCY TYPE: {emergency_type}
            AI DOCTOR SCRIPT: {ai_doctor_script}
            
            Generate video call setup instructions including:
            1. Pre-call checklist
            2. Technical requirements
            3. Patient preparation
            4. Emergency protocols
            5. Backup communication methods
            
            Respond with ONLY a JSON object:
            {{
                "pre_call_checklist": ["item1", "item2", ...],
                "technical_requirements": ["requirement1", "requirement2", ...],
                "patient_preparation": "detailed instructions",
                "emergency_protocols": ["protocol1", "protocol2", ...],
                "backup_methods": ["method1", "method2", ...]
            }}
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return self._get_fallback_setup()
                
        except Exception as e:
            print(f"Error generating video call setup: {e}")
            return self._get_fallback_setup()

    def _create_video_call_link(self, patient_info: dict, emergency_type: str) -> str:
        """Create video call link using free services"""
        try:
            # Use free video calling services
            # Options: Google Meet, Zoom (free tier), Jitsi Meet, Whereby
            
            # For demo, we'll use Jitsi Meet (completely free)
            meeting_id = f"emergency-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            patient_name = patient_info.get('name', 'Patient').replace(' ', '')
            
            # Jitsi Meet URL (free, no registration required)
            jitsi_url = f"https://meet.jit.si/{meeting_id}"
            
            # Alternative: Google Meet (requires Google account but free)
            # google_meet_url = f"https://meet.google.com/{meeting_id}"
            
            # Alternative: Zoom (free tier, requires account)
            # zoom_url = f"https://zoom.us/j/{meeting_id}"
            
            return {
                "primary_url": jitsi_url,
                "meeting_id": meeting_id,
                "service": "Jitsi Meet (Free)",
                "alternatives": {
                    "google_meet": f"https://meet.google.com/{meeting_id}",
                    "zoom": f"https://zoom.us/j/{meeting_id}",
                    "whereby": f"https://whereby.com/{meeting_id}"
                },
                "instructions": "Click the link to join the emergency video consultation. No registration required."
            }
            
        except Exception as e:
            print(f"Error creating video call link: {e}")
            return {
                "primary_url": "https://meet.jit.si/emergency-consultation",
                "service": "Jitsi Meet (Fallback)",
                "error": str(e)
            }

    def _generate_doctor_briefing(self, patient_info: dict, emergency_type: str, ai_doctor_script: str) -> str:
        """Generate briefing for the doctor joining the video call"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are preparing a briefing for an emergency medicine doctor joining a video consultation.
            
            PATIENT INFORMATION:
            {json.dumps(patient_info, indent=2)}
            
            EMERGENCY TYPE: {emergency_type}
            
            AI GENERATED SCRIPT:
            {ai_doctor_script}
            
            Create a concise medical briefing for the doctor including:
            1. Patient demographics and vital information
            2. Presenting symptoms and emergency type
            3. Key medical history points
            4. Immediate concerns and priorities
            5. Suggested initial assessment approach
            
            Format as a professional medical briefing.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating doctor briefing: {e}")
            return f"""
            EMERGENCY MEDICAL BRIEFING
            
            Patient: {patient_info.get('name', 'Unknown')}
            Age: {patient_info.get('age', 'Unknown')}
            Emergency Type: {emergency_type}
            Symptoms: {patient_info.get('symptoms', 'Unknown')}
            
            Please assess patient immediately upon joining video call.
            """

    def _verify_emergency_status(self, patient_info: dict, emergency_type: str) -> bool:
        """Verify if this is a genuine emergency that requires AI virtual doctor"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are an emergency medical coordinator. Verify if this situation requires an AI Virtual Doctor.
            
            PATIENT INFO: {json.dumps(patient_info, indent=2)}
            EMERGENCY TYPE: {emergency_type}
            
            AI VIRTUAL DOCTOR SHOULD ONLY APPEAR FOR CRITICAL LIFE-THREATENING EMERGENCIES:
            - Cardiac arrest or severe heart attack
            - Severe stroke or neurological emergency
            - Severe respiratory distress or breathing failure
            - Unconsciousness or severe altered mental status
            - Severe trauma with life-threatening bleeding
            - Anaphylactic shock or severe allergic reaction
            - Severe overdose or poisoning with critical symptoms
            - Severe burns or electrical injuries
            - Drowning or near-drowning incidents
            - Severe pediatric emergencies
            - Critical obstetric emergencies
            - Severe psychiatric emergencies (suicide risk)
            
            AI VIRTUAL DOCTOR SHOULD NOT APPEAR FOR:
            - Routine consultations and checkups
            - Mild symptoms (cold, minor fever, headache)
            - Non-urgent health questions
            - Follow-up appointments
            - General health advice
            - Minor injuries or pain
            - Chronic condition management
            - Preventive care
            - Medication refills
            - Lab results discussion
            
            Respond with ONLY a JSON object:
            {{
                "is_emergency": true/false,
                "ai_virtual_doctor_justified": true/false,
                "reasoning": "explanation",
                "recommended_action": "what should happen"
            }}
            
            CRITICAL: Be very strict. Only activate AI Virtual Doctor for genuine life-threatening emergencies that require immediate medical intervention.
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                result = json.loads(result_text)
                is_emergency = result.get("is_emergency", False)
                ai_doctor_justified = result.get("ai_virtual_doctor_justified", False)
                
                print(f"📹 Emergency Verification: {is_emergency}, AI Doctor Justified: {ai_doctor_justified}")
                print(f"📋 Reasoning: {result.get('reasoning', 'No reasoning provided')}")
                
                return is_emergency and ai_doctor_justified
                
            except json.JSONDecodeError:
                # Fallback: check emergency type keywords
                emergency_keywords = ['cardiac', 'stroke', 'respiratory', 'trauma', 'allergic', 'toxicology', 'obstetric', 'pediatric', 'psychiatric', 'critical', 'severe']
                return any(keyword in emergency_type.lower() for keyword in emergency_keywords)
                
        except Exception as e:
            print(f"Error verifying emergency status: {e}")
            # Fallback: check emergency type keywords
            emergency_keywords = ['cardiac', 'stroke', 'respiratory', 'trauma', 'allergic', 'toxicology', 'obstetric', 'pediatric', 'psychiatric', 'critical', 'severe']
            return any(keyword in emergency_type.lower() for keyword in emergency_keywords)

    def _get_fallback_setup(self) -> dict:
        """Fallback video call setup if AI generation fails"""
        return {
            "pre_call_checklist": [
                "Ensure stable internet connection",
                "Test camera and microphone",
                "Have patient in well-lit area",
                "Prepare emergency contact numbers",
                "Have patient's medical information ready"
            ],
            "technical_requirements": [
                "Web browser (Chrome, Firefox, Safari)",
                "Camera and microphone",
                "Stable internet connection",
                "Quiet environment"
            ],
            "patient_preparation": "Have patient sit comfortably in a well-lit area. Ensure they can be seen clearly on camera. Have any medications or medical devices nearby.",
            "emergency_protocols": [
                "If video call fails, use phone consultation",
                "If patient condition worsens, call emergency services immediately",
                "Keep emergency contacts readily available",
                "Monitor patient throughout consultation"
            ],
            "backup_methods": [
                "Phone consultation",
                "Text messaging",
                "Emergency services direct call",
                "Local hospital contact"
            ]
        } 

    def _notify_available_doctors(self, patient_info: dict, emergency_type: str, video_call_link: dict) -> dict:
        """Setup AI virtual doctor for video call"""
        try:
            # Import AI virtual doctor tool
            from .ai_virtual_doctor import AIVirtualDoctorTool
            
            # Create AI virtual doctor instance
            ai_doctor_tool = AIVirtualDoctorTool()
            
            # Get patient symptoms
            symptoms = patient_info.get('symptoms', 'Unknown symptoms')
            severity_level = patient_info.get('severity_level', 'Medium')
            
            # Generate AI doctor setup
            ai_doctor_result = ai_doctor_tool._run(
                patient_info=patient_info,
                emergency_type=emergency_type,
                symptoms=symptoms,
                severity_level=severity_level
            )
            
            # Parse the result
            ai_doctor_data = json.loads(ai_doctor_result)
            
            if ai_doctor_data.get('ai_doctor_created', False):
                return {
                    "ai_doctor_ready": True,
                    "doctor_profile": ai_doctor_data.get('doctor_profile', {}),
                    "conversation_script": ai_doctor_data.get('conversation_script', {}),
                    "video_call_link": video_call_link['primary_url'],
                    "emergency_type": emergency_type,
                    "ambulance_decision": ai_doctor_data.get('ambulance_decision', {}),
                    "status": "AI Virtual Doctor ready for video call"
                }
            else:
                return {
                    "ai_doctor_ready": False,
                    "status": "AI doctor setup failed",
                    "error": ai_doctor_data.get('error', 'Unknown error')
                }
                
        except Exception as e:
            print(f"Error setting up AI virtual doctor: {e}")
            return {
                "ai_doctor_ready": False,
                "status": f"Error: {str(e)}"
            }

    def _create_monitoring_session(self, patient_info: dict, emergency_type: str) -> dict:
        """Create real-time monitoring session for the emergency"""
        try:
            session_id = f"emergency-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            monitoring_session = {
                "session_id": session_id,
                "patient_name": patient_info.get('name'),
                "emergency_type": emergency_type,
                "start_time": datetime.now().isoformat(),
                "status": "ACTIVE",
                "monitoring_interval": "30 seconds",
                "vital_signs_tracking": True,
                "alert_thresholds": {
                    "heart_rate": {"min": 60, "max": 100},
                    "blood_pressure": {"min": 90, "max": 140},
                    "respiratory_rate": {"min": 12, "max": 20},
                    "oxygen_saturation": {"min": 95, "max": 100}
                },
                "real_time_updates": True
            }
            
            # Save monitoring session to file
            self._save_monitoring_session(monitoring_session)
            
            return monitoring_session
            
        except Exception as e:
            print(f"Error creating monitoring session: {e}")
            return {
                "session_id": "error",
                "status": "FAILED",
                "error": str(e)
            }

    def _save_monitoring_session(self, session_data: dict):
        """Save monitoring session data"""
        try:
            filename = f"monitoring_session_{session_data['session_id']}.json"
            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)
            print(f"✅ Monitoring session saved: {filename}")
        except Exception as e:
            print(f"⚠️ Could not save monitoring session: {e}") 