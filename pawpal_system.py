"""PawPal+ backend: owner/pet/task data and the daily scheduler.

Design notes
------------
The data types (Task, Pet, Owner, DailyPlan) are structured records — data
that travels together — so they are dataclasses. Scheduler is a behavioral
class: it carries the day's constraints and runs the scheduling algorithm.

Ownership is composition, navigable downward only:

    Owner *-- Pet *-- Task

A Task does not store its Pet. To keep the plan pet-aware, Owner.all_tasks()
pairs each task with its pet on the fly as (Pet, Task) tuples, and the plan
carries that pet through to its output. This keeps Task pure data and avoids
a bidirectional link that could drift out of sync.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta


# Priority is a plain string to match the Streamlit UI: "low" | "medium" | "high".
# Could be promoted to an Enum later; not required yet.


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"      # "low" | "medium" | "high"
    frequency: str = "daily"      # "daily" | "weekly"
    weekdays: list[int] = field(default_factory=list)  # weekly only; 0=Mon..6=Sun
    done: bool = False
    # Anchored tasks (e.g. "meds at 8:00 AM") must happen at a set clock time.
    # None means the task floats and the Scheduler picks its slot.
    fixed_time: time | None = None
    # Preferred time of day as an "HH:MM" 24-hour string (e.g. "08:30"), used by
    # Scheduler.sort_by_time(). Empty string means no preference.
    time: str = ""
    # When this occurrence is due. None for tasks that predate recurrence;
    # next_occurrence() stamps a concrete date on each spawned instance.
    due_date: date | None = None

    def mark_complete(self, today: date | None = None) -> Task | None:
        """Mark this task done and, if it recurs, return its next occurrence.

        Recurring (daily/weekly) tasks spawn a fresh, not-done Task for their
        next due date so the routine keeps going; the caller adds it to the
        pet's task list. Non-recurring tasks return None. Marking complete is
        unconditional, so a one-off still gets marked done.
        """
        self.done = True
        return self.next_occurrence(today)

    def next_occurrence(self, today: date | None = None) -> Task | None:
        """Build the next instance of this task, or None if it doesn't recur.

        The next due date is computed from ``today`` (defaulting to
        ``date.today()``) with timedelta: +1 day for "daily", +7 days for
        "weekly". The new Task copies this one's details but starts not-done,
        with a fresh (unshared) weekdays list.
        """
        today = today or date.today()
        if self.frequency == "daily":
            next_due = today + timedelta(days=1)
        elif self.frequency == "weekly":
            next_due = today + timedelta(days=7)
        else:
            return None
        return replace(
            self,
            done=False,
            due_date=next_due,
            weekdays=list(self.weekdays),
        )

@dataclass
class Pet:
    """A pet, which has many care tasks."""

    name: str
    species: str = "other"  # "dog" | "cat" | "other"
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Owner:
    """The user of the app, which has many pets.

    Also holds the owner's scheduling preferences (the day's time budget and
    when the day starts), which the app uses to configure a Scheduler.
    """

    name: str
    pets: list[Pet] = field(default_factory=list)
    available_minutes: int = 120           # preference: total time budget for the day
    day_start: time = time(8, 0)           # preference: when scheduling begins

    def add_pet(self, name: str, species: str = "other") -> Pet:
        """Create a pet, attach it to this owner, and return it."""
        pet = Pet(name=name, species=species)
        self.pets.append(pet)
        return pet

    def all_tasks(self) -> list[tuple[Pet, Task]]:
        """Flatten every task across all pets, paired with its owning pet.

        Returns (Pet, Task) tuples so the Scheduler and the resulting plan can
        say which pet each task belongs to without Task storing a back-reference.
        """
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def filter_tasks(
        self,
        *,
        done: bool | None = None,
        pet_name: str | None = None,
    ) -> list[tuple[Pet, Task]]:
        """Return (Pet, Task) pairs, optionally narrowed by completion and/or pet.

        Both filters are optional and combine (AND). Leaving one as ``None``
        means "don't filter on that", so ``filter_tasks()`` with no arguments is
        the same as ``all_tasks()``. Keyword-only to keep call sites readable,
        e.g. ``owner.filter_tasks(done=False, pet_name="Mochi")``.
        """
        pairs = self.all_tasks()
        if done is not None:
            pairs = [(pet, task) for pet, task in pairs if task.done == done]
        if pet_name is not None:
            pairs = [(pet, task) for pet, task in pairs if pet.name == pet_name]
        return pairs


@dataclass
class DailyPlan:
    """The Scheduler's output: what got scheduled, what got skipped and why.

    A multi-field bundle, so it earns being a (data) class rather than a bare
    list. "Explain the reasoning" lives in `skipped` (and can be extended to
    annotate scheduled items too). Each entry carries its Pet so the plan can
    be rendered per pet.
    """

    day: date | None = None
    scheduled: list[tuple[time, Pet, Task]] = field(default_factory=list)
    skipped: list[tuple[Pet, Task, str]] = field(default_factory=list)


class Scheduler:
    """Builds a DailyPlan from (Pet, Task) pairs under time constraints.

    Unlike the models, Scheduler is behavioral: it carries the day's constraints
    (config) and decomposes scheduling into testable steps (_sort, _fit).
    Tasks are passed in, not stored, so the scheduler stays a reusable
    "tasks in, plan out" engine.
    """

    # Lower number == scheduled earlier. Unknown priorities fall back to medium.
    _PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, available_minutes: int, day_start: time = time(8, 0)):
        self.available_minutes = available_minutes  # total time budget for the day
        self.day_start = day_start                  # when scheduling begins

    def make_plan(self, pet_tasks: list[tuple[Pet, Task]], day: date) -> DailyPlan:
        """The one public method: (Pet, Task) pairs in, scheduled plan out.

        Tasks are first filtered to those actually due on ``day`` (recurrence)
        and not already done, then ordered, then fitted into the time budget.
        """
        due = [pt for pt in pet_tasks if self._is_due(pt[1], day)]
        ordered = self._sort(due)
        return self._fit(ordered, day)

    def _is_due(self, task: Task, day: date) -> bool:
        """Whether ``task`` should appear on ``day``.

        Already-done tasks are never due. Daily tasks are always due; weekly
        tasks are due only on their listed weekdays (0=Mon..6=Sun).
        """
        if task.done:
            return False
        if task.frequency == "weekly":
            return day.weekday() in task.weekdays
        return True

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their ``time`` attribute ("HH:MM").

        Zero-padded 24-hour strings sort chronologically under a plain string
        comparison, so a lambda key on ``task.time`` is enough — no parsing
        into datetime needed.
        """
        return sorted(tasks, key=lambda task: task.time)

    def find_time_conflicts(
        self, pet_tasks: list[tuple[Pet, Task]]
    ) -> dict[str, list[tuple[Pet, Task]]]:
        """Group (Pet, Task) pairs that share the same preferred ``time``.

        Two or more tasks — whether on the same pet or different pets — set to
        the same non-empty "HH:MM" time can't both happen then, so they're a
        conflict. Tasks with no preferred time ("") are ignored. Returns
        ``{time: [pairs]}`` for conflicting times only (2+ tasks each).
        """
        by_time: dict[str, list[tuple[Pet, Task]]] = {}
        for pet, task in pet_tasks:
            if task.time:  # skip tasks with no preferred time
                by_time.setdefault(task.time, []).append((pet, task))
        return {t: pairs for t, pairs in by_time.items() if len(pairs) > 1}

    def detect_conflicts(self, pet_tasks: list[tuple[Pet, Task]]) -> list[str]:
        """Lightweight conflict check: return a warning per clashing time.

        Never raises — an empty list means "no conflicts". Each message names
        the time and the pets' tasks competing for it, so the caller can warn
        the user instead of the program crashing.
        """
        conflicts = self.find_time_conflicts(pet_tasks)
        warnings = []
        for t in sorted(conflicts):
            names = ", ".join(f"{pet.name}'s '{task.title}'" for pet, task in conflicts[t])
            warnings.append(f"Time conflict at {t}: {names}")
        return warnings

    def _sort(self, pet_tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """High priority first; break ties by shorter duration."""
        return sorted(
            pet_tasks,
            key=lambda pt: (
                self._PRIORITY_RANK.get(pt[1].priority, 1),
                pt[1].duration_minutes,
            ),
        )

    def _fit(self, pet_tasks: list[tuple[Pet, Task]], day: date) -> DailyPlan:
        """Assign start times, skip tasks that exceed the budget.

        Anchored tasks (``fixed_time`` set) are placed at their clock time and
        reserve that slot; floating tasks then flow from ``day_start``, stepping
        over any reserved slot so they never overlap an anchor. Both kinds draw
        from the same minute budget. Records a reason for each skipped task so
        DailyPlan can explain itself. Scheduled items come back time-ordered.
        """
        plan = DailyPlan(day=day)
        used_minutes = 0
        occupied: list[tuple[datetime, datetime]] = []  # reserved anchor slots

        anchored = [pt for pt in pet_tasks if pt[1].fixed_time is not None]
        floating = [pt for pt in pet_tasks if pt[1].fixed_time is None]

        # Place anchors in chronological order so earlier ones reserve first.
        anchored.sort(key=lambda pt: pt[1].fixed_time)  # type: ignore[arg-type,return-value]
        for pet, task in anchored:
            remaining = self.available_minutes - used_minutes
            if task.duration_minutes > remaining:
                plan.skipped.append((pet, task, self._budget_reason(task, remaining)))
                continue

            start = datetime.combine(day, task.fixed_time)  # type: ignore[arg-type]
            end = start + timedelta(minutes=task.duration_minutes)
            if any(start < o_end and end > o_start for o_start, o_end in occupied):
                plan.skipped.append(
                    (pet, task, f"fixed time {task.fixed_time:%I:%M %p} overlaps another task")
                )
                continue

            plan.scheduled.append((start.time(), pet, task))
            occupied.append((start, end))
            used_minutes += task.duration_minutes

        # Flow floating tasks from day_start, stepping over reserved anchor slots.
        cursor = datetime.combine(day, self.day_start)
        for pet, task in floating:
            remaining = self.available_minutes - used_minutes
            if task.duration_minutes > remaining:
                plan.skipped.append((pet, task, self._budget_reason(task, remaining)))
                continue

            cursor = self._next_free(cursor, task.duration_minutes, occupied)
            plan.scheduled.append((cursor.time(), pet, task))
            cursor += timedelta(minutes=task.duration_minutes)
            used_minutes += task.duration_minutes

        plan.scheduled.sort(key=lambda item: item[0])  # present in time order
        return plan

    def _budget_reason(self, task: Task, remaining: int) -> str:
        """Explain why a task didn't fit the remaining time budget."""
        return (
            f"needs {task.duration_minutes} min, only {remaining} of "
            f"{self.available_minutes} min left"
        )

    def _next_free(
        self,
        cursor: datetime,
        duration_minutes: int,
        occupied: list[tuple[datetime, datetime]],
    ) -> datetime:
        """Earliest start at/after ``cursor`` that clears every reserved slot."""
        end = cursor + timedelta(minutes=duration_minutes)
        moved = True
        while moved:
            moved = False
            for o_start, o_end in occupied:
                if cursor < o_end and end > o_start:  # would overlap this anchor
                    cursor = o_end
                    end = cursor + timedelta(minutes=duration_minutes)
                    moved = True
        return cursor
