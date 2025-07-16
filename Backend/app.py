# # api.py
# from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
# from pydantic import BaseModel
# from typing import Optional, Dict, Any, List
# import logging
# import time
# import hashlib
# import traceback
# from state import state_store
# from llm import patient_instructor, clinical_note_writer, cds_helper_ddx, cds_helper_qa
# from text_to_speech_google import synthesize
# from transcribe_assemblyai import AssemblyAITranscriber

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Initialize router
# router = APIRouter()

# # Initialize transcriber
# assemblyai_transcriber = AssemblyAITranscriber()

# # Response models
# class RecordingState(BaseModel):
#     active: bool
#     error: Optional[str] = None

# class TranscriptResponse(BaseModel):
#     transcript: str

# class PatientMessage(BaseModel):
#     text: str

# class PatientMessageResponse(BaseModel):
#     text: str
#     done: bool
#     audio: Optional[str] = None
#     message_id: Optional[str] = None

# class GenerateNotesRequest(BaseModel):
#     doctors_hints: str

# class StopRecordingRequest(BaseModel):
#     value: bool = True

# class StartRecordingRequest(BaseModel):
#     value: bool = True

# class PatientModeRequest(BaseModel):
#     enabled: bool

# class SetSummaryRequest(BaseModel):
#     text: str

# class CDSResponse(BaseModel):
#     content: str

# # Status endpoint
# @router.get("/status")
# async def status():
#     return {"status": "ok"}

# # Start recording endpoint
# @router.post("/start_recording", response_model=RecordingState)
# async def start_recording(request: StartRecordingRequest, background_tasks: BackgroundTasks):
#     logger.info("Starting recording")
    
#     # Handle case where previous recording might still be active
#     if state_store.get("stop"):
#         logger.info("Stopping previous recording first")
#         try:
#             state_store.get("stop")()
#         except Exception as e:
#             logger.error(f"Error stopping previous recording: {e}")
#         state_store["stop"] = None
#         time.sleep(0.5)  # Brief pause to ensure resources are released
    
#     try:
#         # Reset the transcriber to ensure clean state
#         if hasattr(assemblyai_transcriber, 'reset'):
#             assemblyai_transcriber.reset()
        
#         state_store["transcript"] = ""
#         state_store["processing"] = False
        
#         # Reset diagnosis and questions to force regeneration
#         state_store["cds_ddx"] = ""
#         state_store["cds_qa"] = ""
        
#         def transcript_callback(text):
#             try:
#                 if not text:
#                     return

#                 logger.info(f"Transcript received: {text[:50]}..." if len(text) > 50 else f"Transcript received: {text}")

#                 if state_store.get("patient_mode"):
#                     state_store["patient_transcript"] = text
#                     return
                
#                 # For doctor mode, update transcript and process
#                 current_transcript = state_store.get("transcript", "")
#                 state_store["transcript"] = current_transcript + text + "\n"
                
#                 # Clear previous diagnosis and questions to force regeneration
#                 state_store["cds_ddx"] = ""
#                 state_store["cds_qa"] = ""
                
#                 # Process the transcript if we have enough content and not already processing
#                 if len(state_store["transcript"]) > 20 and not state_store.get("processing"):
#                     logger.info("Starting transcript processing")
#                     background_tasks.add_task(process_transcript, state_store["transcript"])
            
#             except Exception as e:
#                 logger.error(f"Error in transcript callback: {e}")
#                 logger.error(traceback.format_exc())
        
#         stop = assemblyai_transcriber.start_transcription(transcript_callback)
#         state_store["stop"] = stop
        
#         return RecordingState(active=True)
#     except Exception as e:
#         logger.error(f"Error starting recording: {e}")
#         return RecordingState(active=False, error=str(e))

# # Stop recording endpoint
# @router.post("/stop_recording", response_model=RecordingState)
# async def stop_recording(request: StopRecordingRequest, background_tasks: BackgroundTasks):
#     logger.info("Stopping recording")
#     try:
#         stop = state_store.get("stop")
#         if stop:
#             result = stop()
#             logger.info(f"Stop recording result: {result}")
#             state_store["stop"] = None
            
#             # Reset the transcriber
#             if hasattr(assemblyai_transcriber, 'reset'):
#                 assemblyai_transcriber.reset()
            
#             # Force one last processing of the transcript
#             if not state_store.get("patient_mode") and state_store.get("transcript"):
#                 logger.info("Triggering final transcript processing after recording stop")
#                 if not state_store.get("processing"):
#                     background_tasks.add_task(process_transcript, state_store.get("transcript"))
                
