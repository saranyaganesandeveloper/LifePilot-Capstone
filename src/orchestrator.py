import asyncio
import argparse
from agents.meal_agent import MealPlannerAgent
from agents.shopping_agent import ShoppingAgent
from agents.travel_agent import TravelAgent
from memory.vector_memory import VectorMemory
from utils.logger import log

# Initialize vector memory
memory = VectorMemory()

# Initialize agents
meal_agent = MealPlannerAgent(memory)
shopping_agent = ShoppingAgent(memory)
travel_agent = TravelAgent(memory)

# ----------------- Orchestrator -----------------
class LifePilotOrchestrator:
    def __init__(self, auto_shopping_fallback=False):
        self.memory = memory
        self.meal_agent = meal_agent
        self.shopping_agent = shopping_agent
        self.travel_agent = travel_agent
        self.auto_shopping_fallback = auto_shopping_fallback

    async def handle_request(self, query):
        log("[LifePilot Log] START orchestrating user request...")

        query_lower = query.lower()

        # Meal planning
        if "meal" in query_lower:
            log("[LifePilot Log] MealAgent: Generating weekly meal plan...")
            plan = self.meal_agent.generate_week_plan(query)
            return plan

        # Shopping
        elif "shopping" in query_lower or "ingredients" in query_lower:
            log("[LifePilot Log] ShoppingAgent: Extracting ingredients...")

            last_meal = self.memory.search("meal")
            if not last_meal:
                if self.auto_shopping_fallback:
                    log("[LifePilot Log] No meal plan found. Auto-generating fallback meal plan...")
                    last_meal_text = self.meal_agent.fallback_menu("vegetarian")
                    self.memory.add(last_meal_text, metadata={"agent": "meal"})
                else:
                    return "No meal plan found. Please generate a meal plan first."
            else:
                last_meal_text = last_meal[0]["text"]

            shopping_list = self.shopping_agent.run(last_meal_text)
            return shopping_list

        # Travel
        elif "travel" in query_lower or "trip" in query_lower:
            log("[LifePilot Log] TravelAgent: Planning itinerary...")
            itinerary = self.travel_agent.run(query)
            return itinerary

        else:
            return "Sorry, I could not understand your request. Please include 'meal', 'shopping', or 'travel'."

# ----------------- CLI Entry -----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LifePilot AI Orchestrator")
    parser.add_argument("--query", type=str, required=True, help="User query for LifePilot")
    parser.add_argument("--auto-shopping-fallback", action="store_true", help="Auto-generate meal plan if shopping list is requested without meal plan")
    args = parser.parse_args()

    orchestrator = LifePilotOrchestrator(auto_shopping_fallback=args.auto_shopping_fallback)

    async def run():
        response = await orchestrator.handle_request(args.query)
        print(response)

    asyncio.run(run())
