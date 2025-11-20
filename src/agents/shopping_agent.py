import os
import random
import re
import google.genai as genai

class ShoppingAgent:
    def __init__(self, memory):
        """
        Initialize ShoppingAgent with vector memory for cross-agent context.
        """
        self.memory = memory
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        self.model = "gemini-2.0-flash"

    def detect_nearby_stores(self, user_location=""):
        """
        Dummy function to simulate nearby store detection.
        """
        stores = [
            {"name": "Walmart", "distance": "1.2 miles"},
            {"name": "Kroger", "distance": "0.8 miles"},
            {"name": "Target", "distance": "2.0 miles"},
        ]
        return stores

    def compare_prices(self, ingredients):
        """
        Generate dummy price comparisons for each ingredient at nearby stores.
        """
        dummy_prices = {}
        for item in ingredients:
            dummy_prices[item] = {
                "Walmart": round(random.uniform(1, 10), 2),
                "Kroger": round(random.uniform(1, 10), 2),
                "Target": round(random.uniform(1, 10), 2),
            }
        return dummy_prices

    def run(self, meal_plan=""):
        """
        Extract ingredients from a meal plan, filter by dietary preference, 
        detect stores, compare prices, and store in memory.
        """
        print("[LifePilot Log] ShoppingAgent: Extracting ingredients...")

        # Fallback meal plan if empty
        if not meal_plan.strip():
            meal_plan = "Quinoa salad, vegetable stir fry, lentils, tofu, paneer, brown rice"

        # Query LLM to extract ingredients
        prompt = f"""
        Extract only the ingredients list from this meal plan.
        Return as comma-separated items.
        Meal Plan:
        {meal_plan}
        """

        try:
            ai = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            ai_text = ai.candidates[0].content.parts[0].text.strip()

            # Safe parsing: extract words/ingredients
            ingredients = re.findall(r'\b[a-zA-Z ]+\b', ai_text)
            ingredients = [i.strip() for i in ingredients if i]

        except Exception as e:
            print(f"[LifePilot Log] ShoppingAgent: LLM extraction failed, using fallback. Error: {e}")
            ingredients = ["quinoa", "chickpeas", "tofu", "lentils", "spinach", "mushrooms", "paneer", "brown rice"]

        # Filter out non-vegetarian items if meal plan is vegetarian
        if "vegetarian" in meal_plan.lower():
            non_veg_keywords = ["chicken", "salmon", "beef", "pork", "fish", "shrimp"]
            ingredients = [i for i in ingredients if not any(k in i.lower() for k in non_veg_keywords)]

        # Detect stores and compare prices
        stores = self.detect_nearby_stores()
        prices = self.compare_prices(ingredients)

        # Save ingredients to vector memory for cross-agent context
        self.memory.add(" ".join(ingredients), metadata={"agent": "shopping"})

        # Return structured output
        return {
            "ingredients": ingredients,
            "stores": stores,
            "price_comparison": prices
        }
