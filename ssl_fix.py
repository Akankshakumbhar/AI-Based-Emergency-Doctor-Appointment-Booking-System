import os
import ssl
import certifi
import urllib3
import warnings

def fix_ssl_issues():
    """
    Fix SSL certificate verification issues on Windows
    """
    print("🔧 Fixing SSL certificate issues...")
    
    # Method 1: Set environment variable to disable SSL warnings
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    # Method 2: Disable SSL warnings in urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Method 3: Set SSL context
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        print("✅ SSL context configured")
    except Exception as e:
        print(f"⚠️ SSL context setup failed: {e}")
    
    # Method 4: Set requests session defaults
    import requests
    session = requests.Session()
    session.verify = False
    
    print("✅ SSL fixes applied")
    return session

if __name__ == "__main__":
    fix_ssl_issues()
    print("\nNow test your application with: python api.py") 