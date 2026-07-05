"""Temporary testing ground for the PawPal+ data classes.

Run with:  python main.py

NOTE: Scheduler._sort/_fit and Owner.all_tasks are still NotImplementedError in
pawpal_system.py, so this script does NOT call the scheduler. It builds the data
model and prints a simple "Today's Schedule" by walking owner -> pets -> tasks
directly. Swap in Scheduler.make_plan() once those methods are implemented.
"""

from datetime import time, timedelta, datetime, date

from pawpal_system import Owner, Pet, Task


def main() -> None:
    # --- Build the data model: one Owner, two Pets, several Tasks ---
    rex = Pet(
        name="Rex",
        species="dog",
        tasks=[
            Task(title="Morning walk", duration_minutes=30, priority="high"),
            Task(title="Breakfast", duration_minutes=10, priority="high"),
        ],
    )

    whiskers = Pet(
        name="Whiskers",
        species="cat",
        tasks=[
            Task(title="Feed", duration_minutes=10, priority="medium"),
            Task(title="Clean litter box", duration_minutes=15, priority="low"),
        ],
    )

    owner = Owner(name="Edwin", pets=[rex, whiskers], day_start=time(8, 0))

    # --- Print "Today's Schedule" ---
    # Assign start times naively by accumulating durations from day_start.
    # (This is a stand-in for Scheduler until _sort/_fit are implemented.)
    print(f"Today's Schedule for {owner.name} ({date.today()})")
    print("=" * 40)

    current = datetime.combine(date.today(), owner.day_start)
    for pet in owner.pets:
        for task in pet.tasks:
            start = current.time()
            print(
                f"{start.strftime('%I:%M %p')}  "
                f"{pet.name:<10} {task.title:<20} "
                f"({task.duration_minutes} min, {task.priority})"
            )
            current += timedelta(minutes=task.duration_minutes)


if __name__ == "__main__":
    main()
