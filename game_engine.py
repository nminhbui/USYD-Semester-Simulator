"""Core semester state creation, week progression, and statistic updates."""

import random

from activities import activity_availability, calculate_activity_effects
from events import available_choices, get_main_event, get_unexpected_event, load_event_data
from financial_system import apply_money_effect, apply_weekly_finances
from student_generator import generate_profile

STAT_ORDER = ["academic", "health", "wellbeing", "social", "career", "family"]
STAT_LABELS = {
    "academic": "Academic Performance", "health": "Health", "wellbeing": "Wellbeing",
    "social": "Social Connection", "career": "Career Prospects", "family": "Family Connection",
}
LIFESTYLE_OPTIONS = {
    "housing": {
        "Close to campus": {"cost": 450, "wellbeing": 1, "health": 1},
        "Further from campus": {"cost": 300, "wellbeing": -1, "health": -1},
    },
    "food": {
        "Cook at home": {"cost": 55, "health": 3, "wellbeing": 1},
        "Eat out": {"cost": 120, "health": 0, "wellbeing": 3},
    },
    "transport": {
        "Train": {"cost": 35, "wellbeing": 0},
        "Bus": {"cost": 25, "wellbeing": -1},
        "Walk": {"cost": 0, "wellbeing": 0},
    },
}


def create_game(name, rng=None):
    """Start a new profile and choose two or three unique surprise events."""
    rng = rng or random.Random()
    profile = generate_profile(name, rng)
    data = load_event_data()
    eligible_weeks = rng.sample([3, 7, 11], k=rng.choice([2, 3]))
    surprise_pool = data["unexpected_events"]
    selected_events = rng.sample(surprise_pool, k=len(eligible_weeks))
    return {
        "version": 1,
        "status": "profile",
        "phase": "profile",
        "current_week": 1,
        "profile": profile,
        "stats": dict(profile["initial_stats"]),
        "money": profile["initial_money"],
        "lifestyle": None,
        "unexpected_schedule": {str(week): event["id"] for week, event in zip(eligible_weeks, selected_events)},
        "unexpected_seen": [],
        "rent_increase_from_week": None,
        "internship_unlocked": False,
        "club_member": False,
        "pending": None,
        "completed_weeks": [],
        "week_history": [],
        "stat_history": [],
        "transactions": [],
        "financial_weeks_processed": [],
        "financial_summary": {
            "starting_balance": profile["initial_money"], "total_family_support": 0,
            "total_employment_income": 0, "total_other_income": 0,
            "total_expenses": 0, "money_sent_to_family": 0,
        },
    }


def choose_lifestyle(state, housing, food, transport):
    """Save the player's lifestyle choices and begin Week 1."""
    choices = (("housing", housing), ("food", food), ("transport", transport))
    if any(option not in LIFESTYLE_OPTIONS[group] for group, option in choices):
        raise ValueError("Choose a valid housing, food, and transport option.")
    state["lifestyle"] = {"housing": housing, "food": food, "transport": transport}
    state["lifestyle"]["housing_cost"] = LIFESTYLE_OPTIONS["housing"][housing]["cost"]
    state["lifestyle"]["food_cost"] = LIFESTYLE_OPTIONS["food"][food]["cost"]
    state["lifestyle"]["transport_cost"] = LIFESTYLE_OPTIONS["transport"][transport]["cost"]
    state["phase"] = "event"
    state["status"] = "playing"


def apply_effects(state, week, effects, description, money_category="other"):
    """Apply event or activity effects and return the actual statistic changes."""
    actual = {}
    for key, amount in effects.items():
        if key == "money":
            apply_money_effect(state, week, description, amount, money_category)
            if amount:
                actual[key] = amount
        elif key in STAT_ORDER:
            before = state["stats"][key]
            state["stats"][key] = max(0, min(100, before + amount))
            delta = state["stats"][key] - before
            if delta:
                actual[key] = delta
    return actual


