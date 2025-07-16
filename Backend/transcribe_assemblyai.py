# # transcribe_assemblyai.py
# import pyaudio
# import wave
# import tempfile
# import requests
# import os
# import time
# import threading
# import logging
# import numpy as np

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def test_microphone():
#     """Test microphone to see if it's working"""
#     try:
#         p = pyaudio.PyAudio()
#         # List all available input devices
#         logger.info("Available audio devices:")
#         for i in range(p.get_device_count()):
#             device_info = p.get_device_info_by_index(i)
#             if device_info.get('maxInputChannels') > 0:
#                 logger.info(f"Device {i}: {device_info.get('name')}")
        
#         # Try to use default device
#         try:
#             default_device = p.get_default_input_device_info()
#             logger.info(f"Default input device: {default_device.get('name')} (index {default_device.get('index')})")
#             default_index = default_device.get('index')
#         except IOError:
#             logger.warning("No default input device available")
#             # Try to find any input device
#             for i in range(p.get_device_count()):
#                 device_info = p.get_device_info_by_index(i)
#                 if device_info.get('maxInputChannels') > 0:
#                     default_index = i
#                     logger.info(f"Using first available input device: {device_info.get('name')} (index {i})")
#                     break
#             else:
#                 logger.error("No input devices found!")
#                 return False
        
#         # Open stream for testing
#         stream = p.open(
#             format=pyaudio.paInt16,
#             channels=1,
#             rate=16000,
#             input=True,
#             frames_per_buffer=1024,
#             input_device_index=default_index
#         )
        
#         logger.info("Recording 3 seconds of audio to test microphone...")
#         frames = []
#         for i in range(0, int(16000 / 1024 * 3)):  # 3 seconds
#             data = stream.read(1024, exception_on_overflow=False)
#             frames.append(data)
        
#         # Check if we got audio (simple volume calculation)
#         audio_data = b''.join(frames)
#         samples = np.frombuffer(audio_data, dtype=np.int16)
#         volume = np.abs(samples).mean()
#         logger.info(f"Average volume: {volume}")
        
#         if volume < 100:
#             logger.warning("Very low audio volume detected! Check microphone connection and volume settings.")
        
#         stream.stop_stream()
#         stream.close()
#         p.terminate()
        
#         # Save test audio to a file for inspection
#         test_file = "mic_test.wav"
#         with wave.open(test_file, 'wb') as wf:
#             wf.setnchannels(1)
#             wf.setsampwidth(2)  # 2 bytes for paInt16
#             wf.setframerate(16000)
#             wf.writeframes(audio_data)
#         logger.info(f"Test audio saved to {test_file}")
        
#         return True
#     except Exception as e:
#         logger.error(f"Microphone test failed: {e}")
#         return False

# # Run a microphone test when the module is loaded
# logger.info("Testing microphone...")
# mic_test_result = test_microphone()
# logger.info(f"Microphone test: {'PASSED' if mic_test_result else 'FAILED'}")

# class AssemblyAITranscriber:
#     def __init__(self, api_key='db4a64a5027a40f89f136e36b3115294'):
#         self.api_key = api_key
#         self.RATE = 16000
#         self.CHUNK = int(self.RATE / 10)  # 100ms chunks
#         self.is_recording = False
#         self.UPLOAD_URL = 'https://api.assemblyai.com/v2/upload'
#         self.TRANSCRIPT_URL = 'https://api.assemblyai.com/v2/transcript'
#         self.current_temp_file = None
#         self.recording_thread = None
#         self.device_index = None
        
#         # Find a working input device
#         self._find_working_input_device()

#     def _find_working_input_device(self):
#         """Find a working microphone input device"""
#         try:
#             p = pyaudio.PyAudio()
            
#             # Try to use default device first
#             try:
#                 default_device = p.get_default_input_device_info()
#                 self.device_index = default_device.get('index')
#                 logger.info(f"Using default input device: {default_device.get('name')} (index {self.device_index})")
#                 p.terminate()
#                 return
#             except IOError:
#                 logger.warning("No default input device available")
            
