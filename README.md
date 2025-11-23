# **LifePilot – Personal AI Multi-Agent Assistant**

- **Category:** 5-Day AI Agents Intensive – Capstone Project
- **Author:** Saranya Ganesan
- **Technologies:** Python, Streamlit, Google Gemini (LLM), AsyncIO, Vector Memory, Multi-Agent System

---

## **📌 1. Project Overview**

**LifePilot** is a personal multi-agent AI assistant that automates:

* Weekly meal planning
* Smart grocery shopping
* Detailed travel itinerary generation

The system uses **multi-agent orchestration**, **vector memory**, and a **Streamlit-based UI** to deliver a unified intelligent assistant.

### **Agents Included**

* **🍽️ MealPlannerAgent** – Personalized weekly meal plans, protein/diet preferences, fallbacks
* **🛒 ShoppingAgent** – Extracts ingredients, finds local stores, price comparison
* **✈️ TravelAgent** – Multi-day itineraries (activities, meals, timings, cost)
* **🧠 VectorMemory** – Cross-agent context sharing across sessions
* **🖥️ Streamlit UI** – Query input, structured tabs, logs, new UI polish

---

## **🎯 2. Problem Statement**

Planning meals, shopping efficiently, and organizing trips usually requires switching between multiple tools. Users lack a unified system that:

* Connects dietary needs to grocery shopping
* Finds best-priced ingredients nearby
* Generates multi-day travel plans with cost & activity balance

**LifePilot solves this with a single intelligent entry point** that handles all three tasks **sequentially or in parallel**, shares memory across agents, and gracefully handles missing information with fallbacks.

---

## **✨ 3. Features**

### **🔹 Multi-Agent System**

* Sequential + parallel execution
* TravelAgent uses refinement loops
* Granular logs for every agent step

### **🔹 Tools**

* MCP + custom scraping tools
* Local store detection
* Fallback meal menus

### **🔹 Sessions & Memory**

* VectorMemory tracks long-term dietary, shopping, and travel context
* Improves results over repeated queries

### **🔹 Updated User Interface (NEW)**

The latest UI includes:

* **Global Input Bar** – One entry point for all requests
* **Modern card-style layout**
* **Dedicated Tabs**:

  * **Meal Plan** – Styled meal cards with icons
  * **Shopping List** – Price comparison table + store list
  * **Travel Itinerary** – Timeline-style display
  * **Logs** – Live agent-by-agent log stream
* **Visual separators & emoji-based headings**
* **Improved color theme and spacing**
* **Loading animations for agent execution**

---

## **🏗️ 4. Architecture**

```
                +-------------------+
User Query ---> |   Orchestrator    | 
                +-------------------+
                   |       |       |
        +----------+       |       +----------+
        |                  |                  |
+---------------+  +---------------+  +---------------+
| MealPlanner   |  | ShoppingAgent |  | TravelAgent   |
| Agent         |  |               |  |               |
+---------------+  +---------------+  +---------------+
        |                  |                  |
        +------------ Vector Memory ----------+
                       |
                       v
                Streamlit Frontend
           (Meal | Shopping | Travel | Logs)
```

---

## **⚙️ 5. Setup Instructions**

### **1. Clone the Repository**

```bash
git clone https://github.com/<your-username>/LifePilot-Capstone.git
cd LifePilot-Capstone
```

### **2. Create Virtual Environment**

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

### **3. Install Dependencies**

```bash
pip install -r requirements.txt
```

### **4. Set Environment Variables**

**Windows (PowerShell)**

```bash
setx GOOGLE_API_KEY "YOUR_GOOGLE_API_KEY"
```

**Mac/Linux**

```bash
export GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
```

### **5. Run the Streamlit UI**

```bash
streamlit run src/ui/app.py
```

## **b) Running with Docker**

**Build**

```bash
docker build -t lifepilot-app .
```

**Run**

```bash
docker run -p 8501:8501 \
  -e GOOGLE_API_KEY=YOUR_API_KEY \
  -e GCP_SERVICE_URL=https://<your-cloud-run-url>.run.app \
  lifepilot-app
```

---

## **🧪 6. Sample Queries & Expected Output**

### **Query Example 1 – Combined Meal + Shopping + Travel**

**User Query:**
*“Plan a 2-day Austin trip for July 15–16 for 2 people. Vegetarian high-protein meals, budget $100/day, moderate fitness, hiking/swimming/outdoor activities, downtown Airbnb, rideshares + walking, mix of touristy/local experiences.”*

### **Meal Plan Tab (Updated UI)**

* Card-based day-wise meal layout
* Icons for Meal / Protein / Calories

**Example:**

* **Day 1:** Paneer Stir Fry + Quinoa
* **Day 2:** Lentil Curry + Brown Rice

### **Shopping List Tab**

* Ingredients auto-extracted
* Store list with distance
* Price comparison table

### **Travel Itinerary Tab**

* Timeline UI
* Time blocks for each activity
* Cost breakdown

### **Logs Tab**

Shows real-time steps such as:

```
[LifePilot] MealAgent → generating meal plan
[LifePilot] MealAgent → stored in VectorMemory
[LifePilot] ShoppingAgent → extracting ingredients
[LifePilot] TravelAgent → planning itinerary loop (iteration 1)
...
```

---

### **Query Example 2 – Fallback Handling**

**User Query:**
“Generate a vegetarian meal plan but do not provide any ingredients.”

**Result:**

* MealAgent produces **fallback vegetarian menu**
* ShoppingAgent shows:

  * “No ingredients provided”
  * Still detects nearest stores
* TravelAgent prompts user for missing trip info

---

## **📝 7. Evaluation Checklist**

### **Category 1 – Pitch (30 pts)**

* Clear problem & solution
* Concept well-structured
* Demonstrated user value

### **Category 2 – Implementation (70 pts)**

* Fully functional multi-agent flow
* VectorMemory integration
* Streamlit UI + logs
* Fallback logic
* MCP-based tools

### **Bonus – Optional (20 pts)**

* Effective Gemini usage
* Deployment on Streamlit / Cloud
* Demo video < 3 minutes

---