def prepare_week(state, event_response_id):
    """Resolve the chosen main event and its scheduled automatic surprise."""
    if state["status"] != "playing" or state["phase"] != "event":
        raise ValueError("The current week is not waiting for an event response.")
    week = state["current_week"]
    event = get_main_event(week)
    choice = next((item for item in available_choices(event, state) if item["id"] == event_response_id), None)
    if choice is None:
        raise ValueError("Choose one of the available responses.")
    actual = apply_effects(state, week, choice["effects"], f"Week {week}: {choice['label']}")
    if week == 7 and event_response_id in {"networking_event", "professional_skills"}:
        state["internship_unlocked"] = True
    unexpected = None
    surprise_id = state["unexpected_schedule"].get(str(week))
    if surprise_id:
        if surprise_id in state["unexpected_seen"]:
            raise ValueError("An unexpected event cannot be repeated.")
        unexpected = get_unexpected_event(surprise_id)
        effects = dict(unexpected["effects"])
        if unexpected.get("variable_money"):
            amount = random.choice(unexpected["variable_money"])
            effects["money"] = amount
            unexpected = dict(unexpected, resolved_money=amount)
        surprise_actual = apply_effects(state, week, effects, f"Week {week}: {unexpected['title']}", unexpected.get("category", "other"))
        if unexpected.get("rent_increase"):
            state["rent_increase_from_week"] = week + 1
        state["unexpected_seen"].append(surprise_id)
        state["pending_unexpected"] = {"id": surprise_id, "title": unexpected["title"], "narrative": unexpected["narrative"], "effects": effects, "actual_effects": surprise_actual, "resolved_money": unexpected.get("resolved_money")}
    state["pending"] = {"event_id": event_response_id, "event_title": event["title"], "choice_label": choice["label"], "effects": dict(choice["effects"]), "actual_effects": actual}
    state["phase"] = "activity"
    return state.get("pending_unexpected")


def available_activities(state):
    """Expose the current activity conditions to the web page."""
    return activity_availability(state)


def complete_week(state, activity_name):
    """Resolve one valid activity and weekly finances, then advance once."""
    if state["status"] != "playing" or state["phase"] != "activity" or not state.get("pending"):
        raise ValueError("Resolve the main event before completing the week.")
    week = state["current_week"]
    effects, notes = calculate_activity_effects(activity_name, state)
    activity_actual = apply_effects(state, week, effects, f"Week {week}: {activity_name}", "employment_income" if activity_name in {"Part-time Work", "Internship"} else "other")
    if activity_name == "Join a Club":
        state["club_member"] = True
    apply_weekly_finances(state, week)
    lifestyle_effects = {
        "wellbeing": LIFESTYLE_OPTIONS["housing"][state["lifestyle"]["housing"]]["wellbeing"] +
                     LIFESTYLE_OPTIONS["food"][state["lifestyle"]["food"]]["wellbeing"] +
                     LIFESTYLE_OPTIONS["transport"][state["lifestyle"]["transport"]]["wellbeing"],
        "health": LIFESTYLE_OPTIONS["housing"][state["lifestyle"]["housing"]]["health"] +
                  LIFESTYLE_OPTIONS["food"][state["lifestyle"]["food"]]["health"] +
                  (2 if state["lifestyle"]["transport"] == "Walk" and state["lifestyle"]["housing"] == "Close to campus" else 0),
    }
    if state["lifestyle"]["transport"] == "Walk" and state["lifestyle"]["housing"] != "Close to campus":
        lifestyle_effects["wellbeing"] -= 1
    lifestyle_actual = apply_effects(state, week, lifestyle_effects, f"Week {week}: lifestyle routine")
    snapshot = [state["stats"][key] for key in STAT_ORDER]
    state["stat_history"].append(snapshot)
    state["completed_weeks"].append(week)
    entry = {
        "week": week, "event_title": state["pending"]["event_title"],
        "choice_label": state["pending"]["choice_label"], "choice_effects": state["pending"]["actual_effects"],
        "unexpected": state.pop("pending_unexpected", None), "activity": activity_name,
        "activity_effects": activity_actual, "activity_notes": notes,
        "lifestyle_effects": lifestyle_actual, "ending_money": state["money"], "stats": dict(state["stats"]),
    }
    state["week_history"].append(entry)
    state["pending"] = None
    if week == 12:
        state["status"] = "complete"
        state["phase"] = "report"
    else:
        state["current_week"] = week + 1
        state["phase"] = "event"
    return entry
