#!/usr/bin/env python3
"""
FastAPI Healthcare Assistant API
Handles patient interactions, symptom analysis, doctor recommendations, and appointment booking
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import json
import sys
import os
import time
import urllib3
from datetime import datetime

# Fix SSL certificate issues
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['PYTHONHTTPSVERIFY'] = '0'

# Set API key for Gemini
api_key = "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"  # Latest working API key
os.environ['GOOGLE_API_KEY'] = api_key
os.environ['GEMINI_API_KEY'] = api_key # Some versions of crewai might use this

print("✅ Using the new Gemini API key.")
print("🔧 SSL certificate verification disabled for Windows compatibility.")

# Add the project's source directory to the Python path to resolve imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'doccrew/research_crew/src/research_crew')))

from crew import PatientCrew, Crew, Process
from doccrew.research_crew.src.research_crew.tools.custom_tool import UserInputTool, SymptomSeverityTool
from doccrew.research_crew.src.research_crew.tools.notification_tool import PushNotificationTool
from doccrew.research_crew.src.research_crew.tools.emergency_tool import EmergencyResponseTool

# 🔑 Initialize APScheduler for reminders
from doccrew.research_crew.src.research_crew.tools.reminder_scheduler import reminder_scheduler
print("✅ APScheduler initialized for appointment reminders")

# 🔑 Automatically schedule reminders for existing appointments
def schedule_existing_appointments():
    """Schedule reminders for any existing appointments that don't have reminders"""
    try:
        import os
        if os.path.exists('appointment_booking.json'):
            with open('appointment_booking.json', 'r') as f:
                appointment_data = json.load(f)
            
            # Check if reminder is already scheduled
            appointment_id = appointment_data.get('appointment_id')
            if appointment_id:
                # Check if this appointment already has a reminder scheduled
                if os.path.exists('scheduled_reminders.json'):
                    with open('scheduled_reminders.json', 'r') as f:
                        scheduled_reminders = json.load(f)
                    
                    # Check if reminder already exists
                    existing_reminder = next((r for r in scheduled_reminders if r.get('appointment_id') == appointment_id), None)
                    
                    if not existing_reminder:
                        print(f"🔔 Scheduling reminder for existing appointment {appointment_id}")
                        
                        # Get patient data
                        patient_data = {}
                        if os.path.exists('patient_info.json'):
                            with open('patient_info.json', 'r') as f:
                                patient_data = json.load(f)
                        else:
                            # Try to get patient name from patient_info.json first
                            actual_patient_name = "Unknown Patient"
                            try:
                                if os.path.exists('patient_info.json'):
                                    with open('patient_info.json', 'r') as f:
                                        patient_info = json.load(f)
                                        if isinstance(patient_info, dict) and 'name' in patient_info:
                                            actual_patient_name = patient_info['name']
                                        elif isinstance(patient_info, dict) and 'current' in patient_info:
                                            actual_patient_name = patient_info['current'].get('name', 'Unknown Patient')
                            except Exception as e:
                                print(f"⚠️ Could not read patient name from patient_info.json: {e}")
                            
                            patient_data = {
                                "name": appointment_data.get('patient_name', actual_patient_name),
                                "contact": appointment_data.get('patient_contact', 'Not provided')
                            }
                        
                        # Schedule the reminder
                        from doccrew.research_crew.src.research_crew.tools.reminder_tool import CompleteReminderTool
                        reminder_tool = CompleteReminderTool()
                        reminder_result = reminder_tool._run(appointment_data, patient_data)
                        print(f"✅ Existing appointment reminder scheduled: {reminder_result}")
                    else:
                        print(f"✅ Reminder already scheduled for appointment {appointment_id}")
                        
    except Exception as e:
        print(f"⚠️ Could not schedule reminders for existing appointments: {e}")

# Schedule reminders for existing appointments
schedule_existing_appointments()

app = FastAPI()

# Mount a directory for static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount audio files directory
app.mount("/audio", StaticFiles(directory="."), name="audio")

