"""Record money movements and apply weekly support and living costs."""


def record_transaction(state, week, description, amount, category="other"):
    """Update the balance and append a transaction exactly once."""
    if amount == 0:
        return None
    updated_balance = state["money"] + amount
    state["money"] = round(updated_balance, 2) if isinstance(updated_balance, float) else updated_balance
    kind = "income" if amount > 0 else "expense"
    transaction = {
        "week": week,
        "description": description,
        "kind": kind,
        "amount": abs(amount),
        "balance": state["money"],
        "category": category,
    }
    state["transactions"].append(transaction)
    summary = state["financial_summary"]
    if amount < 0:
        summary["total_expenses"] += abs(amount)
        if "sent to family" in description.lower():
            summary["money_sent_to_family"] += abs(amount)
    elif category == "family_support":
        summary["total_family_support"] += amount
    elif category == "employment_income":
        summary["total_employment_income"] += amount
    else:
        summary["total_other_income"] += amount
    return transaction


def apply_money_effect(state, week, description, amount, category="other"):
    """Record a choice or event's one-off financial effect."""
    return record_transaction(state, week, description, amount, category)


def apply_weekly_finances(state, week):
    """Process support, regular income, and recurring expenses once weekly."""
    processed = state.setdefault("financial_weeks_processed", [])
    if week in processed:
        raise ValueError("Weekly finances have already been processed.")
    profile = state["profile"]
    support = profile["weekly_family_support"]
    if support:
        # Balances are kept to cents because monthly support converts to a fraction.
        state["money"] = round(state["money"], 2)
        record_transaction(state, week, "Weekly family financial support", support, "family_support")
    if profile["employment_status"] == "Part-time employed":
        record_transaction(state, week, "Regular part-time employment income", 180, "employment_income")
    lifestyle = state["lifestyle"]
    for label, amount in (("Rent", lifestyle["housing_cost"]), ("Food", lifestyle["food_cost"]), ("Transport", lifestyle["transport_cost"])):
        record_transaction(state, week, f"Weekly {label.lower()} cost", -amount, "expense")
    increase_from = state.get("rent_increase_from_week")
    if increase_from is not None and week >= increase_from:
        record_transaction(state, week, "Additional rent after increase", -50, "expense")
    processed.append(week)
