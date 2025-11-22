# agents/travel_agent.py
"""
Robust TravelAgent for LifePilot.

Features:
- extract_info(query): structured info extraction (JSON) from a natural-language query.
- generate_itinerary(travel_info, verbosity): create a detailed, day-by-day itinerary dict.
- run(query, verbosity): convenience entry that extracts info then generates itinerary.
- async_run(query, verbosity): async wrapper for orchestrator compatibility.
- create_itinerary(...) alias to support multiple orchestrator call names.
- Stores generated itinerary in provided vector memory under agent='travel' for reuse.
"""

import json
import time
import os
from typing import Any, Dict, List, Tuple, Union

import google.genai as genai

from utils.logger import log

# Small helper: try to find JSON substring inside text
def _extract_json_substring(text: str) -> Union[dict, None]:
    if not text or "{" not in text:
        return None
    # Find first { and last } and try parse
    start = text.find("{")
    last = text.rfind("}")
    if start == -1 or last == -1 or last <= start:
        return None
    candidate = text[start:last + 1]
    try:
        return json.loads(candidate)
    except Exception:
        # Try to be more forgiving: remove non-JSON lines before/after braces
        # fallback: attempt simple fix-ups (replace single quotes)
        try:
            fixed = candidate.replace("'", '"')
            return json.loads(fixed)
        except Exception:
            return None

