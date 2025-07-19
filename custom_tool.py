import os
import json
from datetime import datetime, timedelta
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import google.generativeai as genai
from model_config import get_model_with_retry
from faker import Faker
import random
import logging
from google.generativeai import GenerativeModel

# Initialize Google Gemini client with API key from environment variable
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Create a model instance with SSL verification disabled
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Gemini model: {e}")
    model = None

fake = Faker()





class PatientDataToolInput(BaseModel):
    patient_data: dict = Field(..., description="Patient info to save")

class PatientDataTool(BaseTool):
    name: str = "Patient Data Saver"
    description: str = "Save patient data to a JSON file while maintaining history"
    args_schema: type[BaseModel] = PatientDataToolInput

    def _run(self, patient_data: dict) -> str:
        file_path = 'patient_info.json'
        try:
            # Try to read existing data first
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    try:
                        all_data = json.load(f)
                        # Ensure data is in the expected format
                        if not isinstance(all_data, dict) or 'history' not in all_data or not isinstance(all_data['history'], list):
                            print("⚠️ Warning: patient_info.json is malformed. Resetting.")
                            all_data = {"history": []}
                    except json.JSONDecodeError:
                        all_data = {"history": []}
            else:
                all_data = {"history": []}

            # Add the new patient data to the history
            history_entry = {
                'data': patient_data,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            all_data["history"].append(history_entry)

            # Save everything back to file
            with open(file_path, 'w') as f:
                json.dump(all_data, f, indent=2)

            # Also save the most recent patient info to a separate file for easy access
            with open('latest_patient.json', 'w') as f:
                json.dump(patient_data, f, indent=2)

            return "✅ Patient data saved successfully to patient_info.json and latest_patient.json"
        except Exception as e:
            return f"❌ Error saving patient data: {str(e)}"

    def get_patient_history(self, patient_name: str) -> list:
        """Get all historical records for a specific patient"""
        try:
            with open('patient_info.json', 'r') as f:
                all_data = json.load(f)
            
            patient_history = []
            
            # Check current record
            if all_data['current'].get('name') == patient_name:
                patient_history.append({
                    'data': all_data['current'],
                    'timestamp': all_data['current'].get('last_updated'),
                    'type': 'current'
                })
            
            # Check history
            for entry in all_data['history']:
                if entry['data'].get('name') == patient_name:
                    patient_history.append(entry)
            
            return patient_history
        except Exception as e:
            return f"Error retrieving patient history: {str(e)}"

class UserInputToolInput(BaseModel):
    question: str = Field(..., description="Question to ask user - must be a simple string, not a dictionary")

class UserInputTool(BaseTool):
    name: str = "Ask User"
    description: str = "Ask the user a question and get their response. IMPORTANT: Pass the question as a simple string, not as a dictionary object."
    args_schema: Type[BaseModel] = UserInputToolInput

    def _run(self, question: str) -> str:
        try:
            # Ensure question is a string
            if isinstance(question, dict):
                question = question.get('description', str(question))
            elif not isinstance(question, str):
                question = str(question)
                
            print(f"\n👤 {question}")
            return input("➡️ ").strip()
        except Exception as e:
            return f"Error getting user input: {str(e)}"

class GeminiChatToolInput(BaseModel):
    prompt: str = Field(..., description="Prompt to send to Gemini")
    temperature: float = Field(default=0.7, description="Temperature for response generation")
    max_tokens: int = Field(default=1000, description="Maximum tokens in response")
    context: str = Field(default="", description="Additional context for the conversation")

class GeminiChatTool(BaseTool):
    name: str = "Gemini Chat Tool"
    description: str = "Enhanced Gemini LLM interaction for medical conversations"
    args_schema: Type[BaseModel] = GeminiChatToolInput

    def _run(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000, context: str = "") -> str:
        try:
            structured_prompt = f"""
            Context: {context}

            Role: You are a medical AI assistant trained to provide helpful, accurate, and empathetic responses.

            Guidelines:
            - Maintain a professional yet friendly tone
            - Provide evidence-based information when possible
            - Be clear about limitations and uncertainties
            - Suggest professional medical consultation when appropriate

            User Query: {prompt}
            """

            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=0.8,
                top_k=40
            )

            response = model.generate_content(
                structured_prompt,
                generation_config=generation_config
            )

            return response.text

        except Exception as e:
            return f"Error calling Gemini API: {str(e)}"

