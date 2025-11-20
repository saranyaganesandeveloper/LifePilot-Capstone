import os
import google.genai as genai

class MealPlannerAgent:
    def __init__(self, memory):
        self.memory = memory
        self.client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.model = "gemini-2.0-flash"

    def fallback_menu(self, user_prefs=""):
        """Return a default weekly meal plan based on dietary preferences"""
        is_veg = "vegetarian" in user_prefs.lower() or "veg" in user_prefs.lower()
        is_high_protein = "high-protein" in user_prefs.lower()

        if is_veg:
            menu = [
                "Monday: Quinoa salad with chickpeas",
                "Tuesday: Vegetable stir fry with tofu",
                "Wednesday: Lentil soup with whole grain bread",
                "Thursday: Grilled veggie wrap with hummus",
                "Friday: Black bean tacos with avocado",
                "Saturday: Spinach and mushroom omelet",
                "Sunday: Paneer curry with brown rice"
            ]
        else:
            menu = [
                "Monday: Chicken stir fry + brown rice",
                "Tuesday: Vegetable pasta + salad",
                "Wednesday: Grilled salmon + quinoa",
                "Thursday: Chickpea curry + naan",
                "Friday: Tacos (veg or chicken)",
                "Saturday: Biryani + raita",
                "Sunday: Paneer butter masala + rice"
            ]

        if is_high_protein:
            menu = [m + " (high-protein option added)" for m in menu]

        return "\n".join(menu)

    def generate_week_plan(self, user_prefs=""):
        """Generate meal plan using LLM if preferences exist, otherwise fallback"""
        try:
            if not user_prefs.strip():
                # No preferences provided → use fallback
                return self.fallback_menu(user_prefs)

            # Model prompt
            prompt = f"""
Create a weekly meal plan based on the user's preferences.
Ensure the meals respect dietary preferences like vegetarian or vegan.
Highlight high-protein options if requested.

User Preferences: {user_prefs}
"""

            ai = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )

            text = ai.candidates[0].content.parts[0].text

            # If model fails or returns empty/irrelevant output, fallback
            if not text.strip() or "fallback" in text.lower():
                return self.fallback_menu(user_prefs)

            # Save in vector memory for cross-agent context
            self.memory.add(text, metadata={"agent": "meal", "preferences": user_prefs})
            return text

        except Exception:
            return self.fallback_menu(user_prefs)
