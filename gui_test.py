import streamlit as st
from agent import Retriever, DietaryRestrictions
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient
import os 


load_dotenv()




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
    try:
        retriever = Retriever()
        retriever.dietary_restrictions = set(st.session_state.dietary_preferences)
        agent = retriever.set_agent()
        if agent is None:
            raise ValueError("Agent creation failed in Retriever.set_agent()")
        return agent
    except Exception as e:
        st.error(f"Error creating agent: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

def main():
    st.title("Recipe Assistant")
    with st.sidebar:
        st.header("Dietary Preferences")
        available_restrictions = [restriction.value for restriction in DietaryRestrictions]

        if "dietary_preferences" not in st.session_state:
            st.session_state.dietary_preferences = []

        selected_restrictions = st.multiselect(
            "Select your dietary restrictions",
            options=available_restrictions,
            default=st.session_state.dietary_preferences
        )

        if selected_restrictions != st.session_state.dietary_preferences:
            st.session_state.dietary_preferences = selected_restrictions
            get_agent.clear()

        
    agent_exec = get_agent()
    if agent_exec is None:
        st.error("Failed to initialize the agent. Please check the error messages above and your configuration.")
        return

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me anything about recipes!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                collection.insert_one({"question": prompt})
                result = agent_exec.invoke({"input": prompt})
                response = result["output"]
                st.markdown(response)
                
                if 'intermediate_steps' in result:
                    with st.expander("See reasoning steps"):
                        for step in result['intermediate_steps']:
                            st.write(step)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.error(f"Traceback: {traceback.format_exc()}")
                st.session_state.messages.append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