#         return RecordingState(active=False)
#     except Exception as e:
#         logger.error(f"Error stopping recording: {e}")
#         return RecordingState(active=False, error=str(e))

# # Set doctor's summary endpoint
# @router.post("/set_summary")
# async def set_summary(request: SetSummaryRequest):
#     state_store.set_doctor_summary(request.text)
#     logger.info(f"Set summary: {request.text[:50]}..." if len(request.text) > 50 else f"Set summary: {request.text}")
#     return {"status": "success"}

# # Toggle patient mode endpoint
# @router.post("/patient_mode")
# async def patient_mode(request: PatientModeRequest):
#     state_store["patient_mode"] = request.enabled
#     logger.info(f"Patient mode: {request.enabled}")
    
#     # Clear transcripts when switching modes
#     if request.enabled:
#         state_store["patient_transcript"] = ""
#     else:
#         state_store["transcript"] = ""
#         state_store["cds_ddx"] = ""
#         state_store["cds_qa"] = ""
    
#     return {"status": "success"}

# # Get transcript endpoint
# @router.get("/transcript", response_model=TranscriptResponse)
# async def get_transcript():
#     transcript = state_store.get("transcript", "")
#     return TranscriptResponse(transcript=transcript)

# # Get patient transcript endpoint
# @router.get("/patient_transcript", response_model=TranscriptResponse)
# async def get_patient_transcript():
#     transcript = state_store.get("patient_transcript", "")
#     return TranscriptResponse(transcript=transcript)

# # Generate clinical notes endpoint
# @router.post("/generate_notes")
# async def generate_notes(request: GenerateNotesRequest, background_tasks: BackgroundTasks):
#     try:
#         transcript = state_store.get("transcript", "")
#         logger.info(f"Generating notes with transcript length: {len(transcript)}")
        
#         # Define a callback function that will be called from another thread
#         # This simulates the streaming behavior from SocketIO
#         notes_result = {"status": "processing", "content": ""}
        
#         def notes_callback(content):
#             notes_result["content"] = content
#             notes_result["status"] = "complete"
        
#         # Run the clinical note generation in a background task
#         background_tasks.add_task(
#             generate_notes_task,
#             request.doctors_hints,
#             transcript,
#             notes_callback
#         )
        
#         task_id = hashlib.md5(transcript.encode()).hexdigest()[:10]
#         return {"status": "processing", "task_id": task_id}
#     except Exception as e:
#         logger.error(f"Error generating notes: {e}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail=str(e))

# # Notes polling endpoint
# @router.get("/notes_status/{task_id}")
# async def get_notes_status(task_id: str):
#     # In a real implementation, this would check a task queue or database
#     # For now, we'll use a simple approach by storing in state
#     result = state_store.get(f"notes_task_{task_id}", {"status": "not_found"})
#     return result

# # Patient message endpoint
# @router.post("/patient_message", response_model=PatientMessageResponse)
# async def patient_message(message: PatientMessage, background_tasks: BackgroundTasks):
#     try:
#         logger.info(f"Received patient message: {message.text}")
        
#         # Create a unique message ID
#         message_id = f"msg_{hashlib.md5((message.text + str(time.time())).encode()).hexdigest()[:10]}"
        
#         # Store initial state
#         state_store[f"message_{message_id}"] = {
#             "text": "",
#             "done": False,
#             "message_id": message_id
#         }
        
#         # Run patient message processing in background
#         background_tasks.add_task(
#             process_patient_message,
#             message.text,
#             message_id
#         )
        
#         return PatientMessageResponse(
#             text="",
#             done=False,
#             message_id=message_id
#         )
#     except Exception as e:
#         logger.error(f"Error in patient_message: {e}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail=str(e))

# # Patient message polling endpoint
# @router.get("/patient_message_status/{message_id}", response_model=PatientMessageResponse)
# async def get_patient_message_status(message_id: str):
#     message_data = state_store.get(f"message_{message_id}")
#     if not message_data:
#         raise HTTPException(status_code=404, detail="Message not found")
#     return PatientMessageResponse(**message_data)

# # CDS DDX endpoint
# @router.get("/cds_ddx", response_model=CDSResponse)
# async def get_cds_ddx(background_tasks: BackgroundTasks):
#     """Get differential diagnosis suggestions"""
#     content = state_store.get("cds_ddx", "")
#     logger.info(f"CDS DDX content length: {len(content)} chars")
    
#     # If content is empty and transcript exists, try processing
#     if not content and state_store.get("transcript"):
#         logger.info("No DDX content available, triggering processing")
#         transcript = state_store.get("transcript", "")
        