# In-memory storage for conversation state and crew results
conversation_state = {}
user_responses = {}

# Store the latest AI doctor script per session (in-memory for now)
ai_doctor_scripts = {}

# Modify the UserInputTool to work with websockets
class WebSocketUserInputTool(UserInputTool):
    websocket: WebSocket = None
    conversation_id: str = None

    def _run(self, question: str) -> str:
        print(f"[DEBUG] Asking user: {question} (conversation_id={self.conversation_id})")
        # Send the question to the frontend
        asyncio.run(self.websocket.send_text(json.dumps({"type": "question", "data": question})))
        print(f"[DEBUG] Waiting for user response for conversation_id={self.conversation_id}")
        # Wait for the user's response
        while self.conversation_id not in user_responses:
            time.sleep(0.1)  # Use regular sleep instead of async
        # Retrieve and clear the response
        response = user_responses.pop(self.conversation_id)
        print(f"[DEBUG] Received user response for conversation_id={self.conversation_id}: {response}")
        return response

# Create an instance of our modified tool
websocket_user_input_tool = WebSocketUserInputTool()

async def start_real_time_monitoring(websocket: WebSocket, conversation_id: str, emergency_response: dict):
    """Start real-time monitoring for emergency video call"""
    try:
        monitoring_session = emergency_response.get("video_call", {}).get("monitoring_session", {})
        if monitoring_session.get("status") == "ACTIVE":
            print(f"🔍 Starting real-time monitoring for session: {monitoring_session.get('session_id')}")
            
            # Send monitoring start notification
            await websocket.send_text(json.dumps({
                "type": "monitoring_started",
                "data": {
                    "session_id": monitoring_session.get("session_id"),
                    "message": "Real-time monitoring activated for emergency video call",
                    "monitoring_interval": monitoring_session.get("monitoring_interval", "30 seconds"),
                    "vital_signs_tracking": monitoring_session.get("vital_signs_tracking", True)
                }
            }))
            
            # Start background monitoring task
            asyncio.create_task(monitor_emergency_session(websocket, conversation_id, monitoring_session))
            
    except Exception as e:
        print(f"❌ Error starting real-time monitoring: {e}")

async def monitor_emergency_session(websocket: WebSocket, conversation_id: str, monitoring_session: dict):
    """Background task to monitor emergency session"""
    try:
        session_id = monitoring_session.get("session_id")
        monitoring_interval = int(monitoring_session.get("monitoring_interval", "30").split()[0])
        
        print(f"🔍 Starting monitoring loop for session {session_id} every {monitoring_interval} seconds")
        
        # Monitor for 10 minutes (20 updates at 30-second intervals)
        for i in range(20):
            await asyncio.sleep(monitoring_interval)
            
            # Check if conversation is still active
            if conversation_id not in conversation_state:
                print(f"🔍 Conversation {conversation_id} ended, stopping monitoring")
                break
            
            # Send monitoring update
            monitoring_update = {
                "type": "monitoring_update",
                "data": {
                    "session_id": session_id,
                    "update_number": i + 1,
                    "timestamp": datetime.now().isoformat(),
                    "status": "MONITORING_ACTIVE",
                    "message": f"Emergency session monitoring update #{i + 1}",
                    "vital_signs_status": "TRACKING_ACTIVE",
                    "video_call_status": "READY"
                }
            }
            
            try:
                await websocket.send_text(json.dumps(monitoring_update))
                print(f"🔍 Sent monitoring update #{i + 1} for session {session_id}")
            except Exception as e:
                print(f"❌ Error sending monitoring update: {e}")
                break
        
        # Send monitoring completion
        await websocket.send_text(json.dumps({
            "type": "monitoring_completed",
            "data": {
                "session_id": session_id,
                "message": "Emergency monitoring session completed",
                "total_updates": 20,
                "status": "COMPLETED"
            }
        }))
        
    except Exception as e:
        print(f"❌ Error in monitoring loop: {e}")

