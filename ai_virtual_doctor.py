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

# Import AI Voice Speaker
try:
    from .ai_voice_speaker import AIVoiceSpeakerTool
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False
    print("⚠️ AI Voice Speaker not available")

class AIVirtualDoctorInput(BaseModel):
    patient_info: dict = Field(..., description="Patient information")
    emergency_type: str = Field(..., description="Type of emergency")
    symptoms: str = Field(..., description="Patient symptoms")
    severity_level: str = Field(..., description="Emergency severity level")

class AIVirtualDoctorTool(BaseTool):
    name: str = "AI Virtual Doctor for Video Calls"
    description: str = "Create a fake AI doctor that appears in video calls and talks to patients using AI-generated scripts"
    args_schema: Type[BaseModel] = AIVirtualDoctorInput

    def _run(self, patient_info: dict, emergency_type: str, symptoms: str, severity_level: str) -> str:
        try:
            print("🤖 AI VIRTUAL DOCTOR TOOL ACTIVATED")
            
            # Generate AI doctor profile and avatar
            doctor_profile = self._generate_ai_doctor_profile(emergency_type, severity_level)
            
            # Generate conversation script for the AI doctor
            conversation_script = self._generate_conversation_script(patient_info, emergency_type, symptoms, severity_level)
            
            # Create video call setup with AI doctor
            video_call_setup = self._create_ai_doctor_video_call(doctor_profile, conversation_script)
            
            # Generate real-time conversation responses
            real_time_responses = self._generate_real_time_responses(patient_info, emergency_type, symptoms)
            
            # Determine if ambulance should be triggered
            ambulance_decision = self._evaluate_ambulance_need(severity_level, emergency_type, symptoms)
            
            # Initialize AI voice speaker for speaking capability
            voice_speaker = None
            if VOICE_AVAILABLE:
                voice_speaker = AIVoiceSpeakerTool()
                # Prepare the script for later use (when patient clicks call button)
                def _as_str(val):
                    if isinstance(val, list):
                        return '\n'.join(str(x) for x in val)
                    return str(val)
                script_parts = [
                    _as_str(conversation_script.get('opening_greeting', '')),
                    _as_str(conversation_script.get('immediate_support', '')),
                    _as_str(conversation_script.get('symptom_specific_advice', '')),
                    _as_str(conversation_script.get('personalized_tips', '')),
                ]
                # Add comforting statements as bullet points
                comforting = conversation_script.get('comforting_statements', [])
                if comforting:
                    script_parts.append('Here are some comforting thoughts:')
                    for s in comforting:
                        script_parts.append(f'- {s}')
                script_parts += [
                    _as_str(conversation_script.get('stress_relief', '')),
                    _as_str(conversation_script.get('next_steps', '')),
                    _as_str(conversation_script.get('ongoing_support', '')),
                    _as_str(conversation_script.get('closing_reassurance', ''))
                ]
                full_script = '\n'.join([s for s in script_parts if s])
                # Store the script for later use (when patient clicks call button)
                # DO NOT speak it immediately - wait for patient interaction
                print(f"📝 AI Doctor script prepared: {full_script[:80]}...")
                print(f"🗣️ Voice speaker ready - will speak when patient clicks call button")
            
            result = {
                "ai_doctor_created": True,
                "doctor_profile": doctor_profile,
                "conversation_script": conversation_script,
                "video_call_setup": video_call_setup,
                "real_time_responses": real_time_responses,
                "ambulance_decision": ambulance_decision,
                "voice_speaker_available": VOICE_AVAILABLE,
                "voice_speaker": voice_speaker is not None,
                "patient_name": patient_info.get('name', 'Unknown'),
                "emergency_type": emergency_type,
                "severity_level": severity_level,
                "timestamp": datetime.now().isoformat(),
                "ai_doctor_status": "READY_FOR_VIDEO_CALL_WITH_VOICE"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            print(f"❌ Error in AI virtual doctor setup: {e}")
            return json.dumps({
                "ai_doctor_created": False,
                "error": str(e),
                "message": "AI doctor setup failed. Please use phone consultation."
            })

    def _generate_ai_doctor_profile(self, emergency_type: str, severity_level: str) -> dict:
        """Generate AI doctor profile and avatar details"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            Create a professional AI doctor profile for emergency video consultation.
            
            EMERGENCY TYPE: {emergency_type}
            SEVERITY LEVEL: {severity_level}
            
            Generate a complete doctor profile including:
            1. Doctor name and credentials
            2. Specialization and experience
            3. Physical appearance (age, gender, professional look)
            4. Speaking style and tone
            5. Professional background
            6. Avatar description for video call
            
            Respond with ONLY a JSON object:
            {{
                "doctor_name": "Dr. [Name]",
                "credentials": "MD, Emergency Medicine",
                "specialization": "Emergency Medicine",
                "experience_years": "15+ years",
                "appearance": {{
                    "age": "45",
                    "gender": "Male/Female",
                    "professional_look": "description",
                    "avatar_style": "professional medical attire"
                }},
                "speaking_style": "calm, professional, reassuring",
                "background": "brief professional background",
                "avatar_description": "detailed description for video avatar"
            }}
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return self._get_fallback_doctor_profile()
                
        except Exception as e:
            print(f"Error generating AI doctor profile: {e}")
            return self._get_fallback_doctor_profile()

    def _generate_conversation_script(self, patient_info: dict, emergency_type: str, symptoms: str, severity_level: str) -> dict:
        """Generate AI doctor conversation script for video call"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            Create a concise, practical conversation script for an AI doctor in an emergency video consultation.
            
            PATIENT DATA:
            {json.dumps(patient_info, indent=2)}
            
            EMERGENCY TYPE: {emergency_type}
            SYMPTOMS: {symptoms}
            SEVERITY LEVEL: {severity_level}
            
            REQUIREMENTS:
            1. Use ALL patient information provided
            2. NO questions - only give specific, actionable advice
            3. Focus on practical tips for their exact symptoms
            4. Keep it concise and direct
            5. Provide 3-4 specific, actionable steps they can take right now
            
            EXAMPLE FOR FEVER/COLD:
            - Take paracetamol every 6 hours (if not allergic)
            - Drink warm fluids (tea, soup) every 2 hours
            - Rest in a cool, well-ventilated room
            - Monitor temperature every 4 hours
            
            EXAMPLE FOR CHEST PAIN:
            - Stay seated and avoid physical exertion
            - Take prescribed medications if available
            - Monitor breathing and heart rate
            - Have someone stay with you
            
            Generate a practical script with specific actions for their exact symptoms.
            
            Respond with ONLY this JSON format (no extra text):
            {{
                "opening_greeting": "Brief personalized greeting using patient name",
                "immediate_support": "2-3 specific, actionable steps for their exact symptoms",
                "symptom_specific_advice": "Practical advice based on their symptoms and medications",
                "personalized_tips": "Age and medical history specific recommendations",
                "comforting_statements": ["2-3 brief reassuring statements"],
                "stress_relief": "One specific breathing or relaxation technique",
                "next_steps": "Clear next steps (monitoring, when to seek help)",
                "ongoing_support": "How they will be monitored",
                "closing_reassurance": "Brief encouraging closing"
            }}
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            print(f"🤖 GEMINI RESPONSE: {result_text[:200]}...")
            
            # Clean up markdown formatting if present
            if result_text.startswith('```json'):
                result_text = result_text.replace('```json', '').replace('```', '').strip()
            elif result_text.startswith('```'):
                result_text = result_text.replace('```', '').strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError as e:
                print(f"❌ JSON PARSE ERROR: {e}")
                print(f"🔍 RAW RESPONSE: {result_text}")
                return self._get_fallback_conversation_script()
                
        except Exception as e:
            print(f"Error generating conversation script: {e}")
            return self._get_fallback_conversation_script()

    def _create_ai_doctor_video_call(self, doctor_profile: dict, conversation_script: dict) -> dict:
        """Create consultation setup with AI doctor avatar"""
        try:
            # AI doctor avatar setup
            avatar_setup = {
                "avatar_type": "AI_Generated_Doctor",
                "doctor_name": doctor_profile.get('doctor_name', 'Dr. AI Assistant'),
                "appearance": doctor_profile.get('appearance', {}),
                "professional_attire": True,
                "background": "Medical Office",
                "lighting": "Professional Medical Lighting"
            }
            
            # Consultation configuration (no video call link needed)
            consultation_config = {
                "ai_doctor_ready": True,
                "avatar_setup": avatar_setup,
                "conversation_script_loaded": True,
                "audio_enabled": True,
                "consultation_type": "Audio_Only",
                "service": "Text-to-Speech"
            }
            
            return consultation_config
            
        except Exception as e:
            print(f"Error creating AI doctor consultation: {e}")
            return {
                "ai_doctor_ready": False,
                "error": str(e)
            }

    def _generate_real_time_responses(self, patient_info: dict, emergency_type: str, symptoms: str) -> dict:
        """Generate real-time AI responses for dynamic conversation"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            Generate real-time AI doctor responses for emergency video consultation.
            
            PATIENT INFO: {json.dumps(patient_info, indent=2)}
            EMERGENCY TYPE: {emergency_type}
            SYMPTOMS: {symptoms}
            
            Create response templates for common patient interactions:
            1. Patient describes worsening symptoms
            2. Patient asks about medication
            3. Patient expresses fear or anxiety
            4. Patient asks about ambulance
            5. Patient describes new symptoms
            6. Patient asks about treatment options
            
            Respond with ONLY a JSON object:
            {{
                "worsening_symptoms": "AI response template",
                "medication_questions": "AI response template",
                "fear_anxiety": "AI response template",
                "ambulance_questions": "AI response template",
                "new_symptoms": "AI response template",
                "treatment_options": "AI response template",
                "general_reassurance": "AI response template"
            }}
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return self._get_fallback_responses()
                
        except Exception as e:
            print(f"Error generating real-time responses: {e}")
            return self._get_fallback_responses()

    def _evaluate_ambulance_need(self, severity_level: str, emergency_type: str, symptoms: str) -> dict:
        """Evaluate if ambulance should be triggered based on emergency assessment"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            Evaluate if an ambulance should be called based on emergency assessment.
            
            SEVERITY LEVEL: {severity_level}
            EMERGENCY TYPE: {emergency_type}
            SYMPTOMS: {symptoms}
            
            Determine ambulance need based on:
            1. Severity level (Critical/High/Medium/Low)
            2. Emergency type (Cardiac/Respiratory/Neurological/etc.)
            3. Specific symptoms
            4. Risk factors
            
            Respond with ONLY a JSON object:
            {{
                "ambulance_needed": true/false,
                "urgency_level": "Immediate/High/Medium/Low",
                "reasoning": "detailed explanation",
                "alternative_action": "what to do if no ambulance",
                "estimated_response_time": "time estimate",
                "recommendations": ["recommendation1", "recommendation2", ...]
            }}
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                return self._get_fallback_ambulance_decision(severity_level)
                
        except Exception as e:
            print(f"Error evaluating ambulance need: {e}")
            return self._get_fallback_ambulance_decision(severity_level)

    def _get_fallback_doctor_profile(self) -> dict:
        """Fallback AI doctor profile"""
        return {
            "doctor_name": "Dr. Sarah Chen",
            "credentials": "MD, Emergency Medicine",
            "specialization": "Emergency Medicine",
            "experience_years": "12 years",
            "appearance": {
                "age": "42",
                "gender": "Female",
                "professional_look": "Professional medical attire, calm demeanor",
                "avatar_style": "Professional medical professional"
            },
            "speaking_style": "calm, professional, reassuring",
            "background": "Board-certified emergency medicine physician with extensive experience in telemedicine",
            "avatar_description": "Professional female doctor in medical scrubs with a calm, reassuring presence"
        }

    def _get_fallback_conversation_script(self) -> dict:
        """Fallback conversation script - comprehensive and personalized with NO questions"""
        return {
            "opening_greeting": "Hello, I'm Dr. Sarah Chen. I can see from your medical information that you're experiencing symptoms and I want you to know that you're not alone. I'm here to help you feel better and provide immediate support.",
            "immediate_support": "Based on your symptoms and medical history, I want to give you some immediate comfort and guidance. You're doing the right thing by seeking help, and I'm here to support you through this.",
            "symptom_specific_advice": "For your current symptoms, here are some immediate steps you can take to feel better. Stay hydrated, rest comfortably, and try to remain calm. Your body is working to heal itself. If you're taking any medications, continue them as prescribed.",
            "personalized_tips": "Given your age and medical history, here are some specific tips: stay in a comfortable position, keep your environment calm and quiet, and avoid any activities that might worsen your symptoms. If you have any current medications, make sure to take them as directed.",
            "comforting_statements": [
                "You're safe and you're going to be okay.",
                "I'm monitoring your condition and will ensure you get the care you need.",
                "It's completely normal to feel anxious, but you're in good hands.",
                "We're taking your symptoms seriously and will provide the best care possible.",
                "Your medical history shows you're managing your health well, and that's a positive sign."
            ],
            "stress_relief": "Take deep breaths and try to relax. Focus on your breathing - inhale slowly for 4 counts, hold for 4, then exhale for 4. This will help calm your nervous system. Find a comfortable position and try to stay as relaxed as possible.",
            "next_steps": "I'll be monitoring your condition and will guide you through the next steps. You don't need to worry about anything - just focus on staying comfortable and following my guidance. Based on your symptoms, we'll determine the best course of action.",
            "ongoing_support": "I'll continue to monitor your progress and provide ongoing support. You're not alone in this, and I'm here to help you every step of the way. We'll work together to ensure you get the care you need.",
            "closing_reassurance": "Remember, you're doing great and you're going to be fine. I'm here for you, and we'll get through this together. Stay calm and trust that you're receiving the best care possible. Your health and safety are my top priorities."
        }

    def _get_fallback_responses(self) -> dict:
        """Fallback real-time responses - supportive and calming with NO questions"""
        return {
            "worsening_symptoms": "I understand you're feeling worse and that's concerning. Let me help you stay calm. I'm monitoring your condition and will provide immediate guidance. You're not alone in this.",
            "medication_questions": "I can see you're taking paracetamol, which is good for fever. Let me give you some specific advice about managing your symptoms safely and effectively.",
            "fear_anxiety": "It's completely normal to feel anxious right now. I want you to know that you're safe and I'm here to help you. Take deep breaths and try to relax - you're doing great.",
            "ambulance_questions": "I'm carefully monitoring your condition to determine the best care for you. Your safety is my absolute priority, and I'll ensure you get exactly what you need.",
            "new_symptoms": "Thank you for sharing that with me. I'm here to support you and provide guidance for managing these symptoms. You're doing the right thing by staying connected.",
            "treatment_options": "Based on your symptoms, I can provide you with specific, helpful guidance for managing your condition. Let me give you some immediate steps to feel better.",
            "general_reassurance": "You're in good hands and I'm here to support you. I'm monitoring your condition and will provide ongoing care. You don't need to worry - just focus on staying comfortable."
        }

    def _get_fallback_ambulance_decision(self, severity_level: str) -> dict:
        """Fallback ambulance decision"""
        if severity_level.lower() in ['critical', 'high']:
            return {
                "ambulance_needed": True,
                "urgency_level": "Immediate",
                "reasoning": "High severity emergency requires immediate medical attention",
                "alternative_action": "If ambulance unavailable, proceed to nearest emergency room immediately",
                "estimated_response_time": "5-10 minutes",
                "recommendations": ["Call emergency services immediately", "Stay calm and follow instructions", "Have someone stay with patient"]
            }
        else:
            return {
                "ambulance_needed": False,
                "urgency_level": "Medium",
                "reasoning": "Condition can be managed with telemedicine consultation",
                "alternative_action": "Continue video consultation and monitor symptoms",
                "estimated_response_time": "N/A",
                "recommendations": ["Continue consultation", "Monitor symptoms", "Seek in-person care if symptoms worsen"]
            }

    def make_ai_doctor_speak(self, text: str, doctor_profile: dict, context: str = "video consultation") -> dict:
        """Make the AI doctor speak during video call"""
        try:
            if not VOICE_AVAILABLE:
                return {
                    "speech_success": False,
                    "message": "Voice speaker not available",
                    "text": text
                }
            
            voice_speaker = AIVoiceSpeakerTool()
            result = voice_speaker._run(
                text_to_speak=text,
                doctor_profile=doctor_profile,
                conversation_context=context,
                urgency_level="normal"
            )
            
            return {
                "speech_success": True,
                "result": result,
                "text": text,
                "doctor": doctor_profile.get('doctor_name', 'Dr. AI Assistant')
            }
            
        except Exception as e:
            print(f"Error making AI doctor speak: {e}")
            return {
                "speech_success": False,
                "error": str(e),
                "text": text
            }

    def speak_immediate_response(self, text: str, doctor_name: str = "Dr. AI Assistant") -> dict:
        """Immediate speech response for real-time interactions"""
        try:
            if not VOICE_AVAILABLE:
                return {
                    "speech_success": False,
                    "message": "Voice speaker not available"
                }
            
            voice_speaker = AIVoiceSpeakerTool()
            result = voice_speaker.speak_immediate(text, doctor_name)
            
            return {
                "speech_success": True,
                "result": result,
                "text": text,
                "doctor": doctor_name
            }
            
        except Exception as e:
            print(f"Error in immediate speech response: {e}")
            return {
                "speech_success": False,
                "error": str(e),
                "text": text
            } 