# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
Today's Schedule for Edwin (2026-07-05)
========================================
08:00 AM  Rex        Morning walk         (30 min, high)
08:30 AM  Rex        Breakfast            (10 min, high)
08:40 AM  Whiskers   Feed                 (10 min, medium)
08:50 AM  Whiskers   Clean litter box     (15 min, low)
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

Beyond the basic daily plan, PawPal+ implements four "smarter" scheduling
behaviors. Each is a small, independently testable method in
[`pawpal_system.py`](pawpal_system.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler._sort()`, `Scheduler.sort_by_time()` | Plan order is high-priority-first, ties broken by shorter duration; `sort_by_time()` orders tasks by their `"HH:MM"` preferred time |
| Filtering | `Owner.filter_tasks()`, `Scheduler._is_due()`, `Scheduler._fit()` | Filter by pet and/or completion status; only due tasks are planned; tasks over the time budget are skipped with a reason |
| Conflict detection | `Scheduler.find_time_conflicts()`, `Scheduler.detect_conflicts()` | Flags tasks sharing a time slot and returns a warning instead of crashing |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()` | Completing a daily/weekly task spawns its next occurrence |

### Sorting behavior

- **`Scheduler.sort_by_time(tasks)`** returns tasks ordered by their `time`
  attribute (a `"HH:MM"` 24-hour string). Zero-padded times sort chronologically
  under a plain string comparison, so a single `sorted()` with a lambda key is
  enough — no datetime parsing.
- **`Scheduler._sort(pet_tasks)`** is the ordering used inside `make_plan()`:
  highest priority first, breaking ties by shorter duration.

### Filtering behavior

- **`Owner.filter_tasks(done=..., pet_name=...)`** returns `(Pet, Task)` pairs
  narrowed by completion status and/or pet name. Both filters are optional and
  combine (AND); with no arguments it equals `all_tasks()`.
- **`Scheduler._is_due(task, day)`** keeps only tasks that actually occur on the
  target day — daily tasks always, weekly tasks only on their listed weekdays,
  and never a task already marked done.
- **`Scheduler._fit(...)`** skips any task that would exceed the day's time
  budget, recording a human-readable reason in `DailyPlan.skipped`.

### Conflict detection

- **`Scheduler.find_time_conflicts(pet_tasks)`** groups tasks that share the same
  preferred `time` — whether on the same pet or different pets — returning only
  the times with two or more tasks.
- **`Scheduler.detect_conflicts(pet_tasks)`** is the lightweight, non-crashing
  entry point: it returns a list of warning strings (empty if there are none),
  so the app can warn the owner rather than raise an error.

### Recurring task logic

- **`Task.mark_complete(today=None)`** marks a task done and, if it recurs,
  returns a fresh not-done `Task` for the next occurrence (the caller adds it to
  the pet's list). Non-recurring tasks return `None`.
- **`Task.next_occurrence(today=None)`** computes that successor's due date with
  `timedelta`: **+1 day** for `"daily"`, **+7 days** for `"weekly"`.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
