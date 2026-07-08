"""Simple smoke tests for the PawPal+ data classes and scheduler."""

from datetime import date, time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


# A fixed reference day so recurrence tests don't depend on "today".
MONDAY = date(2026, 7, 6)   # weekday() == 0
TUESDAY = date(2026, 7, 7)  # weekday() == 1


def _plan_for(tasks, day, available_minutes=120, day_start=time(8, 0)):
    """Run the scheduler over a bare list of tasks under one pet."""
    pet = Pet(name="Mochi", species="cat")
    pet.tasks.extend(tasks)
    scheduler = Scheduler(available_minutes=available_minutes, day_start=day_start)
    pet_tasks = [(pet, task) for task in pet.tasks]
    return scheduler.make_plan(pet_tasks, day)


def test_task_completion():
    """mark_complete() flips a task's status from not-done to done."""
    task = Task(title="Morning walk", duration_minutes=30)
    assert task.done is False

    task.mark_complete()

    assert task.done is True


def test_task_addition():
    """Adding a task to a Pet increases that pet's task count."""
    pet = Pet(name="Rex", species="dog")
    assert len(pet.tasks) == 0

    pet.tasks.append(Task(title="Feed", duration_minutes=10))

    assert len(pet.tasks) == 1


# --- Recurrence: weekly tasks only appear on their listed weekdays (#1) ---

def test_weekly_task_scheduled_on_its_weekday():
    """A Monday-only task is scheduled on a Monday."""
    task = Task(title="Nail trim", duration_minutes=15, frequency="weekly", weekdays=[0])

    plan = _plan_for([task], MONDAY)

    assert [t.title for _, _, t in plan.scheduled] == ["Nail trim"]


def test_weekly_task_absent_on_other_weekdays():
    """A Monday-only task does not appear on Tuesday (not even as skipped)."""
    task = Task(title="Nail trim", duration_minutes=15, frequency="weekly", weekdays=[0])

    plan = _plan_for([task], TUESDAY)

    assert plan.scheduled == []
    assert plan.skipped == []


def test_daily_task_scheduled_every_day():
    """A daily task appears regardless of weekday."""
    task = Task(title="Feed", duration_minutes=10, frequency="daily")

    assert len(_plan_for([task], MONDAY).scheduled) == 1
    assert len(_plan_for([task], TUESDAY).scheduled) == 1


# --- Completion: done tasks drop out of the plan entirely (#2) ---

def test_done_task_is_not_scheduled():
    """A completed task is neither scheduled nor reported as skipped."""
    task = Task(title="Morning walk", duration_minutes=20)
    task.mark_complete()

    plan = _plan_for([task], MONDAY)

    assert plan.scheduled == []
    assert plan.skipped == []


def test_done_task_frees_budget_for_others():
    """Completing a task leaves its minutes available for the rest."""
    done = Task(title="Long groom", duration_minutes=100, priority="high")
    done.mark_complete()
    walk = Task(title="Walk", duration_minutes=90, priority="medium")

    plan = _plan_for([done, walk], MONDAY, available_minutes=120)

    # Without the done task consuming budget, the 90-min walk fits.
    assert [t.title for _, _, t in plan.scheduled] == ["Walk"]


# --- Anchored tasks: fixed_time slots are honored and reserved (#4) ---

def test_fixed_time_task_placed_at_its_clock_time():
    """An anchored task starts at its fixed_time, not at day_start."""
    meds = Task(title="Meds", duration_minutes=10, fixed_time=time(12, 0))

    plan = _plan_for([meds], MONDAY, day_start=time(8, 0))

    start, _, task = plan.scheduled[0]
    assert task.title == "Meds"
    assert start == time(12, 0)


def test_floating_task_flows_around_anchor():
    """A floating task that would collide with an anchor starts after it."""
    meds = Task(title="Meds", duration_minutes=30, fixed_time=time(8, 0))
    walk = Task(title="Walk", duration_minutes=60)

    plan = _plan_for([meds, walk], MONDAY, day_start=time(8, 0))

    starts = {t.title: s for s, _, t in plan.scheduled}
    assert starts["Meds"] == time(8, 0)
    assert starts["Walk"] == time(8, 30)  # pushed past the anchor, no overlap


