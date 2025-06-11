from typing import Optional, Tuple
import json # Added json import
import logging # Added logging
from pydantic import BaseModel, Field
from .config import settings # Added

logger = logging.getLogger(__name__) # Initialized logger

ADK_IMPORTED_SUCCESSFULLY = False
AGENT_INITIALIZED_SUCCESSFULLY = False # New flag

# Attempt to import ADK components. Handle gracefully if not available.
try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    from google.adk.events import Event
    ADK_IMPORTED_SUCCESSFULLY = True
    logger.debug("ADK components imported successfully.")
except ImportError as e:
    logger.error("Failed to import ADK components: %s. AI Agent will not be available.", e, exc_info=True)
    # Dummy ADK class definitions are below and will be used.
    pass

# --- Pydantic Model for Structured Agent Response ---
class AgentStructuredResponse(BaseModel):
    message: str = Field(description="The chat message response from the AI agent.")
    require_form_after_message: bool = Field(
        description="Indicates if the frontend should suggest or display a contact form after this message."
    )

class LlmAgent:
        def __init__(self, *args, **kwargs):
            # This print is in a dummy class, potentially keep as is or change to logger.warning
            # For now, let's assume these dummy classes' prints are for very specific non-ADK scenarios
            print("WARNING: google-adk-python not installed. AI Agent will not function.")
            pass
    class InMemoryRunner:
        def __init__(self, *args, **kwargs):
            pass
        def run(self, *args, **kwargs) -> 'Event': # type: ignore
            return Event(error_message="ADK components not available. Please install google-adk-python.") # type: ignore
    class Event: # type: ignore
        def __init__(self, error_message: Optional[str] = None):
            self.actions = []
            self.error_message = error_message
            self.session_id = None


# Configure your Google Cloud project and credentials if necessary.
# For Gemini, ensure API keys or ADC (Application Default Credentials) are set up.
# You might need to set GOOGLE_API_KEY environment variable if not using ADC.
# The ADK library should pick up Application Default Credentials automatically if set up.

GEMINI_MODEL_NAME = settings.gemini_model_name
# The GOOGLE_API_KEY is expected to be sourced by the ADK from the environment variables
# (which pydantic-settings helps load from .env) or via ADC.
# We log if it's explicitly set via our application settings, for awareness.
if settings.google_api_key:
    logger.info("Application settings include a GOOGLE_API_KEY.")
else:
    logger.info("GOOGLE_API_KEY is not set in application settings. ADK will rely on ADC or an externally set GOOGLE_API_KEY environment variable.")

# Generate JSON schema string for the agent's structured response
AGENT_RESPONSE_JSON_SCHEMA = json.dumps(AgentStructuredResponse.model_json_schema(), indent=2)

chat_agent = None
agent_runner = None

if ADK_IMPORTED_SUCCESSFULLY:
    try:
        chat_agent = LlmAgent(
            name="structured_chat_agent", # Renamed for clarity
            model=GEMINI_MODEL_NAME,
            instruction=f"""You are a highly intelligent and helpful AI assistant for 'Contact Form Widget Corp'.
Your primary role is to answer user questions about our company, our innovative contact form widgets, related whitepapers, and product information.
You MUST always respond with a JSON object that strictly adheres to the following JSON schema:
```json
{AGENT_RESPONSE_JSON_SCHEMA}
```

Here's how to determine the values for the JSON fields:
- `message`: This field should contain your textual response to the user. Be helpful, concise, and informative.
- `require_form_after_message`: This boolean field determines if the user should be prompted with a contact form or a specific call to action after your message.
    - Set this to `true` if the conversation indicates a strong user interest in our products or services, if they are asking for quotes, detailed product comparisons, or if they seem like a qualified lead ready for the next step. For example, if they ask 'How can I get this widget for my site?' or 'Can you tell me the pricing for enterprise users?'.
    - When setting to `true`, the `message` field should naturally lead to this suggestion. For example: 'That's a great question! For detailed pricing and to discuss your specific needs, I recommend reaching out to our sales team. Would you like me to show you a form to contact them?' or 'Our 'Pro Widget X' seems like a perfect fit for your requirements. You can find more details and a purchase link here: [link]. I can also help you get in touch with our team if you'd like.'
    - In all other cases, or if you are unsure, set `require_form_after_message` to `false`. This includes general inquiries, requests for information you can provide directly, or if the user is not yet showing strong buying signals.
You are an expert in our products and aim to guide users effectively.
""",
        output_schema=AgentStructuredResponse, # Pass the Pydantic model here
        # tools=[] # Explicitly no tools, as output_schema disables them
        )
        agent_runner = InMemoryRunner(agent=chat_agent)
        AGENT_INITIALIZED_SUCCESSFULLY = True
        logger.info("AI Agent initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize LlmAgent or InMemoryRunner: %s. AI Agent will not be functional.", e, exc_info=True)
        chat_agent = None # Ensure they are None if init fails
        agent_runner = None
        # AGENT_INITIALIZED_SUCCESSFULLY remains False
else:
    logger.warning("ADK components not imported. AI Agent initialization will be skipped.")
    chat_agent = None
    agent_runner = None

