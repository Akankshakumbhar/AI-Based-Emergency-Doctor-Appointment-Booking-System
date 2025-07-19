from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from pydantic import BaseModel, Field
from tools.custom_tool import PatientDataTool, UserInputTool, SymptomSeverityTool
from tools.doctor_recommendation_tool import DoctorRecommendationTool
from tools.notification_tool import PushNotificationTool
from tools.reminder_tool import CompleteReminderTool, SendReminderTool
from tools.emergency_tool import EmergencyResponseTool
from tools.ai_virtual_doctor import AIVirtualDoctorTool

import os


class PatientInfo(BaseModel):
    patient_id: str = Field(description="Unique identifier for the patient")
    name: str = Field(description="Patient's full name")
    age: int = Field(description="Patient's age in years")
    gender: str = Field(description="Patient's gender")
    contact: str = Field(description="Patient's contact information")
    symptoms: str = Field(description="Patient's symptoms")
    symptom_duration: str = Field(description="Duration of symptoms")
    medical_history: str = Field(description="Patient's medical history")
    current_medications: str = Field(description="Patient's current medications")
    location: str = Field(description="Patient's preferred location (Pune/Mumbai/Nashik/Nagpur)")
    insurance: str = Field(description="Patient's insurance provider (Star Health/ICICI Lombard/HDFC Ergo)")


class SymptomAssessment(BaseModel):
    severity: str = Field(description="Assessed severity level of symptoms")
    urgency: str = Field(description="Urgency level for medical attention")
    reasoning: str = Field(description="Reasoning behind the assessment")
    recommendations: str = Field(description="Initial medical recommendations")


class DoctorRecommendations(BaseModel):
    recommended_specialty: str = Field(description="Recommended medical specialty")
    recommended_doctors: list = Field(description="List of recommended doctors")
    patient_location: str = Field(description="Patient's preferred location")
    patient_insurance: str = Field(description="Patient's insurance provider")
    insurance_matched: bool = Field(description="Whether insurance was matched")
    message: str = Field(description="Recommendation message")
    criteria: dict = Field(description="Filtering criteria used")


class AppointmentBooking(BaseModel):
    appointment_id: str = Field(description="Unique identifier for the appointment")
    patient_name: str = Field(description="Patient's name")
    doctor_name: str = Field(description="Selected doctor's name")
    doctor_specialty: str = Field(description="Doctor's specialty")
    appointment_date: str = Field(description="Appointment date and time")
    hospital: str = Field(description="Hospital name")
    location: str = Field(description="Hospital location")
    cost: int = Field(description="Consultation cost")
    patient_contact: str = Field(description="Patient's contact information")
    notification_sent: bool = Field(description="Whether notification was sent successfully")
    notification_message: str = Field(description="Notification message sent to patient")
    reminder_scheduled: bool = Field(description="Whether reminder was scheduled", default=False)
    reminder_time: str = Field(description="When reminder will be sent", default="")
    reminder_message: str = Field(description="Reminder message content", default="")


class ReminderScheduling(BaseModel):
    status: str = Field(description="Status of reminder scheduling")
    reminder_scheduled: bool = Field(description="Whether reminder was successfully scheduled")
    reminder_time: str = Field(description="When reminder will be sent")
    appointment_time: str = Field(description="Appointment date and time")
    message_preview: str = Field(description="Preview of reminder message")
    appointment_id: str = Field(description="Appointment ID")


class ReminderNotification(BaseModel):
    status: str = Field(description="Status of reminder notification")
    reminder_sent: bool = Field(description="Whether reminder was sent successfully")
    message: str = Field(description="Reminder message content")
    appointment_id: str = Field(description="Appointment ID")


class EmergencyResponse(BaseModel):
    emergency_detected: bool = Field(description="Whether emergency was detected")
    emergency_type: str = Field(description="Type of emergency detected")
    patient_location: str = Field(description="Patient's location")
    ambulance_called: bool = Field(description="Whether ambulance was called")
    ai_doctor_script: str = Field(description="AI-generated doctor consultation script")
    calming_guidance: str = Field(description="Calming guidance for patient")
    immediate_actions: list = Field(description="List of immediate actions to take")
    monitoring_instructions: str = Field(description="Instructions for monitoring patient")