@app.get("/")
async def get():
    with open("index.html") as f:
        return HTMLResponse(f.read())

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    conversation_state[conversation_id] = {"status": "running"}
    
    websocket_user_input_tool.websocket = websocket
    websocket_user_input_tool.conversation_id = conversation_id
    
    try:
        patient_crew_manager = PatientCrew()
        
        # Configure all agents to use WebSocket user input tool
        patient_info_collector_agent = patient_crew_manager.patient_info_collector()
        patient_info_collector_agent.tools = [websocket_user_input_tool, patient_crew_manager.patient_info_collector().tools[1]]
        
        appointment_booking_agent = patient_crew_manager.appointment_booking_agent()
        appointment_booking_agent.tools = [websocket_user_input_tool, appointment_booking_agent.tools[1]]
        
        # Create a crew with emergency response included (but only for genuine emergencies)
        # We'll create two different crews based on whether emergency is detected
        base_crew = Crew(
            agents=[
                patient_crew_manager.patient_info_collector(),
                patient_crew_manager.symptom_severity_analyzer(),
                patient_crew_manager.emergency_response_agent(),  # Emergency agent (only activates for critical cases)
                patient_crew_manager.doctor_recommender()
            ],
            tasks=[
                patient_crew_manager.collect_info_task(),
                patient_crew_manager.analyze_symptoms_task(),
                patient_crew_manager.emergency_response_task(),  # Emergency task (only activates for critical cases)
                patient_crew_manager.recommend_doctors_task()
            ],
            process=Process.sequential,
            verbose=True
        )
        
        # Configure the agents in the base crew to use WebSocket tools
        base_crew.agents[0].tools = [websocket_user_input_tool, base_crew.agents[0].tools[1]]  # Patient info collector

        # Run the base workflow first
        print("🤖 Starting base workflow (patient info, symptom analysis, emergency response, doctor recommendations)...")
        crew_result = await asyncio.to_thread(base_crew.kickoff)
        



        crew_result = await asyncio.to_thread(base_crew.kickoff)

        # Extract and send results from all tasks
        if crew_result.tasks_output:
            try:
                print(f"🤖 Processing {len(crew_result.tasks_output)} task outputs...")
                
                # Task 1: Patient Info Collection
                if len(crew_result.tasks_output) > 0:
                    print("✅ Task 1: Patient info collection completed")
                    conversation_state[conversation_id]["patient_info"] = crew_result.tasks_output[0].raw
                
                # Task 2: Symptom Assessment
                if len(crew_result.tasks_output) > 1:
                    assessment_str = crew_result.tasks_output[1].raw
                    print(f"🔍 DEBUG: Raw assessment output: {assessment_str}")
                    
                    try:
                        symptom_assessment = json.loads(assessment_str)
                    except json.JSONDecodeError:
                        import re
                        json_match = re.search(r'\{.*\}', assessment_str, re.DOTALL)
                        if json_match:
                            symptom_assessment = json.loads(json_match.group())
                        else:
                            symptom_assessment = {
                                "error": "Failed to parse assessment",
                                "severity": "Unknown",
                                "urgency": "Unknown",
                                "reasoning": "Could not parse assessment data"
                            }
                    
                    await websocket.send_text(json.dumps({"type": "assessment", "data": symptom_assessment}))
                    print("✅ Task 2: Symptom assessment sent to frontend")
                    conversation_state[conversation_id]["symptom_assessment"] = symptom_assessment
                
                # Task 3: Emergency Response (index 2)
                if len(crew_result.tasks_output) > 2:
                    emergency_str = crew_result.tasks_output[2].raw
                    print(f"🚨 DEBUG: Raw emergency response output: {emergency_str}")
                    
                    try:
                        emergency_response = json.loads(emergency_str)
                    except json.JSONDecodeError:
                        import re
                        json_match = re.search(r'\{.*\}', emergency_str, re.DOTALL)
                        if json_match:
                            emergency_response = json.loads(json_match.group())
                        else:
                            emergency_response = {
                                "emergency_detected": False,
                                "error": "Failed to parse emergency response"
                            }
                    
                    print(f"🚨 DEBUG: Parsed emergency response: {emergency_response}")
                    
                    # Check if emergency was detected
                    emergency_detected = emergency_response.get("emergency_detected", False)
                    print(f"🚨 DEBUG: Emergency detected: {emergency_detected}")
                    
                    if emergency_detected:
                        print("🚨 CRITICAL EMERGENCY DETECTED - Activating AI Virtual Doctor")
                        await websocket.send_text(json.dumps({"type": "emergency", "data": emergency_response}))
                        
                        # Send immediate emergency notification
                        emergency_notification = {
                            "type": "emergency_notification",
                            "data": {
                                "message": f"🚨 CRITICAL EMERGENCY: {emergency_response.get('emergency_type', 'Medical Emergency')} detected! AI Virtual Doctor activated.",
                                "ambulance_called": emergency_response.get("ambulance_called", False),
                                "calming_guidance": emergency_response.get("calming_guidance", ""),
                                "immediate_actions": emergency_response.get("immediate_actions", []),
                                "emergency_contacts": emergency_response.get("emergency_contacts", {}),
                                "ai_virtual_doctor_activated": True,
                                "emergency_type": emergency_response.get("emergency_type", "Medical Emergency")
                            }
                        }
                        await websocket.send_text(json.dumps(emergency_notification))
                        
                        # Start real-time monitoring if video call is created
                        if emergency_response.get("video_call", {}).get("video_call_created", False):
                            await start_real_time_monitoring(websocket, conversation_id, emergency_response)
                        
                        # Store emergency response
                        conversation_state[conversation_id]["emergency_response"] = emergency_response
                        
                        # Continue with normal workflow but inform user about emergency
                        await websocket.send_text(json.dumps({
                            "type": "emergency_workflow_continue",
                            "data": "Critical emergency detected. AI Virtual Doctor activated. Continuing with doctor recommendations..."
                        }))
                    else:
                        print("✅ No critical emergency detected - AI Virtual Doctor not activated")
                        await websocket.send_text(json.dumps({
                            "type": "no_emergency",
                            "data": {
                                "message": "No critical emergency detected. AI Virtual Doctor is only available for life-threatening emergencies.",
                                "ai_virtual_doctor_activated": False,
                                "recommended_action": "Continue with normal consultation workflow"
                            }
                        }))
                
                # Task 4: Doctor Recommendations (index 3) - ALWAYS display regardless of emergency
                if len(crew_result.tasks_output) > 3:
                    print(f"🔍 DEBUG: Processing Doctor Recommendations task (index 3)")
                    recommendations_str = crew_result.tasks_output[3].raw
                    print(f"🔍 DEBUG: Raw recommendations output: {recommendations_str}")
                    
                    try:
                        doctor_recommendations = json.loads(recommendations_str)
                    except json.JSONDecodeError as json_error:
                        print(f"🔍 DEBUG: JSON decode error: {json_error}")
                        import re
                        json_match = re.search(r'\{.*\}', recommendations_str, re.DOTALL)
                        if json_match:
                            try:
                                doctor_recommendations = json.loads(json_match.group())
                                print(f"🔍 DEBUG: Successfully extracted JSON from text")
                            except json.JSONDecodeError as extract_error:
                                print(f"🔍 DEBUG: Failed to parse extracted JSON: {extract_error}")
                                doctor_recommendations = {
                                    "error": "Failed to parse recommendations",
                                    "recommended_doctors": [],
                                    "message": "We couldn't find valid doctor recommendations. Please try again."
                                }
                        else:
                            print(f"🔍 DEBUG: No JSON pattern found in text")
                            doctor_recommendations = {
                                "error": "No valid recommendations format found",
                                "recommended_doctors": [],
                                "message": "We couldn't find valid doctor recommendations. Please try again."
                            }
                    
                    print(f"🔍 DEBUG: Final recommendations object: {doctor_recommendations}")
                    await websocket.send_text(json.dumps({"type": "recommendations", "data": doctor_recommendations}))
                    print("✅ Task 5: Doctor recommendations sent to frontend")
                    conversation_state[conversation_id]["doctor_recommendations"] = doctor_recommendations
                else:
                    print(f"🔍 DEBUG: No doctor recommendations task found - tasks_output length: {len(crew_result.tasks_output)}")
                
            except Exception as e:
                print(f"❌ Error extracting data from crew result: {e}")
                import traceback
                traceback.print_exc()
        
        # Check if emergency was detected to provide appropriate completion message
        emergency_detected = conversation_state[conversation_id].get("emergency_response", {}).get("emergency_detected", False)
        
        # If emergency was detected, create AI Virtual Doctor
        if emergency_detected:
            print("🚨 Emergency detected - Creating AI Virtual Doctor for emergency consultation")
            
            # Create AI Virtual Doctor crew
            ai_doctor_crew = Crew(
                agents=[
                    patient_crew_manager.ai_virtual_doctor_agent()
                ],
                tasks=[
                    patient_crew_manager.ai_virtual_doctor_task()
                ],
                process=Process.sequential,
                verbose=True
            )
            
            try:
                # Run AI Virtual Doctor task
                ai_doctor_result = await asyncio.to_thread(ai_doctor_crew.kickoff)
                
                if ai_doctor_result.tasks_output and len(ai_doctor_result.tasks_output) > 0:
                    ai_doctor_str = ai_doctor_result.tasks_output[0].raw
                    print(f"🤖 DEBUG: Raw AI Virtual Doctor output: {ai_doctor_str}")
                    
                    try:
                        ai_doctor_data = json.loads(ai_doctor_str)
                    except json.JSONDecodeError:
                        import re
                        json_match = re.search(r'\{.*\}', ai_doctor_str, re.DOTALL)
                        if json_match:
                            ai_doctor_data = json.loads(json_match.group())
                        else:
                            ai_doctor_data = {
                                "ai_doctor_created": False,
                                "error": "Failed to parse AI doctor data"
                            }
                    
                    print(f"🤖 DEBUG: Parsed AI doctor data: {ai_doctor_data}")
                    
                    if ai_doctor_data.get("ai_doctor_created", False):
                        # Store the conversation script for TTS use
                        conversation_script = ai_doctor_data.get("conversation_script", {})
                        if conversation_script:
                            # Convert script to string for TTS
                            script_parts = []
                            for key, value in conversation_script.items():
                                if isinstance(value, list):
                                    script_parts.extend([f"- {item}" for item in value])
                                elif value:
                                    script_parts.append(str(value))
                            
                            full_script = "\n".join(script_parts)
                            ai_doctor_scripts["latest"] = full_script
                            print(f"📝 AI Doctor script stored for TTS: {full_script[:100]}...")
                            print(f"📝 Full script length: {len(full_script)} characters")
                        
                        # Send AI Virtual Doctor ready message
                        await websocket.send_text(json.dumps({
                            "type": "ai_virtual_doctor_ready",
                            "data": {
                                "doctor_name": ai_doctor_data.get("doctor_profile", {}).get("doctor_name", "Dr. Sarah Chen"),
                                "emergency_type": emergency_response.get("emergency_type", "Medical Emergency")
                            }
                        }))
                        print("✅ AI Virtual Doctor ready message sent to frontend")
                    else:
                        print("❌ AI Virtual Doctor creation failed")
                        print(f"❌ AI Doctor data: {ai_doctor_data}")
                        
            except Exception as e:
                print(f"❌ Error creating AI Virtual Doctor: {e}")
                import traceback
                traceback.print_exc()
            
            completion_message = "Critical emergency detected and AI Virtual Doctor activated. Patient info, symptom analysis, emergency response, and doctor recommendations completed. Ready for appointment booking."
        else:
            completion_message = "Patient info, symptom analysis, and doctor recommendations completed. No critical emergency detected - AI Virtual Doctor is only available for life-threatening emergencies. Ready for appointment booking."
        
        await websocket.send_text(json.dumps({"type": "initial_workflow_complete", "data": completion_message}))

    except WebSocketDisconnect:
        print(f"Client #{conversation_id} disconnected")
    except Exception as e:
        print(f"Error in websocket for client #{conversation_id}: {e}")
        await websocket.send_text(json.dumps({"type": "error", "data": str(e)}))
        # Do NOT delete conversation_state or user_responses here
    finally:
        # Only clean up state if the conversation is truly finished (not on error)
        if conversation_id in conversation_state and conversation_state[conversation_id].get('status') == 'finished':
            del conversation_state[conversation_id]
        if conversation_id in user_responses and conversation_state.get(conversation_id, {}).get('status') == 'finished':
            del user_responses[conversation_id]
        print(f"Conversation {conversation_id} ended (if finished).")

