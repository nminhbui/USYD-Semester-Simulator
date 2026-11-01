"""Flask entry point for the USYD Semester Simulator."""

import os
import random

from flask import Flask, flash, redirect, render_template, request, url_for

from activities import ACTIVITIES, activity_availability, calculate_activity_effects
from events import available_choices, get_main_event
from game_engine import LIFESTYLE_OPTIONS, STAT_LABELS, STAT_ORDER, choose_lifestyle, complete_week, create_game, prepare_week
from report_generator import build_report
from save_manager import SaveError, load_game, reset_game, save_game

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "local-semester-simulator-key")


def current_game():
    """Load the single local game save, if one exists."""
    return load_game()


def require_game():
    """Return the current game or send the player to the landing page."""
    state = current_game()
    if state is None:
        flash("Start a new game to begin a semester.", "info")
        return None
    return state


def money_effect_label(value):
    """Format a money effect with an explicit sign."""
    return f"{'+' if value >= 0 else '−'}${abs(value):,.0f}"


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Enter a student name to generate a profile.", "error")
            return redirect(url_for("index"))
        if len(name) > 40:
            flash("Use a name of 40 characters or fewer.", "error")
            return redirect(url_for("index"))
        try:
            state = create_game(name, random.Random())
            save_game(state)
        except (SaveError, OSError, ValueError) as error:
            flash(str(error) if isinstance(error, SaveError) else "The new game could not be created.", "error")
            return redirect(url_for("index"))
        return redirect(url_for("profile"))
    try:
        state = current_game()
        save_problem = None
    except SaveError as error:
        state, save_problem = None, str(error)
    return render_template("index.html", state=state, save_problem=save_problem)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    state = require_game()
    if state is None:
        return redirect(url_for("index"))
    if state["status"] != "profile":
        return redirect(url_for("game"))
    if request.method == "POST":
        try:
            choose_lifestyle(
                state,
                request.form.get("housing", ""),
                request.form.get("food", ""),
                request.form.get("transport", ""),
            )
            save_game(state)
        except (ValueError, SaveError) as error:
            flash(str(error), "error")
            return redirect(url_for("profile"))
        return redirect(url_for("game"))
    return render_template("student_profile.html", state=state, stat_labels=STAT_LABELS, stat_order=STAT_ORDER, options=LIFESTYLE_OPTIONS)


@app.route("/game")
def game():
    state = require_game()
    if state is None:
        return redirect(url_for("index"))
    if state["status"] == "profile":
        return redirect(url_for("profile"))
    if state["status"] == "complete":
        return redirect(url_for("report"))
    week = state["current_week"]
    event = get_main_event(week)
    availability = activity_availability(state)
    predictions = {}
    for name, condition in availability.items():
        if condition["available"]:
            try:
                predictions[name], _ = calculate_activity_effects(name, state)
            except ValueError:
                predictions[name] = {}
    return render_template(
        "game.html", state=state, event=event, choices=available_choices(event, state),
        stat_labels=STAT_LABELS, stat_order=STAT_ORDER, availability=availability,
        predictions=predictions, activity_names=list(ACTIVITIES),
        progress=(len(state["completed_weeks"]) / 12) * 100,
        money_effect_label=money_effect_label,
    )


@app.route("/resolve-event", methods=["POST"])
def resolve_event():
    state = require_game()
    if state is None:
        return redirect(url_for("index"))
    try:
        prepare_week(state, request.form.get("choice", ""))
        save_game(state)
    except (ValueError, SaveError) as error:
        flash(str(error), "error")
        return redirect(url_for("game"))
    return redirect(url_for("game"))


@app.route("/complete-week", methods=["POST"])
def complete_current_week():
    state = require_game()
    if state is None:
        return redirect(url_for("index"))
    try:
        complete_week(state, request.form.get("activity", ""))
        save_game(state)
    except (ValueError, SaveError) as error:
        flash(str(error), "error")
        return redirect(url_for("game"))
    if state["status"] == "complete":
        return redirect(url_for("report"))
    return redirect(url_for("game"))


@app.route("/report")
def report():
    state = require_game()
    if state is None:
        return redirect(url_for("index"))
    if state["status"] != "complete":
        flash("Complete all 12 weeks to view your semester report.", "info")
        return redirect(url_for("game"))
    return render_template("report.html", state=state, report=build_report(state), stat_labels=STAT_LABELS, stat_order=STAT_ORDER)


@app.route("/restart", methods=["POST"])
def restart():
    try:
        reset_game()
    except SaveError as error:
        flash(str(error), "error")
        return redirect(url_for("report"))
    flash("Your previous semester was cleared. Enter a name to generate a new student profile.", "info")
    return redirect(url_for("index"))


@app.errorhandler(SaveError)
def handle_save_error(error):
    """Show save problems without exposing tracebacks."""
    return render_template("error.html", message=str(error)), 500


@app.errorhandler(ValueError)
def handle_data_error(error):
    """Show invalid game-data errors without exposing an internal traceback."""
    return render_template("error.html", message=str(error)), 500


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", message="That page could not be found."), 404


if __name__ == "__main__":
    print("USYD Semester Simulator is running at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
