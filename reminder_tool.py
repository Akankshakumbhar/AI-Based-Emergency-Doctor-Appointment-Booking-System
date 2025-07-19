#!/usr/bin/env python3
"""
Comprehensive reminder tool for appointment reminders
"""

import json
import os
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from datetime import datetime, timedelta
from .date_utils import parse_appointment_time, calculate_reminder_time, format_appointment_date
from .notification_tool import PushNotificationTool
from .reminder_scheduler import reminder_scheduler
import google.generativeai as genai
from model_config import get_model_with_retry

# Initialize Google Gemini for message generation
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class ReminderInput(BaseModel):
    appointment_data: dict = Field(..., description="Appointment information")
    patient_data: dict = Field(..., description="Patient information")

class CompleteReminderTool(BaseTool):
    name: str = "Schedule Complete Reminder"
    description: str = "Handle the entire reminder process - scheduling, message generation, and delivery"
    args_schema: Type[BaseModel] = ReminderInput

    def _run(self, appointment_data: dict, patient_data: dict) -> str:
        """
        Complete reminder workflow:
        1. Calculate reminder time (30 minutes before appointment)
        2. Generate personalized reminder message
        3. Schedule the reminder
        4. Return confirmation
        """
        try:
            # Store appointment data for use in other methods
            self._current_appointment_data = appointment_data.copy()
            
            print(f"🔔 Starting reminder process for appointment: {appointment_data.get('appointment_id', 'Unknown')}")
            
            # Step 1: Parse appointment time and calculate reminder time
            appointment_date_str = appointment_data.get('appointment_date', '')
            appointment_datetime = parse_appointment_time(appointment_date_str)
            # Set reminder 30 minutes before appointment
            reminder_time = appointment_datetime - timedelta(minutes=30)
            
            print(f"📅 Appointment: {format_appointment_date(appointment_datetime)}")
            print(f"⏰ Reminder scheduled for: {format_appointment_date(reminder_time)}")
            
            # Step 2: Generate personalized reminder message
            reminder_message = self._generate_personalized_message(appointment_data, patient_data)
            print(f"💬 Generated reminder message: {reminder_message[:100]}...")
            
            # Step 3: Schedule the reminder (in a real system, this would use a scheduler)
            reminder_scheduled = self._schedule_reminder(
                appointment_data.get('appointment_id'),
                reminder_time,
                reminder_message,
                patient_data  # Pass the actual patient data
            )
            
            # Step 4: Update appointment data with reminder info (keep original appointment_date)
            appointment_data.update({
                "reminder_scheduled": True,
                "reminder_time": reminder_time.isoformat(),
                "reminder_sent": False,
                "reminder_message": reminder_message
            })
            
            # Step 5: Save updated appointment data
            self._save_appointment_data(appointment_data)
            
            result = {
                "status": "success",
                "reminder_scheduled": True,
                "reminder_time": format_appointment_date(reminder_time),
                "appointment_time": format_appointment_date(appointment_datetime),
                "message_preview": reminder_message[:100] + "...",
                "appointment_id": appointment_data.get('appointment_id')
            }
            
            print(f"✅ Reminder successfully scheduled for {format_appointment_date(reminder_time)}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            print(f"❌ Error in reminder process: {e}")
            error_result = {
                "status": "error",
                "error": str(e),
                "reminder_scheduled": False
            }
            return json.dumps(error_result, indent=2)

    def _generate_personalized_message(self, appointment_data: dict, patient_data: dict) -> str:
        """Generate personalized reminder message using LLM"""
        try:
            # Prepare context for LLM
            context = {
                "patient_name": patient_data.get('name', 'Patient'),
                "patient_age": patient_data.get('age', 'Unknown'),
                "symptoms": patient_data.get('symptoms', 'Not specified'),
                "doctor_name": appointment_data.get('doctor_name', 'Doctor'),
                "doctor_specialty": appointment_data.get('doctor_specialty', 'General'),
                "appointment_date": appointment_data.get('appointment_date', ''),
                "hospital": appointment_data.get('hospital', 'Hospital'),
                "appointment_id": appointment_data.get('appointment_id', 'Unknown')
            }
            
            prompt = f"""
            Create a warm, personalized appointment reminder message for a medical appointment.
            
            Patient Information:
            - Name: {context['patient_name']}
            - Age: {context['patient_age']}
            - Symptoms: {context['symptoms']}
            
            Appointment Details:
            - Doctor: {context['doctor_name']} ({context['doctor_specialty']})
            - Date & Time: {context['appointment_date']}
            - Hospital: {context['hospital']}
            - Appointment ID: {context['appointment_id']}
            
            Requirements:
            1. Be warm and caring in tone
            2. Include the appointment ID for reference
            3. Mention the doctor's name and specialty
            4. Include relevant preparation instructions based on specialty
            5. Encourage arriving 15 minutes early
            6. Keep it concise but informative
            7. Make it feel personal and professional
            
            Generate a reminder message that the patient will receive 30 minutes before their appointment.
            """
            
            # Generate message using stable Gemini model
            model = get_model_with_retry()
            response = model.generate_content(prompt)
            message = response.text.strip()
            
            # Add appointment ID if not already included
            if context['appointment_id'] not in message:
                message += f"\n\nAppointment ID: {context['appointment_id']}"
            
            return message
            
        except Exception as e:
            print(f"Error generating personalized message: {e}")
            # Fallback message
            return f"""
            Hi {patient_data.get('name', 'there')}!
            
            This is a friendly reminder about your appointment with {appointment_data.get('doctor_name', 'your doctor')} 
            today at {appointment_data.get('appointment_date', 'the scheduled time')}.
            
            Please arrive 15 minutes early and bring any relevant medical reports.
            
            Appointment ID: {appointment_data.get('appointment_id', 'Unknown')}
            
            See you soon!
            """

    def _schedule_reminder(self, appointment_id: str, reminder_time: datetime, message: str, patient_data: dict) -> bool:
        """Schedule the reminder using APScheduler"""
        try:
            # Use the actual scheduler to schedule the reminder
            from .reminder_scheduler import reminder_scheduler
            
            # Get the complete appointment data from the instance
            # The appointment_data should be available from the calling method
            complete_appointment_data = getattr(self, '_current_appointment_data', {})
            
            # Debug logging to see what we're working with
            print(f"🔍 DEBUG: _current_appointment_data = {complete_appointment_data}")
            
            # Ensure we have at least the appointment ID and message
            complete_appointment_data.update({
                "appointment_id": appointment_id,
                "reminder_message": message
            })
            
            # Additional safety check - if we don't have critical data, try to load from file
            if not complete_appointment_data.get('doctor_name') or not complete_appointment_data.get('appointment_date'):
                print(f"⚠️ Missing critical data, trying to load from appointment file...")
                try:
                    import os
                    import json
                    appointment_file = f"appointment_{appointment_id}.json"
                    if os.path.exists(appointment_file):
                        with open(appointment_file, 'r') as f:
                            file_data = json.load(f)
                            # Merge file data with current data, prioritizing file data
                            complete_appointment_data.update(file_data)
                            print(f"✅ Loaded appointment data from file: {appointment_file}")
                except Exception as e:
                    print(f"❌ Could not load appointment data from file: {e}")
            
            print(f"🔍 DEBUG: Final appointment data being sent to scheduler: {complete_appointment_data}")
            
            # Schedule the reminder
            result = reminder_scheduler.schedule_reminder(complete_appointment_data, patient_data, reminder_time)
            
            if result.get("reminder_scheduled"):
                print(f"✅ Reminder scheduled for {format_appointment_date(reminder_time)} (Job ID: {result.get('job_id')})")
                return True
            else:
                print(f"❌ Failed to schedule reminder: {result.get('error')}")
                return False
            
        except Exception as e:
            print(f"Error scheduling reminder: {e}")
            return False

    def _save_appointment_data(self, appointment_data: dict):
        """Save updated appointment data"""
        try:
            filename = f"appointment_{appointment_data.get('appointment_id', 'unknown')}.json"
            with open(filename, 'w') as f:
                json.dump(appointment_data, f, indent=2)
            print(f"💾 Appointment data saved to {filename}")
        except Exception as e:
            print(f"Error saving appointment data: {e}")

    def _save_reminder_data(self, reminder_info: dict):
        """Save reminder scheduling information"""
        try:
            filename = "scheduled_reminders.json"
            
            # Load existing reminders
            existing_reminders = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_reminders = json.load(f)
            
            # Add new reminder
            existing_reminders.append(reminder_info)
            
            # Save updated list
            with open(filename, 'w') as f:
                json.dump(existing_reminders, f, indent=2)
            
            print(f"💾 Reminder data saved to {filename}")
            
        except Exception as e:
            print(f"Error saving reminder data: {e}")

class SendReminderTool(BaseTool):
    name: str = "Send Reminder"
    description: str = "Send a reminder notification to a patient"
    args_schema: Type[BaseModel] = ReminderInput

    def _run(self, appointment_data: dict, patient_data: dict) -> str:
        """Send the actual reminder notification"""
        try:
            # Generate message
            reminder_message = self._generate_reminder_message(appointment_data, patient_data)
            
            # Send notification
            notification_tool = PushNotificationTool()
            result = notification_tool._run(reminder_message)
            
            # Update appointment data
            appointment_data["reminder_sent"] = True
            appointment_data["reminder_sent_at"] = datetime.now().isoformat()
            
            return json.dumps({
                "status": "success",
                "reminder_sent": True,
                "message": reminder_message,
                "notification_result": result
            }, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error": str(e),
                "reminder_sent": False
            }, indent=2)

    def _generate_reminder_message(self, appointment_data: dict, patient_data: dict) -> str:
        """Generate reminder message for immediate sending"""
        try:
            # Similar to CompleteReminderTool but for immediate sending
            context = {
                "patient_name": patient_data.get('name', 'Patient'),
                "doctor_name": appointment_data.get('doctor_name', 'Doctor'),
                "appointment_date": appointment_data.get('appointment_date', ''),
                "hospital": appointment_data.get('hospital', 'Hospital'),
                "appointment_id": appointment_data.get('appointment_id', 'Unknown')
            }
            
            message = f"""
            Hi {context['patient_name']}! 👋
            
            ⏰ Your appointment with {context['doctor_name']} is in 30 minutes.
            📅 Date & Time: {context['appointment_date']}
            🏥 Hospital: {context['hospital']}
            
            Please arrive 15 minutes early and bring any relevant medical reports.
            
            📋 Appointment ID: {context['appointment_id']}
            
            See you soon! 🏥
            """
            
            return message.strip()
            
        except Exception as e:
            print(f"Error generating reminder message: {e}")
            return f"Reminder: Your appointment with {appointment_data.get('doctor_name', 'your doctor')} is in 30 minutes. Appointment ID: {appointment_data.get('appointment_id', 'Unknown')}" 