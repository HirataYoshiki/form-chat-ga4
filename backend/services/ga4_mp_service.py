# backend/services/ga4_mp_service.py
import httpx
import logging
from typing import List, Dict, Any, Optional
import time # For timestamp_micros default

logger = logging.getLogger(__name__)

GA4_MP_URL = "https://www.google-analytics.com/mp/collect"
# Measurement Protocolリクエストのタイムアウト（秒）
DEFAULT_MP_TIMEOUT = 10.0

async def send_ga4_event(
    api_secret: str,
    measurement_id: str,
    client_id: str,
    events: List[Dict[str, Any]],
    # session_id is typically part of event params, but can be passed for inclusion
    # timestamp_micros defaults to current time if not provided
    timestamp_micros: Optional[int] = None,
    user_properties: Optional[Dict[str, Any]] = None,
    non_personalized_ads: bool = False
) -> bool:
    """
    Sends one or more events to Google Analytics 4 Measurement Protocol.

    Args:
        api_secret: The API secret for the GA4 property.
        measurement_id: The Measurement ID for the GA4 property.
        client_id: The client ID for the user.
        events: A list of event objects. Each event object should be a dictionary
                with 'name' (string) and 'params' (dict) keys.
        timestamp_micros: Event timestamp in microseconds (UTC).
                          If None, current time will be used.
        user_properties: Optional user properties to send.
        non_personalized_ads: Whether these events are for non-personalized ads.

    Returns:
        True if the request was successful (2xx status code), False otherwise.
    """
    if not api_secret or not measurement_id:
        logger.error("GA4 API Secret or Measurement ID is missing. Cannot send event(s) for client_id: %s", client_id)
        return False
    if not client_id:
        logger.error("GA4 Client ID is missing. Cannot send event(s) for measurement_id: %s", measurement_id)
        return False
    if not events:
        logger.warning("No events provided to send to GA4 for client_id: %s, measurement_id: %s.", client_id, measurement_id)
        return True # No events to send is not an error of this function.

    # Prepare the main payload
    payload: Dict[str, Any] = {
        "client_id": client_id,
        "non_personalized_ads": non_personalized_ads,
        "events": events, # Events should already have session_id in their params if needed
    }

    if timestamp_micros is None:
        # Default to current time in microseconds if not provided
        payload["timestamp_micros"] = int(time.time() * 1_000_000)
    else:
        payload["timestamp_micros"] = timestamp_micros

    if user_properties:
        payload["user_properties"] = user_properties

    # Query parameters for the POST request
    query_params = {
        "api_secret": api_secret,
        "measurement_id": measurement_id,
    }

    event_names = [event.get("name", "unknown_event") for event in events]
    logger.debug(
        "Attempting to send GA4 events. Measurement ID: %s, Client ID: %s, Events: %s, Payload: %s",
        measurement_id, client_id, event_names, payload
    )

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_MP_TIMEOUT) as http_client: # Renamed client to http_client
            response = await http_client.post(GA4_MP_URL, params=query_params, json=payload)

        if 200 <= response.status_code < 300:
            logger.info(
                "Successfully sent %d event(s) to GA4: %s (Measurement ID: %s, Client ID: %s)",
                len(events), event_names, measurement_id, client_id
            )
            # Check for validation messages if the validation server was hit (usually by not using "www.")
            # or if GA4 MP returns them in a successful response.
            if response.content:
                try:
                    validation_data = response.json()
                    if validation_data and validation_data.get("validationMessages"):
                        logger.warning(
                            "GA4 Measurement Protocol validation messages for Measurement ID %s, Client ID %s: %s",
                            measurement_id, client_id, validation_data.get("validationMessages")
                        )
                except Exception: # Not a JSON response
                    logger.debug(
                        "GA4 Measurement Protocol response content (non-JSON) for Measurement ID %s, Client ID %s: %s",
                        measurement_id, client_id, response.text[:500]
                    )
            return True
        else:
            logger.error(
                "Failed to send event(s) to GA4: %s (Measurement ID: %s, Client ID: %s). Status: %d, Response: %s",
                event_names, measurement_id, client_id, response.status_code, response.text[:500]
            )
            return False
    except httpx.TimeoutException:
        logger.error(
            "Timeout sending event(s) to GA4: %s (Measurement ID: %s, Client ID: %s).",
            event_names, measurement_id, client_id
        )
        return False
    except httpx.RequestError as e:
        logger.error(
            "RequestError sending event(s) to GA4: %s (Measurement ID: %s, Client ID: %s): %s",
            event_names, measurement_id, client_id, e, exc_info=True
        )
        return False
    except Exception as e:
        logger.error(
            "Unexpected error sending event(s) to GA4: %s (Measurement ID: %s, Client ID: %s): %s",
            event_names, measurement_id, client_id, e, exc_info=True
        )
        return False