#         # Run differential diagnosis if not already processing
#         if not state_store.get("processing"):
#             state_store["processing"] = True
#             background_tasks.add_task(process_transcript, transcript)
#             # Set a placeholder message
#             content = "Analyzing symptoms for diagnosis, please wait..."
#             state_store["cds_ddx"] = content
    
#     return CDSResponse(content=content)

# # CDS QA endpoint
# @router.get("/cds_qa", response_model=CDSResponse)
# async def get_cds_qa(background_tasks: BackgroundTasks):
#     """Get questions to ask suggestions"""
#     content = state_store.get("cds_qa", "")
#     logger.info(f"CDS QA content length: {len(content)} chars")
    
#     # If content is empty and transcript exists, try processing
#     if not content and state_store.get("transcript"):
#         logger.info("No QA content available, triggering processing")
#         transcript = state_store.get("transcript", "")
        
#         # Run QA suggestions if not already processing
#         if not state_store.get("processing"):
#             state_store["processing"] = True
#             background_tasks.add_task(process_transcript, transcript)
#             # Set a placeholder message
#             content = "Generating suggested questions, please wait..."
#             state_store["cds_qa"] = content
    
#     return CDSResponse(content=content)

# # Background task functions

# async def generate_notes_task(doctors_hints, transcript, callback):
#     """Background task for generating clinical notes"""
#     try:
#         logger.info(f"Starting notes generation with hints: {doctors_hints[:50]}..." if len(doctors_hints) > 50 else f"Starting notes generation with hints: {doctors_hints}")
        
#         # Create a callback adapter for the LLM
#         class CallbackAdapter:
#             def __call__(self, content):
#                 callback(content)
        
#         # Run the clinical note generator
#         notes = clinical_note_writer.run(
#             {
#                 "input": doctors_hints,
#                 "transcript": transcript
#             },
#             callbacks=[CallbackAdapter()]
#         )
        
#         # Store the result in state for polling
#         task_id = hashlib.md5(transcript.encode()).hexdigest()[:10]
#         state_store[f"notes_task_{task_id}"] = {
#             "status": "complete",
#             "content": notes
#         }
        
#         logger.info(f"Notes generation complete, length: {len(notes)}")
#         callback(notes)
#     except Exception as e:
#         logger.error(f"Error in generate_notes_task: {e}")
#         logger.error(traceback.format_exc())
#         callback(f"Error generating notes: {e}")

# async def process_patient_message(text, message_id):
#     """Background task for processing patient messages"""
#     try:
#         logger.info(f"Processing patient message: {text[:50]}..." if len(text) > 50 else f"Processing patient message: {text}")
        
#         # Create a callback adapter for streaming updates
#         response_text = ""
        
#         class StreamingCallback:
#             def __call__(self, content):
#                 nonlocal response_text
#                 response_text = content
#                 # Update the state with the latest content
#                 current = state_store.get(f"message_{message_id}", {})
#                 current["text"] = content
#                 state_store[f"message_{message_id}"] = current
        
#         memory = state_store.get_memory()
#         history = memory.load_memory_variables({})["history"]
#         doctor_summary = state_store.get("doctor_summary", "")
        
#         # Run the patient instructor with the callback
#         response = patient_instructor.run(
#             {
#                 "input": text,
#                 "history": history,
#                 "doctor_summary": doctor_summary
#             },
#             callbacks=[StreamingCallback()]
#         )
        
#         if response:
#             logger.info(f"Patient message response generated, length: {len(response)}")
            
#             # Update conversation memory
#             memory.chat_memory.add_user_message(text)
#             memory.chat_memory.add_ai_message(response)
            
#             # Generate audio if possible
#             audio = None
#             try:
#                 audio = synthesize(response)
#                 logger.info("Audio synthesis successful")
#             except Exception as e:
#                 logger.error(f"Audio synthesis failed: {e}")
            
#             # Update the state with the complete response
#             state_store[f"message_{message_id}"] = {
#                 "text": response,
#                 "done": True,
#                 "audio": audio,
#                 "message_id": message_id
#             }
#     except Exception as e:
#         logger.error(f"Error in process_patient_message: {e}")
#         logger.error(traceback.format_exc())
#         # Update the state with the error
#         state_store[f"message_{message_id}"] = {
#             "text": f"Error processing message: {e}",
#             "done": True,
#             "message_id": message_id
#         }

# def process_transcript(transcript):
#     """Process transcript for differential diagnosis and QA suggestions"""
#     try:
#         if state_store.get("processing") and state_store.get("processing_task_id"):
#             logger.info(f"Already processing transcript task {state_store.get('processing_task_id')}, skipping")
#             return
            
