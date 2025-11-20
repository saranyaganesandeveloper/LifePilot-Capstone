class LifePilotMemory:
    def __init__(self):
        self.session_data = {
            "preferences": "vegetarian, high-protein",
            "meal_plan": None,
            "interactions": []
        }

    def get_user_preferences(self):
        return self.session_data["preferences"]

    def add_interaction(self, text):
        self.session_data["interactions"].append(text)

    def save_meal_plan(self, plan):
        self.session_data["meal_plan"] = plan

    def get_meal_plan(self):
        return self.session_data["meal_plan"]
