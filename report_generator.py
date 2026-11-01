"""Build outcome, turning points, and a data-based semester narrative."""

from game_engine import STAT_LABELS, STAT_ORDER


def longest_improvement_streak(rows, column, index=1, current=0, best=0):
    """Recursively find the longest run of week-to-week gains in one statistic."""
    if index >= len(rows):
        return best
    if rows[index][column] > rows[index - 1][column]:
        current += 1
        best = max(best, current)
    else:
        current = 0
    return longest_improvement_streak(rows, column, index + 1, current, best)


def choose_outcome(state):
    """Choose a descriptive category from several final-state signals."""
    initial = state["profile"]["initial_stats"]
    final = state["stats"]
    low_count = sum(final[key] < 22 for key in STAT_ORDER)
    if low_count >= 2 or (final["health"] < 18 and final["wellbeing"] < 20):
        return "Challenging Semester"
    if final["academic"] >= 60 and final["academic"] - initial["academic"] >= 12:
        return "Academically Focused Semester"
    if final["career"] >= 58 and final["career"] - initial["career"] >= 12:
        return "Career Development Semester"
    if final["social"] >= 60 and final["social"] - initial["social"] >= 15:
        return "Socially Active Semester"
    if state["money"] >= 500 and state["money"] >= state["financial_summary"]["starting_balance"]:
        return "Financially Independent Semester"
    if sum(final[key] >= initial[key] for key in STAT_ORDER) >= 4:
        return "Balanced Semester"
    return "Challenging Semester"


def turning_points(state):
    """Select up to three consequential weeks from actual recorded changes."""
    candidates = []
    for entry in state["week_history"]:
        change_size = sum(abs(value) for value in entry["choice_effects"].values())
        if entry["unexpected"]:
            change_size += sum(abs(value) for value in entry["unexpected"].get("actual_effects", {}).values())
        change_size += sum(abs(value) for value in entry["activity_effects"].values())
        if change_size >= 8 or entry["unexpected"]:
            detail = f"Week {entry['week']}: {entry['choice_label']}"
            if entry["unexpected"]:
                detail += f"; {entry['unexpected']['title']} also occurred"
            candidates.append((change_size, detail))
    return [detail for _, detail in sorted(candidates, reverse=True)[:3]]


def build_report(state):
    """Prepare report data, including a trend insight from weekly snapshots."""
    rows = state["stat_history"]
    wellbeing_streak = longest_improvement_streak(rows, STAT_ORDER.index("wellbeing")) if rows else 0
    profile = state["profile"]
    highest = max(STAT_ORDER, key=lambda key: state["stats"][key])
    improvement = state["stats"][highest] - profile["initial_stats"][highest]
    first_sentence = (
        f"{profile['name']} completed a Master's semester in {profile['faculty']}. "
        f"Their {profile['socioeconomic_background']} background and {profile['family_responsibilities'].lower()} family responsibilities shaped the choices available along the way."
    )
    second_sentence = (
        f"By the end, {STAT_LABELS[highest].lower()} was their highest area at {state['stats'][highest]}/100 "
        f"({improvement:+d} from the start). Their semester outcome is {choose_outcome(state).lower()}."
    )
    if state["money"] < 0:
        money_sentence = f"The semester ended with ${abs(state['money']):.2f} in debt after weekly income and costs were recorded."
    else:
        money_sentence = f"The semester ended with ${state['money']:.2f} available after weekly income and costs were recorded."
    if wellbeing_streak:
        trend_sentence = f"Wellbeing rose for {wellbeing_streak} consecutive week-to-week changes at its longest stretch."
    else:
        trend_sentence = "The weekly snapshots show that wellbeing did not rise in consecutive weeks, though individual choices still changed its direction."
    return {
        "outcome": choose_outcome(state),
        "narrative": " ".join([first_sentence, second_sentence, money_sentence, trend_sentence]),
        "turning_points": turning_points(state),
        "wellbeing_streak": wellbeing_streak,
        "stat_order": STAT_ORDER,
        "stat_labels": STAT_LABELS,
    }