def test_scheduled_items_are_time_ordered():
    """Output is sorted by start time even when an anchor sits later in the day."""
    meds = Task(title="Meds", duration_minutes=10, fixed_time=time(18, 0))
    walk = Task(title="Walk", duration_minutes=20)

    plan = _plan_for([meds, walk], MONDAY, day_start=time(8, 0))

    times = [s for s, _, _ in plan.scheduled]
    assert times == sorted(times)


def test_anchor_over_budget_is_skipped_with_reason():
    """An anchored task that busts the budget is skipped and explained."""
    meds = Task(title="Meds", duration_minutes=200, fixed_time=time(9, 0))

    plan = _plan_for([meds], MONDAY, available_minutes=60)

    assert plan.scheduled == []
    assert len(plan.skipped) == 1
    _, task, reason = plan.skipped[0]
    assert task.title == "Meds"
    assert "min left" in reason


# --- sort_by_time: order tasks by their "HH:MM" time attribute ---

def test_sort_by_time_orders_chronologically():
    """Tasks come back earliest-first by their "HH:MM" string."""
    tasks = [
        Task(title="Dinner", duration_minutes=15, time="18:00"),
        Task(title="Breakfast", duration_minutes=15, time="07:30"),
        Task(title="Lunch", duration_minutes=15, time="12:15"),
    ]
    scheduler = Scheduler(available_minutes=120)

    ordered = scheduler.sort_by_time(tasks)

    assert [t.title for t in ordered] == ["Breakfast", "Lunch", "Dinner"]


def test_sort_by_time_does_not_mutate_input():
    """sorted() returns a new list; the original order is untouched."""
    tasks = [
        Task(title="Late", duration_minutes=10, time="22:00"),
        Task(title="Early", duration_minutes=10, time="06:00"),
    ]
    scheduler = Scheduler(available_minutes=120)

    scheduler.sort_by_time(tasks)

    assert [t.title for t in tasks] == ["Late", "Early"]


# --- Owner.filter_tasks: narrow by completion status and/or pet name ---

def _owner_with_two_pets() -> Owner:
    """Owner with Mochi (1 done, 1 pending) and Rex (1 pending)."""
    owner = Owner(name="Jordan")
    mochi = owner.add_pet("Mochi", "cat")
    rex = owner.add_pet("Rex", "dog")
    fed = Task(title="Feed Mochi", duration_minutes=10)
    fed.mark_complete()
    mochi.tasks.extend([fed, Task(title="Brush Mochi", duration_minutes=5)])
    rex.tasks.append(Task(title="Walk Rex", duration_minutes=30))
    return owner


def test_filter_no_args_matches_all_tasks():
    """With no filters, filter_tasks() equals all_tasks()."""
    owner = _owner_with_two_pets()

    assert owner.filter_tasks() == owner.all_tasks()


def test_filter_by_done_status():
    """done=True keeps only completed tasks; done=False only pending ones."""
    owner = _owner_with_two_pets()

    completed = owner.filter_tasks(done=True)
    pending = owner.filter_tasks(done=False)

    assert [t.title for _, t in completed] == ["Feed Mochi"]
    assert sorted(t.title for _, t in pending) == ["Brush Mochi", "Walk Rex"]


def test_filter_by_pet_name():
    """pet_name keeps only that pet's tasks."""
    owner = _owner_with_two_pets()

    rex_tasks = owner.filter_tasks(pet_name="Rex")

    assert [pet.name for pet, _ in rex_tasks] == ["Rex"]
    assert [t.title for _, t in rex_tasks] == ["Walk Rex"]


def test_filter_by_pet_name_and_done_combine():
    """Both filters apply together (AND)."""
    owner = _owner_with_two_pets()

    result = owner.filter_tasks(done=False, pet_name="Mochi")

    assert [t.title for _, t in result] == ["Brush Mochi"]


def test_filter_unknown_pet_returns_empty():
    """An unmatched pet name yields no pairs."""
    owner = _owner_with_two_pets()

    assert owner.filter_tasks(pet_name="Nobody") == []


# --- Recurrence: completing a recurring task spawns its next occurrence ---