#             # Try each input device
#             for i in range(p.get_device_count()):
#                 device_info = p.get_device_info_by_index(i)
#                 if device_info.get('maxInputChannels') > 0:
#                     self.device_index = i
#                     logger.info(f"Using input device: {device_info.get('name')} (index {i})")
#                     break
#             else:
#                 logger.error("No input devices found!")
#                 self.device_index = None
            
#             p.terminate()
#         except Exception as e:
#             logger.error(f"Error finding input device: {e}")
#             self.device_index = None

#     def record_audio(self, filename, duration=None):
#         """Record audio from microphone."""
#         try:
#             p = pyaudio.PyAudio()
            
#             # If we don't have a device index, try to find one
#             if self.device_index is None:
#                 self._find_working_input_device()
            
#             logger.info(f"Opening audio stream with device index: {self.device_index}")
#             stream = p.open(
#                 format=pyaudio.paInt16,
#                 channels=1,
#                 rate=self.RATE,
#                 input=True,
#                 frames_per_buffer=self.CHUNK,
#                 input_device_index=self.device_index
#             )
            
#             logger.info("Recording started...")
#             frames = []
            
#             self.is_recording = True
#             start_time = time.time()
            
#             # For audio level monitoring
#             silent_chunks = 0
            
#             while self.is_recording:
#                 if duration and (time.time() - start_time) > duration:
#                     self.is_recording = False
#                     break
                    
#                 try:
#                     data = stream.read(self.CHUNK, exception_on_overflow=False)
#                     frames.append(data)
                    
#                     # Simple audio level monitoring
#                     if len(frames) % 10 == 0:  # Check every 10 chunks
#                         samples = np.frombuffer(data, dtype=np.int16)
#                         volume = np.abs(samples).mean()
#                         if volume < 50:  # Very low volume
#                             silent_chunks += 1
#                             if silent_chunks >= 5:  # 5 consecutive silent chunks
#                                 logger.warning("Low audio volume detected! Check your microphone.")
#                                 silent_chunks = 0  # Reset counter
#                         else:
#                             silent_chunks = 0  # Reset if we get sound
                    
#                 except Exception as e:
#                     logger.error(f"Error reading audio chunk: {e}")
#                     break
            
#             logger.info("Recording complete.")
            
#             try:
#                 stream.stop_stream()
#                 stream.close()
#             except Exception as e:
#                 logger.error(f"Error closing audio stream: {e}")
#             finally:
#                 p.terminate()
#                 logger.info("PyAudio terminated")
            
#             if not frames:
#                 logger.warning("No audio frames captured!")
#                 return False
                
#             try:
#                 with wave.open(filename, 'wb') as wf:
#                     wf.setnchannels(1)
#                     wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
#                     wf.setframerate(self.RATE)
#                     wf.writeframes(b''.join(frames))
#                 logger.info(f"Audio saved to {filename}")
                
#                 # Quick check if the file has content
#                 file_size = os.path.getsize(filename)
#                 logger.info(f"Audio file size: {file_size} bytes")
#                 if file_size < 1000:  # Very small file
#                     logger.warning("Audio file is very small. Possible recording issue.")
                
#                 return True
#             except Exception as e:
#                 logger.error(f"Error saving audio file: {e}")
#                 return False
                
#         except Exception as e:
#             logger.error(f"Error in record_audio: {e}")
#             return False

#     def upload_audio_file(self, file_path):
#         """Upload audio file to AssemblyAI."""
#         try:
#             # Check if file exists and has content
#             if not os.path.exists(file_path):
#                 logger.error(f"File not found: {file_path}")
#                 return None
                
#             file_size = os.path.getsize(file_path)
#             if file_size == 0:
#                 logger.error(f"File is empty: {file_path}")
#                 return None
                
