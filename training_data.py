import json
import random
from faker import Faker

fake = Faker()

# Example symptom severity mapping
symptom_severity_map = {
    "chest pain": "High",
    "headache": "Medium",
    "skin rash": "Low",
    "anxiety": "Medium",
    "diabetes": "High",
    "cough": "Medium",
    "stomach pain": "Medium",
    "bone pain": "Medium",
    "fever": "Medium",
    "child fever": "High"
}

symptom_list = list(symptom_severity_map.keys())

def random_patient():
    symptom = random.choice(symptom_list)
    age = random.randint(1, 90)
    gender = random.choice(["male", "female"])
    history = random.choice(["none", "hypertension", "diabetes", "asthma", "allergy", "smoker", ""])
    medications = random.choice(["none", "paracetamol", "insulin", "antibiotics", ""])
    duration = random.choice(["1 day", "2 days", "1 week", "3 hours", "since morning"])
    severity = symptom_severity_map[symptom]
    urgency = random.choice(["Routine", "Soon", "Urgent"])
    return {
        "name": fake.name(),
        "age": age,
        "gender": gender,
        "contact": fake.email(),
        "symptoms": symptom,
        "symptom_duration": duration,
        "medical_history": history,
        "current_medications": medications,
        "severity": severity,
        "urgency": urgency
    }

# Generate N records
N = 1000  # You can change this to any number you want
data = [random_patient() for _ in range(N)]

# Save to file
with open("synthetic_patient_training_data.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Generated {N} synthetic patient records in synthetic_patient_training_data.json")