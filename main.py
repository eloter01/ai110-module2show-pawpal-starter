"""Terminal demo for the PawPal+ sorting and filtering methods.

Run with:  python main.py

Builds an Owner with two pets whose tasks are added intentionally OUT OF ORDER
by preferred time, then prints them back through the new methods to confirm
they work end to end:

    * Scheduler.sort_by_time()  -> tasks reordered by their "HH:MM" time
    * Owner.filter_tasks()      -> narrowed by completion status and/or pet
"""

from datetime import date

from pawpal_system import Owner, Scheduler, Task


def print_tasks(heading: str, pairs: list[tuple]) -> None:
    """Pretty-print a list of (Pet, Task) pairs under a heading."""
    print(heading)
    print("-" * len(heading))
    if not pairs:
        print("  (none)")
    for pet, task in pairs:
        clock = task.time or "--:--"
        flag = "done" if task.done else "todo"
        due = task.due_date.isoformat() if task.due_date else "----------"
        print(
            f"  {clock}  {pet.name:<10} {task.title:<18} "
            f"[{task.priority:<6}] due {due} ({flag})"
        )
    print()


def sorted_pairs(scheduler: Scheduler, pairs: list[tuple]) -> list[tuple]:
    """Sort (Pet, Task) pairs by time via Scheduler.sort_by_time().

    sort_by_time() works on Task objects, so we sort the tasks and map each one
    back to its pet. Task is an unhashable dataclass, hence the id() lookup.
    """
    pet_by_task = {id(task): pet for pet, task in pairs}
    ordered = scheduler.sort_by_time([task for _, task in pairs])
    return [(pet_by_task[id(task)], task) for task in ordered]


def main() -> None:
    # --- Build the data model: one Owner, two Pets ---
    owner = Owner(name="Edwin")
    rex = owner.add_pet("Rex", "dog")
    whiskers = owner.add_pet("Whiskers", "cat")

    # Add tasks intentionally OUT OF ORDER by preferred time, so sort_by_time()
    # has something real to reorder.
    rex.tasks.append(Task("Evening walk", 30, priority="high", time="18:00"))
    rex.tasks.append(Task("Breakfast", 10, priority="high", time="07:30"))
    whiskers.tasks.append(Task("Lunch feed", 10, priority="medium", time="12:15"))
    whiskers.tasks.append(Task("Clean litter box", 15, priority="low", time="09:00"))
    # Deliberate clash: Rex's midday meds land at the same 12:15 as Whiskers'
    # lunch feed, so Scheduler.detect_conflicts() has something to warn about.
    rex.tasks.append(Task("Midday meds", 5, priority="high", time="12:15"))

    # Mark one complete so the completion filter has both states to show.
    rex.tasks[1].mark_complete()  # Breakfast -> done

    scheduler = Scheduler(
        available_minutes=owner.available_minutes, day_start=owner.day_start
    )

    print(f"PawPal+ - {owner.name}  ({date.today()})")
    print("=" * 44)
    print()

    # 1) As entered (deliberately unsorted).
    print_tasks("All tasks, as entered:", owner.all_tasks())

    # 2) Sorted by preferred time (sort_by_time).
    print_tasks(
        "All tasks, sorted by time (sort_by_time):",
        sorted_pairs(scheduler, owner.all_tasks()),
    )

    # 3) Filter by completion status (filter_tasks).
    print_tasks("Pending only (filter_tasks done=False):", owner.filter_tasks(done=False))
    print_tasks("Completed only (filter_tasks done=True):", owner.filter_tasks(done=True))

    # 4) Filter by pet name (filter_tasks).
    print_tasks("Rex's tasks (filter_tasks pet_name='Rex'):", owner.filter_tasks(pet_name="Rex"))

    # 5) Combine both filters, then sort the result by time.
    print_tasks(
        "Whiskers' pending, sorted by time (filter + sort):",
        sorted_pairs(scheduler, owner.filter_tasks(done=False, pet_name="Whiskers")),
    )

    # 6) Conflict detection: two tasks at the same time -> a warning, no crash.
    print("Conflict check (detect_conflicts):")
    print("-" * 44)
    conflict_warnings = scheduler.detect_conflicts(owner.all_tasks())
    if conflict_warnings:
        for warning in conflict_warnings:
            print(f"  WARNING: {warning}")
    else:
        print("  No time conflicts.")
    print()

    # 7) Recurrence: completing a recurring task spawns its next occurrence.
    # A weekly task on Whiskers to show the +7 day step alongside a daily +1.
    whiskers.tasks.append(
        Task("Weekly groom", 20, priority="low", frequency="weekly", time="10:00")
    )
    today = date.today()
    print(f"Completing recurring tasks (today = {today})")
    print("-" * 44)
    for pet, task in list(owner.filter_tasks(done=False)):
        successor = task.mark_complete(today=today)
        if successor is not None:
            pet.tasks.append(successor)
            print(
                f"  {pet.name}: '{task.title}' ({task.frequency}) done "
                f"-> next occurrence due {successor.due_date}"
            )
    print()

    # The spawned occurrences are now the pending tasks, each with a due date.
    print_tasks("Pending after completion (next occurrences):", owner.filter_tasks(done=False))


if __name__ == "__main__":
    main()
