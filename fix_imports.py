#!/usr/bin/env python3
"""
Script to fix relative import issues by replacing them with absolute imports
"""

import os
import re

def fix_imports_in_file(file_path):
    """Fix relative imports in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace relative imports with absolute imports
        old_import = "from ..config.model_config import get_model_with_retry"
        new_import = "from model_config import get_model_with_retry"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            print(f"✅ Fixed imports in {file_path}")
        else:
            print(f"⏭️  No relative imports found in {file_path}")
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
    except Exception as e:
        print(f"❌ Error fixing imports in {file_path}: {e}")

def main():
    """Main function to fix all import issues"""
    print("🔧 Fixing relative import issues...")
    
    # List of files to fix
    files_to_fix = [
        "doccrew/research_crew/src/research_crew/tools/ai_virtual_doctor.py",
        "doccrew/research_crew/src/research_crew/tools/doctor_recommendation_tool.py",
        "doccrew/research_crew/src/research_crew/tools/video_call_tool.py",
        "doccrew/research_crew/src/research_crew/tools/reminder_tool.py",
        "doccrew/research_crew/src/research_crew/tools/gemini.py",
        "doccrew/research_crew/src/research_crew/test_system.py"
    ]
    
    for file_path in files_to_fix:
        if os.path.exists(file_path):
            fix_imports_in_file(file_path)
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n🎉 Import fixes completed!")
    print("📝 All tools now use absolute imports from model_config.py")

if __name__ == "__main__":
    main() 