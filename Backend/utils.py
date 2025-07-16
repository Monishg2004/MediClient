# utils.py
import pyaudio
import speech_recognition as sr

def get_mic_index(name=None):
    """
    Get microphone index by name.
    If name is None or not found, returns the default microphone.
    """
    p = pyaudio.PyAudio()
    
    # If a specific name is provided, try to find it
    if name:
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('name') == name:
                p.terminate()
                return i
    
    # If name not found or not provided, find the first input device
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info.get('maxInputChannels') > 0:
            p.terminate()
            return i
    
    # Fallback to default
    p.terminate()
    return None

# Initialize the recognizer
recognizer = sr.Recognizer()

# Try to get specified microphone, fall back to default if not found
try:
    device_index = get_mic_index("Ecamm Live Virtual Mic")
    microphone = sr.Microphone(device_index=device_index)
except:
    print("Specified microphone not found, using default microphone")
    microphone = sr.Microphone()
    
# Set recognition parameters for better accuracy
recognizer.energy_threshold = 300  # minimum audio energy to consider for recording
recognizer.dynamic_energy_threshold = True  # automatically adjust for ambient noise
recognizer.pause_threshold = 0.8  # seconds of non-speaking audio before a phrase is considered complete