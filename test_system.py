#!/usr/bin/env python3
"""
Test script to verify API key, model, and system status
"""

import os
import google.generativeai as genai
from model_config import get_model_with_retry
from crewai import Agent, Task, Crew

def test_api_key():
    """Test the API key directly"""
    print("🔑 Testing API Key...")
    
    # Check environment variable
    env_key = os.getenv('GOOGLE_API_KEY')
    print(f"Environment API Key: {env_key[:20] if env_key else 'NOT SET'}...")
    
    # Test with hardcoded key
    api_key = "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"
    os.environ['GOOGLE_API_KEY'] = api_key
    
    try:
        genai.configure(api_key=api_key)
        model = get_model_with_retry()
        response = model.generate_content("Hello, test message")
        print("✅ Direct API test: SUCCESS")
        print(f"Response: {response.text[:100]}...")
        return True
    except Exception as e:
        print(f"❌ Direct API test: FAILED - {e}")
        return False

def test_crewai_agent():
    """Test CrewAI agent with Gemini"""
    print("\n🤖 Testing CrewAI Agent...")
    
    # Ensure API key is set
    os.environ['GOOGLE_API_KEY'] = "AIzaSyBKfNFHgrdS-5nZ11P1bMrBGlOy-lHR7Ns"
    
    try:
        # Create a simple agent
        test_agent = Agent(
            role="Test Agent",
            goal="Test if the LLM is working",
            backstory="A simple test agent",
            llm="gemini/gemini-2.0-flash",
            verbose=True
        )
        
        # Create a simple task
        test_task = Task(
            description="Say hello and confirm you are working",
            expected_output="A simple hello message",
            agent=test_agent
        )
        
        # Create crew
        crew = Crew(
            agents=[test_agent],
            tasks=[test_task],
            verbose=True
        )
        
        # Execute
        result = crew.kickoff()
        print("✅ CrewAI test: SUCCESS")
        print(f"Result: {result}")
        return True
        
    except Exception as e:
        print(f"❌ CrewAI test: FAILED - {e}")
        return False

def main():
    print("🧪 System Test Suite")
    print("=" * 50)
    
    # Test 1: Direct API
    api_success = test_api_key()
    
    # Test 2: CrewAI Agent
    if api_success:
        crew_success = test_crewai_agent()
    else:
        print("⚠️ Skipping CrewAI test due to API failure")
        crew_success = False
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   API Key: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"   CrewAI:  {'✅ PASS' if crew_success else '❌ FAIL'}")
    
    if api_success and crew_success:
        print("\n🎉 All tests passed! System should work now.")
    else:
        print("\n🚨 Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 