class SymptomSeverityToolInput(BaseModel):
    symptoms: str = Field(..., description="Patient's symptoms - must be a simple string, not a dictionary")
    duration: str = Field(..., description="Duration of symptoms - must be a simple string, not a dictionary")
    impact: str = Field(..., description="Impact on daily life - must be a simple string, not a dictionary")
    medical_history: str = Field(default="", description="Relevant medical history - must be a simple string, not a dictionary")
    age: int = Field(default=0, description="Patient's age - must be a simple integer, not a dictionary")
    current_medications: str = Field(default="", description="Current medications - must be a simple string, not a dictionary")

class SymptomSeverityTool(BaseTool):
    name: str = "Symptom Severity Analyzer"
    description: str = "Gemini-based symptom severity and urgency evaluator. IMPORTANT: Pass all parameters as simple values, not as dictionary objects."
    args_schema: Type[BaseModel] = SymptomSeverityToolInput

    def _run(
        self,
        symptoms: str,
        duration: str,
        impact: str,
        medical_history: str,
        age: int,
        current_medications: str
    ) -> str:
        try:
            # Ensure all inputs are the correct type
            if isinstance(symptoms, dict):
                symptoms = symptoms.get('description', str(symptoms))
            elif not isinstance(symptoms, str):
                symptoms = str(symptoms)
                
            if isinstance(duration, dict):
                duration = duration.get('description', str(duration))
            elif not isinstance(duration, str):
                duration = str(duration)
                
            if isinstance(impact, dict):
                impact = impact.get('description', str(impact))
            elif not isinstance(impact, str):
                impact = str(impact)
                
            if isinstance(medical_history, dict):
                medical_history = medical_history.get('description', str(medical_history))
            elif not isinstance(medical_history, str):
                medical_history = str(medical_history)
                
            if isinstance(age, dict):
                age = age.get('description', 0)
            elif not isinstance(age, int):
                try:
                    age = int(age)
                except:
                    age = 0
                    
            if isinstance(current_medications, dict):
                current_medications = current_medications.get('description', str(current_medications))
            elif not isinstance(current_medications, str):
                current_medications = str(current_medications)
            
            # Configure Gemini with API key
            api_key = "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"
            genai.configure(api_key=api_key)
            model = get_model_with_retry()
            prompt = f"""
You are a medical assistant AI. A patient's symptom data is given below.
Your job is to analyze it and respond ONLY with a JSON object like:

{{
  "severity": "Low | Medium | High",
  "urgency": "Routine | Soon | Urgent",
  "reasoning": "Explain briefly why you chose that severity and urgency."
}}

Patient Info:
- Symptoms: {symptoms}
- Duration: {duration}
- Impact on daily life: {impact}
- Medical history: {medical_history}
- Age: {age}
- Current medications: {current_medications}
"""

            generation_config = genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=800,
                top_p=0.9,
                top_k=40
            )

            response = model.generate_content(prompt, generation_config=generation_config)
            output_text = response.text.strip()

            # Try to return clean JSON
            return output_text if output_text.startswith("{") else json.dumps({
                "severity": "Unknown",
                "urgency": "Unknown",
                "reasoning": "LLM response invalid or unexpected",
                "raw_output": output_text
            })

        except Exception as e:
            return json.dumps({
                "error": str(e),
                "severity": "Unknown",
                "urgency": "Unknown",
                "reasoning": "Exception occurred during Gemini analysis"
            })


