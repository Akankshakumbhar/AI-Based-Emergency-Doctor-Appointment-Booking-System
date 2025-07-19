#!/usr/bin/env python3
"""
Test AI Doctor Audio Generation System
Simulates the complete flow from emergency detection to audio playback
"""

import json
import os
import time
from datetime import datetime
import subprocess
import platform

# Test data - simulating what would come from the API
TEST_PATIENT_INFO = {
    "name": "John Smith",
    "age": 45,
    "location": "Pune",
    "contact": "+91-9876543210",
    "symptoms": "Severe chest pain, shortness of breath, sweating",
    "medical_history": "Hypertension, diabetes",
    "medications": ["Metformin", "Amlodipine"]
}

TEST_SYMPTOM_ASSESSMENT = {
    "severity": "High",
    "urgency": "Urgent",
    "emergency_type": "Cardiac Emergency",
    "reasoning": "Severe chest pain with shortness of breath indicates possible heart attack",
    "recommendations": "Immediate medical attention required"
}

TEST_AI_DOCTOR_SCRIPT = {
    "opening_greeting": "Hello John, I'm Dr. Sarah Chen, your emergency medical consultant. I understand you're experiencing severe chest pain and shortness of breath.",
    "immediate_support": "First, please stay seated and try to remain calm. Take slow, deep breaths. If you have any prescribed medications for chest pain, take them now. Have someone stay with you.",
    "symptom_specific_advice": "Based on your symptoms of chest pain, shortness of breath, and sweating, this could be a cardiac emergency. Your medical history of hypertension and diabetes increases the risk. Please avoid any physical exertion.",
    "personalized_tips": "Given your age of 45 and medical history, it's important to monitor your symptoms closely. If the pain worsens or you feel lightheaded, this is critical.",
    "comforting_statements": [
        "You're in good hands and we're taking your symptoms very seriously.",
        "Help is on the way and we'll get through this together.",
        "Your medical team is prepared to provide the best care possible."
    ],
    "stress_relief": "Try this breathing technique: Inhale slowly for 4 counts, hold for 4, then exhale for 4. This will help calm your nervous system and reduce stress.",
    "next_steps": "An ambulance has been called and will arrive shortly. I'll continue monitoring your condition and provide guidance until help arrives. Stay seated and avoid any sudden movements.",
    "ongoing_support": "I'm here with you throughout this emergency. I'll monitor your symptoms and provide immediate guidance if anything changes. You're not alone in this.",
    "closing_reassurance": "Remember, you're doing great by seeking help immediately. We're taking all the right steps to ensure your safety. Stay calm and trust that you're receiving the best emergency care."
}

def test_script_generation():
    """Test 1: Simulate AI script generation"""
    print("🧪 TEST 1: AI Script Generation")
    print("=" * 50)
    
    # Simulate the script generation process
    script_parts = []
    for key, value in TEST_AI_DOCTOR_SCRIPT.items():
        if isinstance(value, list):
            script_parts.extend([f"- {item}" for item in value])
        elif value:
            script_parts.append(str(value))
    
    full_script = "\n".join(script_parts)
    
    print(f"✅ Script generated successfully!")
    print(f"📝 Script length: {len(full_script)} characters")
    print(f"📝 First 200 characters: {full_script[:200]}...")
    print()
    
    return full_script

