# orchestrator.py — LifePilot orchestrator (robust TravelAgent handling + readable travel markdown)
import asyncio
import argparse
import json
import sys
import traceback
from datetime import datetime
from typing import Any

from agents.meal_agent import MealPlannerAgent
from agents.shopping_agent import ShoppingAgent
from agents.travel_agent import TravelAgent
from memory.vector_memory import VectorMemory
from utils.logger import log as external_log

# Shared singletons
memory = VectorMemory()
meal_agent = MealPlannerAgent(memory)
shopping_agent = ShoppingAgent(memory)
travel_agent = TravelAgent(memory)


class LifePilotOrchestrator:
    def __init__(self, auto_shopping_fallback=False, verbosity="balanced", include_shopping=False):
        self.memory = memory
        self.meal_agent = meal_agent
        self.shopping_agent = shopping_agent
        self.travel_agent = travel_agent
        self.auto_shopping_fallback = auto_shopping_fallback
        self.verbosity = verbosity
        self.include_shopping = include_shopping
        self._logs = []

    def _log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{ts}] {msg}"
        self._logs.append(entry)
        try:
            external_log(entry)
        except Exception:
            # keep going even if external logging fails
            pass

    # Convert various travel-agent outputs to readable markdown
    def _format_travel_markdown(self, travel_output: Any) -> str:
        """
        - If travel_output is a string: return it.
        - If dict with keys like 'title','summary','itinerary' or 'days' -> produce markdown.
        - If list of day objects -> produce markdown.
        - Otherwise, json-dump it prettily.
        """
        if travel_output is None:
            return "No itinerary returned."

        # If it's already a string, assume it's human-readable
        if isinstance(travel_output, str):
            return travel_output

        # If it's a list, assume list of day items
        if isinstance(travel_output, list):
            md_lines = []
            for i, item in enumerate(travel_output, start=1):
                md_lines.append(f"**Day {i}**")
                if isinstance(item, dict):
                    title = item.get("title") or item.get("day") or ""
                    if title:
                        md_lines.append(f"*{title}*")
                    desc = item.get("description") or item.get("notes") or ""
                    if desc:
                        md_lines.append(desc)
                    activities = item.get("activities") or item.get("things") or item.get("plans")
                    if activities:
                        for a in activities:
                            md_lines.append(f"- {a}")
                else:
                    md_lines.append(f"- {item}")
                md_lines.append("")  # blank line
            return "\n".join(md_lines)

        # If it's a dict, try to extract fields
        if isinstance(travel_output, dict):
            md = []
            title = travel_output.get("title") or travel_output.get("trip_title") or travel_output.get("name")
            if title:
                md.append(f"# {title}\n")
            summary = travel_output.get("summary") or travel_output.get("overview") or travel_output.get("description")
            if summary:
                md.append(summary + "\n")

            # If there is an 'itinerary' or 'days' or 'plans' key
            itinerary = travel_output.get("itinerary") or travel_output.get("days") or travel_output.get("plan")
            if itinerary:
                # reuse list handling
                md.append("## Itinerary\n")
                md.append(self._format_travel_markdown(itinerary))
            else:
                # Try extracting numbered keys like day_1, day1, day-1
                days = []
                for k, v in travel_output.items():
                    if isinstance(k, str) and ("day" in k.lower() or k.lower().startswith("d")):
                        days.append((k, v))
                if days:
                    md.append("## Itinerary\n")
                    # sort keys to stable order
                    days_sorted = sorted(days, key=lambda x: x[0])
                    for key, val in days_sorted:
                        md.append(f"### {key}\n")
                        if isinstance(val, (str, int, float)):
                            md.append(str(val))
                        else:
                            md.append(self._format_travel_markdown(val))
                else:
                    # Last resort: pretty-print JSON of dict
                    md.append("### Details\n")
                    md.append("```\n" + json.dumps(travel_output, indent=2, ensure_ascii=False) + "\n```\n")

            # Optional shopping list included for travel (e.g., packing list / grocery)
            packing = travel_output.get("packing_list") or travel_output.get("shopping_list")
            if packing:
                md.append("## Packing / Shopping\n")
                if isinstance(packing, (list, tuple)):
                    md.extend([f"- {p}" for p in packing])
                elif isinstance(packing, dict):
                    # flatten common structures
                    items = packing.get("items") or packing.get("ingredients") or []
                    if items:
                        md.extend([f"- {it}" for it in items])
                    else:
                        md.append("```\n" + json.dumps(packing, indent=2, ensure_ascii=False) + "\n```\n")
                else:
                    md.append(str(packing))

            return "\n".join(md)

        # Fallback: dump whatever it is
        try:
            return json.dumps(travel_output, indent=2, ensure_ascii=False)
        except Exception:
            return str(travel_output)

    async def _call_travel_agent(self, query: str):
        """
        Attempt a robust set of ways to call travel agent:
        - travel_agent.run(query, verbosity=...)
        - travel_agent.plan(query) / travel_agent.generate_itinerary(query)
        - travel_agent.create_itinerary(...)
        - travel_agent.async_run(...) (await if coroutine)
        Capture exceptions and return tuple(success_flag, result_or_error)
        """
        candidate_calls = []

        # common expected call signatures
        candidate_calls.append(("run_with_verbosity", lambda: self.travel_agent.run(query, verbosity=self.verbosity)))
        candidate_calls.append(("run_simple", lambda: self.travel_agent.run(query)))
        candidate_calls.append(("plan_with_verbosity", lambda: self.travel_agent.plan(query, verbosity=self.verbosity)))
        candidate_calls.append(("plan_simple", lambda: self.travel_agent.plan(query)))
        candidate_calls.append(("generate_itinerary", lambda: self.travel_agent.generate_itinerary(query)))
        candidate_calls.append(("create_itinerary", lambda: self.travel_agent.create_itinerary(query)))
        candidate_calls.append(("async_run", lambda: self.travel_agent.async_run(query)))
        candidate_calls.append(("callable_fallback", lambda: self.travel_agent(query) if callable(self.travel_agent) else None))

        last_exc = None
        for name, call in candidate_calls:
            try:
                self._log(f"TravelAgent: trying method `{name}`")
                result = call()
                # if result is a coroutine (async), await it
                if asyncio.iscoroutine(result):
                    self._log(f"TravelAgent: awaiting coroutine from `{name}`")
                    result = await result
                # if result is None, continue trying other methods but accept None as valid result
                self._log(f"TravelAgent: method `{name}` returned (type: {type(result).__name__})")
                return True, {"method": name, "output": result}
            except AttributeError as ae:
                # method not implemented on agent — try next
                last_exc = ae
                self._log(f"TravelAgent: method `{name}` not available: {ae}")
                continue
            except Exception as e:
                last_exc = e
                tb = traceback.format_exc()
                self._log(f"TravelAgent: method `{name}` raised exception: {e}\n{tb}")
                # try next candidate rather than failing hard immediately
                continue

        # if we exhausted candidates, return error
        err_msg = f"No working TravelAgent method found. Last exception: {repr(last_exc)}"
        return False, {"method": "none", "error": err_msg, "exception": repr(last_exc)}

    async def handle_request(self, query: str):
        try:
            self._log("START orchestrating user request")
            query_lower = (query or "").strip().lower()

            # Meal planning
            if "meal" in query_lower or "menu" in query_lower:
                self._log("MealAgent: Generating weekly meal plan")
                try:
                    plan = self.meal_agent.generate_week_plan(query, verbosity=self.verbosity)
                except TypeError:
                    plan = self.meal_agent.generate_week_plan(query)
                # Optionally include shopping list
                shopping_list = None
                if self.include_shopping or self.auto_shopping_fallback:
                    try:
                        self._log("ShoppingAgent: extracting ingredients for generated meal plan")
                        shopping_list = self.shopping_agent.run(plan)
                    except Exception as e:
                        self._log(f"ShoppingAgent error: {e}")
                return {"type": "meal", "response": plan, "shopping_list": shopping_list}

            # Shopping
            elif "shopping" in query_lower or "ingredients" in query_lower or "grocery" in query_lower:
                self._log("ShoppingAgent: Extracting ingredients from last meal or fallback")
                last_meal = self.memory.search("meal")
                if not last_meal:
                    if self.auto_shopping_fallback:
                        self._log("No meal plan in memory; generating vegetarian fallback")
                        try:
                            fallback = self.meal_agent.fallback_menu("vegetarian")
                        except TypeError:
                            fallback = self.meal_agent.fallback_menu()
                        try:
                            self.memory.add(fallback, metadata={"agent": "meal", "fallback": True})
                        except Exception:
                            self._log("Warning: could not add fallback to memory")
                        last_meal_text = fallback
                    else:
                        return {"type": "shopping", "response": "No meal plan found. Please generate a meal plan first.", "shopping_list": None}
                else:
                    last_meal_text = last_meal[0].get("text", last_meal[0])
                shopping_list = self.shopping_agent.run(last_meal_text)
                return {"type": "shopping", "response": "Shopping list generated.", "shopping_list": shopping_list}

            # Travel
            elif "travel" in query_lower or "trip" in query_lower or "itinerary" in query_lower:
                self._log("TravelAgent: planning itinerary")
                success, travel_result = await self._call_travel_agent(query)
                if not success:
                    # travel agent didn't work: return user-friendly error + logs
                    err = travel_result.get("error", "Unknown travel agent failure.")
                    self._log("TravelAgent failed to produce itinerary.")
                    return {"type": "travel", "response": f"Sorry — I couldn't generate a travel itinerary: {err}", "travel_debug": travel_result}

                # travel_result contains {'method':..., 'output':...}
                travel_output = travel_result.get("output")
                # If travel agent returned structured object, convert to markdown for UI display
                travel_markdown = self._format_travel_markdown(travel_output)
                # optionally include packing/shopping info extracted from structured output if present
                packing = None
                if isinstance(travel_output, dict):
                    packing = travel_output.get("packing_list") or travel_output.get("shopping_list")

                return {"type": "travel", "response": travel_markdown, "raw_travel": travel_output, "packing_list": packing, "travel_method": travel_result.get("method")}

            else:
                self._log("Could not understand request intent")
                return {"type": "unknown", "response": "Sorry, I could not understand your request. Please include 'meal', 'shopping', or 'travel'."}

        except Exception as e:
            tb = traceback.format_exc()
            self._log(f"Unhandled exception in orchestrator: {e}\n{tb}")
            return {"type": "error", "response": str(e), "traceback": tb}

    async def run_and_print(self, query: str):
        result = await self.handle_request(query)
        output = {
            "metadata": {
                "auto_shopping_fallback": self.auto_shopping_fallback,
                "verbosity": self.verbosity,
                "include_shopping": self.include_shopping,
            },
            "logs": self._logs,
            "result": result,
        }
        # Print JSON to stdout. UI reads and parses it.
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LifePilot AI Orchestrator (robust TravelAgent)")
    parser.add_argument("--query", type=str, required=True, help="User query for LifePilot")
    parser.add_argument("--auto-shopping-fallback", action="store_true", help="Auto-generate meal plan if shopping list requested without meal plan")
    parser.add_argument("--verbosity", choices=["concise", "balanced", "detailed"], default="balanced", help="Response verbosity")
    parser.add_argument("--include-shopping", action="store_true", help="When generating meal plans, also produce a shopping list")
    args = parser.parse_args()

    orchestrator = LifePilotOrchestrator(
        auto_shopping_fallback=args.auto_shopping_fallback,
        verbosity=args.verbosity,
        include_shopping=args.include_shopping,
    )

    async def _main():
        try:
            await orchestrator.run_and_print(args.query)
            return 0
        except Exception as e:
            tb = traceback.format_exc()
            external_log(f"Orchestrator fatal error: {e}\n{tb}")
            print(json.dumps({
                "metadata": {"auto_shopping_fallback": args.auto_shopping_fallback, "verbosity": args.verbosity},
                "logs": [f"fatal: {e}"],
                "result": {"type": "error", "response": str(e), "traceback": tb}
            }, ensure_ascii=False, indent=2))
            return 2

    rc = asyncio.run(_main())
    sys.exit(rc)