#         # Set a unique task ID for this processing job
#         task_id = hashlib.md5((transcript + str(time.time())).encode()).hexdigest()[:10]
#         state_store["processing"] = True
#         state_store["processing_task_id"] = task_id
        
#         logger.info(f"Processing transcript of length: {len(transcript)} with task ID: {task_id}")
        
#         if len(transcript.strip()) < 10:
#             logger.info("Transcript too short for meaningful analysis")
#             state_store["cds_ddx"] = "Transcript too short. Please continue the conversation to receive diagnosis suggestions."
#             state_store["cds_qa"] = "Transcript too short. Please continue the conversation to receive question suggestions."
#             state_store["processing"] = False
#             state_store["processing_task_id"] = None
#             return
        
#         # Create callback adapters
#         class DDXCallback:
#             def __call__(self, content):
#                 logger.info(f"DDX callback received content of length: {len(str(content))}")
#                 state_store["cds_ddx"] = str(content)
        
#         class QACallback:
#             def __call__(self, content):
#                 logger.info(f"QA callback received content of length: {len(str(content))}")
#                 state_store["cds_qa"] = str(content)
        
#         # Run differential diagnosis
#         logger.info(f"Running differential diagnosis analysis for task {task_id}")
#         ddx_result = cds_helper_ddx.run(
#             {"transcript": transcript},
#             callbacks=[DDXCallback()]
#         )
        
#         if ddx_result:
#             logger.info(f"DDX analysis completed for task {task_id}, result length: {len(str(ddx_result))}")
#             state_store["cds_ddx"] = str(ddx_result)
#         else:
#             logger.warning(f"DDX analysis returned no results for task {task_id}")
#             state_store["cds_ddx"] = "Could not generate differential diagnosis. Please add more clinical information."
        
#         # Run QA suggestions
#         logger.info(f"Running questions to ask analysis for task {task_id}")
#         qa_result = cds_helper_qa.run(
#             {"transcript": transcript},
#             callbacks=[QACallback()]
#         )
        
#         if qa_result:
#             logger.info(f"QA analysis completed for task {task_id}, result length: {len(str(qa_result))}")
#             state_store["cds_qa"] = str(qa_result)
#         else:
#             logger.warning(f"QA analysis returned no results for task {task_id}")
#             state_store["cds_qa"] = "Could not generate suggested questions. Please add more clinical information."
    
#     except Exception as e:
#         logger.error(f"Error processing transcript: {e}")
#         logger.error(traceback.format_exc())
#         state_store["cds_ddx"] = f"Error generating differential diagnosis: {str(e)}"
#         state_store["cds_qa"] = f"Error generating questions: {str(e)}"
#     finally:
#         state_store["processing"] = False
#         state_store["processing_task_id"] = None
#         logger.info("Transcript processing completed")

# app.py - Fixed version
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import time
import hashlib
import traceback
import datetime
import json
import os
from state import state_store
from llm import patient_instructor, clinical_note_writer, cds_helper_ddx, cds_helper_qa
from text_to_speech_google import synthesize
from transcribe_assemblyai import AssemblyAITranscriber

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter()

# Initialize transcriber
assemblyai_transcriber = AssemblyAITranscriber()

# Response models
class RecordingState(BaseModel):
    active: bool
    error: Optional[str] = None

class TranscriptResponse(BaseModel):
    transcript: str

class PatientMessage(BaseModel):
    text: str

class PatientMessageResponse(BaseModel):
    text: str
    done: bool
    audio: Optional[str] = None
    message_id: Optional[str] = None

class GenerateNotesRequest(BaseModel):
    doctors_hints: str

class StopRecordingRequest(BaseModel):
    value: bool = True

class StartRecordingRequest(BaseModel):
    value: bool = True

class PatientModeRequest(BaseModel):
    enabled: bool

class SetSummaryRequest(BaseModel):
    text: str

class CDSResponse(BaseModel):
    content: str

class SaveConversationRequest(BaseModel):
    transcript: str
    audio: Optional[str] = None
    title: str

# Status endpoint
@router.get("/status")
async def status():
    return {"status": "ok"}