# Normalize travel_info to ensure required keys exist
def _normalize_travel_info(info: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["destination", "duration", "interests", "budget", "transport", "companions", "start_location", "dates"]
    out = {}
    for k in keys:
        v = info.get(k) if isinstance(info, dict) else None
        if v is None:
            out[k] = ""
        else:
            out[k] = v
    # normalize some fields
    if isinstance(out["interests"], list):
        out["interests"] = ", ".join(out["interests"])
    return out

class TravelAgent:
    def __init__(self, memory):
        self.memory = memory
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY", ""))
        self.model = os.environ.get("TRAVEL_AGENT_MODEL", "gemini-2.0-flash")
        # small local caching
        self._last_itinerary = None
        # tuning
        self._max_extract_retries = 2
        self._max_generate_retries = 2
        self._timeout_seconds = 30

    # ----- Extraction: parse user query into structured JSON -----
    def extract_info(self, query: str) -> Dict[str, Any]:
        """
        Extract travel information from a user query into JSON with required fields.
        If the LLM does not return valid JSON the method will attempt a follow-up prompt
        to coerce JSON output. Returns dict (may contain "error" key).
        """
        log("[LifePilot Log] TravelAgent.extract_info: starting extraction")
        prompt = (
            "You are a travel assistant. Extract the user's travel request into VALID JSON.\n\n"
            "Return a JSON object with these fields:\n"
            "  - destination (string)\n"
            "  - duration (string, e.g. '2 days', or number of days)\n"
            "  - dates (string, optional, e.g. '2025-07-15 to 2025-07-17')\n"
            "  - interests (comma-separated string or list of strings)\n"
            "  - budget (string, e.g. 'budget', 'mid', 'luxury', or numeric per day')\n"
            "  - transport (string, e.g. 'flights', 'car', 'public transit')\n"
            "  - companions (string, e.g. 'solo', '2 adults', 'family of 4')\n"
            "  - start_location (string or empty)\n"
            "If a value is missing, use an empty string for that field. DO NOT add extra top-level fields.\n\n"
            f"User query: {query}\n\n"
            "Only output the JSON object (no extra commentary)."
        )

        for attempt in range(1, self._max_extract_retries + 1):
            try:
                ai = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    temperature=0.0,
                    max_output_tokens=512,
                )
                text = ai.candidates[0].content.parts[0].text.strip()
                log(f"[LifePilot Log] TravelAgent.extract_info: raw LLM output (attempt {attempt}): {text[:200]}")
                parsed = _extract_json_substring(text)
                if parsed:
                    # ensure keys exist
                    parsed = _normalize_travel_info(parsed)
                    return parsed
                else:
                    # If the model returns plain text, try a stricter follow-up that asks only for JSON
                    if attempt < self._max_extract_retries:
                        follow = (
                            "You returned non-JSON text. Please extract again and ONLY return a JSON object "
                            "with the required keys: destination, duration, dates, interests, budget, transport, companions, start_location.\n\n"
                            f"Original model output:\n{text}\n\nUser query:\n{query}\n\nReturn only the JSON object."
                        )
                        ai2 = self.client.models.generate_content(
                            model=self.model,
                            contents=follow,
                            temperature=0.0,
                            max_output_tokens=512,
                        )
                        text2 = ai2.candidates[0].content.parts[0].text.strip()
                        parsed2 = _extract_json_substring(text2)
                        if parsed2:
                            parsed2 = _normalize_travel_info(parsed2)
                            return parsed2
                        else:
                            # continue to retry outer loop
                            continue
                    else:
                        # give up cleanly
                        return {"error": "Failed to reliably extract structured travel info", "raw_text": text}
            except Exception as e:
                log(f"[LifePilot Log] TravelAgent.extract_info: exception on attempt {attempt}: {e}")
                last_exc = e
                time.sleep(0.2 * attempt)
                continue

        # fallback
        return {"error": "Extraction failed after retries."}

    # ----- Itinerary generation -----
    def _build_itinerary_prompt(self, travel_info: Dict[str, Any], verbosity: str = "balanced") -> str:
        """
        Build a prompt to generate a structured itinerary JSON. The model is asked to return valid JSON
        with fields: title, summary, days (list of day objects), packing_list (optional), estimated_costs (optional).
        """
        info_snip = json.dumps(travel_info, ensure_ascii=False)
        prompt = (
            "You are a friendly travel planner. Based on the provided travel_info, generate a clear, practical itinerary.\n\n"
            "REQUIREMENTS:\n"
            "  - Return ONLY a single JSON object (no extra text) with keys:\n"
            "    * title (string)\n"
            "    * summary (short string)\n"
            "    * days (array of objects, each with 'day' and 'activities' list; each activity: name, time, notes)\n"
            "    * packing_list (array of strings) - optional\n"
            "    * estimated_costs (object) - optional (keys: accommodation, food, transport, activities, total)\n"
            "Use reasonable defaults when fields are missing. Keep the itinerary practical and concise.\n\n"
            f"travel_info: {info_snip}\n\n"
            f"verbosity: {verbosity}\n\n"
            "Output: ONLY the JSON object. Ensure valid JSON."
        )
        return prompt

    def generate_itinerary(self, travel_info: Dict[str, Any], verbosity: str = "balanced") -> Dict[str, Any]:
        """
        Generate an itinerary dict. Attempts to coerce JSON output and will attempt a short retry on failure.
        """
        # Ensure travel_info is normalized dict
        travel_info = _normalize_travel_info(travel_info) if isinstance(travel_info, dict) else {}
        prompt = self._build_itinerary_prompt(travel_info, verbosity=verbosity)

        for attempt in range(1, self._max_generate_retries + 1):
            try:
                ai = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    temperature=0.2 if verbosity == "detailed" else 0.0,
                    max_output_tokens=1024,
                )
                text = ai.candidates[0].content.parts[0].text.strip()
                log(f"[LifePilot Log] TravelAgent.generate_itinerary: raw output (attempt {attempt}): {text[:300]}")
                parsed = _extract_json_substring(text)
                if parsed and isinstance(parsed, dict):
                    # Save to memory for later shopping/packing lookups
                    try:
                        self.memory.add(parsed if isinstance(parsed, dict) else json.dumps(parsed), metadata={"agent": "travel"})
                    except Exception:
                        # memory is optional; do not fail if it breaks
                        log("[LifePilot Log] TravelAgent: failed to write itinerary to memory (non-fatal)")
                    self._last_itinerary = parsed
                    return parsed
                else:
                    # try an immediate follow-up instructing strictly JSON output
                    if attempt < self._max_generate_retries:
                        follow = (
                            "The model returned non-JSON. Please respond again with ONLY a valid JSON object matching the required schema:\n"
                            '{"title":"", "summary":"", "days":[{"day": "Day 1", "activities":[{"name":"", "time":"", "notes":""}]}], "packing_list":[], "estimated_costs":{}}\n'
                        )
                        ai2 = self.client.models.generate_content(
                            model=self.model,
                            contents=follow + "\n\nOriginal output:\n" + text,
                            temperature=0.0,
                            max_output_tokens=1024,
                        )
                        text2 = ai2.candidates[0].content.parts[0].text.strip()
                        parsed2 = _extract_json_substring(text2)
                        if parsed2 and isinstance(parsed2, dict):
                            try:
                                self.memory.add(parsed2, metadata={"agent": "travel"})
                            except Exception:
                                pass
                            self._last_itinerary = parsed2
                            return parsed2
                        else:
                            continue
                    else:
                        # final fallback: produce a minimal dict with text summary
                        return {"title": travel_info.get("destination", "Trip"), "summary": text, "days": [], "packing_list": []}
            except Exception as e:
                log(f"[LifePilot Log] TravelAgent.generate_itinerary: exception on attempt {attempt}: {e}")
                time.sleep(0.2 * attempt)
                continue

        # Give up
        return {"error": "Failed to generate itinerary."}

    # ----- Public run methods (sync/async) -----
    def run(self, query: str, verbosity: str = "balanced") -> Dict[str, Any]:
        """
        Primary synchronous entrypoint used by the orchestrator.
        Steps:
          1. Extract travel_info from query.
          2. If fields missing, attempt an LLM follow-up to fill missing info automatically.
          3. Generate itinerary.
        Returns a structured dict (or an error dict).
        """
        log("[LifePilot Log] TravelAgent.run: starting planning loop")
        travel_info = self.extract_info(query)
        if "error" in travel_info:
            # return helpful string explaining failure
            return {"error": travel_info.get("error", "extraction_failed"), "raw_text": travel_info.get("raw_text", "")}

        # If critical fields missing, try to auto-fill them with a short LLM prompt (no user interaction)
        missing = [k for k, v in travel_info.items() if k in ("destination", "duration") and not v]
        if missing:
            log(f"[LifePilot Log] TravelAgent.run: missing critical fields {missing}. Attempting auto-fill.")
            # Ask LLM to infer missing fields from the original query text
            infer_prompt = (
                "Infer missing travel fields from the user's query. Respond ONLY with JSON containing the missing keys.\n"
                f"Missing keys: {missing}\nUser query: {query}\n\nReturn JSON only."
            )
            try:
                ai = self.client.models.generate_content(
                    model=self.model,
                    contents=infer_prompt,
                    temperature=0.0,
                    max_output_tokens=256,
                )
                text = ai.candidates[0].content.parts[0].text.strip()
                parsed = _extract_json_substring(text)
                if parsed:
                    for k, v in parsed.items():
                        if travel_info.get(k, "") == "":
                            travel_info[k] = v
                log(f"[LifePilot Log] TravelAgent.run: inferred fields: {parsed}")
            except Exception as e:
                log(f"[LifePilot Log] TravelAgent.run: inference attempt failed: {e}")

        itinerary = self.generate_itinerary(travel_info, verbosity=verbosity)
        # If the itinerary is a dict but empty days, provide a friendly fallback message
        if isinstance(itinerary, dict) and not itinerary.get("days") and "summary" in itinerary:
            # keep as structured response but it's ok
            return itinerary
        return itinerary

    async def async_run(self, query: str, verbosity: str = "balanced"):
        # async wrapper so orchestrator can await
        return self.run(query, verbosity=verbosity)

    # Provide compatibility aliases expected by orchestrator
    def generate_itinerary_entry(self, travel_info: Dict[str, Any], verbosity: str = "balanced"):
        return self.generate_itinerary(travel_info, verbosity=verbosity)

    def create_itinerary(self, *args, **kwargs):
        # alias that attempts to accept either query (string) or travel_info (dict)
        if args and isinstance(args[0], dict):
            return self.generate_itinerary(args[0], verbosity=kwargs.get("verbosity", "balanced"))
        elif args and isinstance(args[0], str):
            return self.run(args[0], verbosity=kwargs.get("verbosity", "balanced"))
        else:
            return {"error": "create_itinerary requires travel_info dict or query string."}

    # Optional: pretty text output for older code paths
    def pretty_text(self, itinerary: Dict[str, Any]) -> str:
        if not itinerary:
            return "No itinerary available."
        title = itinerary.get("title") or itinerary.get("summary") or "Trip Plan"
        lines = [f"**{title}**\n"]
        summary = itinerary.get("summary")
        if summary:
            lines.append(summary + "\n")
        days = itinerary.get("days") or []
        for d in days:
            day_label = d.get("day") or d.get("date") or "Day"
            lines.append(f"**{day_label}**")
            activities = d.get("activities") or []
            for a in activities:
                name = a.get("name") if isinstance(a, dict) else str(a)
                time_s = a.get("time", "")
                notes = a.get("notes", "")
                line = f"- {name}"
                if time_s:
                    line += f" ({time_s})"
                if notes:
                    line += f": {notes}"
                lines.append(line)
            lines.append("")  # blank line
        # packing
        packing = itinerary.get("packing_list")
        if packing:
            lines.append("**Packing / Shopping**")
            for p in packing:
                lines.append(f"- {p}")
        return "\n".join(lines)
