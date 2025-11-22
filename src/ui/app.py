# app.py — Streamlit UI for LifePilot (JSON parsing + pretty rendering)
import os
import subprocess
import streamlit as st
from datetime import datetime
import json
import pandas as pd
from textwrap import shorten

st.set_page_config(page_title="🌟 LifePilot", page_icon="🌟", layout="wide")

# ---------- Styles ----------
st.markdown(
    """
    <style>
    .header {
        background: linear-gradient(90deg,#6EE7B7 0%,#60A5FA 50%,#C7B2FF 100%);
        padding: 16px;
        border-radius: 10px;
        color: #082032;
        margin-bottom: 12px;
    }
    .small-muted { font-size:12px; color:#667085; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="header"><h2 style="margin:0">🌟 LifePilot — AI Personal Assistant</h2>'
    '<div class="small-muted">Meals • Shopping • Travel — pretty results, shopping tables, and logs</div></div>',
    unsafe_allow_html=True,
)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Options")
    auto_shopping = st.checkbox("Auto-shopping fallback", value=True)
    include_shopping = st.checkbox("Include shopping with meal plans", value=False)
    verbosity = st.selectbox("Answer verbosity", ["concise", "balanced", "detailed"], index=1)
    st.markdown("---")
    st.header("History")
    if "history" not in st.session_state:
        st.session_state.history = []
    if st.session_state.history:
        for i, entry in enumerate(reversed(st.session_state.history[-8:]), 1):
            st.markdown(f"**{entry['time']}** — {shorten(entry['query'], width=50)}")
            if st.button(f"Load #{i}", key=f"load_{i}"):
                st.session_state.prefill = entry["query"]
    else:
        st.info("No history yet — ask something to get started.")
    st.markdown("---")
    if st.button("Clear history"):
        st.session_state.history = []
        st.experimental_rerun()

# ---------- Helper renderers ----------
def render_markdown_response(text: str):
    """Render the main textual response as markdown for readability."""
    if not text:
        st.info("No textual response.")
        return
    # Allow the AI response to include markdown (it already contains bold / lists)
    st.markdown(text)

def render_shopping_list(shopping_obj):
    """Render shopping list object: ingredients list, stores, price comparison.

    This implementation avoids using Styler.hide_index() for compatibility across pandas versions.
    """
    if not shopping_obj:
        st.info("No shopping list returned.")
        return

    ingredients = shopping_obj.get("ingredients") or []
    stores = shopping_obj.get("stores") or []
    prices = shopping_obj.get("price_comparison") or {}

    st.subheader("🛒 Shopping List")
    if ingredients:
        cols = st.columns([3, 1])
        with cols[0]:
            st.markdown("**Ingredients**")
            # Display each ingredient on its own line if the list is long, otherwise a comma-joined line
            if len(ingredients) > 10:
                for ing in ingredients:
                    st.write(f"- {ing}")
            else:
                st.write(", ".join(ingredients))
        with cols[1]:
            st.markdown("**Count**")
            st.write(len(ingredients))

    if stores:
        st.markdown("**Nearby Stores**")
        try:
            stores_df = pd.DataFrame(stores)
            st.table(stores_df)
        except Exception:
            # Fallback: show as plain text if structure varies
            for s in stores:
                st.write(s)

    if prices:
        st.markdown("**Price Comparison**")
        # Build DataFrame where rows are items and columns are stores
        rows = []
        for item, store_map in prices.items():
            row = {"Item": item}
            for store, val in store_map.items():
                row[store] = val
            rows.append(row)

        price_df = pd.DataFrame(rows)

        # Convert numeric columns to numbers where possible and format
        for col in price_df.columns:
            if col == "Item":
                continue
            try:
                price_df[col] = pd.to_numeric(price_df[col])
            except Exception:
                # Leave non-numeric entries as-is
                pass

        # Use Styler formatting if possible; otherwise show raw DataFrame
        try:
            # Format numbers to two decimal places; replace NaN with '-'
            sty = price_df.style.format("{:.2f}", na_rep="-")
            st.dataframe(sty)
        except Exception:
            st.dataframe(price_df)

# ---------- Main layout ----------
left, right = st.columns([3, 1])

with left:
    st.subheader("Ask LifePilot")
    with st.form("query_form", clear_on_submit=False):
        query = st.text_area("Your query", value=st.session_state.get("prefill", ""), height=120, placeholder="e.g. Plan a 2-day high-protein vegetarian trip to Austin.")
        submitted = st.form_submit_button("Submit ✨")

    if submitted:
        if not query.strip():
            st.warning("Please enter a query.")
        else:
            # prepare command
            orchestrator_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator.py"))
            cmd = ["python", orchestrator_path, "--query", query, "--verbosity", verbosity]
            if auto_shopping:
                cmd.append("--auto-shopping-fallback")
            if include_shopping:
                cmd.append("--include-shopping")

            st.info("Running LifePilot...")
            with st.spinner("Processing..."):
                try:
                    res = subprocess.run(cmd, text=True, capture_output=True, check=True, timeout=180)
                    stdout = res.stdout.strip()
                    stderr = res.stderr.strip()
                except subprocess.CalledProcessError as e:
                    st.error("Orchestrator failed.")
                    st.code(e.stderr or str(e), language="bash")
                    stdout = e.stdout or ""
                    stderr = e.stderr or str(e)
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    stdout = ""
                    stderr = str(e)

            # Try to parse JSON from stdout
            parsed = None
            try:
                parsed = json.loads(stdout)
            except Exception:
                # fallback: sometimes logs are printed before JSON or stdout is plain text
                # try to locate the first "{" in stdout and parse substring
                if stdout:
                    idx = stdout.find("{")
                    if idx != -1:
                        try:
                            parsed = json.loads(stdout[idx:])
                        except Exception:
                            parsed = None

            # Save to history
            st.session_state.history.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": query,
                "raw_stdout": stdout,
                "raw_stderr": stderr,
                "parsed": parsed,
            })
            st.session_state.latest = st.session_state.history[-1]

    # After submission, show pretty output if present
    if st.session_state.get("latest"):
        latest = st.session_state.latest
        parsed = latest.get("parsed")
        raw_stdout = latest.get("raw_stdout", "")
        raw_stderr = latest.get("raw_stderr", "")

        st.markdown("### ✅ Result")
        if parsed:
            # Show summary / textual response (result.result.response)
            result_obj = parsed.get("result") or {}
            main_text = result_obj.get("response") or parsed.get("result", "")
            render_markdown_response(main_text)

            # If it's a meal or shopping result, render shopping details
            if result_obj.get("type") == "meal":
                shopping_obj = result_obj.get("shopping_list") or parsed.get("result", {}).get("shopping_list")
                if shopping_obj:
                    render_shopping_list(shopping_obj)
            elif result_obj.get("type") == "shopping":
                shopping_obj = parsed.get("result", {})  # in shopping case shopping_list often is top-level in result
                # normalize
                if "shopping_list" in shopping_obj:
                    render_shopping_list(shopping_obj["shopping_list"])
                else:
                    render_shopping_list(shopping_obj)
            elif result_obj.get("type") == "travel":
                # travel itinerary: already displayed as markdown; optionally parse shopping_list if included
                shopping_obj = result_obj.get("packing_list") or result_obj.get("packing") or result_obj.get("shopping_list")
                if shopping_obj:
                    render_shopping_list(shopping_obj)

            # Metadata & logs summary
            meta = parsed.get("metadata", {})
            st.markdown("**Metadata**")
            st.write(meta)

            # Compact logs (expandable)
            with st.expander("Show internal logs (friendly)"):
                logs = parsed.get("logs", [])
                if logs:
                    for l in logs:
                        st.text(l)
                else:
                    st.write("No logs found in JSON output.")
        else:
            # Not parsed — show raw text in a friendly block
            st.warning("Could not parse structured output. Showing raw output below.")
            if raw_stdout:
                st.code(raw_stdout)
            if raw_stderr:
                st.code(raw_stderr, language="bash")

        # Downloads
        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button("Download response (.txt)", data=latest.get("raw_stdout", ""), file_name=f"lifepilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with col2:
            # If parsed exists, prefer logs from parsed JSON; otherwise fallback to stderr
            logs_download = ""
            if parsed:
                logs_download = "\n".join(parsed.get("logs", []))
            else:
                logs_download = latest.get("raw_stderr", "")
            st.download_button("Download logs (.txt)", data=logs_download, file_name="lifepilot_logs.txt")
        with col3:
            st.download_button("Download raw JSON", data=json.dumps(parsed, indent=2) if parsed else latest.get("raw_stdout", ""), file_name="lifepilot_raw.json")

with right:
    st.subheader("Logs & Debug")
    if st.session_state.get("latest"):
        parsed = st.session_state.latest.get("parsed")
        if parsed:
            with st.expander("Raw JSON"):
                st.json(parsed)
        else:
            st.info("No structured JSON output available for the last run.")
    else:
        st.info("Run a query to see logs & debug info here.")

st.markdown("---")
st.markdown("Built with ❤️ — Ask clear questions, and toggle `Include shopping` if you want shopping lists with meal plans.")
