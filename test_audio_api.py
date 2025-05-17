import requests
import json
import os

# Test audio transcription endpoint
def test_audio_transcription():
    audio_file = os.path.join(os.getcwd(), "harvard.wav")
    url = "http://localhost:8000/audio-transcription"
    
    print(f"Testing audio transcription with {audio_file}...")
    
    headers = {
        "Authorization": "101secretkey"
    }
    
    files = {
        "file": open(audio_file, "rb")
    }
    
    data = {
        "remove_noise": "true",
        "force_english": "true"
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        print("Response:")
        print(json.dumps(response.json(), indent=4))
        return response
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
    finally:
        files["file"].close()

# Test audio analysis endpoint
def test_audio_analysis():
    audio_file = os.path.join(os.getcwd(), "harvard.wav")
    url = "http://localhost:8000/audio-analysis"
    
    print(f"Testing audio analysis with {audio_file}...")
    
    headers = {
        "Authorization": "101secretkey"
    }
    
    files = {
        "file": open(audio_file, "rb")
    }
    
    data = {
        "prompt": "Summarize the key points from this audio",
        "remove_noise": "true",
        "force_english": "true",
        "model_name": "gpt-4o-mini"
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        print("Response:")
        print(json.dumps(response.json(), indent=4))
        return response
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
    finally:
        files["file"].close()

if __name__ == "__main__":
    print("Testing audio transcription...")
    test_audio_transcription()
    
    print("\nTesting audio analysis...")
    test_audio_analysis()
