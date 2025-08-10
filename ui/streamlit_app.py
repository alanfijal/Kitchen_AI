import streamlit as st
import requests
import traceback
from app.api.schemas import DietaryRestrictions 

# Configuration
API_URL = "http://localhost:8000/api/ask"

st.set_page_config(page_title="ChefAI", layout="wide")
st.title("🍳 ChefAI Recipe Assistant")

# --- Sidebar for Preferences ---
with st.sidebar:
    st.header("Dietary Preferences")
    available_restrictions = [restriction.value for restriction in DietaryRestrictions]

    if "dietary_preferences" not in st.session_state:
        st.session_state.dietary_preferences = []

    selected_restrictions = st.multiselect(
        "Select your dietary restrictions",
        options=available_restrictions,
        default=st.session_state.dietary_preferences,
        key="multiselect_restrictions"
    )
    st.session_state.dietary_preferences = selected_restrictions

# --- Chat Interface ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! How can I help you in the kitchen today?"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me for a recipe!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                payload = {
                    "question": prompt,
                    "dietary_restrictions": st.session_state.dietary_preferences
                }
                
                response = requests.post(API_URL, json=payload)
                response.raise_for_status()  # Raises an exception for bad status codes
                
                answer = response.json()["answer"]
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except requests.exceptions.RequestException as e:
                error_message = f"Could not connect to the backend. Please ensure the API is running. Error: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"An unexpected error occurred: {str(e)}"
                st.error(error_message)
                st.error(f"Traceback: {traceback.format_exc()}")
                st.session_state.messages.append({"role": "assistant", "content": error_message})