#!/usr/bin/env python3
"""
Reminder Scheduler Service using APScheduler
"""

import os
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from .notification_tool import PushNotificationTool
from .date_utils import parse_appointment_time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReminderScheduler:
    """Background scheduler for sending appointment reminders"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        self.notification_tool = PushNotificationTool()
        logger.info("✅ Reminder Scheduler initialized and started")
    
    def schedule_reminder(self, appointment_data: dict, patient_data: dict, reminder_time: datetime):
        """
        Schedule a reminder to be sent at the specified time
        
        Args:
            appointment_data: Dictionary containing appointment information
            patient_data: Dictionary containing patient information
            reminder_time: When to send the reminder
        """
        try:
            # Create a unique job ID
            job_id = f"reminder_{appointment_data.get('appointment_id', 'unknown')}"
            
            # Schedule the reminder
            self.scheduler.add_job(
                func=self._send_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[appointment_data, patient_data],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"✅ Reminder scheduled for {reminder_time} (Job ID: {job_id})")
            
            # Save reminder info
            self._save_reminder_info(appointment_data, patient_data, reminder_time, job_id)
            
            return {
                "status": "success",
                "reminder_scheduled": True,
                "reminder_time": reminder_time.isoformat(),
                "job_id": job_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error scheduling reminder: {e}")
            return {
                "status": "error",
                "error": str(e),
                "reminder_scheduled": False
            }
    
    def _send_reminder(self, appointment_data: dict, patient_data: dict):
        """
        Send the actual reminder notification
        
        Args:
            appointment_data: Dictionary containing appointment information
            patient_data: Dictionary containing patient information
        """
        try:
            logger.info(f"🔔 Sending reminder for appointment {appointment_data.get('appointment_id', 'Unknown')}")
            
            # Generate reminder message
            reminder_message = self._generate_reminder_message(appointment_data, patient_data)
            
            # Send notification
            result = self.notification_tool._run(reminder_message)
            
            # Update appointment data
            appointment_data["reminder_sent"] = True
            appointment_data["reminder_sent_at"] = datetime.now().isoformat()
            appointment_data["reminder_message"] = reminder_message
            
            # Save updated appointment data
            self._save_appointment_data(appointment_data)
            
            logger.info(f"✅ Reminder sent successfully: {result}")
            
        except Exception as e:
            logger.error(f"❌ Error sending reminder: {e}")
    
    def _generate_reminder_message(self, appointment_data: dict, patient_data: dict) -> str:
        """Generate personalized reminder message"""
        try:
            # Debug: Log what data we received
            logger.info(f"🔍 _generate_reminder_message received appointment_data: {appointment_data}")
            logger.info(f"🔍 _generate_reminder_message received patient_data: {patient_data}")
            
            # If we're missing critical data, try to load it from the appointment file
            appointment_id = appointment_data.get('appointment_id', 'Unknown')
            if not appointment_data.get('doctor_name') or not appointment_data.get('appointment_date') or appointment_data.get('doctor_name') == 'Doctor':
                logger.warning(f"⚠️ Missing critical data for {appointment_id}, attempting to load from file...")
                try:
                    appointment_file = f"appointment_{appointment_id}.json"
                    if os.path.exists(appointment_file):
                        with open(appointment_file, 'r') as f:
                            file_data = json.load(f)
                            # Merge file data, prioritizing file data over passed data
                            for key, value in file_data.items():
                                if key not in ['reminder_sent', 'reminder_sent_at', 'reminder_message']:
                                    appointment_data[key] = value
                            logger.info(f"✅ Loaded complete data from {appointment_file}")
                            logger.info(f"🔍 Updated appointment_data: {appointment_data}")
                except Exception as e:
                    logger.error(f"❌ Could not load appointment data from file: {e}")
            
            context = {
                "patient_name": patient_data.get('name', 'Patient'),
                "doctor_name": appointment_data.get('doctor_name', 'Doctor'),
                "doctor_specialty": appointment_data.get('doctor_specialty', 'General'),
                "appointment_date": appointment_data.get('appointment_date', ''),
                "hospital": appointment_data.get('hospital', 'Hospital'),
                "appointment_id": appointment_data.get('appointment_id', 'Unknown')
            }
            
            logger.info(f"🔍 Final context for message generation: {context}")
            
            message = f"""
            Hi {context['patient_name']}! 👋
            
            ⏰ Your appointment with {context['doctor_name']} ({context['doctor_specialty']}) is in 30 minutes.
            📅 Date & Time: {context['appointment_date']}
            🏥 Hospital: {context['hospital']}
            
            Please arrive 15 minutes early and bring any relevant medical reports.
            
            📋 Appointment ID: {context['appointment_id']}
            
            See you soon! 🏥
            """
            
            return message.strip()
            
        except Exception as e:
            logger.error(f"Error generating reminder message: {e}")
            return f"Reminder: Your appointment with {appointment_data.get('doctor_name', 'your doctor')} is in 30 minutes. Appointment ID: {appointment_data.get('appointment_id', 'Unknown')}"
    
    def _save_reminder_info(self, appointment_data: dict, patient_data: dict, reminder_time: datetime, job_id: str):
        """Save reminder scheduling information"""
        try:
            filename = "scheduled_reminders.json"
            
            # Load existing reminders
            existing_reminders = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    existing_reminders = json.load(f)
            
            # Debug logging to see what data we're getting
            logger.info(f"📋 Saving reminder info for appointment: {appointment_data.get('appointment_id')}")
            logger.info(f"📋 Doctor name: {appointment_data.get('doctor_name')}")
            logger.info(f"📋 Appointment date: {appointment_data.get('appointment_date')}")
            logger.info(f"📋 Full appointment_data: {appointment_data}")
            logger.info(f"📋 Full patient_data: {patient_data}")
            
            # Add new reminder - only include fields with valid data
            reminder_info = {
                "appointment_id": appointment_data.get('appointment_id'),
                "reminder_time": reminder_time.isoformat(),
                "job_id": job_id,
                "scheduled_at": datetime.now().isoformat(),
                "status": "scheduled"
            }
            
            # Only add patient name if it exists and is not a placeholder
            patient_name = patient_data.get('name')
            if patient_name and patient_name.strip() and patient_name not in ['Unknown Patient', 'Patient']:
                reminder_info["patient_name"] = patient_name
            
            # Only add doctor name if it exists and is not a placeholder
            doctor_name = appointment_data.get('doctor_name')
            if doctor_name and doctor_name.strip() and doctor_name != 'Doctor':
                reminder_info["doctor_name"] = doctor_name
            
            # Only add appointment date if it exists
            appointment_date = appointment_data.get('appointment_date')
            if appointment_date and appointment_date.strip():
                reminder_info["appointment_date"] = appointment_date
            
            logger.info(f"📋 Final reminder_info being saved: {reminder_info}")
            
            existing_reminders.append(reminder_info)
            
            # Save updated list
            with open(filename, 'w') as f:
                json.dump(existing_reminders, f, indent=2)
            
            logger.info(f"💾 Reminder info saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving reminder info: {e}")
    
    def _save_appointment_data(self, appointment_data: dict):
        """Save updated appointment data"""
        try:
            filename = f"appointment_{appointment_data.get('appointment_id', 'unknown')}.json"
            with open(filename, 'w') as f:
                json.dump(appointment_data, f, indent=2)
            logger.info(f"💾 Appointment data saved to {filename}")
        except Exception as e:
            logger.error(f"Error saving appointment data: {e}")
    
    def get_scheduled_jobs(self):
        """Get all scheduled reminder jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "job_id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "func_name": job.func.__name__
            })
        return jobs
    
    def cancel_reminder(self, appointment_id: str):
        """Cancel a scheduled reminder"""
        try:
            job_id = f"reminder_{appointment_id}"
            self.scheduler.remove_job(job_id)
            logger.info(f"✅ Reminder cancelled for appointment {appointment_id}")
            return {"status": "success", "message": "Reminder cancelled"}
        except Exception as e:
            logger.error(f"❌ Error cancelling reminder: {e}")
            return {"status": "error", "error": str(e)}
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("🛑 Reminder Scheduler shutdown")

# Global scheduler instance
reminder_scheduler = ReminderScheduler() 