#!/usr/bin/env python3
"""
Test script to verify audio integration works through the API
This tests the same functionality as test_ai_doctor_audio.py but through the API endpoint
"""

import requests
import json
import time
import os

def test_audio_integration():
    """Test the audio integration through the API endpoint"""
    
    print("🧪 Testing Audio Integration through API...")
    
    # Test data - same as test_ai_doctor_audio.py
    test_script = """
    Hello, I'm Dr. Sarah Chen, your AI Virtual Doctor. I understand you're experiencing a medical emergency.
    
    I'm here to provide immediate guidance and support while emergency services are on their way.
    
    Please remain calm and follow my instructions carefully. I'll help you through this situation.
    
    First, let me assess your current condition and provide appropriate medical guidance.
    """
    
    # Step 1: Store the script
    print("📝 Step 1: Storing AI doctor script...")
    store_response = requests.post('http://localhost:8080/store_ai_script', 
                                 json={"script": test_script})
    
    if store_response.status_code == 200:
        print("✅ Script stored successfully")
    else:
        print(f"❌ Failed to store script: {store_response.text}")
        return
    
    # Step 2: Start AI doctor call
    print("👨‍⚕️ Step 2: Starting AI doctor call...")
    call_response = requests.post('http://localhost:8080/start_ai_doctor_call',
                                json={
                                    "type": "consultation",
                                    "doctor_name": "Dr. Sarah Chen"
                                })
    
    if call_response.status_code == 200:
        result = call_response.json()
        print(f"✅ AI doctor call response: {result}")
        
        if result.get("status") in ["started", "audio_generated"]:
            print(f"🎵 Audio file: {result.get('audio_file')}")
            print(f"📏 Script length: {result.get('script_length')}")
            print(f"⏱️ Duration: {result.get('duration')} seconds")
            print(f"👨‍⚕️ Doctor profile: {result.get('doctor_profile')}")
            
            # Check if audio file exists
            audio_file = result.get("full_path")
            if audio_file and os.path.exists(audio_file):
                print(f"✅ Audio file exists: {audio_file}")
                print(f"📁 File size: {os.path.getsize(audio_file)} bytes")
            else:
                print(f"❌ Audio file not found: {audio_file}")
        else:
            print(f"❌ Audio generation failed: {result.get('message')}")
    else:
        print(f"❌ Failed to start AI doctor call: {call_response.text}")

if __name__ == "__main__":
    # Wait a moment for the server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    try:
        test_audio_integration()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the API is running on http://localhost:8080")
    except Exception as e:
        print(f"❌ Test failed: {e}") 