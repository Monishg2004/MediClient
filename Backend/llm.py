# # llm.py
# import google.generativeai as genai
# from langchain.prompts.prompt import PromptTemplate
# import logging
# import traceback

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class GeminiLLM:
#     def __init__(self, api_key=None):
#         """Initialize Gemini model with API key."""
#         api_key = api_key or 'AIzaSyAy90rkKCrJct5D4aNPblNctU6XOXvDcBI'
#         genai.configure(api_key=api_key)
#         self.model = genai.GenerativeModel('gemini-2.0-flash')  # Use the latest model version
#         self.generation_config = {
#             'temperature': 0.7,
#             'top_p': 0.9,
#             'top_k': 40,
#             'max_output_tokens': 2048,
#         }
#         logger.info("Gemini LLM initialized")

#     def generate(self, prompt):
#         """Generate content from a prompt."""
#         try:
#             logger.info(f"Sending prompt to Gemini API (length: {len(prompt)})")
#             response = self.model.generate_content(
#                 prompt,
#                 generation_config=self.generation_config
#             )
#             result_text = response.text.strip()
#             logger.info(f"Received response from Gemini API (length: {len(result_text)})")
#             return result_text
#         except Exception as e:
#             logger.error(f"Gemini API Error: {e}")
#             logger.error(traceback.format_exc())
#             return f"Error generating response: {str(e)}"

# # Initialize the GeminiLLM with the API key
# gemini_llm = GeminiLLM()

# # Clinical note writer prompt template
# clinical_note_writer_template = PromptTemplate(
#     input_variables=["transcript", "input"],
#     template="""Act as an experienced medical professional. Generate a detailed clinical note based on the consultation transcript and doctor's hints.

# Format the note as follows:
# 1. Chief Complaint:
# 2. History of Present Illness:
# 3. Past Medical History:
# 4. Current Medications:
# 5. Physical Examination:
# 6. Assessment:
# 7. Plan:
#     - Medications (New/Modified/Continued)
#     - Tests Ordered
#     - Follow-up Instructions

# Use professional medical terminology and be concise but thorough. If information is not available in the transcript, note that it was not provided rather than inventing details.

# Transcript: {transcript}
# Doctor's Notes: {input}
# """
# )

# # Clinical decision support - differential diagnosis prompt
# cds_helper_ddx_prompt = PromptTemplate(
#     input_variables=["transcript"],
#     template="""Act as a medical diagnostic expert. Based on the consultation transcript, provide a detailed differential diagnosis analysis.

# Rules:
# 1. List potential diagnoses in order of likelihood (even with limited information)
# 2. For each diagnosis:
#     - Provide supporting symptoms/findings
#     - Assign confidence score (0-100)
#     - List key diagnostic criteria missing/needed
# 3. Suggest critical rule-outs

# IMPORTANT: Even with minimal information, provide at least 2-3 potential diagnoses based on the symptoms mentioned.
# Format your response with markdown using # for titles and - for list items to ensure proper display.

# Consultation Transcript:
# {transcript}

# # Differential Diagnosis Analysis
# """
# )

# # Clinical decision support - suggested questions prompt
# cds_helper_qa_prompt = PromptTemplate(
#     input_variables=["transcript"],
#     template="""Based on the provided transcript from a doctor-patient consultation, suggest potential questions the doctor could ask to facilitate the diagnosis process.

# Review the patient's stated symptoms, their medical history, and any other relevant information presented in the transcript. Then suggest questions that would help clarify the diagnosis or gather more information.

# IMPORTANT: Even with minimal information, provide at least 3 relevant questions that a doctor should ask based on whatever symptoms or conditions are mentioned.
# Format your response with markdown using # for titles and - for list items to ensure proper display.

# Consultation Transcript:
# {transcript}

# # Recommended Questions
# """
# )

# # Patient instruction prompt template
# patient_instructions_template = PromptTemplate(
#     input_variables=["history", "input", "doctor_summary"],
#     template="""You are Paco, an empathetic medical assistant. Your role is to:
# 1. Provide clear, patient-friendly explanations
# 2. Focus on medication adherence and lifestyle recommendations
# 3. Use simple language avoiding medical jargon
# 4. Express empathy while maintaining professionalism
# 5. Stay within scope of prescribed treatment plan

# Recent Clinical Notes:
# {doctor_summary}

# Conversation History:
# {history}

# Patient Question: {input}

# Response (in patient-friendly language):"""
# )

# class EnhancedMedicalChain:
#     """Chain for handling medical prompts and callbacks."""
    
#     def __init__(self, llm, prompt, verbose=False):
#         """Initialize the chain with LLM and prompt template."""
#         self.llm = llm
#         self.prompt = prompt
#         self.verbose = verbose
#         logger.info(f"Initialized EnhancedMedicalChain with prompt template: {prompt.template[:50]}...")

#     def run(self, input_data, callbacks=None):
#         """Run the chain with input data and optional callbacks."""
#         try:
#             # Format the prompt with input data
#             formatted_prompt = self.prompt.format(**input_data)
            
