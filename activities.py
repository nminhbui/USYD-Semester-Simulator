"""Activity rules, eligibility checks and outcome calculations."""

ACTIVITIES = {
    "Study": {"money": 0, "academic": 8, "health": -1, "wellbeing": -2, "social": 0, "career": 1},
    "Part-time Work": {"money": 220, "academic": -2, "health": -2, "wellbeing": -2, "social": 0, "career": 3},
    "Socialise": {"money": -50, "academic": -1, "health": 0, "wellbeing": 4, "social": 8, "career": 1},
    "Join a Club": {"money": -25, "academic": 0, "health": 0, "wellbeing": 3, "social": 7, "career": 3},
    "Rest and Recover": {"money": 0, "academic": -1, "health": 5, "wellbeing": 7, "social": 0, "career": 0},
    "Career Development": {"money": -20, "academic": 1, "health": -1, "wellbeing": 0, "social": 2, "career": 6},
    "Internship": {"money": 280, "academic": 1, "health": -1, "wellbeing": 1, "social": 2, "career": 8},
}


def internship_eligible(state):
    """Check simple, visible pathways to an internship activity."""
    profile = state["profile"]
    stats = state["stats"]
    ordinary_path = (
        stats["career"] >= 55
        or (stats["academic"] >= 60 and stats["career"] >= 40)
        or (stats["social"] >= 60 and stats["career"] >= 45)
    )
    experience_path = profile["work_experience"] == "Relevant experience" and stats["career"] >= 45
    event_path = state.get("internship_unlocked", False)
    if profile["family_responsibilities"] == "High" and not event_path:
        ordinary_path = ordinary_path and stats["career"] >= 65
        experience_path = experience_path and stats["career"] >= 55
    return ordinary_path or experience_path or event_path


def activity_availability(state):
    """Return availability and a clear reason for each activity."""
    health = state["stats"]["health"]
    money = state["money"]
    result = {}
    for name in ACTIVITIES:
        allowed, reason = True, "Available"
        if name == "Study" and health < 20:
            allowed, reason = False, "Unavailable while Health is below 20. Rest first."
        elif name == "Part-time Work" and health < 30:
            allowed, reason = False, "Unavailable while Health is below 30. Rest first."
        elif name == "Socialise" and money < 50:
            allowed, reason = False, "Requires $50 available for this week's activity."
        elif name == "Join a Club" and state.get("club_member"):
            allowed, reason = False, "You are already a club member."
        elif name == "Join a Club" and money < 25:
            allowed, reason = False, "Requires $25 available for the club fee."
        elif name == "Career Development" and money < 20:
            allowed, reason = False, "Requires $20 available for materials or travel."
        elif name == "Internship" and not internship_eligible(state):
            allowed, reason = False, "Requires Career 55, or relevant experience with Career 45, or a career event unlock."
        result[name] = {"available": allowed, "reason": reason}
    return result


def calculate_activity_effects(name, state):
    """Apply health and wellbeing conditions to an activity's baseline effects."""
    if name not in ACTIVITIES or not activity_availability(state)[name]["available"]:
        raise ValueError("That activity is not available.")
    effects = dict(ACTIVITIES[name])
    notes = []
    health = state["stats"]["health"]
    if name == "Study" and 20 <= health <= 39:
        effects["academic"] = 4
        notes.append("Health between 20 and 39 reduced the Study gain by half.")
    elif name == "Study" and state["stats"]["wellbeing"] < 20:
        effects["academic"] = 4
        notes.append("Wellbeing below 20 reduced the Study gain by half.")
    if name == "Part-time Work" and 30 <= health <= 39:
        effects["money"] = 110
        notes.append("Health between 30 and 39 reduced work income by half.")
    return effects, notes