def get_chat_response(message: str, session_id: Optional[str] = None) -> Tuple[str, Optional[str], bool]:
    """
    Gets a chat response from the AI agent.
    Returns:
        Tuple[str, Optional[str], bool]: (reply_message, session_id, require_form_flag)
    """
    # Changed level to debug and improved message snippet handling
    logger.debug(
        "get_chat_response called with session_id: %s, message_snippet: %s",
        session_id,
        message[:80] + "..." if message and len(message) > 80 else message
    )

    # Input Validation for 'message'
    if not message or not message.strip():
        logger.warning(
            "Input validation failed for get_chat_response: message is empty or consists only of whitespace. Session_id: %s",
            session_id
        )
        return "Message cannot be empty. Please provide a valid message.", session_id, False

    if not AGENT_INITIALIZED_SUCCESSFULLY:
        fallback_message = ""
        if not ADK_IMPORTED_SUCCESSFULLY:
            fallback_message = "AI Agent is unavailable due to missing dependencies. Please check server logs."
            logger.debug("Serving fallback because ADK components not imported.")
        else:
            # This means ADK was imported, but LlmAgent/InMemoryRunner initialization failed
            fallback_message = "AI Agent is currently experiencing setup issues. Please try again later or contact support."
            logger.debug("Serving fallback because AI Agent failed to initialize.")
        return fallback_message, session_id, False

    if agent_runner is None:
        logger.error("agent_runner is None despite AGENT_INITIALIZED_SUCCESSFULLY being true. This indicates a logic flaw.", exc_info=True)
        return "AI Agent is unexpectedly unavailable. Please contact support.", session_id, False

    try:
        event: Event = agent_runner.run(request=message, session_id=session_id)

        reply = "[No response from agent or empty response]" # Default reply
        require_form = False # Default value
        response_session_id = session_id # Default to passed-in session_id

        if event.error_message:
            logger.error("Agent event returned error_message: %s", event.error_message)
            reply = f"[Agent Error: {event.error_message}]"
        elif event.actions and event.actions[0].parts:
            action_part = event.actions[0].parts[0]
            if hasattr(action_part, 'text') and action_part.text:
                raw_agent_text = action_part.text
                try:
                    structured_response_data = json.loads(raw_agent_text)
                    parsed_response = AgentStructuredResponse(**structured_response_data)
                    reply = parsed_response.message
                    require_form = parsed_response.require_form_after_message
                except json.JSONDecodeError as jde:
                    logger.error("Failed to decode JSON response from agent. Text was: %s", raw_agent_text, exc_info=True)
                    reply = "[Agent Error: Failed to decode JSON response]"
                except Exception as pydantic_error: # Catch Pydantic validation errors
                    logger.error("Invalid JSON structure from agent. Text was: %s Error: %s", raw_agent_text, pydantic_error, exc_info=True)
                    reply = f"[Agent Error: Invalid JSON structure]"
            else:
                logger.warning("Agent produced no actionable text output. Event details: %s", event)
                reply = "[Agent produced no actionable text output]"
        else:
            logger.warning("Agent event had no error_message and no actionable parts. Event details: %s", event)
            # reply remains "[No response from agent or empty response]"

        if hasattr(event, 'session_id') and event.session_id:
            response_session_id = event.session_id
        
        logger.debug(
            "Returning chat response. Session_id: %s, require_form: %s, reply snippet: %.80s",
            response_session_id, require_form, reply
        )
        return reply, response_session_id, require_form

    except Exception as e:
        logger.error("Error during agent_runner.run or response processing: %s", e, exc_info=True)
        reply = f"[Error communicating with AI Agent]" # Simplified user-facing message
        response_session_id = session_id
        require_form = False
        return reply, response_session_id, require_form

# Example of how you might test this function directly (requires ADK and auth)
if __name__ == '__main__':
    if AGENT_INITIALIZED_SUCCESSFULLY: # Check if agent is ready for testing
        print("Testing AI Agent locally (ensure GOOGLE_API_KEY or ADC is set up)...")
        # Test 1: Simple message
        test_message = "Hello, how are you?"
        test_session_id = "local_test_session_123"
        
        print(f"\nSending message: '{test_message}' with session_id: '{test_session_id}'")
        reply_text, returned_session_id, require_form = get_chat_response(test_message, test_session_id)
        print(f"  Agent Reply: {reply_text}")
        print(f"  Returned Session ID: {returned_session_id}")
        print(f"  Require Form: {require_form}")

        # Test 2: Message without session_id
        test_message_2 = "What's the weather like?"
        print(f"\nSending message: '{test_message_2}' with no session_id")
        reply_text_2, returned_session_id_2, require_form_2 = get_chat_response(test_message_2)
        print(f"  Agent Reply: {reply_text_2}")
        print(f"  Returned Session ID: {returned_session_id_2}")
        print(f"  Require Form: {require_form_2}")
        
        # Test 3: Potentially problematic (empty message, though ADK might handle it)
        # test_message_3 = ""
        # print(f"\nSending message: '{test_message_3}'")
        # reply_text_3, returned_session_id_3, require_form_3 = get_chat_response(test_message_3)
        # print(f"  Agent Reply: {reply_text_3}")
        # print(f"  Returned Session ID: {returned_session_id_3}")
        # print(f"  Require Form: {require_form_3}")
    elif not ADK_IMPORTED_SUCCESSFULLY:
        print("ADK components not imported. Cannot run local test.")
        reply, sid, req_form = get_chat_response("test message if ADK components not imported")
        print(f"Reply: '{reply}', Session ID: {sid}, Require Form: {req_form}")
    else: # ADK imported but agent not initialized
        print("AI Agent failed to initialize. Cannot run local test.")
        reply, sid, req_form = get_chat_response("test message if AI agent failed to initialize")
        print(f"Reply: '{reply}', Session ID: {sid}, Require Form: {req_form}")