#             # Log prompt length for debugging
#             if self.verbose:
#                 logger.info(f"Running chain with prompt length: {len(formatted_prompt)}")
#                 logger.info(f"Input data keys: {list(input_data.keys())}")
                
#             # Check if transcript is too short
#             if 'transcript' in input_data and len(input_data['transcript'].strip()) < 10:
#                 logger.warning("Transcript too short for meaningful analysis")
#                 result = "The transcript is too brief for analysis. Please provide more conversation data."
#                 if callbacks:
#                     for callback in callbacks:
#                         callback(result)
#                 return result
            
#             # Generate response
#             logger.info("Sending prompt to Gemini API")
#             response = self.llm.generate(formatted_prompt)
#             logger.info(f"Received response of length: {len(response)}")
            
#             # Process callbacks if provided
#             if callbacks:
#                 for callback in callbacks:
#                     callback(response)
            
#             return response
#         except Exception as e:
#             logger.error(f"Chain execution error: {e}")
#             logger.error(traceback.format_exc())
#             error_msg = f"An error occurred while processing your request: {str(e)}"
            
#             if callbacks:
#                 for callback in callbacks:
#                     callback(error_msg)
                    
#             return error_msg

# # Initialize the chains
# clinical_note_writer = EnhancedMedicalChain(gemini_llm, clinical_note_writer_template, verbose=True)
# cds_helper_ddx = EnhancedMedicalChain(gemini_llm, cds_helper_ddx_prompt, verbose=True)
# cds_helper_qa = EnhancedMedicalChain(gemini_llm, cds_helper_qa_prompt, verbose=True)
# patient_instructor = EnhancedMedicalChain(gemini_llm, patient_instructions_template, verbose=True)

# llm.py
import google.generativeai as genai
from langchain.prompts.prompt import PromptTemplate
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiLLM:
    def __init__(self, api_key=None):
        """Initialize Gemini model with API key."""
        api_key = api_key or 'AIzaSyAy90rkKCrJct5D4aNPblNctU6XOXvDcBI'
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')  # Use the latest model version
        self.generation_config = {
            'temperature': 0.7,
            'top_p': 0.9,
            'top_k': 40,
            'max_output_tokens': 2048,
        }
        logger.info("Gemini LLM initialized")

    def generate(self, prompt):
        """Generate content from a prompt."""
        try:
            logger.info(f"Sending prompt to Gemini API (length: {len(prompt)})")
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            result_text = response.text.strip()
            logger.info(f"Received response from Gemini API (length: {len(result_text)})")
            return result_text
        except Exception as e:
            logger.error(f"Gemini API Error: {e}")
            logger.error(traceback.format_exc())
            return f"Error generating response: {str(e)}"

# Initialize the GeminiLLM with the API key
gemini_llm = GeminiLLM()

# Clinical note writer prompt template
clinical_note_writer_template = PromptTemplate(
    input_variables=["transcript", "input"],
    template="""You are an experienced medical professional generating clinical documentation. Based on the consultation transcript and doctor's notes, create a comprehensive clinical note that adheres to medical documentation standards.

Format the note with the following sections:

1. Chief Complaint:
   - Primary reason for visit in patient's own words

2. History of Present Illness (HPI):
   - Detailed chronology of symptoms
   - Onset, duration, character, aggravating/alleviating factors
   - Related symptoms and their progression

3. Past Medical History:
   - Significant past diagnoses
   - Surgeries and hospitalizations
   - Allergies (medication and non-medication)

4. Current Medications:
   - Name, dosage, frequency, and reason for each medication
   - Include over-the-counter medications and supplements if mentioned

5. Physical Examination:
   - Vital signs (if provided)
   - Relevant system examinations
   - Objective findings organized by body system

6. Assessment:
   - Primary diagnosis with ICD-10 code if possible
   - Secondary/differential diagnoses considered
   - Clinical reasoning supporting the assessment

7. Plan:
   - Medications (New/Modified/Continued)
   - Diagnostic tests ordered with rationale
   - Referrals to specialists if needed
   - Patient education provided
   - Follow-up instructions and timeline

Use professional medical terminology and be thorough yet concise. Only include information that is explicitly stated or can be reasonably inferred from the transcript. For any critical information not available, clearly indicate "Not documented" rather than inventing details.

Consultation Transcript:
{transcript}

Doctor's Notes/Hints:
{input}
"""
)

# Clinical decision support - differential diagnosis prompt
cds_helper_ddx_prompt = PromptTemplate(
    input_variables=["transcript"],
    template="""You are a senior medical diagnostician analyzing a patient consultation. Based on the transcript, provide a structured differential diagnosis analysis.

# Differential Diagnosis Analysis

## Patient Presentation Summary
First, summarize the key presenting symptoms, relevant history, and objective findings from the transcript.

## Ranked Differential Diagnoses
List potential diagnoses in order of likelihood, from most to least probable. For each diagnosis:

1. **[Diagnosis Name] (Probability: High/Medium/Low)**
   - **Supporting Evidence**: List specific symptoms/findings from the transcript that support this diagnosis
   - **Confidence Score**: [0-100]
   - **Missing Information**: List key data points that would help confirm or rule out this diagnosis
   - **Recommended Diagnostics**: Suggest specific tests or examinations that would help confirm this diagnosis

## Critical Rule-Outs
List any potentially serious or life-threatening conditions that should be ruled out, even if they are lower probability, with brief justification.

## Next Steps
Recommend the most important next steps to narrow the differential diagnosis.

IMPORTANT: Even with limited information, provide at least 3 potential diagnoses based on the available symptoms. If information is very limited, acknowledge this but still provide your best clinical assessment based on what is known.

Use precise medical terminology but include clear explanations of your reasoning.

Consultation Transcript:
{transcript}
"""
)

