import os
import json
from crew import PatientCrew, Crew, Task

def extract_json_from_text(text):
    """Extract JSON data from a text string"""
    try:
        # Find the first occurrence of a JSON-like structure
        start_idx = text.find('{')
        if start_idx == -1:
            return None
            
        # Track brackets to find the matching closing brace
        bracket_count = 0
        for i in range(start_idx, len(text)):
            if text[i] == '{':
                bracket_count += 1
            elif text[i] == '}':
                bracket_count -= 1
                if bracket_count == 0:
                    # Found complete JSON structure
                    json_str = text[start_idx:i+1]
                    return json.loads(json_str)
        return None
    except Exception:
        return None





def main():
    print("🩺 Welcome to the AI Healthcare Assistant!")
    
    # Set API key for Gemini
    api_key = "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"  # Latest working API key
    os.environ['GOOGLE_API_KEY'] = api_key
    os.environ['GEMINI_API_KEY'] = api_key # Some versions of crewai might use this
    
    # Check if API key is set
    if api_key == "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns":
        print("✅ Using the latest working Gemini API key.")
    else:
        print("⚠️  Please replace the API key with your actual Gemini API key!")
        return

    try:
        # Initialize the main crew for patient intake and symptom analysis
        patient_crew_manager = PatientCrew()
        main_crew = patient_crew_manager.crew()
        
        # Kick off the main crew to get patient info and symptom assessment
        print("\n📋 Starting patient intake and symptom analysis process...")
        crew_result = main_crew.kickoff()
        
        print("\n✅ Process completed successfully!")
        print("Thank you for using AI Healthcare Assistant!")
            
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {str(e)}")
        print("🔧 Please check your configuration, API keys, and internet connection.")

if __name__ == "__main__":
    main()
