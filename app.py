
from datetime import date, time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# --- Session vault: create the Owner ONCE, then reuse it across re-runs. ---
# Streamlit re-runs this whole script on every interaction, so a plain local
# variable would be rebuilt (and lose its pets/tasks) each time. The guard
# below constructs the Owner only when it isn't already in the vault.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)

owner = st.session_state.owner
owner.name = owner_name  # keep the persisted Owner's name in sync with the input


def get_or_create_pet(owner: Owner, name: str, species: str) -> Pet:
    """Return the owner's pet with this name, creating and adding it if absent."""
    for pet in owner.pets:
        if pet.name == name:
            return pet
    return owner.add_pet(name, species)  # Owner owns how pets get attached


if st.button("Add pet"):
    if any(pet.name == pet_name for pet in owner.pets):
        st.info(f"{pet_name} is already one of {owner.name}'s pets.")
    else:
        owner.add_pet(pet_name, species)
        st.success(f"Added {pet_name} ({species}).")

if owner.pets:
    st.caption("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))

st.markdown("### Tasks")
st.caption("Add a few tasks. These are stored as real Task objects on the pet.")

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col4, col5 = st.columns(2)
with col4:
    frequency = st.selectbox("Frequency", ["daily", "weekly"])
with col5:
    weekdays = st.multiselect(
        "On weekdays (weekly only)",
        options=list(range(7)),
        format_func=lambda i: WEEKDAY_LABELS[i],
        disabled=(frequency != "weekly"),
    )

anchor = st.checkbox("Anchor to a fixed start time")
fixed_time = st.time_input("Fixed start time", value=time(8, 0)) if anchor else None

if st.button("Add task"):
    pet = get_or_create_pet(owner, pet_name, species)
    pet.tasks.append(
        Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            weekdays=weekdays if frequency == "weekly" else [],
            fixed_time=fixed_time,
        )
    )

# Let the owner mark a pending task complete. Placed above the table so the
# table below reflects the change in the same rerun (no one-click lag).
pending = [(pet, task) for pet in owner.pets for task in pet.tasks if not task.done]
if pending:
    done_idx = st.selectbox(
        "Mark a task complete",
        options=list(range(len(pending))),
        format_func=lambda i: f"{pending[i][0].name} — {pending[i][1].title}",
    )
    if st.button("Mark done"):
        pending[done_idx][1].mark_complete()
        st.success(f"Marked '{pending[done_idx][1].title}' done.")


def _when(task: Task) -> str:
    """Human-readable recurrence for the task table."""
    if task.frequency == "weekly":
        if not task.weekdays:
            return "weekly (no days set)"
        return "weekly: " + ", ".join(WEEKDAY_LABELS[i] for i in task.weekdays)
    return "daily"


# Build the display table by walking owner -> pets -> tasks directly.
task_rows = [
    {
        "pet": pet.name,
        "title": task.title,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
        "when": _when(task),
        "fixed_time": task.fixed_time.strftime("%I:%M %p") if task.fixed_time else "—",
        "done": task.done,
    }
    for pet in owner.pets
    for task in pet.tasks
]

if task_rows:
    st.write("Current tasks:")
    st.table(task_rows)
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Calls Scheduler.make_plan() with this owner's tasks.")

if st.button("Generate schedule"):
    scheduler = Scheduler(
        available_minutes=owner.available_minutes,
        day_start=owner.day_start,
    )
    try:
        plan = scheduler.make_plan(owner.all_tasks(), date.today())
    except NotImplementedError:
        st.warning(
            "Scheduler / Owner.all_tasks() aren't implemented yet. "
            "Implement _sort, _fit, and all_tasks in pawpal_system.py, "
            "then this button will render a real plan."
        )
    else:
        st.markdown(f"### Today's Schedule — {plan.day}")
        if plan.scheduled:
            st.table(
                [
                    {
                        "time": start.strftime("%I:%M %p"),
                        "pet": pet.name,
                        "task": task.title,
                        "duration": task.duration_minutes,
                        "priority": task.priority,
                    }
                    for start, pet, task in plan.scheduled
                ]
            )
        else:
            st.info("Nothing scheduled.")

        if plan.skipped:
            st.markdown("#### Skipped")
            st.table(
                [
                    {"pet": pet.name, "task": task.title, "reason": reason}
                    for pet, task, reason in plan.skipped
                ]
            )
