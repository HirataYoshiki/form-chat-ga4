from typing import Optional, Tuple
import os

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

if ADK_AVAILABLE:
    chat_agent = LlmAgent(
        name="simple_chat_agent",
        model=GEMINI_MODEL_NAME,
        instruction="You are a friendly and helpful chatbot. Respond concisely.",
        # If GOOGLE_API_KEY is set, ADK's underlying client might pick it up.
        # Alternatively, ensure ADC is configured in the environment where this runs.
    )
    agent_runner = InMemoryRunner(agent=chat_agent)
else:
    # Provide dummy initializations if ADK is not available
    chat_agent = LlmAgent() # This will print the warning
    agent_runner = InMemoryRunner(agent=chat_agent)


def get_chat_response(message: str, session_id: Optional[str] = None) -> Tuple[str, Optional[str], bool]:
    """
    Gets a chat response from the AI agent.
    Returns:
        Tuple[str, Optional[str], bool]: (reply_message, session_id, require_form_flag)
    """
    if not ADK_AVAILABLE:
        return "AI Agent is not available (google-adk-python not installed).", session_id, False

    try:
        # Run the agent with the user's message
        event: Event = agent_runner.run(request=message, session_id=session_id)

        reply = "[No response from agent or empty response]"
        response_session_id = session_id # Default to passed-in session_id

        if event.error_message:
            reply = f"[Agent Error: {event.error_message}]"
        elif event.actions and event.actions[0].parts:
            action_part = event.actions[0].parts[0]
            if hasattr(action_part, 'text') and action_part.text is not None:
                reply = action_part.text
            elif hasattr(action_part, 'code') and action_part.code is not None: # Example for code part
                reply = f"[Agent produced code: {action_part.code.code}]"
            else:
                reply = "[Agent produced a non-text/non-code response]"
        
        # Prefer session_id from the event if available and different
        if hasattr(event, 'session_id') and event.session_id:
            response_session_id = event.session_id
        
    except Exception as e:
        # Consider logging the full exception e for debugging
        print(f"Error communicating with AI Agent: {e}") # Simple print for now
        reply = f"[Error communicating with AI Agent: {str(e)}]"
        response_session_id = session_id

    return reply, response_session_id, False

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
