
# text_to_speech_google.py
from gtts import gTTS
import os
import base64
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def synthesize(text):
    """
    Convert text to speech using Google Text-to-Speech API.
    Returns the audio content as a base64-encoded string.
    """
    logger.info(f'Rendering TTS for text: {text[:50]}...' if len(text) > 50 else f'Rendering TTS for text: {text}')
    
    try:
        # Create a gTTS object
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to a BytesIO object instead of file
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # Convert to base64 for easy transmission
        audio_content = mp3_fp.read()
        encoded_audio = base64.b64encode(audio_content).decode('utf-8')
        
        # Log audio size for debugging
        logger.info(f'Generated audio of size: {len(encoded_audio)} bytes')
        
        return encoded_audio
    except Exception as e:
        logger.error(f'Error generating speech: {e}')
        return ''

def save_to_audio_file(audio_content, output_path="output.mp3"):
    """
    Save base64-encoded audio content to a file.
    Useful for debugging or saving audio locally.
    """
    try:
        # Decode base64
        decoded_audio = base64.b64decode(audio_content)
        
        with open(output_path, "wb") as out:
            out.write(decoded_audio)
            logger.info(f'Audio content written to file "{output_path}"')
        
        return True
    except Exception as e:
        logger.error(f'Error saving audio to file: {e}')
        return False

if __name__ == "__main__":
    # Test the TTS functionality
    test_text = "Hello, I'm Paco, your medical assistant. How can I help you today?"
    audio = synthesize(test_text)
    if audio:
        save_to_audio_file(audio)