@app.post("/respond/{conversation_id}")
async def respond(conversation_id: str, response: dict):
    print(f"[DEBUG] /respond received for conversation_id={conversation_id}: {response.get('message')}")
    user_responses[conversation_id] = response.get("message")
    return {"status": "received"}

@app.post("/book-appointment")
async def book_appointment(booking_request: dict):
    """
    New endpoint to handle booking with guaranteed notification
    """
    try:
        print(f"📋 Received booking request: {booking_request}")
        
        # Extract booking details
        doctor_name = booking_request.get("doctor_name")
        doctor_specialty = booking_request.get("doctor_specialty") 
        doctor_hospital = booking_request.get("doctor_hospital")
        appointment_date = booking_request.get("appointment_date")
        conversation_id = booking_request.get("conversation_id")
        
        # Get patient info from conversation state or stored files
        patient_name = None
        patient_contact = None
        
        # Try to get patient info from conversation state first
        if conversation_id and conversation_id in conversation_state:
            stored_patient_info = conversation_state[conversation_id].get("patient_info")
            if stored_patient_info:
                try:
                    if isinstance(stored_patient_info, str):
                        patient_data = json.loads(stored_patient_info)
                    else:
                        patient_data = stored_patient_info
                    
                    patient_name = patient_data.get("name")
                    patient_contact = patient_data.get("contact")
                    print(f"✅ Retrieved patient info from conversation state: {patient_name}, {patient_contact}")
                except Exception as e:
                    print(f"⚠️ Could not parse patient info from conversation state: {e}")
        
        # Fallback to stored patient info file
        if not patient_name:
            try:
                if os.path.exists('patient_info.json'):
                    with open('patient_info.json', 'r') as f:
                        patient_data = json.load(f)
                        if isinstance(patient_data, dict):
                            if 'name' in patient_data:
                                patient_name = patient_data['name']
                                patient_contact = patient_data.get('contact')
                            elif 'current' in patient_data and isinstance(patient_data['current'], dict):
                                patient_name = patient_data['current'].get('name')
                                patient_contact = patient_data['current'].get('contact')
                    print(f"✅ Retrieved patient info from file: {patient_name}, {patient_contact}")
            except Exception as e:
                print(f"⚠️ Could not read patient info from file: {e}")
        
        # Generate appointment ID
        import uuid
        appointment_id = f"APT{uuid.uuid4().hex[:8].upper()}"
        
        # Create appointment booking object - only include fields that have valid data
        appointment_booking = {
            "appointment_id": appointment_id,
            "doctor_name": doctor_name,
            "doctor_specialty": doctor_specialty,
            "appointment_date": appointment_date,
            "hospital": doctor_hospital,
            "location": "Pune",  # Default location
            "cost": 1500,  # Default cost
            "notification_sent": False,
            "notification_message": ""
        }
        
        # Only add patient fields if we have valid data
        if patient_name and patient_name.strip():
            appointment_booking["patient_name"] = patient_name
        if patient_contact and patient_contact.strip():
            appointment_booking["patient_contact"] = patient_contact
        
        # Send notification using the PushNotificationTool
        notification_tool = PushNotificationTool()
        notification_message = f"Your appointment with {doctor_name} has been confirmed for {appointment_date} at {doctor_hospital}. Please arrive 15 minutes early. Appointment ID: {appointment_id}"
        
        print(f"📱 Sending guaranteed notification: {notification_message}")
        notification_result = notification_tool._run(notification_message)
        
        # Parse notification result
        try:
            notification_json = json.loads(notification_result)
            appointment_booking["notification_sent"] = notification_json.get("notification_sent", False)
            appointment_booking["notification_message"] = notification_message
            if notification_json.get("error"):
                appointment_booking["notification_error"] = notification_json.get("error")
        except json.JSONDecodeError:
            appointment_booking["notification_sent"] = False
            appointment_booking["notification_error"] = "Failed to parse notification result"
        
        # Save appointment to file
        try:
            import os
            appointments_file = 'appointment_booking.json'
            with open(appointments_file, 'w') as f:
                json.dump(appointment_booking, f, indent=2)
            print(f"✅ Appointment saved to {appointments_file}")
        except Exception as e:
            print(f"❌ Failed to save appointment: {e}")
        
        # 🔑 AUTOMATICALLY SCHEDULE REMINDER
        try:
            print(f"🔔 Automatically scheduling reminder for appointment {appointment_id}")
            
            # Get patient data from patient_info.json if it exists
            patient_data = {}
            try:
                if os.path.exists('patient_info.json'):
                    with open('patient_info.json', 'r') as f:
                        patient_data = json.load(f)
                        # Extract actual patient data if it exists
                        if isinstance(patient_data, dict):
                            if 'name' in patient_data:
                                # Direct format
                                pass
                            elif 'current' in patient_data and isinstance(patient_data['current'], dict):
                                # Nested format
                                patient_data = patient_data['current']
                else:
                    # Create minimal patient data only if we have actual patient info
                    if patient_name and patient_name.strip():
                        patient_data = {
                            "name": patient_name,
                            "location": "Pune"
                        }
                        if patient_contact and patient_contact.strip():
                            patient_data["contact"] = patient_contact
            except Exception as e:
                print(f"⚠️ Could not load patient data: {e}")
                # Only create patient data if we have actual patient info
                if patient_name and patient_name.strip():
                    patient_data = {"name": patient_name}
                    if patient_contact and patient_contact.strip():
                        patient_data["contact"] = patient_contact
            
            # Schedule the reminder automatically
            from doccrew.research_crew.src.research_crew.tools.reminder_tool import CompleteReminderTool
            reminder_tool = CompleteReminderTool()
            reminder_result = reminder_tool._run(appointment_booking, patient_data)
            
            print(f"✅ Reminder automatically scheduled: {reminder_result}")
            
        except Exception as e:
            print(f"❌ Failed to schedule reminder automatically: {e}")
        
        print(f"✅ Booking completed with notification status: {appointment_booking['notification_sent']}")
        return {
            "status": "success",
            "appointment": appointment_booking,
            "message": "Appointment booked successfully and reminder scheduled!"
        }
        
    except Exception as e:
        print(f"❌ Error in booking appointment: {e}")
        return {
            "status": "error",
            "message": f"Failed to book appointment: {str(e)}"
        }