#             logger.info(f"Uploading file: {file_path} ({file_size} bytes)")
            
#             headers = {'authorization': self.api_key}
            
#             with open(file_path, 'rb') as f:
#                 response = requests.post(self.UPLOAD_URL, headers=headers, data=f)
            
#             if response.status_code == 200:
#                 upload_url = response.json()['upload_url']
#                 logger.info(f"Audio uploaded successfully: {upload_url}")
#                 return upload_url
#             else:
#                 logger.error(f"Upload failed: {response.text}")
#                 return None
#         except Exception as e:
#             logger.error(f"Error in upload_audio_file: {e}")
#             return None

#     def transcribe_audio(self, upload_url):
#         """Create transcription job with uploaded audio."""
#         try:
#             headers = {
#                 'authorization': self.api_key,
#                 'content-type': 'application/json'
#             }
#             data = {
#                 'audio_url': upload_url,
#                 'language_detection': True
#             }
            
#             response = requests.post(self.TRANSCRIPT_URL, json=data, headers=headers)
            
#             if response.status_code == 200:
#                 transcript_id = response.json()['id']
#                 logger.info(f"Transcription job created: {transcript_id}")
#                 return transcript_id
#             else:
#                 logger.error(f"Transcription request failed: {response.text}")
#                 return None
#         except Exception as e:
#             logger.error(f"Error in transcribe_audio: {e}")
#             return None

#     def get_transcription_result(self, transcript_id):
#         """Poll for transcription result."""
#         try:
#             headers = {'authorization': self.api_key}
#             max_retries = 30
#             retry_count = 0
            
#             while retry_count < max_retries:
#                 response = requests.get(f'{self.TRANSCRIPT_URL}/{transcript_id}', headers=headers)
#                 result = response.json()
                
#                 if result['status'] == 'completed':
#                     logger.info(f"Transcription completed: {transcript_id}")
#                     return result['text']
#                 elif result['status'] == 'error':
#                     logger.error(f"Transcription error: {result}")
#                     return None
#                 elif result['status'] == 'processing':
#                     logger.info(f"Transcription processing: {transcript_id}")
                
#                 retry_count += 1
#                 time.sleep(3)
            
#             logger.error("Transcription timeout")
#             return None
#         except Exception as e:
#             logger.error(f"Error in get_transcription_result: {e}")
#             return None

#     def cleanup(self):
#         """Clean up temporary files."""
#         if self.current_temp_file and os.path.exists(self.current_temp_file):
#             try:
#                 os.unlink(self.current_temp_file)
#                 logger.info(f"Cleaned up temporary file: {self.current_temp_file}")
#                 self.current_temp_file = None
#             except Exception as e:
#                 logger.error(f"Error cleaning up temporary file: {e}")

#     def reset(self):
#         """Reset the transcriber to a clean state"""
#         logger.info("Resetting transcriber state...")
#         self.is_recording = False
        
#         # Wait for recording thread to finish if it's running
#         if self.recording_thread and self.recording_thread.is_alive():
#             logger.info("Waiting for recording thread to finish...")
#             self.recording_thread.join(timeout=1.0)
        
#         self.cleanup()
        
#         # Force garbage collection to release audio resources
#         import gc
#         gc.collect()
#         logger.info("Transcriber reset complete")
        
#         # Re-detect audio devices
#         self._find_working_input_device()

#     def start_transcription(self, transcript_callback, duration=None):
#         """Start recording and transcription process."""
#         try:
#             # Clean up any existing temporary file
#             self.cleanup()
            
#             # Create new temporary file
#             temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
#             self.current_temp_file = temp_file.name
#             temp_file.close()
#             logger.info(f"Created temporary file: {self.current_temp_file}")

#             def process_and_cleanup():
#                 logger.info("Starting audio recording thread")
#                 success = self.record_audio(self.current_temp_file, duration)
                
