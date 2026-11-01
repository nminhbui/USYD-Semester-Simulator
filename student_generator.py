"""Create a plausible student profile and balanced starting statistics."""

import random


FACULTY_DEGREES = {
    "Faculty of Arts and Social Sciences": ("Master of Social Work", ["Bachelor of Arts", "Bachelor of Social Science", "Bachelor of Psychology"]),
    "Sydney School of Architecture, Design and Planning": ("Master of Architecture", ["Bachelor of Design", "Bachelor of Architecture", "Bachelor of Planning"]),
    "University of Sydney Business School": ("Master of Commerce", ["Bachelor of Commerce", "Bachelor of Economics", "Bachelor of Business"]),
    "Faculty of Engineering": ("Master of Professional Engineering", ["Bachelor of Engineering", "Bachelor of Science", "Bachelor of Computer Science"]),
    "Sydney Law School": ("Master of Laws", ["Bachelor of Laws", "Bachelor of Arts", "Bachelor of Commerce"]),
    "Faculty of Medicine and Health": ("Master of Public Health", ["Bachelor of Health Sciences", "Bachelor of Science", "Bachelor of Nursing"]),
    "Sydney Conservatorium of Music": ("Master of Music Studies", ["Bachelor of Music", "Bachelor of Arts", "Bachelor of Music Education"]),
    "Faculty of Science": ("Master of Data Science", ["Bachelor of Science", "Bachelor of Computer Science", "Bachelor of Mathematics"]),
}

BASELINES = {
    "financially comfortable": {"academic": 40, "health": 40, "wellbeing": 40, "social": 35, "career": 35, "family": 40},
    "middle-income": {"academic": 38, "health": 38, "wellbeing": 36, "social": 33, "career": 32, "family": 38},
    "financially disadvantaged": {"academic": 35, "health": 36, "wellbeing": 30, "social": 30, "career": 28, "family": 35},
    "independent": {"academic": 38, "health": 36, "wellbeing": 32, "social": 32, "career": 33, "family": 32},
    "high family responsibilities": {"academic": 35, "health": 34, "wellbeing": 28, "social": 28, "career": 28, "family": 38},
}


def generate_profile(name, rng=None):
    """Generate a student using the supplied random generator when provided."""
    rng = rng or random.Random()
    faculty = rng.choice(list(FACULTY_DEGREES))
    masters_degree, bachelor_options = FACULTY_DEGREES[faculty]
    related = rng.random() < 0.65
    bachelor_degree = rng.choice(bachelor_options if related else [degree for degrees in FACULTY_DEGREES.values() for degree in degrees[1]])
    year = rng.choice([1, 2])

    socioeconomic = rng.choices(
        ["financially comfortable", "middle-income", "financially disadvantaged"],
        weights=[25, 50, 25], k=1
    )[0]
    living = rng.choices(
        ["Share house", "Student accommodation", "Living with family", "Living alone"],
        weights=[42, 22, 18, 18], k=1
    )[0]
    employment = rng.choices(["Unemployed", "Part-time employed"], weights=[45, 55], k=1)[0]
    experience = rng.choices(["None", "1–2 years", "Relevant experience"], weights=[35, 35, 30], k=1)[0]
    siblings = rng.randint(0, 4)
    parents_health = rng.choice(["Both generally well", "One parent has an ongoing health condition", "A parent needs regular support"])
    responsibility = rng.choices(["Low", "Moderate", "High"], weights=[42, 38, 20], k=1)[0]
    expectations = rng.choice(["Encouraging", "High academic expectations", "Still discussing future plans"])
    relationship = rng.choice(["Close and supportive", "Supportive but busy", "Some distance at the moment", "Strained by recent pressures"])

    support_options = {
        "financially comfortable": [1000, 2000, 2500, 3000, 3500, 4000, 5000],
        "middle-income": [0, 1000, 2000, 2500, 3000, 3500],
        "financially disadvantaged": [0, 0, 1000, 2000, 2500],
    }
    monthly_support = rng.choice(support_options[socioeconomic])
    family_can_help = monthly_support > 0 and rng.random() < (0.82 if socioeconomic != "financially disadvantaged" else 0.45)
    baseline_key = (
        "high family responsibilities" if responsibility == "High"
        else "independent" if monthly_support == 0 and living != "Living with family"
        else socioeconomic
    )
    initial = {key: value + rng.randint(-3, 3) for key, value in BASELINES[baseline_key].items()}
    if related:
        initial["academic"] += 2
    if experience == "Relevant experience":
        initial["career"] += 3
    if responsibility == "High":
        initial["wellbeing"] -= 2
    if relationship == "Close and supportive":
        initial["family"] += 3
    if socioeconomic == "financially disadvantaged":
        initial["wellbeing"] -= 2
    initial = {key: max(0, min(100, value)) for key, value in initial.items()}

    starting_money = {"financially comfortable": 900, "middle-income": 600, "financially disadvantaged": 300}[socioeconomic]
    if living == "Living with family":
        starting_money += 150

    return {
        "name": name.strip(),
        "faculty": faculty,
        "masters_degree": masters_degree,
        "year": year,
        "bachelor_degree": bachelor_degree,
        "related_bachelor": related,
        "living_arrangement": living,
        "employment_status": employment,
        "work_experience": experience,
        "socioeconomic_background": socioeconomic,
        "siblings": siblings,
        "parents_health": parents_health,
        "family_responsibilities": responsibility,
        "family_expectations": expectations,
        "family_relationship": relationship,
        "monthly_family_support": monthly_support,
        "weekly_family_support": round(monthly_support * 12 / 52, 2),
        "family_can_help": family_can_help,
        "initial_money": starting_money,
        "initial_stats": initial,
    }
