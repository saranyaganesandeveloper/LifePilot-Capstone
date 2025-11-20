import json
import google.genai as genai
import os
from utils.logger import log

class TravelAgent:
    def __init__(self, memory):
        """
        TravelAgent with vector memory for cross-agent context.
        """
        self.memory = memory
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        self.model = "gemini-2.0-flash"

    def extract_info(self, query):
        """
        Extract structured travel info from user query.
        Returns JSON if possible, else returns plain text fallback.
        """
        prompt = f"""
        Extract travel info from this query and return as valid JSON:
        Required fields: destination, duration, interests, budget, transport, companions, start_location
        If any info is missing, leave the value as an empty string.
        Query: {query}
        """

        ai = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        ai_text = ai.candidates[0].content.parts[0].text.strip()

        if not ai_text:
            return {"error": "No travel info extracted. Please provide more details."}

        try:
            return json.loads(ai_text)
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON, received text instead", "raw_text": ai_text}

    def generate_itinerary(self, travel_info):
        """
        Generate a simple itinerary based on the extracted info.
        Loops to refine if info is missing.
        """
        itinerary = {}
        loop_count = 0
        max_loops = 3

        while loop_count < max_loops:
            loop_count += 1
            log(f"[LifePilot Log] TravelAgent: Loop iteration #{loop_count}")

            missing_fields = [
                k for k, v in travel_info.items() if not v and k != "error"
            ]

            if missing_fields:
                # Ask user (or LLM) to fill missing info
                log(f"[LifePilot Log] TravelAgent: Missing info - {missing_fields}")
                travel_info_text = ", ".join([f"{f}: unknown" for f in missing_fields])
                itinerary["note"] = f"Cannot complete itinerary, missing: {travel_info_text}"
                break
            else:
                # Generate sample itinerary
                itinerary["Day 1"] = f"Visit popular spots in {travel_info['destination']} and dine at recommended restaurants."
                itinerary["Day 2"] = f"Explore outdoors, local attractions, and shopping in {travel_info['destination']}."
                itinerary["summary"] = f"Itinerary for {travel_info['duration']} in {travel_info['destination']} completed."
                break

        return itinerary

    def run(self, query):
        """
        Main entry for TravelAgent.
        Returns structured itinerary or fallback note.
        """
        log("[LifePilot Log] TravelAgent: Starting planning loop...")

        travel_info = self.extract_info(query)

        if "error" in travel_info:
            return f"TravelAgent: {travel_info['error']}\nDetails: {travel_info.get('raw_text', '')}"

        itinerary = self.generate_itinerary(travel_info)
        return itinerary
