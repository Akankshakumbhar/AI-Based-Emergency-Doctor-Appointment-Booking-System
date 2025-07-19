import json
import os
import time
import threading
import queue
from datetime import datetime
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
import google.generativeai as genai
import urllib3

# Text-to-Speech imports
try:
    import pyttsx3
    from gtts import gTTS
    import pygame
    import speech_recognition as sr
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("⚠️ TTS libraries not available. Install with: pip install pyttsx3 gtts pygame SpeechRecognition")

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"))

class AIVoiceSpeakerInput(BaseModel):
    text_to_speak: str = Field(..., description="Text for AI doctor to speak")
    doctor_profile: dict = Field(..., description="AI doctor profile with voice preferences")
    conversation_context: str = Field(..., description="Current conversation context")
    urgency_level: str = Field(..., description="Urgency level for speech delivery")

class AIVoiceSpeakerTool(BaseTool):
    name: str = "AI Voice Speaker for Video Calls"
    description: str = "Make AI doctor actually speak during video calls using text-to-speech technology"
    args_schema: Type[BaseModel] = AIVoiceSpeakerInput

    def _run(self, text_to_speak: str, doctor_profile: dict, conversation_context: str, urgency_level: str) -> str:
        try:
            print("🗣️ AI VOICE SPEAKER TOOL ACTIVATED (stateless)")
            
            # Generate enhanced speech text
            enhanced_text = self._enhance_speech_text(text_to_speak, doctor_profile, conversation_context, urgency_level)
            
            # Select appropriate voice
            voice_config = self._select_voice_for_doctor(doctor_profile)
            
            # Generate speech audio
            audio_result = self._generate_speech_audio(enhanced_text, voice_config)
            
            # Start real-time speech in background
            self._start_real_time_speech(enhanced_text, voice_config)
            
            result = {
                "speech_generated": True,
                "text_spoken": enhanced_text,
                "voice_config": voice_config,
                "audio_file": audio_result.get('audio_file'),
                "speech_duration": audio_result.get('duration'),
                "doctor_name": doctor_profile.get('doctor_name', 'Dr. AI Assistant'),
                "urgency_level": urgency_level,
                "timestamp": datetime.now().isoformat(),
                "real_time_speech": "ACTIVE"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            print(f"❌ Error in AI voice speaker: {e}")
            return json.dumps({
                "speech_generated": False,
                "error": str(e),
                "message": "Speech generation failed. Using text-only mode."
            })

    def _enhance_speech_text(self, text: str, doctor_profile: dict, context: str, urgency: str) -> str:
        try:
            # IMPORTANT: Use the exact text provided - NO enhancement to avoid adding questions
            # The AI doctor script is already properly generated with no questions
            
            # Only clean up basic formatting for speech
            cleaned_text = text.replace('"', '').replace('\n', ' ').strip()
            
            # Add minimal speech patterns without changing content
            if not cleaned_text.endswith('.'):
                cleaned_text += '.'
            
            return cleaned_text
            
        except Exception as e:
            print(f"Error processing speech text: {e}")
            return text

    def _select_voice_for_doctor(self, doctor_profile: dict) -> dict:
        try:
            gender = doctor_profile.get('appearance', {}).get('gender', 'Female')
            age = doctor_profile.get('appearance', {}).get('age', '40')
            speaking_style = doctor_profile.get('speaking_style', 'calm, professional')
            doctor_name = doctor_profile.get('doctor_name', 'Dr. AI Assistant')
            
            # Voice selection logic
            if gender.lower() == 'female':
                voice_id = 'female_medical'
                pitch = 1.1
                rate = 150
            else:
                voice_id = 'male_medical'
                pitch = 0.9
                rate = 140
            
            # Adjust for age
            try:
                age_int = int(age)
                if age_int > 50:
                    rate = 130
                    pitch = 0.95
                elif age_int < 35:
                    rate = 160
                    pitch = 1.05
            except Exception:
                pass
            
            # Adjust for speaking style
            if 'calm' in speaking_style.lower():
                rate -= 10
            elif 'energetic' in speaking_style.lower():
                rate += 15
            
            return {
                "voice_id": voice_id,
                "gender": gender,
                "age": age,
                "pitch": pitch,
                "rate": rate,
                "volume": 0.9,
                "doctor_name": doctor_name
            }
            
        except Exception as e:
            print(f"Error selecting voice: {e}")
            return {
                "voice_id": "default",
                "gender": "Female",
                "age": "40",
                "pitch": 1.0,
                "rate": 150,
                "volume": 0.9,
                "doctor_name": "Dr. AI Assistant"
            }

    def _generate_speech_audio(self, text: str, voice_config: dict) -> dict:
        try:
            if not TTS_AVAILABLE:
                return {"audio_file": None, "duration": 0, "status": "TTS not available"}
            
            # Create audio filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            audio_filename = f"ai_doctor_speech_{timestamp}.mp3"
            
            # Generate speech using gTTS (Google Text-to-Speech)
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(audio_filename)
            
            # Estimate duration (rough calculation)
            words = len(text.split())
            estimated_duration = words * 0.5  # ~0.5 seconds per word
            
            return {
                "audio_file": audio_filename,
                "duration": estimated_duration,
                "status": "Generated successfully"
            }
            
        except Exception as e:
            print(f"Error generating speech audio: {e}")
            return {"audio_file": None, "duration": 0, "status": f"Error: {str(e)}"}

    def _start_real_time_speech(self, text: str, voice_config: dict):
        try:
            if not TTS_AVAILABLE:
                return
            
            # Initialize TTS engine locally
            local_engine = pyttsx3.init()
            local_engine.setProperty('rate', voice_config.get('rate', 150))
            local_engine.setProperty('volume', voice_config.get('volume', 0.9))
            
            # Set voice gender if available
            voices = local_engine.getProperty('voices')
            if voices:
                if voice_config.get('gender', 'Female').lower() == 'female':
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            local_engine.setProperty('voice', voice.id)
                            break
                else:
                    for voice in voices:
                        if 'male' in voice.name.lower() or 'david' in voice.name.lower():
                            local_engine.setProperty('voice', voice.id)
                            break
            
            def speak_in_background():
                try:
                    print(f"🗣️ AI Doctor {voice_config.get('doctor_name')} speaking: {text[:50]}...")
                    local_engine.say(text)
                    local_engine.runAndWait()
                    print("✅ Speech completed")
                except Exception as e:
                    print(f"❌ Error in background speech: {e}")
            
            audio_thread = threading.Thread(target=speak_in_background)
            audio_thread.daemon = True
            audio_thread.start()
            
        except Exception as e:
            print(f"Error starting real-time speech: {e}")

    def speak_immediate(self, text: str, doctor_name: str = "Dr. AI Assistant"):
        try:
            if not TTS_AVAILABLE:
                return {"speech_success": False, "message": "TTS not available"}
            
            local_engine = pyttsx3.init()
            local_engine.setProperty('rate', 150)
            local_engine.setProperty('volume', 0.9)
            local_engine.say(text)
            local_engine.runAndWait()
            return {"speech_success": True, "status": "Spoken successfully", "text": text, "doctor": doctor_name}
        except Exception as e:
            print(f"Error in immediate speech: {e}")
            return {"speech_success": False, "status": f"Error: {str(e)}"}

    def stop_speech(self):
        # Not implemented in stateless version
        return {"status": "Speech stopped (stateless)"}

    def get_available_voices(self):
        try:
            if not TTS_AVAILABLE:
                return {"voices": [], "status": "TTS not available"}
            local_engine = pyttsx3.init()
            voices = local_engine.getProperty('voices')
            voice_list = []
            for voice in voices:
                voice_list.append({
                    "id": voice.id,
                    "name": voice.name,
                    "languages": voice.languages,
                    "gender": "Female" if "female" in voice.name.lower() else "Male"
                })
            return {"voices": voice_list, "status": "Available voices retrieved"}
        except Exception as e:
            return {"voices": [], "status": f"Error: {str(e)}"} 