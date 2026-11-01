"""Load event data and provide the event choices available to a student."""

import json
from pathlib import Path


DATA_PATH = Path(__file__).resolve().parent / "data" / "events.json"


def load_event_data(path=DATA_PATH):
    """Read the structured event definitions from JSON."""
    try:
        with path.open(encoding="utf-8") as event_file:
            data = json.load(event_file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Game event data could not be loaded. Make sure data/events.json is present and valid.") from error
    if not isinstance(data, dict):
        raise ValueError("Game event data must use the expected JSON structure.")
    main_events = data.get("main_events", [])
    if not isinstance(main_events, list) or len(main_events) != 12 or any(not isinstance(event, dict) for event in main_events) or [event.get("week") for event in main_events] != list(range(1, 13)):
        raise ValueError("The event file must contain one main event for each week.")
    unexpected = data.get("unexpected_events")
    if not isinstance(unexpected, list) or len(unexpected) < 3 or any(not isinstance(event, dict) or not isinstance(event.get("id"), str) for event in unexpected):
        raise ValueError("The event file must contain a valid unexpected event pool.")
    if len({event["id"] for event in unexpected}) != len(unexpected):
        raise ValueError("Unexpected event identifiers must be unique.")
    return data


def get_main_event(week, event_data=None):
    """Return the predefined event for a semester week."""
    event_data = event_data or load_event_data()
    return event_data["main_events"][week - 1]


def available_choices(event, state):
    """Hide responses whose profile-specific conditions are not met."""
    return [choice for choice in event["choices"]
            if not choice.get("requires_family_help") or state["profile"]["family_can_help"]]


def get_unexpected_event(event_id, event_data=None):
    """Find an unexpected event by its stable identifier."""
    event_data = event_data or load_event_data()
    for event in event_data["unexpected_events"]:
        if event["id"] == event_id:
            return event
    raise ValueError("Unknown unexpected event.")
