# backend/tests/test_ai_agent.py
import pytest
from unittest.mock import MagicMock, patch, ANY as AnyMockValue, call
import logging # For logger type hints and levels if needed by before_sleep_log

# It's assumed that the following can be imported from the SUT (System Under Test)
# This might require specific PYTHONPATH setup for the test runner.
# For subtask execution, if these cannot be resolved, the test might rely on patching
# at a higher level or the subtask might need to adjust paths/mocking.
try:
    from backend.ai_agent import get_chat_response # The SUT
    from backend.config import Settings # For type hinting mock_settings if needed
    from google.adk.events import Event # Type used in ai_agent.py
except ImportError as e:
    # Fallback for subtask environment if imports fail
    # This indicates a potential issue with how tests would run in the actual project
    # and should ideally be resolved by proper test environment setup.
    logging.getLogger(__name__).warning(f"Import error in test_ai_agent.py: {e}. Using placeholders.")
    # Define dummy/placeholder for Event if needed for mock spec, or rely on MagicMock's flexibility
    class Event: pass
    # get_chat_response will be patched or tested via API if direct import fails robustly


# Fixture to mock ai_agent.settings for controlling retry parameters in tests
@pytest.fixture
def mock_ai_agent_settings(mocker):
    # Patch the settings instance within the ai_agent module
    mock_settings_instance = mocker.patch("backend.ai_agent.settings")

    mock_settings_instance.ai_agent_retry_attempts = 3
    mock_settings_instance.ai_agent_retry_wait_initial_seconds = 0.01 # Very short for testing
    mock_settings_instance.ai_agent_retry_wait_multiplier = 1 # No exponential backoff for faster tests
    mock_settings_instance.ai_agent_retry_wait_max_seconds = 0.05 # Short max wait
    return mock_settings_instance

# Test cases
@patch("backend.ai_agent.agent_runner") # Mock the global agent_runner in ai_agent.py
@patch("backend.ai_agent.logger")      # Mock the logger in ai_agent.py
async def test_get_chat_response_success_first_try(
    mock_logger, mock_runner, mock_ai_agent_settings # Fixture is injected
):
    # Ensure AGENT_INITIALIZED_SUCCESSFULLY is True for these tests
    # This is a module-level variable in ai_agent.py
    with patch("backend.ai_agent.AGENT_INITIALIZED_SUCCESSFULLY", True):
        mock_event = MagicMock(spec=Event)
        mock_event.error_message = None
        # Simulate a valid JSON response structure
        mock_event.actions = [MagicMock(parts=[MagicMock(text='{"message": "AI Success", "require_form_after_message": false}')])]
        mock_event.session_id = "session_success_1st" # Ensure runner's event can set this

        mock_runner.run.return_value = mock_event

        # Directly import and call the decorated function
        from backend.ai_agent import get_chat_response
        reply, session_id, require_form = await get_chat_response("hello", "session_success_1st_input")

    assert reply == "AI Success"
    assert session_id == "session_success_1st" # Check if session_id from event is used
    assert require_form is False
    mock_runner.run.assert_called_once_with(request="hello", session_id="session_success_1st_input")
    # Check that no retry warning logs were made
    assert not any("Retrying AI Agent call" in c[0][0] for c in mock_logger.warning.call_args_list if isinstance(c[0][0], str))


@patch("backend.ai_agent.agent_runner")
@patch("backend.ai_agent.logger")
async def test_get_chat_response_retry_then_success(
    mock_logger, mock_runner, mock_ai_agent_settings
):
    with patch("backend.ai_agent.AGENT_INITIALIZED_SUCCESSFULLY", True):
        mock_event_success = MagicMock(spec=Event)
        mock_event_success.error_message = None
        mock_event_success.actions = [MagicMock(parts=[MagicMock(text='{"message": "AI Retry Success", "require_form_after_message": true}')])]
        mock_event_success.session_id = "session_retry_success"

        mock_runner.run.side_effect = [
            RuntimeError("Simulated network error"), # First call fails
            mock_event_success                     # Second call succeeds
        ]
        from backend.ai_agent import get_chat_response
        reply, session_id, require_form = await get_chat_response("retry please", "session_retry_input")

    assert reply == "AI Retry Success"
    assert require_form is True
    assert session_id == "session_retry_success"
    assert mock_runner.run.call_count == 2 # Initial call + 1 retry
    # Check if tenacity's before_sleep_log (which logs at WARNING) was called once
    assert mock_logger.warning.call_count == 1
    # Example check for log content if needed:
    # mock_logger.warning.assert_any_call(AnyMockValue(containing="Retrying AI Agent call"))


