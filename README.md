# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## ✨ Features

The scheduling logic lives in [`pawpal_system.py`](pawpal_system.py). Each feature is a small, independently tested algorithm:

- **Priority-based scheduling** — `make_plan()` orders tasks high → medium → low priority, breaking ties by shorter duration (`Scheduler._sort()`), then fits them into the day's minute budget.
- **Sorting by time** — `Scheduler.sort_by_time()` reorders tasks chronologically by their `"HH:MM"` preferred time (plain string comparison on zero-padded 24-hour times — no datetime parsing).
- **Time-budget fitting with explanations** — `Scheduler._fit()` places tasks within `available_minutes` and records a human-readable reason for anything skipped (e.g. `"needs 200 min, only 60 left"`).
- **Anchored (fixed-time) tasks** — tasks with a `fixed_time` are pinned to that clock time and reserve the slot; floating tasks flow around them, and two anchors competing for the same slot are resolved by skipping the loser with an overlap reason.
- **Conflict warnings** — `Scheduler.detect_conflicts()` flags two or more tasks sharing the same preferred time (same or different pets) and returns warning strings instead of crashing; surfaced in the UI as `st.warning`.
- **Daily & weekly recurrence** — completing a recurring task (`Task.mark_complete()`) spawns its next occurrence: **+1 day** for daily, **+7 days** for weekly (`Task.next_occurrence()`). Weekly tasks are only due on their listed weekdays.
- **Filtering** — `Owner.filter_tasks()` narrows `(Pet, Task)` pairs by completion status and/or pet name, and `Scheduler._is_due()` keeps only tasks that actually occur on the target day.

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

Sample test output: Confidence Level 5

```
===================================================================================== test session starts =====================================================================================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\elote\Repositories\CodePath Foundations of AI Engineering\ai110-module2show-pawpal-starter
plugins: anyio-4.14.1
collected 34 items                                                                                                                                                                             

tests\test_pawpal.py ..................................                                                                                                                                  [100%]

===================================================================================== 34 passed in 0.05s ======================================================================================
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

### What you can do in the app

Launch the Streamlit UI with:

```bash
streamlit run app.py
```

The single-page app lets a user:

- **Set up an owner and pets** — enter the owner's name and add one or more pets (name + species). Pets persist across Streamlit reruns via `st.session_state`.
- **Add tasks to a pet** — title, duration, priority (low/medium/high), frequency (daily/weekly, with weekday picker), an optional preferred time (`HH:MM`), and an optional fixed anchor time.
- **Mark tasks complete** — completing a recurring task automatically schedules its next occurrence.
- **Filter and sort the task table** — narrow by completion status and/or pet, and optionally sort by preferred time. The table is rendered with `st.table`.
- **See conflict warnings** — if two tasks share the same preferred time, an `st.warning` appears; otherwise an `st.success` confirms the schedule is clean.
- **Generate today's schedule** — builds a `DailyPlan`, showing scheduled tasks with start times plus a "Skipped" table explaining anything that didn't fit.

### Example workflow

1. Enter owner **Edwin** and click **Add pet** to add **Rex** (dog) and **Whiskers** (cat).
2. Add tasks — e.g. Rex's *Morning walk* (30 min, high) and *Midday meds* (5 min, high, preferred `12:15`), and Whiskers' *Lunch feed* (10 min, medium, preferred `12:15`).
3. Notice the **conflict warning**: both 12:15 tasks trigger `⚠️ Time conflict at 12:15: …`.
4. Toggle **Sort tasks by preferred time** to reorder the table chronologically.
5. Click **Generate schedule** to see today's plan with assigned start times, and any over-budget task listed under **Skipped** with a reason.
6. **Mark a task complete** — a recurring task spawns its next occurrence (daily +1 day, weekly +7 days).

### Key Scheduler behaviors on display

- **Sorting** — the table can be sorted by time (`sort_by_time`); the generated plan orders by priority then duration (`_sort`).
- **Conflict warnings** — `detect_conflicts` surfaces same-time clashes without crashing.
- **Recurrence** — completing daily/weekly tasks generates the next occurrence.
- **Budget fitting** — tasks that exceed `available_minutes` are skipped with an explanation.

### Sample CLI output

`main.py` is a terminal demo that exercises the same backend without Streamlit. Running `python main.py` produces:

```text
PawPal+ - Edwin  (2026-07-07)
============================================

All tasks, as entered:
----------------------
  18:00  Rex        Evening walk       [high  ] due ---------- (todo)
  07:30  Rex        Breakfast          [high  ] due ---------- (done)
  12:15  Rex        Midday meds        [high  ] due ---------- (todo)
  12:15  Whiskers   Lunch feed         [medium] due ---------- (todo)
  09:00  Whiskers   Clean litter box   [low   ] due ---------- (todo)

All tasks, sorted by time (sort_by_time):
-----------------------------------------
  07:30  Rex        Breakfast          [high  ] due ---------- (done)
  09:00  Whiskers   Clean litter box   [low   ] due ---------- (todo)
  12:15  Rex        Midday meds        [high  ] due ---------- (todo)
  12:15  Whiskers   Lunch feed         [medium] due ---------- (todo)
  18:00  Rex        Evening walk       [high  ] due ---------- (todo)

Pending only (filter_tasks done=False):
---------------------------------------
  18:00  Rex        Evening walk       [high  ] due ---------- (todo)
  12:15  Rex        Midday meds        [high  ] due ---------- (todo)
  12:15  Whiskers   Lunch feed         [medium] due ---------- (todo)
  09:00  Whiskers   Clean litter box   [low   ] due ---------- (todo)

Completed only (filter_tasks done=True):
----------------------------------------
  07:30  Rex        Breakfast          [high  ] due ---------- (done)

Rex's tasks (filter_tasks pet_name='Rex'):
------------------------------------------
  18:00  Rex        Evening walk       [high  ] due ---------- (todo)
  07:30  Rex        Breakfast          [high  ] due ---------- (done)
  12:15  Rex        Midday meds        [high  ] due ---------- (todo)

Whiskers' pending, sorted by time (filter + sort):
--------------------------------------------------
  09:00  Whiskers   Clean litter box   [low   ] due ---------- (todo)
  12:15  Whiskers   Lunch feed         [medium] due ---------- (todo)

Conflict check (detect_conflicts):
--------------------------------------------
  WARNING: Time conflict at 12:15: Rex's 'Midday meds', Whiskers's 'Lunch feed'

Completing recurring tasks (today = 2026-07-07)
--------------------------------------------
  Rex: 'Evening walk' (daily) done -> next occurrence due 2026-07-08
  Rex: 'Midday meds' (daily) done -> next occurrence due 2026-07-08
  Whiskers: 'Lunch feed' (daily) done -> next occurrence due 2026-07-08
  Whiskers: 'Clean litter box' (daily) done -> next occurrence due 2026-07-08
  Whiskers: 'Weekly groom' (weekly) done -> next occurrence due 2026-07-14

Pending after completion (next occurrences):
--------------------------------------------
  18:00  Rex        Evening walk       [high  ] due 2026-07-08 (todo)
  12:15  Rex        Midday meds        [high  ] due 2026-07-08 (todo)
  12:15  Whiskers   Lunch feed         [medium] due 2026-07-08 (todo)
  09:00  Whiskers   Clean litter box   [low   ] due 2026-07-08 (todo)
  10:00  Whiskers   Weekly groom       [low   ] due 2026-07-14 (todo)
```
