# Mediclient (MediCompanion)

## Overview

Mediclient is an AI-powered healthcare assistant that streamlines clinical workflows and patient communication. It features two interactive modes:

* **Doctor Mode**: Real-time transcription, clinical documentation, differential diagnosis (DDX), and suggested follow-up questions.
* **Patient Mode**: Virtual assistant “Paco” translates medical language into accessible explanations, offers medication guidance, and provides empathetic support via text and voice.

This project leverages FastAPI, AssemblyAI, Google Text-to-Speech, and Google’s Gemini 2.0 model to deliver a responsive, scalable, and secure healthcare companion.

---

## Table of Contents

1. [Features](#features)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Running the Application](#running-the-application)
7. [API Endpoints](#api-endpoints)
8. [State Management](#state-management)
9. [Contributing](#contributing)
10. [Future Works](#future-works)
11. [License](#license)

---

## Features

### Doctor Mode

* **Real-Time Transcription**: Stream doctor-patient conversations via AssemblyAI.
* **Automated Clinical Documentation**: Generate professional medical notes using Gemini 2.0.
* **Differential Diagnosis (DDX)**: Suggests potential diagnoses with context-aware evidence.
* **Suggested Questions**: Proposes targeted follow-up questions to fill data gaps.
* **Consultation Management**: Save, organize, and retrieve past consultations.

### Patient Mode (“Paco”)

* **Conversational Chatbot**: Text and voice interface at a 6th–8th grade reading level.
* **Medication Guidance**: Explains dosage, side effects, and practical tips.
* **Treatment Plan Clarification**: Plain-language breakdowns of instructions.
* **Audio Responses**: Google TTS support for accessibility.
* **Health Resources**: Links to trusted references and emergency contacts.

---

## Architecture

```text
+---------------+       +---------------------+       +---------------------+
|               |       |                     |       |                     |
|   Frontend    |  <--  |   FastAPI Backend   |  <--  |   AssemblyAI / LLM  |
| (HTML/CSS,    |       |  (APIRouter, Tasks) |       |  (Gemini 2.0, AAI)  |
| Socket.IO)    |       |                     |       |                     |
+---------------+       +---------------------+       +---------------------+
         |                        |                            |
     real-time               callbacks                  AI generation
         ↓                        ↓                            ↓
   User inputs      speech-to-text & text-to-speech   Clinical notes, DDX, QA
```

---

## Tech Stack

* **Backend**: FastAPI, Python 3.10+, Uvicorn
* **Speech-to-Text**: AssemblyAI API
* **Text-to-Speech**: Google Text-to-Speech API
* **LLM**: Google Gemini 2.0 via custom prompt engineering
* **State Management**: In-memory `state_store`, JSON storage
* **Frontend**: HTML, CSS, Socket.IO
* **Data Storage**: Local JSON files for conversation history

---

## Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/mediclient.git
   cd mediclient
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

1. **AssemblyAI API Key**

   * Export your key:

     ```bash
     export ASSEMBLYAI_API_KEY="<your_assemblyai_key>"
     ```

2. **Google TTS Credentials**

   * Place your service account JSON in `credentials/google_tts.json` and set:

     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="credentials/google_tts.json"
     ```

3. **Gemini 2.0 Access**

   * Ensure your environment has access to Gemini API (via Google Cloud or Flash SDK).

---

## Running the Application

Start the FastAPI server with Uvicorn:

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:8000` in your browser to access the frontend.

---

## API Endpoints

### Health Check

* **GET** `/status`

  ```json
  { "status": "ok" }
  ```

### Recording Control

* **POST** `/start_recording`

  * Body: `{ "value": true }`
  * Response: `{ "active": true }`
* **POST** `/stop_recording`

  * Body: `{ "value": true }`
  * Response: `{ "active": false }`

### Transcripts

* **GET** `/transcript`
* **GET** `/patient_transcript`

### Clinical Notes

* **POST** `/generate_notes`

  * Body: `{ "doctors_hints": "<your hints>" }`
  * Response: `{ "status": "processing", "task_id": "abc123" }`
* **GET** `/notes_status/{task_id}`

### Patient Chat

* **POST** `/patient_message`

  * Body: `{ "text": "How do I take my medication?" }`
* **GET** `/patient_message_status/{message_id}`

### Decision Support

* **GET** `/cds_ddx`
* **GET** `/cds_qa`

### Conversation Management

* **POST** `/save_conversation`
* **GET** `/conversations`
* **GET** `/conversation/{conversation_id}`

Refer to the inline docs in `app/main.py` for detailed request/response schemas.

---

## State Management

All runtime state is stored in `state_store`:

| Key                  | Purpose                          |
| -------------------- | -------------------------------- |
| `transcript`         | Current doctor transcript        |
| `patient_transcript` | Current patient transcript       |
| `cds_ddx`, `cds_qa`  | DDX & QA suggestions             |
| `doctor_summary`     | Final summary for patient mode   |
| `message_<id>`       | Streaming patient message state  |
| `notes_task_<id>`    | Note generation status & content |
| `conversations`      | List of saved consultations      |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -m "Add awesome feature"`
4. Push: `git push origin feature/my-feature`
5. Open a Pull Request

Please follow the existing code style and add tests for new functionality.

---

## Future Works

* Real-time symptom severity scoring & risk grading
* EHR integration (FHIR, HL7)
* Multilingual support
* Appointment booking & reminders
* Custom fine-tuned medical LLMs
* Mobile app extension (iOS/Android)
* Wearables/IoT data integration
* Full HIPAA & GDPR compliance

---

##

---

*Developed with ❤️ by Monish*