#                 if not success:
#                     logger.error("Recording failed")
#                     self.cleanup()
#                     return
                    
#                 logger.info("Audio recording completed, uploading...")
#                 upload_url = self.upload_audio_file(self.current_temp_file)
                
#                 if not upload_url:
#                     logger.error("Upload failed")
#                     self.cleanup()
#                     return
                    
#                 logger.info("Audio uploaded, starting transcription...")
#                 transcript_id = self.transcribe_audio(upload_url)
                
#                 if not transcript_id:
#                     logger.error("Transcription request failed")
#                     self.cleanup()
#                     return
                    
#                 logger.info("Getting transcription results...")
#                 transcript = self.get_transcription_result(transcript_id)
                
#                 if transcript and transcript_callback:
#                     logger.info("Transcription successful, sending callback")
#                     transcript_callback(transcript)
#                 else:
#                     logger.error("Failed to get transcription")
                    
#                 self.cleanup()
#                 logger.info("Audio processing complete")

#             # Start recording in a separate thread
#             self.recording_thread = threading.Thread(target=process_and_cleanup)
#             self.recording_thread.daemon = True
#             self.recording_thread.start()
#             logger.info(f"Started recording thread: {self.recording_thread.name}")

#             def stop_recording():
#                 logger.info("Stop recording called")
#                 if self.is_recording:
#                     self.is_recording = False
#                     # Give the recording thread time to detect the state change
#                     time.sleep(0.2)
#                     return True
#                 return False

#             return stop_recording

#         except Exception as e:
#             logger.error(f"Error in start_transcription: {e}")
#             self.cleanup()
#             return lambda: False

# if __name__ == "__main__":
#     # Test the transcriber
#     transcriber = AssemblyAITranscriber()
    
#     def print_transcript(text):
#         print("Transcription Result:", text)
    
#     print("Starting 10-second test recording...")
#     stop_fn = transcriber.start_transcription(print_transcript)
    
#     # Let it record for 5 seconds
#     time.sleep(5)
    
#     print("Stopping recording...")
#     if stop_fn():
#         print("Recording stopped successfully")
#     else:
#         print("Failed to stop recording")
    
#     # Wait for transcription to complete
#     print("Waiting for transcription to complete...")
#     if transcriber.recording_thread:
#         transcriber.recording_thread.join()
    
#     print("Test complete")

