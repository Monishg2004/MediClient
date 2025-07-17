
# state.py
from langchain.memory import ConversationBufferMemory
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateStore:
    def __init__(self):
        # Set up directory structure
        os.makedirs("storage", exist_ok=True)
        os.makedirs("storage/conversations", exist_ok=True)
        
        # Initialize state and load persistent data
        self.reset_state()
        self.load_state()
        
        logger.info("StateStore initialized")
    
    def reset_state(self):
        """Reset the state to initial values"""
        logger.info("Resetting state to initial values")
        self.state = {
            "transcript": "",
            "patient_transcript": "",
            "doctor_summary": "",
            "patient_mode": False,
            "processing": False,
            "processing_task_id": None,
            "stop": None,
            "cds_ddx": "",
            "cds_qa": "",
            "current_recording": None,
            # Additional fields for new features
            "conversations": []
        }
        self.memory = self._initialize_memory()
    
    def load_state(self):
        """Load persistent state from disk if available"""
        state_file = os.path.join("storage", "state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, "r") as f:
                    saved_state = json.load(f)
                    logger.info(f"Loaded state from {state_file}")
                    
                    # Only load persistent fields (not runtime fields like 'stop')
                    persistent_fields = [
                        "doctor_summary", 
                        "conversations"
                    ]
                    for field in persistent_fields:
                        if field in saved_state:
                            self.state[field] = saved_state[field]
                            logger.info(f"Restored {field} from saved state")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
        
        # If no conversations were loaded, try to read from the conversations directory
        if not self.state.get("conversations"):
            self._load_conversations_from_disk()
    
    def _load_conversations_from_disk(self):
        """Load conversations from individual JSON files in the conversations directory"""
        conversations_dir = os.path.join("storage", "conversations")
        conversations = []
        
        if os.path.exists(conversations_dir):
            logger.info(f"Loading conversations from {conversations_dir}")
            for filename in os.listdir(conversations_dir):
                if filename.endswith(".json"):
                    file_path = os.path.join(conversations_dir, filename)
                    try:
                        with open(file_path, "r") as f:
                            data = json.load(f)
                            # Create a list item without the full audio data to save memory
                            list_item = {
                                "id": data.get("id"),
                                "title": data.get("title"),
                                "date": data.get("date"),
                                "transcript": data.get("transcript", ""),
                                # Include a reference to the audio but not the full data
                                "has_audio": bool(data.get("audio"))
                            }
                            conversations.append(list_item)
                            logger.info(f"Loaded conversation: {list_item['id']} - {list_item['title']}")
                    except Exception as e:
                        logger.error(f"Error reading conversation file {filename}: {e}")
            
            # Sort by date (newest first)
            conversations.sort(key=lambda x: x.get("date", ""), reverse=True)
            self.state["conversations"] = conversations
            logger.info(f"Loaded {len(conversations)} conversations from disk")
    
    def save_state(self):
        """Save persistent state to disk"""
        os.makedirs("storage", exist_ok=True)
        state_file = os.path.join("storage", "state.json")
        
        # Only save persistent fields
        save_data = {
            "doctor_summary": self.state.get("doctor_summary", ""),
            "conversations": self.state.get("conversations", [])
        }
        
        try:
            with open(state_file, "w") as f:
                json.dump(save_data, f)
            logger.info(f"State saved to {state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _initialize_memory(self):
        """Initialize conversation memory"""
        memory = ConversationBufferMemory(
            ai_prefix="Paco",
            human_prefix="Patient",
            return_messages=True,
            memory_key="history"
        )
        memory.chat_memory.add_ai_message(
            "Hello, I'm Paco, your medical knowledge assistant. How can I assist you today with your prescriptions?"
        )
        return memory
    
    def set_doctor_summary(self, summary):
        """Set doctor's summary and persist to disk"""
        self.state["doctor_summary"] = summary
        logger.info(f"Set doctor summary: {len(summary)} chars")
        # Save the summary to disk immediately
        self.save_state()
    
    def add_conversation(self, conversation):
        """Add a conversation to the list and persist to disk"""
        if "conversations" not in self.state:
            self.state["conversations"] = []
        
        # Create a lightweight entry for the conversations list
        list_entry = {
            "id": conversation.get("id"),
            "title": conversation.get("title"),
            "date": conversation.get("date"),
            "transcript": conversation.get("transcript"),
            "has_audio": bool(conversation.get("audio"))
        }
        
        self.state["conversations"].append(list_entry)
        logger.info(f"Added conversation to state: {list_entry['id']} - {list_entry['title']}")
        
        # Keep only the latest 50 conversations in memory
        if len(self.state["conversations"]) > 50:
            self.state["conversations"] = self.state["conversations"][-50:]
        
        # Save the individual conversation file
        self._save_conversation_file(conversation)
        
        # Update the main state file
        self.save_state()
    
    def _save_conversation_file(self, conversation):
        """Save a conversation to an individual file"""
        conversation_id = conversation.get("id")
        if not conversation_id:
            logger.error("Cannot save conversation: missing ID")
            return
        
        conversations_dir = os.path.join("storage", "conversations")
        os.makedirs(conversations_dir, exist_ok=True)
        
        file_path = os.path.join(conversations_dir, f"{conversation_id}.json")
        
        try:
            with open(file_path, "w") as f:
                json.dump(conversation, f)
            logger.info(f"Conversation saved to {file_path}")
        except Exception as e:
            logger.error(f"Error saving conversation file: {e}")
    
    def get_memory(self):
        """Get conversation memory"""
        return self.memory
    
    def __getitem__(self, key):
        return self.state.get(key)
    
    def __setitem__(self, key, value):
        self.state[key] = value
        
        # Auto-save if adding a persistent field
        if key in ["doctor_summary", "conversations"]:
            self.save_state()
    
    def get(self, key, default=None):
        return self.state.get(key, default)

# Initialize global state store
state_store = StateStore()
