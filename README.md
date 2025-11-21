LifePilot – Personal AI Multi-Agent Assistant

Category: 5-Day AI Agents Intensive Capstone Project
Author: Saranya Ganesan
Technologies: Python, Streamlit, Google Gemini (LLM), AsyncIO, Vector Memory, Multi-Agent System

1️⃣ Project Overview

LifePilot is a personal AI assistant that automates meal planning, grocery shopping, and travel itinerary generation. Using a multi-agent system, it integrates:

MealPlannerAgent – Generates personalized weekly meal plans with dietary and protein preferences, with fallback menus.

ShoppingAgent – Extracts ingredients, finds nearby stores, and compares prices.

TravelAgent – Builds detailed travel itineraries with activities, meals, timings, and costs.

VectorMemory – Cross-agent memory for context sharing across sessions.

Streamlit UI – Single input box for all requests with logs and structured output.

2️⃣ Problem Statement

Planning meals, shopping efficiently, and organizing trips is time-consuming. Individuals often lack tools to:

Align dietary needs with grocery shopping

Get price comparisons from nearby stores

Build coherent multi-day itineraries for travel

LifePilot solves this by combining multiple agents into a unified assistant that handles all tasks in one query, remembers context, and gracefully handles incomplete or fallback scenarios.

3️⃣ Features
Multi-Agent System

Sequential + Parallel execution: Meal planning → Shopping → Travel

Loop agents: TravelAgent iterates to refine itineraries

Tools

MCP + custom tools for price comparison, store detection

Fallback menus for meal planning

Sessions & Memory

VectorMemory enables cross-agent context sharing

Persistent session for repeat queries

Observability

Logs every agent step

Fallback handling and error messages

User Interface

Streamlit-based UI

Tabs for Meal Plan, Shopping List, Travel Itinerary, Logs

4️⃣ Architecture
                +-------------------+
User Query ---> |  Orchestrator     | 
                +-------------------+
                   |     |     |
        +----------+     |     +----------+
        |                |                |
+---------------+  +---------------+  +---------------+
| MealPlanner    |  | ShoppingAgent |  | TravelAgent   |
| Agent         |  |               |  |               |
+---------------+  +---------------+  +---------------+
        |                |                |
        +-------Vector Memory------------+
                   |
                   v
            Streamlit UI
       (Meal / Shopping / Travel / Logs)

5️⃣ Setup Instructions
# 1. Clone repository
git clone https://github.com/<your-username>/LifePilot-Capstone.git
cd LifePilot-Capstone

# 2. Create virtual environment
python -m venv venv
# Activate
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variable
# Windows PowerShell
setx GOOGLE_API_KEY "YOUR_GOOGLE_API_KEY"
# Linux/macOS
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"

# 5. Run Streamlit UI
streamlit run src/ui/app.py

6️⃣ Sample Queries & Expected Output
Query 1 – Meal + Shopping + Travel
Plan a 2-day Austin trip for July 15-16 for 2 people. Vegetarian high-protein meals, budget $100/day, moderate fitness, hiking/swimming/outdoor activities, downtown Airbnb, rideshares + walking, mix of touristy/local experiences.


Expected Streamlit Output:

Meal Plan Tab

Day 1: Paneer stir fry + quinoa + salad

Day 2: Lentil curry + brown rice + steamed vegetables

Shopping List Tab

Ingredients: Paneer, Quinoa, Salad, Lentils, Brown rice, Steamed vegetables

Stores: Walmart (1.2 mi), Kroger (0.8 mi), Target (2.0 mi)

Price Comparison per store

Travel Itinerary Tab

Day 1: Hiking Barton Creek Greenbelt → Lunch at Bouldin Creek Cafe → Barton Springs → Dinner Casa de Luz → Live music

Day 2: Breakfast & Farmers Market → Graffiti Park → Kayaking Lady Bird Lake → Zilker Park → Dinner Gourdough’s → Relax at Airbnb

Logs Tab
[LifePilot Log] START orchestrating user request...
[LifePilot Log] MealAgent: Generating weekly meal plan...
[LifePilot Log] MealAgent: Meal plan stored in memory.
[LifePilot Log] ShoppingAgent: Extracting ingredients...
[LifePilot Log] ShoppingAgent: Detected nearby stores.
[LifePilot Log] TravelAgent: Starting itinerary planning loop...
[LifePilot Log] TravelAgent: Itinerary generated successfully.

Query 2 – Fallback Example
Generate a vegetarian meal plan but do not provide any ingredients.


MealAgent returns fallback menu

ShoppingAgent shows empty ingredients but still detects nearby stores

TravelAgent prompts for missing trip info

7️⃣ Evaluation Checklist

Category 1 – Pitch (30 points)

Clear problem & solution

Core concept explained

Value demonstrated

Category 2 – Implementation (70 points)

Multi-agent system + memory

Tools & fallback handling

Observability/logging

UI for combined functionality

Bonus – Optional (20 points)

Effective Gemini usage

Agent Deployment (Streamlit UI or Cloud)

Demo Video < 3 min
