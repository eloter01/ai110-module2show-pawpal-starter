"""PawPal+ backend: owner/pet/task data and the daily planner.

Design notes
------------
The data types (Task, Pet, Owner, DailyPlan) are structured records — data
that travels together — so they are dataclasses. Planner is a behavioral
class: it carries the day's constraints and runs the scheduling algorithm.

Ownership hierarchy holds references downward only:

    Owner --> Pet --> Task

A task's owner is a derived fact (the owner of the pet that has the task),
navigated through the chain rather than stored on the task itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time


# Priority is a plain string to match the Streamlit UI: "low" | "medium" | "high".
# Could be promoted to an Enum later; not required yet.


@dataclass
class Task:
    """A single unit of pet care (a walk, a feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"


@dataclass
class Pet:
    """A pet, which has many care tasks."""

    name: str
    species: str = "other"  # "dog" | "cat" | "other"
    tasks: list[Task] = field(default_factory=list)


@dataclass
class Owner:
    """The user of the app, which has many pets.

    Kept as a class so the model can grow to multiple owners/users later.
    """

    name: str
    pets: list[Pet] = field(default_factory=list)

    def all_tasks(self) -> list[Task]:
        """Flatten every task across all of this owner's pets.

        This is what feeds the Planner. (If you later need to label plan
        items with the pet's name, return list[tuple[Pet, Task]] instead.)
        """
        raise NotImplementedError


@dataclass
class DailyPlan:
    """The Planner's output: what got scheduled, what got skipped and why.

    A multi-field bundle, so it earns being a (data) class rather than a bare
    list. "Explain the reasoning" lives in `skipped` (and can be extended to
    annotate scheduled items too).
    """

    scheduled: list[tuple[time, Task]] = field(default_factory=list)
    skipped: list[tuple[Task, str]] = field(default_factory=list)


class Planner:
    """Builds a DailyPlan from a list of tasks under time constraints.

    Unlike the models, Planner is behavioral: it carries the day's constraints
    (config) and decomposes scheduling into testable steps (_sort, _fit).
    Tasks are passed in, not stored, so the planner stays a reusable
    "tasks in, plan out" engine.
    """

    def __init__(self, available_minutes: int, day_start: time = time(8, 0)):
        self.available_minutes = available_minutes  # total time budget for the day
        self.day_start = day_start                  # when scheduling begins

    def make_plan(self, tasks: list[Task]) -> DailyPlan:
        """The one public method: tasks in, scheduled plan out."""
        ordered = self._sort(tasks)
        return self._fit(ordered)

    def _sort(self, tasks: list[Task]) -> list[Task]:
        """High priority first; break ties by shorter duration."""
        raise NotImplementedError

    def _fit(self, tasks: list[Task]) -> DailyPlan:
        """Assign start times in order, skip tasks that exceed the budget.

        Records a reason for each skipped task so DailyPlan can explain itself.
        """
        raise NotImplementedError