# Clinical decision support - suggested questions prompt
cds_helper_qa_prompt = PromptTemplate(
    input_variables=["transcript"],
    template="""You are an experienced physician helping to guide a clinical interview. Based on the provided doctor-patient consultation transcript, suggest targeted follow-up questions to improve diagnostic accuracy and patient care.

# Consultation Analysis

## Key Information Already Obtained
Briefly summarize the critical information already gathered from the patient.

## Information Gaps Identified
Identify areas where more information would significantly improve diagnostic clarity.

# Recommended Questions

## High-Priority Questions
List 3-5 essential questions that should be asked immediately to clarify the most critical aspects of the case:
- [Question 1]
- [Question 2]
- [Question 3]

## Symptom Clarification Questions
Suggest questions that would help better characterize the nature, timing, and severity of reported symptoms:
- [Specific question about symptom onset, duration, etc.]

## History-Related Questions
Suggest questions about medical history, family history, or social factors that could be relevant:
- [Specific questions about history]

## Medication and Treatment Questions
Questions about current medications, prior treatments, and response to interventions:
- [Specific questions about medications/treatments]

Use clear, concise language that a physician could adopt directly in conversation with the patient. For each question, include a brief note on why the information is clinically relevant.

Consultation Transcript:
{transcript}
"""
)

# Patient instruction prompt template
patient_instructions_template = PromptTemplate(
    input_variables=["history", "input", "doctor_summary"],
    template="""You are Paco, an empathetic medical assistant with expertise in patient education. Your purpose is to help patients understand their medical care in clear, accessible terms.

Your communication guidelines:
1. Use plain, everyday language (aim for 6th-8th grade reading level)
2. Break down complex medical concepts into simple explanations
3. Prioritize medication information and practical care instructions
4. Express empathy and understanding for the patient's concerns
5. Stay strictly within the boundaries of the doctor's treatment plan
6. Never contradict the physician's advice or suggest alternative treatments
7. When uncertain, acknowledge limitations rather than guessing

When explaining medications, always include:
- What the medication is for (in simple terms)
- How and when to take it
- Important side effects to watch for
- Practical tips for remembering doses

Recent Clinical Notes (for your reference only):
{doctor_summary}

Previous Conversation:
{history}

Patient Question: {input}

Response (in warm, clear, and patient-friendly language):
"""
)

class EnhancedMedicalChain:
    """Chain for handling medical prompts and callbacks."""
    
    def __init__(self, llm, prompt, verbose=False):
        """Initialize the chain with LLM and prompt template."""
        self.llm = llm
        self.prompt = prompt
        self.verbose = verbose
        logger.info(f"Initialized EnhancedMedicalChain with prompt template: {prompt.template[:50]}...")

    def run(self, input_data, callbacks=None):
        """Run the chain with input data and optional callbacks."""
        try:
            # Format the prompt with input data
            formatted_prompt = self.prompt.format(**input_data)
            
            # Log prompt length for debugging
            if self.verbose:
                logger.info(f"Running chain with prompt length: {len(formatted_prompt)}")
                logger.info(f"Input data keys: {list(input_data.keys())}")
                
            # Check if transcript is too short
            if 'transcript' in input_data and len(input_data['transcript'].strip()) < 10:
                logger.warning("Transcript too short for meaningful analysis")
                result = "The transcript is too brief for analysis. Please provide more conversation data."
                if callbacks:
                    for callback in callbacks:
                        callback(result)
                return result
            
            # Generate response
            logger.info("Sending prompt to Gemini API")
            response = self.llm.generate(formatted_prompt)
            logger.info(f"Received response of length: {len(response)}")
            
            # Process callbacks if provided
            if callbacks:
                for callback in callbacks:
                    callback(response)
            
            return response
        except Exception as e:
            logger.error(f"Chain execution error: {e}")
            logger.error(traceback.format_exc())
            error_msg = f"An error occurred while processing your request: {str(e)}"
            
            if callbacks:
                for callback in callbacks:
                    callback(error_msg)
                    
            return error_msg

# Initialize the chains
clinical_note_writer = EnhancedMedicalChain(gemini_llm, clinical_note_writer_template, verbose=True)
cds_helper_ddx = EnhancedMedicalChain(gemini_llm, cds_helper_ddx_prompt, verbose=True)
cds_helper_qa = EnhancedMedicalChain(gemini_llm, cds_helper_qa_prompt, verbose=True)
patient_instructor = EnhancedMedicalChain(gemini_llm, patient_instructions_template, verbose=True)