"""Simple smoke tests for the PawPal+ data classes."""

from pawpal_system import Pet, Task


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
