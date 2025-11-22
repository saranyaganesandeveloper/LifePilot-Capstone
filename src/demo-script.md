Title: LifePilot — Live Demo

Version/Date: v0.1 — (add date)

Overview:
This demo shows LifePilot coordinating meal planning, grocery shopping, and travel planning agents to create a simple daily plan and shopping list. Target audience: product stakeholders and potential users.

Goals:

Show end-to-end flow from user intent → agents → final plan.
Demonstrate memory (session + vector) persisted across requests.
Show UI (if available) and show CLI/orchestrator run.
Highlight how the system handles missing info and follow-ups.
Prerequisites / Environment:

Python 3.11+ installed.
From project root, install dependencies: pip install -r requirements.txt (run in virtualenv).
Start any required services (if using Docker, docker compose up or docker build + docker run).
Commands to run locally (confirm these match your setup):
Start backend/orchestrator: python src/orchestrator.py
Start UI (if using local Flask/FastAPI): python src/ui/app.py
Open browser to http://localhost:8000 (adjust port as needed).
Demo Flow & Scenarios (2–3 mins each):

Scenario A — "Quick Dinner Plan" (Meal agent)
Input: "I want a quick vegetarian dinner for 2 tonight."
Expected: Meal agent proposes 2 recipe options and a shopping list.
Scenario B — "Grocery List + Shop" (Shopping agent)
Input: select recipe → generate consolidated shopping list and estimated cost.
Expected: Shopping agent groups items by aisle and suggests substitutes for unavailable items.
Scenario C — "Weekend Trip Planning" (Travel agent)
Input: "Plan a 2-day weekend trip to Portland with budget $400."
Expected: Travel agent returns itinerary, estimated cost, and packing checklist.
Presenter Script (copy/paste ready)
0:00 — "Hi everyone, I’m [Name]. Today I’ll show LifePilot: an AI-driven assistant that coordinates planning tasks across agents."
0:15 — "First, I’ll start the backend." (Run python src/orchestrator.py and show logs.)
0:30 — "Now I’ll ask it to plan a quick vegetarian dinner for two." (Type/paste input in UI or send request in CLI.)
0:45 — "It’s asking a follow-up: do you prefer spicy or mild?" (Demonstrate the follow-up prompt and answer.)
1:00 — "Here are the recipe options with estimated prep time. I’ll pick one." (Select option.)
1:20 — "Next, the shopping agent consolidates the list and organizes by aisle." (Show the generated list.)
1:45 — "Finally, I’ll show a travel planning example." (Switch context, paste travel prompt.)
2:30 — "That concludes the short demo. Summary: we showed end-to-end planning, memory across steps, and agent coordination."

Expected Verification:

For Meal: recipes with ingredients, prep time shown.
For Shopping: consolidated list grouped by aisle, suggested substitutes present.
For Travel: itinerary with dates and budget check.
Edge Cases / Fallbacks:

If an API or external price lookup fails, the shopping agent returns partial results with a note.
If user input is ambiguous, show that the orchestrator asks clarifying questions.
Troubleshooting (common quick fixes):

Backend fails to start: check error logs in terminal, ensure required env vars set.
UI not loading: confirm port, check CORS and console errors.
Missing packages: run pip install -r requirements.txt.
Recording / Logistics Checklist:

Microphone muted/unmuted check.
Open only required browser tabs.
Start screen recording (Zoom/OBS).
Keep demo ≤ 10 minutes.
Q&A Prompts:

"How does the system remember previous sessions?" (Discuss session.py and vector_memory.py.)
"How are agents coordinated?" (Explain orchestrator.py.)
"What are common failure modes?"
Assets to include:

Short GIFs of the UI flow, screenshots of agent outputs, links to README and architecture diagram.