# Start recording endpoint
@router.post("/start_recording", response_model=RecordingState)
async def start_recording(request: StartRecordingRequest, background_tasks: BackgroundTasks):
    logger.info("Starting recording")
    
    # Handle case where previous recording might still be active
    if state_store.get("stop"):
        logger.info("Stopping previous recording first")
        try:
            state_store.get("stop")()
        except Exception as e:
            logger.error(f"Error stopping previous recording: {e}")
        state_store["stop"] = None
        time.sleep(0.5)  # Brief pause to ensure resources are released
    
    try:
        # Reset the transcriber to ensure clean state
        if hasattr(assemblyai_transcriber, 'reset'):
            assemblyai_transcriber.reset()
        
        # Reset transcript state
        if state_store.get("patient_mode"):
            logger.info("Resetting patient transcript state")
            state_store["patient_transcript"] = ""
        else:
            logger.info("Resetting doctor transcript state")
            state_store["transcript"] = ""
        
        # Reset processing state
        state_store["processing"] = False
        state_store["processing_task_id"] = None
        
        # Reset diagnosis and questions to force regeneration
        state_store["cds_ddx"] = ""
        state_store["cds_qa"] = ""
        
        def transcript_callback(text):
            try:
                if not text:
                    logger.warning("Empty transcript received in callback")
                    return

                logger.info(f"Transcript received: {text}")

                if state_store.get("patient_mode"):
                    logger.info(f"PATIENT MODE - Setting transcript: '{text}'")
                    # FIXED: Set the entire transcript instead of appending
                    state_store["patient_transcript"] = text
                    logger.info(f"Patient transcript updated: '{text}'")
                    return
                
                # For doctor mode, update transcript and process
                logger.info(f"DOCTOR MODE - Setting transcript: '{text}'")
                # FIXED: Set the entire transcript instead of appending
                state_store["transcript"] = text
                logger.info(f"Doctor transcript updated: '{text}'")
                
                # Only trigger CDS processing if we have enough content and not already processing
                if len(state_store["transcript"]) > 20 and not state_store.get("processing"):
                    logger.info("Starting transcript processing")
                    background_tasks.add_task(process_transcript, state_store["transcript"])
            
            except Exception as e:
                logger.error(f"Error in transcript callback: {e}")
                logger.error(traceback.format_exc())
        
        stop = assemblyai_transcriber.start_transcription(transcript_callback)
        state_store["stop"] = stop
        
        return RecordingState(active=True)
    except Exception as e:
        logger.error(f"Error starting recording: {e}")
        return RecordingState(active=False, error=str(e))

# Stop recording endpoint
@router.post("/stop_recording", response_model=RecordingState)
async def stop_recording(request: StopRecordingRequest, background_tasks: BackgroundTasks):
    logger.info("Stopping recording")
    try:
        stop = state_store.get("stop")
        if stop:
            result = stop()
            logger.info(f"Stop recording result: {result}")
            state_store["stop"] = None
            
            # Reset the transcriber
            if hasattr(assemblyai_transcriber, 'reset'):
                assemblyai_transcriber.reset()
            
            # Force one last processing of the transcript
            if not state_store.get("patient_mode") and state_store.get("transcript"):
                logger.info("Triggering final transcript processing after recording stop")
                if not state_store.get("processing"):
                    background_tasks.add_task(process_transcript, state_store.get("transcript"))
                
        return RecordingState(active=False)
    except Exception as e:
        logger.error(f"Error stopping recording: {e}")
        return RecordingState(active=False, error=str(e))

# Set doctor's summary endpoint
@router.post("/set_summary")
async def set_summary(request: SetSummaryRequest):
    state_store.set_doctor_summary(request.text)
    logger.info(f"Set summary: {request.text[:50]}..." if len(request.text) > 50 else f"Set summary: {request.text}")
    return {"status": "success"}

# Toggle patient mode endpoint
@router.post("/patient_mode")
async def patient_mode(request: PatientModeRequest):
    state_store["patient_mode"] = request.enabled
    logger.info(f"Patient mode: {request.enabled}")
    
    # Clear transcripts when switching modes
    if request.enabled:
        state_store["patient_transcript"] = ""
    else:
        state_store["transcript"] = ""
        state_store["cds_ddx"] = ""
        state_store["cds_qa"] = ""
    
    return {"status": "success"}

# Get transcript endpoint
@router.get("/transcript", response_model=TranscriptResponse)
async def get_transcript():
    transcript = state_store.get("transcript", "")
    logger.info(f"GET /transcript - Returning {len(transcript)} chars: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'")
    return TranscriptResponse(transcript=transcript)

# Get patient transcript endpoint
@router.get("/patient_transcript", response_model=TranscriptResponse)
async def get_patient_transcript():
    transcript = state_store.get("patient_transcript", "")
    logger.info(f"GET /patient_transcript - Returning {len(transcript)} chars: '{transcript[:50]}{'...' if len(transcript) > 50 else ''}'")
    return TranscriptResponse(transcript=transcript)

