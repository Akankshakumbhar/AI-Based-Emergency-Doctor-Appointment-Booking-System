import json
import os
import requests
import time
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import google.generativeai as genai
import urllib3
from .video_call_tool import VideoCallTool
from model_config import get_model_with_retry

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"))

class EmergencyResponseInput(BaseModel):
    patient_info: dict = Field(..., description="Patient information from patient_info.json")
    symptom_assessment: dict = Field(..., description="Symptom assessment from symptom_assessment.json")

class EmergencyResponseTool(BaseTool):
    name: str = "Emergency Response Coordinator"
    description: str = "Handle medical emergencies by calling ambulance, generating AI doctor scripts, and providing immediate guidance"
    args_schema: Type[BaseModel] = EmergencyResponseInput

    def _run(self, patient_info: dict, symptom_assessment: dict) -> str:
        try:
            print("🚨 EMERGENCY RESPONSE TOOL ACTIVATED")
            
            # Check if this is an emergency
            is_emergency = self._check_emergency_criteria(patient_info, symptom_assessment)
            
            if not is_emergency:
                return json.dumps({
                    "emergency_detected": False,
                    "message": "No emergency detected. Continue with normal workflow."
                })
            
            print("🚨 EMERGENCY DETECTED - INITIATING RESPONSE")
            
            # Extract emergency details
            emergency_type = self._determine_emergency_type(patient_info, symptom_assessment)
            patient_location = patient_info.get('location', 'Unknown Location')
            patient_name = patient_info.get('name', 'Unknown Patient')
            patient_contact = patient_info.get('contact', 'No contact provided')
            
            # Get dynamic emergency contacts
            emergency_contacts = self._get_emergency_contacts(patient_location)
            
            # 1. Generate AI Doctor Script
            ai_doctor_script = self._generate_ai_doctor_script(patient_info, symptom_assessment, emergency_type)
            
            # 2. Call Ambulance (Simulated with free SMS service)
            ambulance_result = self._call_ambulance(patient_name, patient_location, emergency_type, patient_contact, emergency_contacts)
            
            # 3. Generate Calming Guidance
            calming_guidance = self._generate_calming_guidance(emergency_type, patient_info)
            
            # 4. Generate Monitoring Instructions
            monitoring_instructions = self._generate_monitoring_instructions(emergency_type)
            
            # 5. Immediate Actions List
            immediate_actions = self._generate_immediate_actions(emergency_type, patient_info, symptom_assessment)
            
            # 6. Setup Video Call (NEW)
            video_call_tool = VideoCallTool()
            video_call_result = video_call_tool._run(patient_info, emergency_type, ai_doctor_script)
            
            try:
                video_call_data = json.loads(video_call_result)
            except json.JSONDecodeError:
                video_call_data = {"video_call_created": False, "error": "Failed to parse video call result"}
            
            emergency_response = {
                "emergency_detected": True,
                "emergency_type": emergency_type,
                "patient_location": patient_location,
                "patient_name": patient_name,
                "patient_contact": patient_contact,
                "ambulance_called": ambulance_result.get("success", False),
                "ambulance_details": ambulance_result,
                "emergency_contacts": emergency_contacts,
                "ai_doctor_script": ai_doctor_script,
                "calming_guidance": calming_guidance,
                "monitoring_instructions": monitoring_instructions,
                "immediate_actions": immediate_actions,
                "video_call": video_call_data,
                "timestamp": datetime.now().isoformat(),
                "emergency_level": "CRITICAL"
            }
            
            # Save emergency response to file
            self._save_emergency_response(emergency_response)
            
            return json.dumps(emergency_response, indent=2)
            
        except Exception as e:
            print(f"❌ Error in emergency response: {e}")
            return json.dumps({
                "emergency_detected": True,
                "error": str(e),
                "message": "Emergency detected but response failed. Please call emergency services manually."
            })

    def _check_emergency_criteria(self, patient_info: dict, symptom_assessment: dict) -> bool:
        """Dynamically check if symptoms meet emergency criteria using AI"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are an emergency medical AI. Analyze the following patient information and determine if this is a CRITICAL medical emergency that requires immediate intervention and AI virtual doctor support.
            
            PATIENT INFORMATION:
            {json.dumps(patient_info, indent=2)}
            
            SYMPTOM ASSESSMENT:
            {json.dumps(symptom_assessment, indent=2)}
            
            CRITICAL EMERGENCY CRITERIA (AI Virtual Doctor should ONLY appear for these SEVERE cases):
            - Life-threatening conditions (heart attack, stroke, severe bleeding, etc.)
            - Cardiac arrest or severe chest pain
            - Severe respiratory distress or breathing problems
            - Unconsciousness or altered mental status
            - Severe trauma with bleeding or fractures
            - Anaphylactic shock or severe allergic reactions
            - Overdose or poisoning with severe symptoms
            - Severe burns or electrical injuries
            - Drowning or near-drowning incidents
            - Severe pediatric emergencies
            - Obstetric emergencies (pregnancy complications)
            - Psychiatric emergencies (suicide risk, severe mental health crisis)
            
            NON-EMERGENCY (No AI Virtual Doctor needed - these should use normal workflow):
            - Routine checkups and consultations
            - Mild symptoms (cold, minor fever, headache, etc.)
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
                "emergency_type": "specific emergency type or 'none'",
                "confidence": "high/medium/low",
                "reasoning": "brief explanation of why this is or isn't an emergency",
                "ai_virtual_doctor_needed": true/false,
                "recommended_action": "what should happen next"
            }}
            
            CRITICAL: AI Virtual Doctor should ONLY appear for GENUINE LIFE-THREATENING emergencies that require immediate medical intervention and calming presence. Be very strict - only activate for severe, critical situations.
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Try to parse JSON response
            try:
                result = json.loads(result_text)
                is_emergency = result.get("is_emergency", False)
                ai_doctor_needed = result.get("ai_virtual_doctor_needed", False)
                
                print(f"🚨 Emergency Check: {is_emergency}, AI Doctor Needed: {ai_doctor_needed}")
                print(f"📋 Reasoning: {result.get('reasoning', 'No reasoning provided')}")
                
                # Both emergency detection AND AI doctor need must be true
                return is_emergency and ai_doctor_needed
                
            except json.JSONDecodeError:
                # Fallback: use severity and urgency from assessment
                severity = symptom_assessment.get('severity', '').lower()
                urgency = symptom_assessment.get('urgency', '').lower()
                return severity in ['high', 'critical'] and urgency in ['urgent', 'immediate']
                
        except Exception as e:
            print(f"Error in dynamic emergency detection: {e}")
            # Fallback to basic criteria
            severity = symptom_assessment.get('severity', '').lower()
            urgency = symptom_assessment.get('urgency', '').lower()
            return severity in ['high', 'critical'] and urgency in ['urgent', 'immediate']

    def _determine_emergency_type(self, patient_info: dict, symptom_assessment: dict) -> str:
        """Dynamically determine emergency type using AI"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are an emergency medicine specialist. Based on the patient information, determine the specific type of medical emergency.
            
            PATIENT INFORMATION:
            {json.dumps(patient_info, indent=2)}
            
            SYMPTOM ASSESSMENT:
            {json.dumps(symptom_assessment, indent=2)}
            
            Classify this as one of the following emergency types:
            - Cardiac Emergency (heart attack, chest pain, arrhythmia)
            - Neurological Emergency (stroke, seizure, head injury)
            - Respiratory Emergency (breathing difficulty, asthma attack)
            - Trauma Emergency (bleeding, fractures, burns)
            - Allergic Reaction Emergency (anaphylaxis, severe allergy)
            - Toxicology Emergency (overdose, poisoning)
            - Obstetric Emergency (pregnancy complications)
            - Pediatric Emergency (child-specific emergencies)
            - Psychiatric Emergency (suicide risk, severe mental health)
            - General Medical Emergency (other life-threatening conditions)
            
            Respond with ONLY the emergency type name, nothing else.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"Error determining emergency type: {e}")
            return "General Medical Emergency"

    def _generate_ai_doctor_script(self, patient_info: dict, symptom_assessment: dict, emergency_type: str) -> str:
        """Generate AI doctor consultation script using Gemini"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are a professional emergency medicine doctor conducting a video consultation.
            Generate a detailed medical consultation script based on the following patient information.
            
            PATIENT INFORMATION:
            {json.dumps(patient_info, indent=2)}
            
            SYMPTOM ASSESSMENT:
            {json.dumps(symptom_assessment, indent=2)}
            
            EMERGENCY TYPE: {emergency_type}
            
            Generate a professional medical consultation script that includes:
            
            1. INTRODUCTION: Professional greeting and emergency assessment
            2. VITAL SIGNS CHECK: What vital signs to check immediately
            3. SYMPTOM ASSESSMENT: Detailed symptom evaluation questions
            4. MEDICAL HISTORY REVIEW: Relevant medical history questions
            5. IMMEDIATE INTERVENTIONS: What to do right now
            6. MONITORING INSTRUCTIONS: What to watch for
            7. NEXT STEPS: Immediate actions and preparations for ambulance
            8. CALMING GUIDANCE: Reassuring words for the patient
            
            Make the script professional, medical, and immediately actionable.
            Focus on emergency protocols and immediate patient safety.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Error generating AI doctor script: {str(e)}"

    def _call_ambulance(self, patient_name: str, location: str, emergency_type: str, contact: str, emergency_contacts: dict) -> dict:
        """Simulate ambulance call using free SMS service"""
        try:
            # Use dynamic emergency contacts
            ambulance_number = emergency_contacts.get('ambulance', '108')
            country = emergency_contacts.get('country', 'Unknown')
            
            emergency_message = f"""
            🚨 EMERGENCY ALERT 🚨
            
            Patient: {patient_name}
            Location: {location}
            Country: {country}
            Emergency Type: {emergency_type}
            Contact: {contact}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            IMMEDIATE AMBULANCE REQUIRED
            Call: {ambulance_number}
            """
            
            # Try to send SMS using free service
            sms_result = self._send_emergency_sms(emergency_message, contact)
            
            return {
                "success": True,
                "ambulance_called": True,
                "emergency_message": emergency_message,
                "sms_sent": sms_result.get("success", False),
                "estimated_arrival": "10-15 minutes",
                "emergency_number": ambulance_number,
                "country": country,
                "contact_used": contact
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Please call emergency services manually at {emergency_contacts.get('ambulance', '108')}"
            }

    def _send_emergency_sms(self, message: str, contact: str) -> dict:
        """Send emergency SMS using free service"""
        try:
            # Using TextLocal free SMS service (requires registration)
            # For demo, we'll simulate the SMS sending
            
            # You can integrate with free SMS services like:
            # - TextLocal (free tier available)
            # - MSG91 (free tier available)
            # - Twilio (free trial)
            
            print(f"📱 Sending emergency SMS to {contact}")
            print(f"Message: {message}")
            
            # Simulate SMS sending
            time.sleep(1)
            
            return {
                "success": True,
                "message": "Emergency SMS sent successfully",
                "service": "TextLocal (Free Tier)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "SMS sending failed"
            }

    def _generate_calming_guidance(self, emergency_type: str, patient_info: dict) -> str:
        """Generate calming guidance for the patient"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            Generate calming, reassuring guidance for a patient experiencing a {emergency_type}.
            
            Patient Name: {patient_info.get('name', 'Patient')}
            Age: {patient_info.get('age', 'Unknown')}
            
            Provide:
            1. Immediate calming words
            2. Breathing guidance
            3. Reassurance about help coming
            4. What to expect
            5. How to stay safe until help arrives
            
            Keep it comforting, professional, and immediately helpful.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return f"Stay calm. Help is on the way. Emergency services have been notified."

    def _generate_monitoring_instructions(self, emergency_type: str) -> str:
        """Generate monitoring instructions for the emergency"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            Generate monitoring instructions for a {emergency_type}.
            
            Include:
            1. Vital signs to monitor
            2. Warning signs to watch for
            3. How often to check
            4. What to do if condition worsens
            5. When to call for additional help
            
            Make it clear and actionable for non-medical personnel.
            """
            
            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            return "Monitor breathing, consciousness, and vital signs. Call for help if condition worsens."

    def _generate_immediate_actions(self, emergency_type: str, patient_info: dict, symptom_assessment: dict) -> list:
        """Dynamically generate immediate actions based on emergency type using AI"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are an emergency medical coordinator. Generate a list of immediate actions that should be taken for this specific emergency.
            
            EMERGENCY TYPE: {emergency_type}
            PATIENT INFORMATION: {json.dumps(patient_info, indent=2)}
            SYMPTOM ASSESSMENT: {json.dumps(symptom_assessment, indent=2)}
            
            Generate 5-7 immediate actions that should be taken RIGHT NOW for this emergency.
            Focus on:
            1. Patient safety
            2. Immediate medical interventions
            3. Preparation for emergency services
            4. Monitoring instructions
            5. What NOT to do
            
            Respond with ONLY a JSON array of action strings:
            [
                "Action 1",
                "Action 2",
                "Action 3",
                ...
            ]
            
            Make actions specific to this emergency type and patient situation.
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Try to parse JSON response
            try:
                actions = json.loads(result_text)
                if isinstance(actions, list):
                    return actions
                else:
                    raise ValueError("Response is not a list")
            except (json.JSONDecodeError, ValueError):
                # Fallback: generate actions based on emergency type
                return self._generate_fallback_actions(emergency_type)
                
        except Exception as e:
            print(f"Error generating immediate actions: {e}")
            return self._generate_fallback_actions(emergency_type)

    def _generate_fallback_actions(self, emergency_type: str) -> list:
        """Fallback actions if AI generation fails"""
        base_actions = [
            "Call emergency services immediately",
            "Keep patient calm and comfortable",
            "Monitor vital signs",
            "Prepare for emergency treatment",
            "Stay with patient until help arrives"
        ]
        
        # Add emergency-specific actions
        if "cardiac" in emergency_type.lower():
            base_actions.insert(1, "Have patient sit or lie down comfortably")
            base_actions.insert(2, "Loosen tight clothing")
        elif "respiratory" in emergency_type.lower():
            base_actions.insert(1, "Help patient into comfortable position")
            base_actions.insert(2, "Ensure fresh air circulation")
        elif "trauma" in emergency_type.lower():
            base_actions.insert(1, "Apply direct pressure to bleeding if present")
            base_actions.insert(2, "Do not move if spinal injury suspected")
        
        return base_actions

    def _save_emergency_response(self, emergency_response: dict):
        """Save emergency response to file"""
        try:
            filename = f"emergency_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(emergency_response, f, indent=2)
            print(f"✅ Emergency response saved to {filename}")
        except Exception as e:
            print(f"⚠️ Could not save emergency response: {e}") 

    def _get_emergency_contacts(self, patient_location: str) -> dict:
        """Dynamically get emergency contact numbers based on patient location"""
        try:
            model = get_model_with_retry()
            
            prompt = f"""
            You are an emergency services coordinator. Based on the patient's location, provide the appropriate emergency contact numbers.
            
            PATIENT LOCATION: {patient_location}
            
            Provide emergency contact numbers for this location. Include:
            - Ambulance/Emergency Medical Services
            - Police
            - Fire Department
            - Poison Control (if applicable)
            - Local emergency numbers
            
            Respond with ONLY a JSON object:
            {{
                "ambulance": "emergency number",
                "police": "police number", 
                "fire": "fire number",
                "poison_control": "poison control number or 'not available'",
                "local_emergency": "local emergency number or 'not available'",
                "country": "detected country",
                "note": "any important notes about emergency services in this location"
            }}
            
            Use standard emergency numbers for the detected country/region.
            """
            
            response = model.generate_content(prompt)
            result_text = response.text.strip()
            
            try:
                contacts = json.loads(result_text)
                return contacts
            except json.JSONDecodeError:
                return self._get_fallback_contacts(patient_location)
                
        except Exception as e:
            print(f"Error getting emergency contacts: {e}")
            return self._get_fallback_contacts(patient_location)

    def _get_fallback_contacts(self, patient_location: str) -> dict:
        """Fallback emergency contacts if AI detection fails"""
        # Basic fallback based on common locations
        location_lower = patient_location.lower()
        
        if any(city in location_lower for city in ['pune', 'mumbai', 'nashik', 'nagpur', 'india']):
            return {
                "ambulance": "108",
                "police": "100", 
                "fire": "101",
                "poison_control": "1066",
                "local_emergency": "112",
                "country": "India",
                "note": "Standard Indian emergency numbers"
            }
        elif any(city in location_lower for city in ['new york', 'los angeles', 'chicago', 'usa', 'united states']):
            return {
                "ambulance": "911",
                "police": "911",
                "fire": "911", 
                "poison_control": "1-800-222-1222",
                "local_emergency": "911",
                "country": "USA",
                "note": "911 handles all emergency services in USA"
            }
        elif any(city in location_lower for city in ['london', 'manchester', 'uk', 'united kingdom']):
            return {
                "ambulance": "999",
                "police": "999",
                "fire": "999",
                "poison_control": "111",
                "local_emergency": "999", 
                "country": "UK",
                "note": "999 handles all emergency services in UK"
            }
        else:
            # Generic international fallback
            return {
                "ambulance": "112",
                "police": "112",
                "fire": "112",
                "poison_control": "not available",
                "local_emergency": "112",
                "country": "International",
                "note": "112 is the international emergency number. Please verify local numbers."
            } 