class AIVirtualDoctor(BaseModel):
    ai_doctor_created: bool = Field(description="Whether AI doctor was successfully created")
    doctor_profile: dict = Field(description="AI doctor profile and credentials")
    conversation_script: dict = Field(description="AI doctor conversation script")
    video_call_setup: dict = Field(description="Video call configuration with AI doctor")
    real_time_responses: dict = Field(description="Real-time response templates")
    ambulance_decision: dict = Field(description="Ambulance need evaluation")
    patient_name: str = Field(description="Patient's name")
    emergency_type: str = Field(description="Type of emergency")
    severity_level: str = Field(description="Emergency severity level")


@CrewBase
class PatientCrew():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def patient_info_collector(self) -> Agent:
        return Agent(
            config=self.agents_config['patient_info_collector'],
            tools=[UserInputTool(), PatientDataTool()],
            verbose=True
        )

    @agent
    def symptom_severity_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['symptom_severity_analyzer'],
            tools=[SymptomSeverityTool()],
            verbose=True
        )

    @agent
    def doctor_recommender(self) -> Agent:
        return Agent(
            config=self.agents_config['doctor_recommender'],
            tools=[DoctorRecommendationTool()],
            verbose=True
        )

    @agent
    def appointment_booking_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['appointment_booking_agent'],
            tools=[UserInputTool(), PushNotificationTool()],
            verbose=True
        )

    @agent
    def reminder_specialist(self) -> Agent:
        return Agent(
            config=self.agents_config['reminder_specialist'],
            tools=[CompleteReminderTool(), SendReminderTool()],
            verbose=True
        )

    @agent
    def emergency_response_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['emergency_response_agent'],
            tools=[EmergencyResponseTool()],
            verbose=True
        )

    @agent
    def ai_virtual_doctor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['ai_virtual_doctor_agent'],
            tools=[AIVirtualDoctorTool()],
            verbose=True
        )

    @task
    def collect_info_task(self) -> Task:
        return Task(
            config=self.tasks_config['collect_info_task'],
            output_json=PatientInfo,
            output_file='patient_info.json'
        )

    @task
    def analyze_symptoms_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_symptoms_task'],
            output_json=SymptomAssessment,
            output_file='symptom_assessment.json',
            context=[self.collect_info_task()]
        )

    @task
    def recommend_doctors_task(self) -> Task:
        return Task(
            config=self.tasks_config['recommend_doctors_task'],
            output_json=DoctorRecommendations,
            output_file='doctor_recommendations.json',
            context=[self.collect_info_task(), self.analyze_symptoms_task()]
        )

    @task
    def book_appointment_task(self) -> Task:
        return Task(
            config=self.tasks_config['book_appointment_task'],
            output_json=AppointmentBooking,
            output_file='appointment_booking.json',
            context=[self.collect_info_task(), self.analyze_symptoms_task(), self.recommend_doctors_task()]
        )

    @task
    def schedule_reminder_task(self) -> Task:
        return Task(
            config=self.tasks_config['schedule_reminder_task'],
            output_json=ReminderScheduling,
            output_file='reminder_scheduling.json',
            context=[self.collect_info_task(), self.book_appointment_task()]
        )

    @task
    def send_immediate_reminder_task(self) -> Task:
        return Task(
            config=self.tasks_config['send_immediate_reminder_task'],
            output_json=ReminderNotification,
            output_file='reminder_notification.json',
            context=[self.collect_info_task(), self.book_appointment_task()]
        )

    @task
    def emergency_response_task(self) -> Task:
        return Task(
            config=self.tasks_config['emergency_response_task'],
            output_json=EmergencyResponse,
            output_file='emergency_response.json',
            context=[self.collect_info_task(), self.analyze_symptoms_task()]
        )

    @task
    def ai_virtual_doctor_task(self) -> Task:
        return Task(
            config=self.tasks_config['ai_virtual_doctor_task'],
            output_json=AIVirtualDoctor,
            output_file='ai_virtual_doctor.json',
            context=[self.collect_info_task(), self.analyze_symptoms_task()]
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.patient_info_collector(),
                self.symptom_severity_analyzer(),
                self.emergency_response_agent(),
                self.ai_virtual_doctor_agent(),
                self.doctor_recommender(),
                self.appointment_booking_agent(),
                self.reminder_specialist()
            ],
            tasks=[
                self.collect_info_task(),
                self.analyze_symptoms_task(),
                self.emergency_response_task(),
                self.ai_virtual_doctor_task(),
                self.recommend_doctors_task(),
                self.book_appointment_task(),
                self.schedule_reminder_task(),
                self.send_immediate_reminder_task()
            ],
            process=Process.sequential,
            verbose=True
        )
