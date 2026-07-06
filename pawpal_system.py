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

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta


# Priority is a plain string to match the Streamlit UI: "low" | "medium" | "high".
# Could be promoted to an Enum later; not required yet.


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"      # "low" | "medium" | "high"
    frequency: str = "daily"      # "daily" | "weekly"  (recurrence logic later)
    weekdays: list[int] = field(default_factory=list)  # weekly only; 0=Mon..6=Sun
    done: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.done = True

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
        """The one public method: (Pet, Task) pairs in, scheduled plan out."""
        ordered = self._sort(pet_tasks)
        return self._fit(ordered, day)

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
        """Assign start times in order, skip tasks that exceed the budget.

        Records a reason for each skipped task so DailyPlan can explain itself.
        """
        plan = DailyPlan(day=day)
        used_minutes = 0
        cursor = datetime.combine(day, self.day_start)

        for pet, task in pet_tasks:
            remaining = self.available_minutes - used_minutes
            if task.duration_minutes > remaining:
                reason = (
                    f"needs {task.duration_minutes} min, only {remaining} of "
                    f"{self.available_minutes} min left"
                )
                plan.skipped.append((pet, task, reason))
                continue

            plan.scheduled.append((cursor.time(), pet, task))
            cursor += timedelta(minutes=task.duration_minutes)
            used_minutes += task.duration_minutes

        return plan
