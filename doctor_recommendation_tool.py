import pandas as pd
import json
import os
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import google.generativeai as genai
from model_config import get_model_with_retry
from datetime import datetime, timedelta
from .date_utils import get_next_available_slots, convert_slot_to_actual_date

# Initialize Google Gemini client
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
try:
    model = genai.GenerativeModel('gemini-1.5-pro')
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Gemini model: {e}")
    model = None

class DoctorRecommendationInput(BaseModel):
    patient_info: dict = Field(..., description="Patient information including symptoms, location, insurance")
    symptom_assessment: dict = Field(..., description="Symptom severity assessment")

class DoctorRecommendationTool(BaseTool):
    name: str = "Doctor Recommendation from CSV"
    description: str = "Recommend doctors from CSV database based on patient info, symptoms, location, and insurance preferences"
    args_schema: Type[BaseModel] = DoctorRecommendationInput

    def _run(self, patient_info: dict, symptom_assessment: dict) -> str:
        try:
            # Configure Gemini
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            
            # Get API key for fallback
            api_key = "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"
            
            print(f"DEBUG: DoctorRecommendationTool using API key: {api_key[:20]}...")
            
            # Use stable Gemini model
            try:
                model = get_model_with_retry()
            except:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                except:
                    model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Load doctor database from CSV - use single consolidated database
            possible_paths = [
                os.path.join(os.getcwd(), 'doctor_database.csv'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'doctor_database.csv'),
                'doctor_database.csv'
            ]
            
            # Debug: Print all possible paths
            print(f"DEBUG: Current working directory: {os.getcwd()}")
            print(f"DEBUG: File location: {__file__}")
            for i, path in enumerate(possible_paths):
                exists = os.path.exists(path)
                print(f"DEBUG: Path {i+1}: {path} - EXISTS: {exists}")
            
            csv_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    csv_path = path
                    print(f"DEBUG: Found CSV at: {csv_path}")
                    break
            
            if not csv_path:
                print("DEBUG: No CSV file found in any location!")
                return json.dumps({
                    "error": "Doctor database not found",
                    "recommended_doctors": [],
                    "message": "We couldn't find the doctor database. Please contact support."
                })

            df = pd.read_csv(csv_path)
            print(f"DEBUG: Successfully loaded CSV with {len(df)} rows")
            print(f"DEBUG: CSV columns: {list(df.columns)}")
            print(f"DEBUG: First few rows:")
            print(df.head(3))
            
            # Extract patient preferences
            patient_location = patient_info.get('location', 'Pune')
            patient_insurance = patient_info.get('insurance', '')
            symptoms = patient_info.get('symptoms', '')
            severity = symptom_assessment.get('severity', 'Medium')
            
            print(f"DEBUG: Full patient_info: {patient_info}")
            print(f"DEBUG: Full symptom_assessment: {symptom_assessment}")
            print(f"DEBUG: Patient location: {patient_location}")
            print(f"DEBUG: Patient insurance: {patient_insurance}")
            print(f"DEBUG: Patient symptoms: {symptoms}")
            print(f"DEBUG: Symptom severity: {severity}")
            
            # Use LLM to determine appropriate specialty based on symptoms
            specialty_prompt = f"""
            Based on the patient's symptoms, determine the most appropriate medical specialty.
            Symptoms: {symptoms}
            Severity: {severity}
            
            IMPORTANT: Map symptoms to the correct specialty (in order of preference):
            - Fever, common cold, general illness → General Physician (FIRST CHOICE for general symptoms)
            - Stomach ache, abdominal pain, digestive issues → Gastroenterologist
            - Heart/chest pain, cardiovascular issues → Cardiologist  
            - Severe headache, brain/nervous system issues → Neurologist
            - Skin problems, rashes → Dermatologist
            - Mental health, depression, anxiety → Psychiatrist
            - Bone/joint pain, fractures → Orthopedist
            - Diabetes, hormone issues → Endocrinologist
            - Children's health → Pediatrician
            
            For fever and headache, recommend General Physician first.
            Return only the specialty name, nothing else.
            """
            
            specialty_response = model.generate_content(specialty_prompt)
            recommended_specialty = specialty_response.text.strip()
            
            # Filter doctors by location and specialty
            print(f"DEBUG: Looking for doctors in {patient_location} with specialty {recommended_specialty}")
            print(f"DEBUG: Available locations in CSV: {df['location'].unique()}")
            print(f"DEBUG: Available specialties in CSV: {df['specialty'].unique()}")
            
            # First try: exact location and specialty match
            filtered_doctors = df[
                (df['location'].str.lower() == patient_location.lower()) &
                (df['specialty'].str.lower() == recommended_specialty.lower())
            ]
            print(f"DEBUG: Found {len(filtered_doctors)} doctors with exact match")
            
            # Second try: if no exact match, try any doctor in the location
            if filtered_doctors.empty:
                print(f"DEBUG: No exact specialty match in {patient_location}, trying any doctor in location")
                filtered_doctors = df[df['location'].str.lower() == patient_location.lower()]
                print(f"DEBUG: Found {len(filtered_doctors)} doctors in {patient_location}")
            
            # Third try: if still no doctors, expand to all locations with the specialty
            if filtered_doctors.empty:
                print(f"DEBUG: No doctors found in {patient_location}, expanding search to all locations with specialty {recommended_specialty}")
                filtered_doctors = df[df['specialty'].str.lower() == recommended_specialty.lower()]
                print(f"DEBUG: Found {len(filtered_doctors)} doctors with specialty {recommended_specialty} in all locations")
            
            # Fourth try: if still no doctors, show any available doctors
            if filtered_doctors.empty:
                print(f"DEBUG: No doctors found with specialty {recommended_specialty}, showing all available doctors")
                filtered_doctors = df
                print(f"DEBUG: Found {len(filtered_doctors)} total doctors available")
            
            if filtered_doctors.empty:
                return json.dumps({
                    "error": "No suitable doctors found",
                    "recommended_doctors": [],
                    "message": "We couldn't find any doctors matching your requirements. Please try a different location or contact us for assistance."
                })
            
            # Process insurance matching
            recommended_doctors = []
            insurance_matched = False
            
            for _, doctor in filtered_doctors.iterrows():
                doctor_insurances = doctor['insurance'].split(',') if pd.notna(doctor['insurance']) else []
                doctor_insurances = [ins.strip().lower() for ins in doctor_insurances]
                
                # Check if patient's insurance is accepted (case-insensitive)
                # Fix: Add null check for patient_insurance before calling .lower()
                insurance_accepted = False
                if patient_insurance and patient_insurance.strip():  # Check if insurance exists and is not empty
                    insurance_accepted = patient_insurance.lower() in doctor_insurances
                
                if insurance_accepted:
                    insurance_matched = True
                
                # Parse available slots with actual dates
                slots_str = doctor['available_slots'] if pd.notna(doctor['available_slots']) else ""
                available_slots = []
                if slots_str:
                    # Use the new date utility to get actual dates
                    available_slots = get_next_available_slots(slots_str, max_slots=5)
                    print(f"DEBUG: Generated {len(available_slots)} actual date slots for {doctor['name']}")
                    
                    # --- ENHANCED URGENT CASE LOGIC ---
                    urgency = symptom_assessment.get('urgency', '').lower()
                    if urgency in ['soon', 'urgent']:
                        print(f"DEBUG: Urgent case detected ({urgency}) - creating immediate slots")
                        
                        # Create immediate/same-day emergency slots
                        now = datetime.now()
                        emergency_slots = []
                        
                        # Add slots for today if it's before 6 PM
                        if now.hour < 18:  # Before 6 PM
                            # Add emergency slots every 2 hours starting from next hour
                            for hours_ahead in [1, 3, 5, 7]:
                                emergency_time = now + timedelta(hours=hours_ahead)
                                if emergency_time.hour < 18:  # Only during business hours
                                    emergency_slots.append({
                                        "datetime": emergency_time.isoformat(),
                                        "formatted_date": emergency_time.strftime("%Y-%m-%d %I:%M %p"),
                                        "available": True,
                                        "original_slot": f"URGENT - {emergency_time.strftime('%I:%M %p')}",
                                        "is_emergency": True
                                    })
                        
                        # Add tomorrow's early slots for urgent cases
                        tomorrow = now + timedelta(days=1)
                        for hour in [8, 10, 12, 14, 16]:  # 8 AM, 10 AM, 12 PM, 2 PM, 4 PM
                            tomorrow_slot = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
                            emergency_slots.append({
                                "datetime": tomorrow_slot.isoformat(),
                                "formatted_date": tomorrow_slot.strftime("%Y-%m-%d %I:%M %p"),
                                "available": True,
                                "original_slot": f"URGENT - {tomorrow_slot.strftime('%A %I:%M %p')}",
                                "is_emergency": True
                            })
                        
                        # Use emergency slots for urgent cases, keep regular slots as backup
                        if emergency_slots:
                            available_slots = emergency_slots[:5]  # Limit to 5 urgent slots
                            print(f"DEBUG: Created {len(available_slots)} emergency slots for urgent case")
                        else:
                            # Fallback: use regular slots but prioritize earliest ones
                            available_slots = available_slots[:3]  # Limit to earliest 3 slots
                            print(f"DEBUG: No emergency slots available, using earliest regular slots")
                    # --- END ENHANCED URGENT CASE LOGIC ---
                else:
                    print(f"DEBUG: No slots available for {doctor['name']}")
                
                doctor_info = {
                    "name": doctor['name'],
                    "specialty": doctor['specialty'],
                    "location": doctor['location'],
                    "hospital": doctor['hospital'],
                    "cost": int(doctor['cost']) if pd.notna(doctor['cost']) else 0,
                    "insurance": doctor_insurances,
                    "available_slots": available_slots,
                    "insurance_accepted": insurance_accepted
                }
                
                recommended_doctors.append(doctor_info)
            
            # Sort by insurance acceptance first, then by cost
            recommended_doctors.sort(key=lambda x: (not x['insurance_accepted'], x['cost']))
            
            # Limit to top 5 recommendations
            recommended_doctors = recommended_doctors[:5]
            
            # Create response message
            if patient_insurance and not insurance_matched:
                message = f"We found {len(recommended_doctors)} doctors in {patient_location} specializing in {recommended_specialty}. Unfortunately, none of them accept {patient_insurance} insurance. However, we've listed alternative options with different insurance providers."
            else:
                message = f"We found {len(recommended_doctors)} doctors in {patient_location} specializing in {recommended_specialty}."
            
            result = {
                "recommended_specialty": recommended_specialty,
                "recommended_doctors": recommended_doctors,
                "patient_location": patient_location,
                "patient_insurance": patient_insurance,
                "insurance_matched": insurance_matched,
                "message": message,
                "criteria": {
                    "location": patient_location,
                    "specialty": recommended_specialty,
                    "insurance": patient_insurance,
                    "severity": severity
                }
            }
            
            print(f"DEBUG: Final result before JSON conversion: {result}")
            json_result = json.dumps(result, indent=2)
            print(f"DEBUG: JSON result: {json_result}")
            return json_result
            
        except Exception as e:
            print(f"DEBUG: Exception in DoctorRecommendationTool: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({
                "error": f"Failed to recommend doctors: {str(e)}",
                "recommended_doctors": [],
                "message": "We encountered an error while finding doctors. Please try again.",
                "patient_location": patient_info.get('location', 'Unknown'),
                "patient_insurance": patient_info.get('insurance', 'Unknown'),
                "insurance_matched": False
            }) 