# Generate clinical notes endpoint
@router.post("/generate_notes")
async def generate_notes(request: GenerateNotesRequest, background_tasks: BackgroundTasks):
    try:
        transcript = state_store.get("transcript", "")
        logger.info(f"Generating notes with transcript length: {len(transcript)}")
        
        # Define a callback function that will be called from another thread
        task_id = hashlib.md5(transcript.encode()).hexdigest()[:10]
        state_store[f"notes_task_{task_id}"] = {
            "status": "processing",
            "content": ""
        }
        
        def notes_callback(content):
            state_store[f"notes_task_{task_id}"]["content"] = content
            state_store[f"notes_task_{task_id}"]["status"] = "complete"
        
        # Run the clinical note generation in a background task
        background_tasks.add_task(
            generate_notes_task,
            request.doctors_hints,
            transcript,
            notes_callback,
            task_id
        )
        
        return {"status": "processing", "task_id": task_id}
    except Exception as e:
        logger.error(f"Error generating notes: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Notes polling endpoint
@router.get("/notes_status/{task_id}")
async def get_notes_status(task_id: str):
    result = state_store.get(f"notes_task_{task_id}", {"status": "not_found"})
    
    # If we've just detected that notes are complete, ensure it's in the doctor's summary
    if result.get("status") == "complete" and "content" in result:
        # Double-check that the doctor's summary is set
        current_summary = state_store.state.get("doctor_summary", "")
        if not current_summary and result["content"]:
            logger.info(f"Setting doctor summary from notes_status endpoint for task {task_id}")
            state_store.set_doctor_summary(result["content"])
    
    return result

# Patient message endpoint
@router.post("/patient_message", response_model=PatientMessageResponse)
async def patient_message(message: PatientMessage, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received patient message: {message.text}")
        
        # Create a unique message ID
        message_id = f"msg_{hashlib.md5((message.text + str(time.time())).encode()).hexdigest()[:10]}"
        
        # Store initial state
        state_store[f"message_{message_id}"] = {
            "text": "",
            "done": False,
            "message_id": message_id
        }
        
        # Run patient message processing in background
        background_tasks.add_task(
            process_patient_message,
            message.text,
            message_id
        )
        
        return PatientMessageResponse(
            text="",
            done=False,
            message_id=message_id
        )
    except Exception as e:
        logger.error(f"Error in patient_message: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Patient message polling endpoint
@router.get("/patient_message_status/{message_id}", response_model=PatientMessageResponse)
async def get_patient_message_status(message_id: str):
    message_data = state_store.get(f"message_{message_id}")
    if not message_data:
        raise HTTPException(status_code=404, detail="Message not found")
    return PatientMessageResponse(**message_data)

# CDS DDX endpoint
@router.get("/cds_ddx", response_model=CDSResponse)
async def get_cds_ddx(background_tasks: BackgroundTasks):
    """Get differential diagnosis suggestions"""
    content = state_store.state.get("cds_ddx", "")
    logger.info(f"GET /cds_ddx - Content length: {len(content)} chars")
    
    # If content is empty or just a placeholder, and transcript exists, trigger processing
    if (not content or content == "Analyzing symptoms for diagnosis, please wait...") and state_store.get("transcript"):
        logger.info("No DDX content available or just placeholder, triggering processing")
        transcript = state_store.get("transcript", "")
        
        # Run differential diagnosis if not already processing
        if not state_store.get("processing"):
            logger.info("Starting background processing for DDX")
            state_store["processing"] = True
            background_tasks.add_task(process_transcript, transcript)
            # Set a placeholder message that will show up immediately in the UI
            content = "Analyzing symptoms for diagnosis, please wait..."
            state_store.state["cds_ddx"] = content
    
    return CDSResponse(content=content)

# CDS QA endpoint
@router.get("/cds_qa", response_model=CDSResponse)
async def get_cds_qa(background_tasks: BackgroundTasks):
    """Get questions to ask suggestions"""
    content = state_store.state.get("cds_qa", "")
    logger.info(f"GET /cds_qa - Content length: {len(content)} chars")
    
    # If content is empty or just a placeholder, and transcript exists, trigger processing
    if (not content or content == "Generating suggested questions, please wait...") and state_store.get("transcript"):
        logger.info("No QA content available or just placeholder, triggering processing")
        transcript = state_store.get("transcript", "")
        
        # Run QA suggestions if not already processing
        if not state_store.get("processing"):
            logger.info("Starting background processing for QA")
            state_store["processing"] = True
            background_tasks.add_task(process_transcript, transcript)
            # Set a placeholder message that will show up immediately in the UI
            content = "Generating suggested questions, please wait..."
            state_store.state["cds_qa"] = content
    
    return CDSResponse(content=content)

# Save conversation endpoint
@router.post("/save_conversation")
async def save_conversation(request: SaveConversationRequest):
    try:
        conversation_id = f"conv_{hashlib.md5((request.title + str(time.time())).encode()).hexdigest()[:10]}"
        
        # Create conversation object
        conversation = {
            "id": conversation_id,
            "title": request.title,
            "date": datetime.datetime.now().isoformat(),
            "transcript": request.transcript,
            "audio": request.audio
        }
        
        # Save conversation
        state_store.add_conversation(conversation)
        
        return {"status": "success", "id": conversation_id}
    except Exception as e:
        logger.error(f"Error saving conversation: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Get conversations list endpoint
@router.get("/conversations")
async def get_conversations():
    try:
        conversations = state_store.get("conversations", [])
        # Add a preview of the transcript for the frontend
        for conv in conversations:
            if "transcript" in conv:
                conv["transcript_preview"] = conv["transcript"][:200] if conv["transcript"] else ""
        
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Get conversation by ID endpoint
@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    try:
        # Look for the conversation in the state store
        conversations = state_store.get("conversations", [])
        for conv in conversations:
            if conv.get("id") == conversation_id:
                # If there's a matching ID, load the full conversation from file
                conversations_dir = os.path.join("storage", "conversations")
                file_path = os.path.join(conversations_dir, f"{conversation_id}.json")
                
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        return json.load(f)
                else:
                    # If no file exists, return the basic conversation info
                    return conv
                
        # If no conversation is found
        raise HTTPException(status_code=404, detail=f"Conversation with ID {conversation_id} not found")
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions

async def generate_notes_task(doctors_hints, transcript, callback, task_id):
    """Background task for generating clinical notes"""
    try:
        logger.info(f"Starting notes generation with hints: {doctors_hints[:50]}..." if len(doctors_hints) > 50 else f"Starting notes generation with hints: {doctors_hints}")
        
        # Create a callback adapter for the LLM
        class CallbackAdapter:
            def __call__(self, content):
                callback(content)
        
        # Run the clinical note generator
        notes = clinical_note_writer.run(
            {
                "input": doctors_hints,
                "transcript": transcript
            },
            callbacks=[CallbackAdapter()]
        )
        
        # Store the result in state for polling
        state_store[f"notes_task_{task_id}"] = {
            "status": "complete",
            "content": notes
        }
        
        # ADDED: Set this as the doctor's summary to make it available for patient chat
        state_store.set_doctor_summary(notes)
        logger.info(f"Doctor summary set from notes generation, length: {len(notes)}")
        
        logger.info(f"Notes generation complete, length: {len(notes)}")
        callback(notes)
    except Exception as e:
        logger.error(f"Error in generate_notes_task: {e}")
        logger.error(traceback.format_exc())
        callback(f"Error generating notes: {e}")

async def process_patient_message(text, message_id):
    """Background task for processing patient messages"""
    try:
        logger.info(f"Processing patient message: {text[:50]}..." if len(text) > 50 else f"Processing patient message: {text}")
        
        # Create a callback adapter for streaming updates
        response_text = ""
        
        class StreamingCallback:
            def __call__(self, content):
                nonlocal response_text
                response_text = content
                # Update the state with the latest content
                current = state_store.get(f"message_{message_id}", {})
                current["text"] = content
                state_store[f"message_{message_id}"] = current
        
        memory = state_store.get_memory()
        history = memory.load_memory_variables({})["history"]
        
        # Get doctor summary with enhanced logging
        doctor_summary = state_store.state.get("doctor_summary", "")
        logger.info(f"Retrieved doctor summary for patient message (length: {len(doctor_summary)})")
        if len(doctor_summary) > 0:
            logger.info(f"Doctor summary preview: {doctor_summary[:100]}...")
        else:
            logger.warning("Doctor summary is empty - patient response may be generic!")
        
        # Run the patient instructor with the callback
        logger.info("Running patient instructor with doctor summary")
        response = patient_instructor.run(
            {
                "input": text,
                "history": history,
                "doctor_summary": doctor_summary
            },
            callbacks=[StreamingCallback()]
        )
        
        if response:
            logger.info(f"Patient message response generated, length: {len(response)}")
            logger.info(f"Response preview: {response[:100]}...")
            
            # Update conversation memory
            memory.chat_memory.add_user_message(text)
            memory.chat_memory.add_ai_message(response)
            
            # Generate audio if possible
            audio = None
            try:
                audio = synthesize(response)
                logger.info("Audio synthesis successful")
            except Exception as e:
                logger.error(f"Audio synthesis failed: {e}")
            
            # Update the state with the complete response
            state_store[f"message_{message_id}"] = {
                "text": response,
                "done": True,
                "audio": audio,
                "message_id": message_id
            }
    except Exception as e:
        logger.error(f"Error in process_patient_message: {e}")
        logger.error(traceback.format_exc())
        # Update the state with the error
        state_store[f"message_{message_id}"] = {
            "text": f"Error processing message: {e}",
            "done": True,
            "message_id": message_id
        }

def process_transcript(transcript):
    """Process transcript for differential diagnosis and QA suggestions"""
    try:
        # Check if we're already processing and handle that case
        if state_store.get("processing") and state_store.get("processing_task_id"):
            # If it's been processing for more than 3 minutes, force reset
            task_id = state_store.get("processing_task_id")
            logger.info(f"Already processing transcript task {task_id}, checking status")
            # For now, we'll just continue with the new processing
            state_store["processing"] = False
            state_store["processing_task_id"] = None
            
        # Set a unique task ID for this processing job
        task_id = hashlib.md5((transcript + str(time.time())).encode()).hexdigest()[:10]
        state_store["processing"] = True
        state_store["processing_task_id"] = task_id
        
        logger.info(f"Processing transcript of length: {len(transcript)} with task ID: {task_id}")
        
        if len(transcript.strip()) < 10:
            logger.info("Transcript too short for meaningful analysis")
            state_store.state["cds_ddx"] = "Transcript too short. Please continue the conversation to receive diagnosis suggestions."
            state_store.state["cds_qa"] = "Transcript too short. Please continue the conversation to receive question suggestions."
            state_store["processing"] = False
            state_store["processing_task_id"] = None
            return
        
        # Create callback adapters with improved logging
        class DDXCallback:
            def __call__(self, content):
                content_str = str(content)
                logger.info(f"DDX callback received content of length: {len(content_str)}")
                logger.info(f"DDX content preview: {content_str[:100]}...")
                # Explicitly store in the state
                state_store.state["cds_ddx"] = content_str
                logger.info("DDX content stored in state")
        
        class QACallback:
            def __call__(self, content):
                content_str = str(content)
                logger.info(f"QA callback received content of length: {len(content_str)}")
                logger.info(f"QA content preview: {content_str[:100]}...")
                # Explicitly store in the state
                state_store.state["cds_qa"] = content_str
                logger.info("QA content stored in state")
        
        # Process DDX and QA in sequence with proper error handling
        try:
            # Run differential diagnosis first
            logger.info(f"Running differential diagnosis analysis for task {task_id}")
            ddx_result = cds_helper_ddx.run(
                {"transcript": transcript},
                callbacks=[DDXCallback()]
            )
            
            if ddx_result:
                logger.info(f"DDX analysis completed for task {task_id}, result length: {len(str(ddx_result))}")
                state_store.state["cds_ddx"] = str(ddx_result)
            else:
                logger.warning(f"DDX analysis returned no results for task {task_id}")
                state_store.state["cds_ddx"] = "Could not generate differential diagnosis. Please add more clinical information."
        except Exception as e:
            logger.error(f"Error processing DDX: {e}")
            logger.error(traceback.format_exc())
            state_store.state["cds_ddx"] = f"Error generating differential diagnosis: {str(e)}"
        
        try:
            # Then run QA suggestions
            logger.info(f"Running questions to ask analysis for task {task_id}")
            qa_result = cds_helper_qa.run(
                {"transcript": transcript},
                callbacks=[QACallback()]
            )
            
            if qa_result:
                logger.info(f"QA analysis completed for task {task_id}, result length: {len(str(qa_result))}")
                state_store.state["cds_qa"] = str(qa_result)
            else:
                logger.warning(f"QA analysis returned no results for task {task_id}")
                state_store.state["cds_qa"] = "Could not generate suggested questions. Please add more clinical information."
        except Exception as e:
            logger.error(f"Error processing QA: {e}")
            logger.error(traceback.format_exc())
            state_store.state["cds_qa"] = f"Error generating questions: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error processing transcript: {e}")
        logger.error(traceback.format_exc())
        state_store.state["cds_ddx"] = f"Error generating differential diagnosis: {str(e)}"
        state_store.state["cds_qa"] = f"Error generating questions: {str(e)}"
    finally:
        # Always make sure to reset processing state
        state_store["processing"] = False
        state_store["processing_task_id"] = None
        logger.info("Transcript processing completed")