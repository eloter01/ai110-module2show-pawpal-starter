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

My scheduler weighs five things:

1. Time budget (`available_minutes`) — a hard cap on the total minutes the owner has in a day. Anything that doesn't fit is skipped with a reason.
2. Priority (`high` / `medium` / `low`) — the primary sort key, so important care happens first.
3. Duration — the tie-breaker within a priority level (shorter tasks first, so more tasks fit).
4. Fixed times / anchors (`fixed_time`) — tasks like meds that must happen at a set clock time; they reserve their slot and floating tasks flow around them.
5. Due date / completion (`_is_due`) — only tasks actually due on the target day and not already done are considered (daily always, weekly only on listed weekdays).

I decided priority mattered most because the scenario is a busy owner who can't get to everything. The worst failure is missing something important (meds, a walk) while spending the budget on a low-stakes task. Priority-first ordering directly guards against that. The time budget is the hard constraint that makes the problem interesting: without it, everything would just be scheduled. Fixed-time anchors come next because some care genuinely can't move.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

The scheduler is greedy, not optimal: it sorts by priority (then duration) and fills the day in that order, skipping anything that doesn't fit. It does not search for the combination of tasks that would pack the most care into the budget. So a single high-priority 90-minute task can consume budget that two medium 45-minute tasks could have used. The greedy choice "wastes" capacity a smarter bin-packer would recover.

That tradeoff is reasonable here because the plan has to be explainable and predictable, not mathematically optimal. A pet owner wants to trust that "the most important things came first," and the skipped list can say plainly why something was dropped ("needs 90 min, only 30 left"). An optimization that quietly demoted a high-priority task to fit two lower ones would be harder to trust and harder to reason about, for a payoff (a few extra minutes packed) that doesn't matter much across a single day's care routine.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI across the whole workflow, but always with me steering scope:

- **Design brainstorming** — talking through the UML class structure and deciding on the four-class design (Task / Pet / Owner + Scheduler, plus DailyPlan).
- **Implementation & refactoring** — building the scheduling methods incrementally and reviewing them for readability.
- **Test authoring** — asking the AI to first *check what was already covered* and only add non-redundant tests for genuinely untested behaviors (priority sort, empty lists, same-time anchors, over-budget floats).
- **Documentation** — drafting the README Features list and Demo Walkthrough, and keeping the UML diagram in sync with the final code.
- **UI wiring** — surfacing scheduler output (like conflict warnings) in Streamlit.

The most helpful prompts were specific and scoped: e.g. "refine the UML to match what I actually built," "list the untested core behaviors and only implement the gaps," and pointed questions like "how should a conflict be presented in the UI?" Telling the AI what to ignore was just as useful. Early on I had it set aside the README's "Smarter Scheduler" section so it wouldn't over-engineer the class design before I was ready.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

I examined the Scheduler._next_free() method for complexity and to see whether it could be optimized for readability or performance. What it does is a helper that finds the earliest start time for a floating task that doesn't collide with a reserved anchor slot in my logic. These anchors are sorted but yet the algorithm makes the defensive assumption that they might not be. 

At the time, I decided against modifying because I wanted to do some manual testing to fully understand the logic better first. I also prefer a more defensive style of programming being risk-averse. The tradeoff is O(n) versus O(n log n) in terms of performance.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The suite (34 tests) covers the scheduler's core guarantees plus the edge cases most likely to break it:

- **Recurrence / due dates** — daily tasks are always due; weekly tasks only on their listed weekdays; completing a recurring task spawns the next occurrence (+1 day daily, +7 weekly) with an independent weekdays list; one-off tasks spawn nothing.
- **Completion** — done tasks drop out of the plan entirely and free their budget for others.
- **Priority ordering** — high → medium → low, ties broken by shorter duration, with unknown priorities falling back to medium.
- **Anchored tasks** — fixed_time tasks are placed at their clock time, floating tasks flow around them, output stays time-ordered, and an anchor over budget is skipped with a reason.
- **Conflict detection** — same preferred time (across or within pets) is flagged; distinct or blank times are not; it returns warnings rather than raising.
- **Filtering** — by completion status, by pet, both combined, and an unknown pet returning empty.
- **Edge cases** — an empty task list and a petless owner (empty plan, no crash), two anchors competing for the exact same slot (one scheduled, one skipped), and a floating task over budget skipped with a reason.

These matter because they are the promises the app makes to the owner: the right tasks on the right day, nothing double-booked, the budget respected, and the routine self-perpetuating. The edge cases are where a naive scheduler would crash or silently misbehave, so pinning them down is what lets me change the code later without fear.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Medium-high (4). All 34 tests pass and cover the core behaviors and the edge cases I could think of, so I'm confident in the intended single-day scope. I hold back from full confidence because some realistic situations remain unexercised.

Edge cases I'd test next:

- Fixed-time anchor overlaps surfaced up front (right now they only appear as skipped rows after generating, not as a warning like preferred-time clashes).
- Invalid / malformed time strings (e.g. "25:99" or non-HH:MM input) — currently sorted as plain strings with no validation.
- A weekly task with an empty weekdays list** — is it ever due?
- Day-boundary behavior — a task whose duration runs past midnight, or a fixed_time earlier than day_start.
- Scale — a large number of tasks/anchors, to check _next_free's behavior under many reserved slots.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with the test coverage. The 34-test suite doesn't just check the happy paths, it pins down the edge cases (empty task lists, two tasks competing for the same slot, over-budget skips, unknown priorities) that are exactly where scheduling logic tends to break. Beyond catching bugs, the tests became a safety net: I could refactor and let the AI touch the code knowing that any regression in a core behavior would show up immediately. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd resolve the fact that a Task tracks time two different ways: time (a preferred "HH:MM" string used for sorting and conflict detection) and fixed_time (a time anchor used to pin a task in _fit). Having two representations of "when" is confusing and is the root cause of the app's split personality around conflicts — preferred-time clashes are warned about up front, but fixed-time overlaps only surface as skipped rows after generating. Next iteration I'd either unify them into a single time concept (one field, one code path, with a flag for "hard anchor vs. preference") or drop one if the use cases don't justify both. That would simplify the model and make conflict handling consistent.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

Verify AI output; don't trust it blindly. The clearest example was Scheduler._next_free() — rather than accepting it as correct, I read through the logic, noticed it defensively re-checks anchor slots that are already sorted, and chose to understand it through manual testing before deciding whether to change it (see 3b). The tests reinforced the same lesson: AI can produce plausible-looking code fast, but it's the reading, questioning, and testing that tell you whether it actually does what you need. AI accelerated the work, but the judgment about whether it was right stayed with me.
