import os
import subprocess
import streamlit as st

st.set_page_config(page_title="🌟 LifePilot", layout="wide")
st.title("🌟 LifePilot – AI Personal Assistant")

query = st.text_input("Ask LifePilot anything (meal, shopping, travel):")

if st.button("Submit"):
    if not query.strip():
        st.warning("Please enter a query.")
    else:
        try:
            # Absolute path to orchestrator.py
            orchestrator_path = os.path.join(os.path.dirname(__file__), "..", "orchestrator.py")
            orchestrator_path = os.path.abspath(orchestrator_path)

            # Run orchestrator with subprocess
            # --auto-shopping-fallback ensures ShoppingAgent can generate a meal plan if memory is empty
            result = subprocess.run(
                ["python", orchestrator_path, "--query", query, "--auto-shopping-fallback"],
                text=True,
                capture_output=True,
                check=True
            )

            # Display raw logs + AI response
            st.subheader("📄 Logs & Response")
            st.text(result.stdout)

        except subprocess.CalledProcessError as e:
            st.error("⚠️ An error occurred while running LifePilot:")
            st.text(e.stderr or str(e))