@patch("backend.ai_agent.agent_runner")
@patch("backend.ai_agent.logger")
async def test_get_chat_response_retry_all_attempts_fail(
    mock_logger, mock_runner, mock_ai_agent_settings
):
    with patch("backend.ai_agent.AGENT_INITIALIZED_SUCCESSFULLY", True):
        # Make all attempts fail
        mock_runner.run.side_effect = RuntimeError("Persistent failure")

        from backend.ai_agent import get_chat_response
        reply, session_id, require_form = await get_chat_response("this will fail", "session_fail_all")

    assert "AI Agent Error after retries" in reply
    assert require_form is False
    assert session_id == "session_fail_all" # Original session_id should be returned on full failure
    assert mock_runner.run.call_count == mock_ai_agent_settings.ai_agent_retry_attempts
    # Number of sleeps (and thus before_sleep_log calls) is attempts - 1
    assert mock_logger.warning.call_count == mock_ai_agent_settings.ai_agent_retry_attempts - 1
    # Check for the final error log after all retries are exhausted
    mock_logger.error.assert_called_once()
    # More specific check for the error log content
    args, kwargs = mock_logger.error.call_args
    assert "AI Agent call failed after %s attempts" in args[0]
    assert args[1] == mock_ai_agent_settings.ai_agent_retry_attempts
    assert args[2] == "session_fail_all"


@patch("backend.ai_agent.logger") # Only logger needed for this, agent_runner not called
async def test_get_chat_response_agent_not_initialized_import_failed(mock_logger):
    # Simulate ADK_IMPORTED_SUCCESSFULLY = False, AGENT_INITIALIZED_SUCCESSFULLY = False
    with patch("backend.ai_agent.AGENT_INITIALIZED_SUCCESSFULLY", False), \
         patch("backend.ai_agent.ADK_IMPORTED_SUCCESSFULLY", False):
        from backend.ai_agent import get_chat_response
        reply, session_id, require_form = await get_chat_response("query to broken agent", "session_broken_1")

    assert "AI Agent is unavailable due to missing dependencies" in reply
    assert require_form is False
    # Check the debug log for fallback reason
    # The actual log message in get_chat_response is "Serving fallback because ADK components not imported."
    # and it's logged via logger.debug, not logger.warning for this specific case.
    # The prompt has logger.warning.assert_any_call for these, let's adjust if the code uses debug.
    # Based on ai_agent.py: logger.debug("Serving fallback because ADK components not imported.")
    # So, this test case should check logger.debug.
    # However, the prompt's test code uses mock_logger.warning.assert_any_call.
    # For consistency with the prompt, I'll assume the test logic is what's desired.
    # If the actual log level is different, this assertion would need to change.
    # The current ai_agent.py logs these fallback reasons at DEBUG level.
    # The test prompt specified: mock_logger.warning.assert_any_call
    # Let's assume for the test that the logger in get_chat_response for this was changed to warning,
    # or the test intent is to ensure *some* log indicates the fallback.
    # For now, I will keep the test as per prompt, but this might be a discrepancy.
    # Looking at the actual code:
    # logger.debug("Serving fallback because ADK components not imported.")
    # logger.debug("Serving fallback because AI Agent failed to initialize.")
    # The tests should check logger.debug for these specific messages.
    # I will adjust the test to check logger.debug as per the actual implementation.

    # Corrected assertion based on actual implementation logging level
    found_log = False
    for call_args in mock_logger.debug.call_args_list:
        if "Serving fallback because ADK components not imported." in call_args[0][0]:
            found_log = True
            break
    assert found_log, "Expected debug log for ADK import failure not found."


@patch("backend.ai_agent.logger") # Only logger needed
async def test_get_chat_response_agent_not_initialized_init_failed(mock_logger):
    # Simulate ADK_IMPORTED_SUCCESSFULLY = True, AGENT_INITIALIZED_SUCCESSFULLY = False
    with patch("backend.ai_agent.AGENT_INITIALIZED_SUCCESSFULLY", False), \
         patch("backend.ai_agent.ADK_IMPORTED_SUCCESSFULLY", True):
        from backend.ai_agent import get_chat_response
        reply, session_id, require_form = await get_chat_response("query to broken agent", "session_broken_2")

    assert "AI Agent is currently experiencing setup issues" in reply
    assert require_form is False
    # Corrected assertion based on actual implementation logging level
    found_log = False
    for call_args in mock_logger.debug.call_args_list:
        if "Serving fallback because AI Agent failed to initialize." in call_args[0][0]:
            found_log = True
            break
    assert found_log, "Expected debug log for AI agent initialization failure not found."
