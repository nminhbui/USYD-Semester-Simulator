"""Small JSON save manager with validation and atomic file replacement."""

import json
import math
import os
import tempfile
from pathlib import Path


SAVE_PATH = Path(__file__).resolve().parent / "saves" / "game_state.json"
REQUIRED_FIELDS = {"version", "status", "phase", "current_week", "profile", "stats", "money", "transactions", "week_history"}


class SaveError(Exception):
    """Raised when saved data cannot safely be read or written."""


def validate_state(state):
    """Check the minimum structure and ranges needed before using a save."""
    if not isinstance(state, dict) or not REQUIRED_FIELDS.issubset(state):
        raise SaveError("The saved game is incomplete. Start a new game to continue.")
    if state.get("version") != 1 or state.get("status") not in {"profile", "playing", "complete"}:
        raise SaveError("The saved game uses an unsupported format. Start a new game to continue.")
    if type(state.get("current_week")) is not int or not 1 <= state["current_week"] <= 12:
        raise SaveError("The saved week is invalid. Start a new game to continue.")
    profile_fields = {"name", "faculty", "masters_degree", "year", "bachelor_degree", "related_bachelor", "living_arrangement", "employment_status", "work_experience", "socioeconomic_background", "siblings", "parents_health", "family_responsibilities", "family_expectations", "family_relationship", "monthly_family_support", "weekly_family_support", "family_can_help", "initial_money", "initial_stats"}
    if not isinstance(state.get("profile"), dict) or not profile_fields.issubset(state["profile"]) or not isinstance(state["profile"].get("name"), str):
        raise SaveError("The saved student profile is invalid.")
    expected = {"academic", "health", "wellbeing", "social", "career", "family"}
    if not isinstance(state.get("stats"), dict) or set(state["stats"]) != expected:
        raise SaveError("The saved statistics are invalid. Start a new game to continue.")
    if any(type(value) is not int or not 0 <= value <= 100 for value in state["stats"].values()):
        raise SaveError("A saved statistic is outside its allowed range.")
    initial_stats = state["profile"].get("initial_stats")
    if not isinstance(initial_stats, dict) or set(initial_stats) != expected or any(type(value) is not int or not 0 <= value <= 100 for value in initial_stats.values()):
        raise SaveError("The saved starting statistics are invalid.")
    if type(state.get("money")) not in {int, float} or not math.isfinite(state["money"]):
        raise SaveError("The saved money balance is invalid.")
    if not isinstance(state.get("transactions"), list) or not isinstance(state.get("week_history"), list):
        raise SaveError("The saved history is invalid.")
    completed = state.get("completed_weeks")
    if not isinstance(completed, list) or completed != list(range(1, len(completed) + 1)):
        raise SaveError("The saved week progression is invalid.")
    if len(state["week_history"]) != len(completed):
        raise SaveError("The saved week history is inconsistent.")
    if state.get("phase") not in {"profile", "event", "activity", "report"}:
        raise SaveError("The saved game phase is invalid.")
    if state["status"] == "profile" and (state["phase"] != "profile" or completed):
        raise SaveError("The saved profile phase is inconsistent.")
    if state["status"] == "playing":
        if state["phase"] not in {"event", "activity"} or completed != list(range(1, state["current_week"])) or not isinstance(state.get("lifestyle"), dict):
            raise SaveError("The saved game progression is inconsistent.")
        if not {"housing", "food", "transport", "housing_cost", "food_cost", "transport_cost"}.issubset(state["lifestyle"]):
            raise SaveError("The saved lifestyle choices are incomplete.")
        if (state["phase"] == "activity") != isinstance(state.get("pending"), dict):
            raise SaveError("The saved event response is inconsistent.")
    if state["status"] == "complete" and (state["phase"] != "report" or completed != list(range(1, 13))):
        raise SaveError("The saved final report is incomplete.")
    snapshots = state.get("stat_history")
    if not isinstance(snapshots, list) or len(snapshots) != len(completed):
        raise SaveError("The saved statistic history is inconsistent.")
    if any(not isinstance(row, list) or len(row) != 6 or any(type(value) is not int or not 0 <= value <= 100 for value in row) for row in snapshots):
        raise SaveError("A saved weekly statistic snapshot is invalid.")
    schedule = state.get("unexpected_schedule")
    if not isinstance(schedule, dict) or len(schedule) not in {2, 3} or not set(schedule).issubset({"3", "7", "11"}) or len(set(schedule.values())) != len(schedule):
        raise SaveError("The saved unexpected event schedule is invalid.")
    summary = state.get("financial_summary")
    summary_fields = {"starting_balance", "total_family_support", "total_employment_income", "total_other_income", "total_expenses", "money_sent_to_family"}
    if not isinstance(summary, dict) or not summary_fields.issubset(summary):
        raise SaveError("The saved financial summary is incomplete.")
    if any(type(summary[field]) not in {int, float} or not math.isfinite(summary[field]) for field in summary_fields):
        raise SaveError("A saved financial total is invalid.")
    for transaction in state["transactions"]:
        if (not isinstance(transaction, dict) or not isinstance(transaction.get("description"), str)
                or transaction.get("kind") not in {"income", "expense"}
                or type(transaction.get("week")) is not int or not 1 <= transaction["week"] <= 12
                or type(transaction.get("amount")) not in {int, float} or transaction["amount"] < 0
                or not math.isfinite(transaction["amount"])
                or type(transaction.get("balance")) not in {int, float} or not math.isfinite(transaction["balance"])):
            raise SaveError("A saved financial transaction is invalid.")
    for expected_week, entry in enumerate(state["week_history"], start=1):
        if (not isinstance(entry, dict) or entry.get("week") != expected_week
                or not isinstance(entry.get("event_title"), str)
                or not isinstance(entry.get("choice_label"), str)
                or not isinstance(entry.get("activity"), str)
                or type(entry.get("ending_money")) not in {int, float}):
            raise SaveError("A saved weekly history entry is invalid.")
    return state


def load_game(path=SAVE_PATH):
    """Load an existing save, returning None if no game has been saved."""
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as save_file:
            return validate_state(json.load(save_file))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        if isinstance(error, SaveError):
            raise
        raise SaveError("The saved game could not be read. The file was left untouched; start a new game to continue.") from error


def save_game(state, path=SAVE_PATH):
    """Write a validated game save using a temporary file and atomic replace."""
    validate_state(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as temporary:
            json.dump(state, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    except OSError as error:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)
        raise SaveError("The game could not be saved. Check that the project folder is writable.") from error


def reset_game(path=SAVE_PATH):
    """Remove the current save when the player explicitly starts again."""
    try:
        path.unlink(missing_ok=True)
    except OSError as error:
        raise SaveError("The previous game could not be cleared. Check that the project folder is writable.") from error