# transcribe_assemblyai.py
import pyaudio
import wave
import tempfile
import requests
import os
import time
import threading
import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AssemblyAITranscriber:
    def __init__(self, api_key='db4a64a5027a40f89f136e36b3115294'):  # Replace with your AssemblyAI API key
        self.api_key = api_key
        self.RATE = 16000
        self.CHUNK = int(self.RATE / 10)  # 100ms chunks
        self.is_recording = False
        self.UPLOAD_URL = 'https://api.assemblyai.com/v2/upload'
        self.TRANSCRIPT_URL = 'https://api.assemblyai.com/v2/transcript'
        self.current_temp_file = None
        self.recording_thread = None
        self.device_index = None
        
        # Find a working input device
        self._find_working_input_device()

    def _find_working_input_device(self):
        """Find a working microphone input device"""
        try:
            p = pyaudio.PyAudio()
            
            # Try to use default device first
            try:
                default_device = p.get_default_input_device_info()
                self.device_index = default_device.get('index')
                logger.info(f"Using default input device: {default_device.get('name')} (index {self.device_index})")
                p.terminate()
                return
            except IOError:
                logger.warning("No default input device available")
            
            # Try each input device
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info.get('maxInputChannels') > 0:
                    self.device_index = i
                    logger.info(f"Using input device: {device_info.get('name')} (index {i})")
                    break
            else:
                logger.error("No input devices found!")
                self.device_index = None
            
            p.terminate()
        except Exception as e:
            logger.error(f"Error finding input device: {e}")
            self.device_index = None

    def record_audio(self, filename, duration=None):
        """Record audio from microphone."""
        try:
            p = pyaudio.PyAudio()
            
            # If we don't have a device index, try to find one
            if self.device_index is None:
                self._find_working_input_device()
            
            logger.info(f"Opening audio stream with device index: {self.device_index}")
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                input_device_index=self.device_index
            )
            
            logger.info("Recording started...")
            frames = []
            
            self.is_recording = True
            start_time = time.time()
            
            # For audio level monitoring
            silent_chunks = 0
            
            while self.is_recording:
                if duration and (time.time() - start_time) > duration:
                    self.is_recording = False
                    break
                    
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    frames.append(data)
                    
                    # Simple audio level monitoring
                    if len(frames) % 10 == 0:  # Check every 10 chunks
                        samples = np.frombuffer(data, dtype=np.int16)
                        volume = np.abs(samples).mean()
                        if volume < 50:  # Very low volume
                            silent_chunks += 1
                            if silent_chunks >= 5:  # 5 consecutive silent chunks
                                logger.warning("Low audio volume detected! Check your microphone.")
                                silent_chunks = 0  # Reset counter
                        else:
                            silent_chunks = 0  # Reset if we get sound
                    
                except Exception as e:
                    logger.error(f"Error reading audio chunk: {e}")
                    break
            
            logger.info("Recording complete.")
            
            try:
                stream.stop_stream()
                stream.close()
            except Exception as e:
                logger.error(f"Error closing audio stream: {e}")
            finally:
                p.terminate()
                logger.info("PyAudio terminated")
            
            if not frames:
                logger.warning("No audio frames captured!")
                return False
                
            try:
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
                    wf.setframerate(self.RATE)
                    wf.writeframes(b''.join(frames))
                logger.info(f"Audio saved to {filename}")
                
                # Quick check if the file has content
                file_size = os.path.getsize(filename)
                logger.info(f"Audio file size: {file_size} bytes")
                if file_size < 1000:  # Very small file
                    logger.warning("Audio file is very small. Possible recording issue.")
                
                return True
            except Exception as e:
                logger.error(f"Error saving audio file: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error in record_audio: {e}")
            return False

    def upload_audio_file(self, file_path):
        """Upload audio file to AssemblyAI."""
        try:
            # Check if file exists and has content
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None
                
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.error(f"File is empty: {file_path}")
                return None
                
            logger.info(f"Uploading file: {file_path} ({file_size} bytes)")
            
            headers = {'authorization': self.api_key}
            
            with open(file_path, 'rb') as f:
                response = requests.post(self.UPLOAD_URL, headers=headers, data=f)
            
            if response.status_code == 200:
                upload_url = response.json()['upload_url']
                logger.info(f"Audio uploaded successfully: {upload_url}")
                return upload_url
            else:
                logger.error(f"Upload failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error in upload_audio_file: {e}")
            return None

    def transcribe_audio(self, upload_url):
        """Create transcription job with uploaded audio."""
        try:
            headers = {
                'authorization': self.api_key,
                'content-type': 'application/json'
            }
            data = {
                'audio_url': upload_url,
                'language_detection': True
            }
            
            response = requests.post(self.TRANSCRIPT_URL, json=data, headers=headers)
            
            if response.status_code == 200:
                transcript_id = response.json()['id']
                logger.info(f"Transcription job created: {transcript_id}")
                return transcript_id
            else:
                logger.error(f"Transcription request failed: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error in transcribe_audio: {e}")
            return None

    def get_transcription_result(self, transcript_id):
        """Poll for transcription result."""
        try:
            headers = {'authorization': self.api_key}
            max_retries = 30
            retry_count = 0
            
            while retry_count < max_retries:
                response = requests.get(f'{self.TRANSCRIPT_URL}/{transcript_id}', headers=headers)
                result = response.json()
                
                if result['status'] == 'completed':
                    logger.info(f"Transcription completed: {transcript_id}")
                    return result['text']
                elif result['status'] == 'error':
                    logger.error(f"Transcription error: {result}")
                    return None
                elif result['status'] == 'processing':
                    logger.info(f"Transcription processing: {transcript_id}")
                
                retry_count += 1
                time.sleep(3)
            
            logger.error("Transcription timeout")
            return None
        except Exception as e:
            logger.error(f"Error in get_transcription_result: {e}")
            return None

    def cleanup(self):
        """Clean up temporary files."""
        if self.current_temp_file and os.path.exists(self.current_temp_file):
            try:
                os.unlink(self.current_temp_file)
                logger.info(f"Cleaned up temporary file: {self.current_temp_file}")
                self.current_temp_file = None
            except Exception as e:
                logger.error(f"Error cleaning up temporary file: {e}")

    def reset(self):
        """Reset the transcriber to a clean state"""
        logger.info("Resetting transcriber state...")
        self.is_recording = False
        
        # Wait for recording thread to finish if it's running
        if self.recording_thread and self.recording_thread.is_alive():
            logger.info("Waiting for recording thread to finish...")
            self.recording_thread.join(timeout=1.0)
        
        self.cleanup()
        
        # Force garbage collection to release audio resources
        import gc
        gc.collect()
        logger.info("Transcriber reset complete")
        
        # Re-detect audio devices
        self._find_working_input_device()

    def start_transcription(self, transcript_callback, duration=None):
        """Start recording and transcription process."""
        try:
            # Clean up any existing temporary file
            self.cleanup()
            
            # Create new temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            self.current_temp_file = temp_file.name
            temp_file.close()
            logger.info(f"Created temporary file: {self.current_temp_file}")

            def process_and_cleanup():
                logger.info("Starting audio recording thread")
                success = self.record_audio(self.current_temp_file, duration)
                
                if not success:
                    logger.error("Recording failed")
                    self.cleanup()
                    return
                    
                logger.info("Audio recording completed, uploading...")
                upload_url = self.upload_audio_file(self.current_temp_file)
                
                if not upload_url:
                    logger.error("Upload failed")
                    self.cleanup()
                    return
                    
                logger.info("Audio uploaded, starting transcription...")
                transcript_id = self.transcribe_audio(upload_url)
                
                if not transcript_id:
                    logger.error("Transcription request failed")
                    self.cleanup()
                    return
                    
                logger.info("Getting transcription results...")
                transcript = self.get_transcription_result(transcript_id)
                
                if transcript and transcript_callback:
                    logger.info("Transcription successful, sending callback")
                    transcript_callback(transcript)
                else:
                    logger.error("Failed to get transcription")
                    
                self.cleanup()
                logger.info("Audio processing complete")

            # Start recording in a separate thread
            self.recording_thread = threading.Thread(target=process_and_cleanup)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            logger.info(f"Started recording thread: {self.recording_thread.name}")

            def stop_recording():
                logger.info("Stop recording called")
                if self.is_recording:
                    self.is_recording = False
                    # Give the recording thread time to detect the state change
                    time.sleep(0.2)
                    return True
                return False

            return stop_recording

        except Exception as e:
            logger.error(f"Error in start_transcription: {e}")
            self.cleanup()
            return lambda: False

if __name__ == "__main__":
    # Test the transcriber
    transcriber = AssemblyAITranscriber()
    
    def print_transcript(text):
        print("Transcription Result:", text)
    
    print("Starting 10-second test recording...")
    stop_fn = transcriber.start_transcription(print_transcript)
    
    # Let it record for 5 seconds
    time.sleep(5)
    
    print("Stopping recording...")
    if stop_fn():
        print("Recording stopped successfully")
    else:
        print("Failed to stop recording")
    
    # Wait for transcription to complete
    print("Waiting for transcription to complete...")
    if transcriber.recording_thread:
        transcriber.recording_thread.join()
    
    print("Test complete")