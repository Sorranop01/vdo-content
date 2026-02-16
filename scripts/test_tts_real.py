
import os
import requests
import base64
from dotenv import load_dotenv

def test_synthesis():
    load_dotenv(override=True)
    api_key = os.getenv("GOOGLE_TTS_API_KEY")
    
    print(f"🔍 Testing Synthesis with Key: {api_key[:5]}...{api_key[-5:]}")
    
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {
        "X-Goog-Api-Key": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }
    data = {
        "input": {"text": "ทดสอบเสียง Neural2 ครับ"},
        "voice": {"languageCode": "th-TH", "name": "th-TH-Neural2-C"},
        "audioConfig": {"audioEncoding": "MP3"}
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Synthesis SUCCESS! (Audio generated)")
        else:
            print(f"❌ Synthesis FAILED: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    test_synthesis()