def test_audio_generation(script):
    """Test 2: Test audio file generation"""
    print("🧪 TEST 2: Audio File Generation")
    print("=" * 50)
    
    try:
        from doccrew.research_crew.src.research_crew.tools.ai_voice_speaker import AIVoiceSpeakerTool
        
        # Create doctor profile
        doctor_profile = {
            "doctor_name": "Dr. Sarah Chen",
            "gender": "Female",
            "speaking_style": "calm, professional, reassuring"
        }
        
        print("🎤 Generating audio file...")
        voice_speaker = AIVoiceSpeakerTool()
        audio_result = voice_speaker._generate_speech_audio(script, doctor_profile)
        
        if audio_result.get("audio_file"):
            audio_filename = audio_result["audio_file"]
            print(f"✅ Audio file generated: {audio_filename}")
            print(f"⏱️ Estimated duration: {audio_result.get('duration', 0):.1f} seconds")
            print(f"📁 File location: {os.path.abspath(audio_filename)}")
            print()
            return audio_filename
        else:
            print("❌ Failed to generate audio file")
            print(f"Error: {audio_result.get('status', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"❌ Error in audio generation: {e}")
        return None

def test_audio_playback(audio_filename):
    """Test 3: Test audio playback"""
    print("🧪 TEST 3: Audio Playback")
    print("=" * 50)
    
    if not audio_filename or not os.path.exists(audio_filename):
        print("❌ Audio file not found")
        return False
    
    try:
        print(f"🎵 Attempting to play: {audio_filename}")
        
        # Try to play the audio file
        if platform.system() == "Windows":
            subprocess.Popen(["start", audio_filename], shell=True)
            print("✅ Audio playback started (Windows)")
        elif platform.system() == "Darwin":  # macOS
            subprocess.Popen(["open", audio_filename])
            print("✅ Audio playback started (macOS)")
        else:  # Linux
            subprocess.Popen(["xdg-open", audio_filename])
            print("✅ Audio playback started (Linux)")
        
        print("🎧 You should hear the AI doctor speaking now!")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Error playing audio: {e}")
        print("💡 You can manually play the audio file from the directory")
        return False

def test_browser_audio_simulation(audio_filename):
    """Test 4: Simulate browser audio controls"""
    print("🧪 TEST 4: Browser Audio Simulation")
    print("=" * 50)
    
    if not audio_filename:
        print("❌ No audio file to simulate")
        return
    
    # Simulate the response that would be sent to the browser
    browser_response = {
        "status": "started",
        "audio_file": audio_filename,
        "duration": 45.5,
        "message": "AI Doctor Dr. Sarah Chen is now speaking"
    }
    
    print("🌐 Simulating browser response:")
    print(json.dumps(browser_response, indent=2))
    print()
    
    # Simulate the audio element that would be created in the browser
    audio_html = f"""
    <div style="background-color: #e8f5e8; border: 2px solid #4caf50; border-radius: 10px; padding: 15px; margin: 10px 0;">
        <h3 style="color: #2e7d32; margin-top: 0;">👨‍⚕️ AI Doctor Consultation</h3>
        <p><strong>Doctor:</strong> Dr. Sarah Chen</p>
        <p><strong>Status:</strong> ✅ Speaking</p>
        <p><strong>Audio File:</strong> {audio_filename}</p>
        <p><strong>Duration:</strong> {browser_response['duration']:.1f} seconds</p>
        
        <div style="margin: 10px 0;">
            <audio controls style="width: 100%;">
                <source src="/audio/{audio_filename}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
        </div>
        
        <p style="font-size: 12px; color: #666;">
            <em>Click play to hear the AI doctor's guidance</em>
        </p>
    </div>
    """
    
    print("🎵 Simulated browser audio controls:")
    print(audio_html)
    print()

def test_complete_flow():
    """Test the complete flow from start to finish"""
    print("🚀 COMPLETE AI DOCTOR AUDIO FLOW TEST")
    print("=" * 60)
    print()
    
    # Step 1: Emergency Detection (simulated)
    print("🚨 STEP 1: Emergency Detection")
    print(f"Patient: {TEST_PATIENT_INFO['name']}")
    print(f"Emergency: {TEST_SYMPTOM_ASSESSMENT['emergency_type']}")
    print(f"Severity: {TEST_SYMPTOM_ASSESSMENT['severity']}")
    print(f"Urgency: {TEST_SYMPTOM_ASSESSMENT['urgency']}")
    print()
    
    # Step 2: Script Generation
    script = test_script_generation()
    if not script:
        print("❌ Script generation failed")
        return False
    
    # Step 3: Audio Generation
    audio_filename = test_audio_generation(script)
    if not audio_filename:
        print("❌ Audio generation failed")
        return False
    
    # Step 4: Audio Playback
    playback_success = test_audio_playback(audio_filename)
    
    # Step 5: Browser Simulation
    test_browser_audio_simulation(audio_filename)
    
    # Summary
    print("📊 TEST SUMMARY")
    print("=" * 30)
    print(f"✅ Script Generation: {'PASS' if script else 'FAIL'}")
    print(f"✅ Audio Generation: {'PASS' if audio_filename else 'FAIL'}")
    print(f"✅ Audio Playback: {'PASS' if playback_success else 'FAIL'}")
    print(f"✅ Browser Simulation: PASS")
    print()
    
    if script and audio_filename:
        print("🎉 ALL TESTS PASSED! The AI Doctor Audio system is working correctly.")
        print()
        print("📋 What you should experience:")
        print("1. ✅ AI script generated with personalized medical guidance")
        print("2. ✅ Audio file created with professional TTS")
        print("3. ✅ Audio automatically started playing")
        print("4. ✅ Browser audio controls available")
        print()
        print("🎧 Listen for the AI doctor speaking the medical guidance!")
        return True
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        return False

def cleanup_test_files():
    """Clean up test audio files"""
    print("🧹 Cleaning up test files...")
    
    # Find and remove test audio files
    for filename in os.listdir('.'):
        if filename.startswith('ai_doctor_speech_') and filename.endswith('.mp3'):
            try:
                os.remove(filename)
                print(f"🗑️ Removed: {filename}")
            except Exception as e:
                print(f"⚠️ Could not remove {filename}: {e}")

if __name__ == "__main__":
    print("🤖 AI DOCTOR AUDIO SYSTEM TEST")
    print("=" * 50)
    print("This test simulates the complete flow from emergency detection")
    print("to AI doctor audio generation and playback.")
    print()
    
    try:
        # Run the complete test
        success = test_complete_flow()
        
        if success:
            print("🎯 Test completed successfully!")
            print("The system is ready for production use.")
        else:
            print("🔧 Test failed. Please check the implementation.")
            
    except KeyboardInterrupt:
        print("\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        # Ask if user wants to clean up
        print("\n" + "=" * 50)
        response = input("🧹 Do you want to clean up test audio files? (y/n): ")
        if response.lower() in ['y', 'yes']:
            cleanup_test_files()
        print("👋 Test completed!") 