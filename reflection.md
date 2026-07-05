# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Owner / account
- Create an owner (enter name) — Owner(name=...)
- add more owners. Supported structurally, not exercised yet

Pets
- Add a pet to an owner — append to owner.pets
- View all pets for the owner — read owner.pets
- Edit a pet's info (name, species) — mutate the Pet
- Remove a pet — remove from owner.pets

Tasks
- Add a task to a pet (title, duration, priority) — append to pet.tasks
- Edit a task (change duration/priority/title) — mutate the Task
- Remove a task — remove from pet.tasks
- View all tasks — via:
    - per pet → pet.tasks
    - across all pets (for the day) → owner.all_tasks()

Planning
- Set the day's constraints — construct Planner(available_minutes=..., day_start=...)
- Generate a daily plan — planner.make_plan(tasks) → DailyPlan
- View the schedule — read plan.scheduled (task + start time)
- See what was skipped and why — read plan.skipped (the "explain the reasoning" action)


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

1. when designing the class structure, the AI initially started with a simpler design but then created more complexity by adding additional classes when it looked at the "Smarter Scheduler" section of the Readme. I preferred to start at more simple and wanted it to use the suggested four classes per the instructions so we went with that after I told it to ignore the "Smarter Scheduler" section for now.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
