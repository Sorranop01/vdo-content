import os
import requests
from dotenv import load_dotenv

def check_google_tts():
    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_TTS_API_KEY")
    
    print("🔍 Checking Google TTS API Key...")
    
    if not api_key:
        print("❌ GOOGLE_TTS_API_KEY not found in .env")
        return
        
    print(f"🔑 Key found: {api_key[:5]}...{api_key[-5:]}")
    
    url = f"https://texttospeech.googleapis.com/v1/voices?key={api_key}&languageCode=th-TH"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print("✅ API Key is VALID! (Status 200)")
            voices = response.json().get("voices", [])
            print(f"   Found {len(voices)} Thai voices available.")
        else:
            print(f"❌ API Key INVALID (Status {response.status_code})")
            print(f"   Error: {response.text}")
            print("\n💡 Troubleshooting:")
            if response.status_code == 403:
                print("   - API might not be enabled (Text-to-Speech API)")
                print("   - Billing might not be enabled")
                print("   - Key restrictions (IP/Referrer) might be blocking")
                
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    check_google_tts()