def test_daily_completion_spawns_next_day():
    """A daily task's successor is due today + 1 day."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")

    successor = task.mark_complete(today=MONDAY)

    assert task.done is True
    assert successor is not None
    assert successor.done is False
    assert successor.due_date == MONDAY + timedelta(days=1)
    assert successor.title == "Walk"


def test_weekly_completion_spawns_next_week():
    """A weekly task's successor is due today + 7 days."""
    task = Task(title="Groom", duration_minutes=20, frequency="weekly", weekdays=[0])

    successor = task.mark_complete(today=MONDAY)

    assert successor is not None
    assert successor.due_date == MONDAY + timedelta(days=7)


def test_non_recurring_completion_returns_none():
    """A task with a non-recurring frequency is marked done but spawns nothing."""
    task = Task(title="One-off vet visit", duration_minutes=45, frequency="once")

    successor = task.mark_complete(today=MONDAY)

    assert task.done is True
    assert successor is None


def test_successor_has_independent_weekdays_list():
    """Mutating the successor's weekdays must not affect the original task."""
    task = Task(title="Groom", duration_minutes=20, frequency="weekly", weekdays=[0])

    successor = task.mark_complete(today=MONDAY)
    successor.weekdays.append(3)

    assert task.weekdays == [0]


def test_next_occurrence_does_not_mark_done():
    """next_occurrence() computes the successor without completing the task."""
    task = Task(title="Walk", duration_minutes=20, frequency="daily")

    successor = task.next_occurrence(today=MONDAY)

    assert task.done is False  # untouched
    assert successor.due_date == MONDAY + timedelta(days=1)


# --- Conflict detection: two tasks scheduled at the same time ---

def test_find_time_conflicts_flags_same_time_across_pets():
    """Two tasks at 12:15 (different pets) are a conflict; a lone time is not."""
    owner = Owner(name="Jordan")
    rex = owner.add_pet("Rex", "dog")
    cat = owner.add_pet("Mochi", "cat")
    rex.tasks.append(Task("Meds", 5, time="12:15"))
    cat.tasks.append(Task("Lunch", 10, time="12:15"))
    rex.tasks.append(Task("Walk", 20, time="18:00"))  # no clash
    scheduler = Scheduler(available_minutes=120)

    conflicts = scheduler.find_time_conflicts(owner.all_tasks())

    assert set(conflicts) == {"12:15"}
    assert {t.title for _, t in conflicts["12:15"]} == {"Meds", "Lunch"}


def test_find_time_conflicts_same_pet():
    """Two tasks at the same time on the SAME pet also conflict."""
    owner = Owner(name="Jordan")
    rex = owner.add_pet("Rex", "dog")
    rex.tasks.append(Task("Meds", 5, time="08:00"))
    rex.tasks.append(Task("Walk", 20, time="08:00"))
    scheduler = Scheduler(available_minutes=120)

    conflicts = scheduler.find_time_conflicts(owner.all_tasks())

    assert set(conflicts) == {"08:00"}
    assert len(conflicts["08:00"]) == 2


def test_no_conflict_when_times_differ_or_unset():
    """Distinct times and blank times ("") never register as conflicts."""
    owner = Owner(name="Jordan")
    pet = owner.add_pet("Mochi", "cat")
    pet.tasks.append(Task("A", 5, time="08:00"))
    pet.tasks.append(Task("B", 5, time="09:00"))
    pet.tasks.append(Task("C", 5, time=""))  # no preferred time
    pet.tasks.append(Task("D", 5, time=""))  # blank does not clash with blank
    scheduler = Scheduler(available_minutes=120)

    assert scheduler.find_time_conflicts(owner.all_tasks()) == {}
    assert scheduler.detect_conflicts(owner.all_tasks()) == []


def test_detect_conflicts_returns_warning_not_exception():
    """detect_conflicts returns a warning string per clash; it never raises."""
    owner = Owner(name="Jordan")
    rex = owner.add_pet("Rex", "dog")
    cat = owner.add_pet("Mochi", "cat")
    rex.tasks.append(Task("Meds", 5, time="12:15"))
    cat.tasks.append(Task("Lunch", 10, time="12:15"))
    scheduler = Scheduler(available_minutes=120)

    warnings = scheduler.detect_conflicts(owner.all_tasks())

    assert len(warnings) == 1
    assert warnings[0].startswith("Time conflict at 12:15:")
    assert "Rex's 'Meds'" in warnings[0]
    assert "Mochi's 'Lunch'" in warnings[0]
