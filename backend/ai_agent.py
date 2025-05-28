from typing import Optional, Tuple
import os
import json # Added json import
from pydantic import BaseModel, Field

# Attempt to import ADK components. Handle gracefully if not available.
try:
    from google.adk.agents import LlmAgent
    from google.adk.runners import InMemoryRunner
    from google.adk.events import Event
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    # Define dummy classes if ADK is not available, so the rest of the file can still be parsed
    # and the API can run with a clear indication that the ADK part is non-functional.

# --- Pydantic Model for Structured Agent Response ---
class AgentStructuredResponse(BaseModel):
    message: str = Field(description="The chat message response from the AI agent.")
    require_form_after_message: bool = Field(
        description="Indicates if the frontend should suggest or display a contact form after this message."
    )

class LlmAgent:
        def __init__(self, *args, **kwargs):
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

GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash-latest")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # ADK might use this if provided

# Generate JSON schema string for the agent's structured response
AGENT_RESPONSE_JSON_SCHEMA = json.dumps(AgentStructuredResponse.model_json_schema(), indent=2)

if ADK_AVAILABLE:
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
else:
    # Define dummy chat_agent and agent_runner if ADK is not available
    chat_agent = None # type: ignore
    agent_runner = None # type: ignore


def get_chat_response(message: str, session_id: Optional[str] = None) -> Tuple[str, Optional[str], bool]:
    """
    Gets a chat response from the AI agent.
    Returns:
        Tuple[str, Optional[str], bool]: (reply_message, session_id, require_form_flag)
    """
    if not ADK_AVAILABLE or agent_runner is None: # Check agent_runner as well
        return "AI Agent is not available (google-adk-python not installed or agent_runner is None).", session_id, False

    try:
        # Run the agent with the user's message
        event: Event = agent_runner.run(request=message, session_id=session_id)

        reply = "[No response from agent or empty response]"
        require_form = False # Default value
        response_session_id = session_id # Default to passed-in session_id

        if event.error_message:
            reply = f"[Agent Error: {event.error_message}]"
        elif event.actions and event.actions[0].parts:
            action_part = event.actions[0].parts[0]
            # Assuming the agent now returns JSON in the 'text' field of the first part
            if hasattr(action_part, 'text') and action_part.text:
                try:
                    structured_response_data = json.loads(action_part.text)
                    # Validate with Pydantic model (optional but good practice)
                    parsed_response = AgentStructuredResponse(**structured_response_data)
                    reply = parsed_response.message
                    require_form = parsed_response.require_form_after_message
                except json.JSONDecodeError:
                    reply = "[Agent Error: Failed to decode JSON response]"
                except Exception as pydantic_error: # Catch Pydantic validation errors
                    reply = f"[Agent Error: Invalid JSON structure: {pydantic_error}]"
            else:
                reply = "[Agent produced no actionable text output]"
        
        # Prefer session_id from the event if available and different
        if hasattr(event, 'session_id') and event.session_id:
            response_session_id = event.session_id
        
    except Exception as e:
        # Consider logging the full exception e for debugging
        print(f"Error communicating with AI Agent: {e}") # Simple print for now
        reply = f"[Error communicating with AI Agent: {str(e)}]"
        response_session_id = session_id
        require_form = False # Ensure require_form is always returned

    return reply, response_session_id, require_form

# Example of how you might test this function directly (requires ADK and auth)
if __name__ == '__main__':
    if ADK_AVAILABLE:
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
    else:
        print("ADK not available, cannot run local test.")
        reply, sid, req_form = get_chat_response("test message if ADK not installed")
        print(f"Reply when ADK not installed: '{reply}', Session ID: {sid}, Require Form: {req_form}")