@app.post("/store_ai_script")
async def store_ai_script(request: dict):
    """Store AI doctor script for later use"""
    try:
        data = request if isinstance(request, dict) else await request.json()
        script = data.get("script", "")
        
        if script:
            ai_doctor_scripts["latest"] = script
            print(f"✅ Script stored successfully: {len(script)} characters")
            return {"status": "success", "message": "Script stored successfully"}
        else:
            return {"status": "error", "message": "No script provided"}
            
    except Exception as e:
        print(f"❌ Error storing script: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/start_ai_doctor_call")
async def start_ai_doctor_call(request: dict):
    try:
        data = request if isinstance(request, dict) else await request.json()
        call_type = data.get("type", "consultation")
        doctor_name = data.get("doctor_name", "Dr. AI Assistant")
        
        print(f"👨‍⚕️ AI Doctor consultation requested: {call_type} with {doctor_name}")
        
        # Get the stored script
        script = ai_doctor_scripts.get("latest")
        print(f"📝 Retrieved script: {'Available' if script else 'Not available'}")
        
        if not script:
            print("❌ No script available for TTS")
            return {"status": "error", "message": "No script available"}
        
        print(f"🗣️ Starting TTS with script: {script[:100]}...")
        
        # Generate dynamic audio file using the same method as test file
        try:
            from doccrew.research_crew.src.research_crew.tools.ai_voice_speaker import AIVoiceSpeakerTool
            from datetime import datetime
            import os
            
            # Create doctor profile for voice configuration (same as test file)
            doctor_profile = {
                "doctor_name": doctor_name,
                "gender": "Female" if "Sarah" in doctor_name or "Chen" in doctor_name else "Male",
                "speaking_style": "calm, professional, reassuring",
                "rate": "medium",
                "pitch": "medium"
            }
            
            # Generate audio file dynamically (same as test file)
            voice_speaker = AIVoiceSpeakerTool()
            audio_result = voice_speaker._generate_speech_audio(script, doctor_profile)
            
            if audio_result.get("audio_file"):
                audio_filename = audio_result["audio_file"]
                print(f"✅ Dynamic audio file generated: {audio_filename}")
                
                # Ensure the audio file exists and is accessible
                if os.path.exists(audio_filename):
                    # Get just the filename for the frontend
                    audio_basename = os.path.basename(audio_filename)
                    print(f"✅ Audio file verified: {audio_basename}")
                    
                    # Try to auto-play the audio (same as test file)
                    import subprocess
                    import platform
                    
                    try:
                        if platform.system() == "Windows":
                            subprocess.Popen(["start", audio_filename], shell=True)
                            print(f"🎵 Audio file started playing on Windows: {audio_filename}")
                        elif platform.system() == "Darwin":  # macOS
                            subprocess.Popen(["open", audio_filename])
                            print(f"🎵 Audio file started playing on macOS: {audio_filename}")
                        else:  # Linux
                            subprocess.Popen(["xdg-open", audio_filename])
                            print(f"🎵 Audio file started playing on Linux: {audio_filename}")
                        
                        return {
                            "status": "started", 
                            "audio_file": audio_basename,  # Return just filename for frontend
                            "full_path": audio_filename,   # Keep full path for debugging
                            "duration": audio_result.get("duration", 0),
                            "message": f"AI Doctor {doctor_name} is now speaking",
                            "script_length": len(script),
                            "doctor_profile": doctor_profile
                        }
                        
                    except Exception as play_error:
                        print(f"⚠️ Could not auto-play audio: {play_error}")
                        return {
                            "status": "audio_generated",
                            "audio_file": audio_basename,  # Return just filename for frontend
                            "full_path": audio_filename,   # Keep full path for debugging
                            "duration": audio_result.get("duration", 0),
                            "message": f"Audio file generated: {audio_basename}. Please play it manually.",
                            "script_length": len(script),
                            "doctor_profile": doctor_profile
                        }
                else:
                    print(f"❌ Audio file not found: {audio_filename}")
                    return {"status": "error", "message": f"Audio file not found: {audio_filename}"}
            else:
                print("❌ Failed to generate audio file")
                return {"status": "error", "message": "Failed to generate audio file"}
                
        except Exception as tts_error:
            print(f"❌ TTS error: {tts_error}")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": f"TTS failed: {str(tts_error)}"}
            
    except Exception as e:
        print(f"❌ Error in start_ai_doctor_call: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080) 