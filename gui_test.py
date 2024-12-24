import streamlit as st
from agent import Retriever, DietaryRestriciton
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

# MongoDB config
cosmos_mongo_uri = os.getenv("COSMOS_MONGO_URI")
database_name = os.getenv("DATABASE_NAME")
collection_name = os.getenv("COLLECTION_NAME")

client = MongoClient(cosmos_mongo_uri)
db = client[database_name]
collection = db[collection_name]

if "messages" not in st.session_state:
    st.session_state.messages = []
if "dietary_restrictions" not in st.session_state:
    st.session_state.dietary_restrictions = []

@st.cache_resource
def get_agent():
    """
    This function is cached so that we don't rebuild the agent on every rerun 
    unless the dietary restrictions or other critical variables change.
    """
    try:
        retriever = Retriever()

        # If the user has selected restrictions in the sidebar, set them now:
        if st.session_state.dietary_restrictions:
            restrictions_str = ", ".join(st.session_state.dietary_restrictions)
            set_msg = retriever.set_dietary_restrictions(restrictions_str)
            # Optional: Show debugging info in Streamlit:
            st.write(f"DEBUG: {set_msg}")

        agent = retriever.set_agent()
        if agent is None:
            raise ValueError("Agent creation failed in Retriever.set_agent()")

        return retriever, agent
    except Exception as e:
        st.error(f"Error creating agent: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None, None

def main():
    st.title("Recipe Assistant")

    with st.sidebar:
        st.header("Dietary Preferences")
        available_restrictions = [restriction.value for restriction in DietaryRestriciton]

        # Let the user pick multiple dietary restrictions
        selected_restrictions = st.multiselect(
            "Select your dietary restrictions:",
            options=available_restrictions,
            default=st.session_state.dietary_restrictions
        )

        # If the user changed them, update session state and clear the cached agent
        if selected_restrictions != st.session_state.dietary_restrictions:
            st.session_state.dietary_restrictions = selected_restrictions
            # Force re-init of the agent next run
            get_agent.clear()

    # Build or fetch the cached agent
    retriever, agent_exec = get_agent()
    if agent_exec is None:
        st.error("Failed to initialize the agent. Please check the error messages above.")
        return

    # Show conversation so far
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input box for user
    if prompt := st.chat_input("Ask me anything about recipes!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Now we pass the prompt to the agent
        with st.chat_message("assistant"):
            try:
                # Save the user query to Mongo (optional)
                collection.insert_one({"question": prompt})

                # The agent processes the prompt
                result = agent_exec.invoke({"input": prompt})
                response = result["output"]
                st.markdown(response)

                # Optionally show reasoning steps
                if 'intermediate_steps' in result:
                    with st.expander("See reasoning steps"):
                        for step in result['intermediate_steps']:
                            st.write(step)

                # Add the agent's reply to our conversation
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_message = "An error occurred while processing your request. Possibly dietary restrictions filtering or agent error."
                st.error(error_message)
                # Provide technical details for debugging
                st.error(f"Technical details: {str(e)}")
                st.error(f"Traceback: {traceback.format_exc()}")
                st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
