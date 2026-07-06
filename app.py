
from datetime import date

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
    pet = Pet(name=name, species=species)
    owner.pets.append(pet)
    return pet


st.markdown("### Tasks")
st.caption("Add a few tasks. These are stored as real Task objects on the pet.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    pet = get_or_create_pet(owner, pet_name, species)
    pet.tasks.append(
        Task(title=task_title, duration_minutes=int(duration), priority=priority)
    )

# Build the display table by walking owner -> pets -> tasks directly.
task_rows = [
    {
        "pet": pet.name,
        "title": task.title,
        "duration_minutes": task.duration_minutes,
        "priority": task.priority,
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
