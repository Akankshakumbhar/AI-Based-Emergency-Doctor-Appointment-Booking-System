#!/usr/bin/env python3
"""
Script to update all model instances to use the new model configuration
"""

import os
import re

def update_file_models(file_path):
    """Update model instances in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file already has the import
        if "from ..config.model_config import get_model_with_retry" not in content:
            # Add import if not present
            if "import google.generativeai as genai" in content:
                content = content.replace(
                    "import google.generativeai as genai",
                    "import google.generativeai as genai\nfrom ..config.model_config import get_model_with_retry"
                )
            elif "import google.generativeai as genai" in content:
                content = content.replace(
                    "import google.generativeai as genai",
                    "import google.generativeai as genai\nfrom ..config.model_config import get_model_with_retry"
                )
        
        # Replace model instances
        old_pattern = r"genai\.GenerativeModel\('gemini-2\.0-flash'\)"
        new_pattern = "get_model_with_retry()"
        
        if re.search(old_pattern, content):
            content = re.sub(old_pattern, new_pattern, content)
            print(f"✅ Updated {file_path}")
        else:
            print(f"⏭️  No gemini-2.0-flash found in {file_path}")
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"❌ Error updating {file_path}: {e}")

def main():
    """Main function to update all model files"""
    print("🔄 Updating model instances to use new configuration...")
    
    # List of files to update
    files_to_update = [
        "doccrew/research_crew/src/research_crew/tools/emergency_tool.py",
        "doccrew/research_crew/src/research_crew/tools/ai_virtual_doctor.py",
        "doccrew/research_crew/src/research_crew/tools/custom_tool.py",
        "doccrew/research_crew/src/research_crew/tools/doctor_recommendation_tool.py",
        "doccrew/research_crew/src/research_crew/tools/video_call_tool.py",
        "doccrew/research_crew/src/research_crew/tools/reminder_tool.py",
        "doccrew/research_crew/src/research_crew/tools/gemini.py",
        "doccrew/research_crew/src/research_crew/test_system.py"
    ]
    
    for file_path in files_to_update:
        if os.path.exists(file_path):
            update_file_models(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n🎉 Model update completed!")
    print("📝 The system will now use gemini-1.5-flash as the default model")
    print("🔄 If that fails, it will automatically try fallback models")

if __name__ == "__main__":
    main() 