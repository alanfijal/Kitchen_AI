import streamlit as st
from agent import Retriever, DietaryRestrictions
import traceback
from dotenv import load_dotenv
from pymongo import MongoClient
import os 
import datetime



load_dotenv()




cosmos_mongo_uri = os.getenv("COSMOS_MONGO_URI")
database_name = os.getenv("DATABASE_NAME")
collection_name = os.getenv("COLLECTION_NAME")
collection_name_saved = os.getenv("COLLECTION_NAME_SAVED")

client = MongoClient(cosmos_mongo_uri)
db = client[database_name]
collection = db[collection_name]
collection_recipes = db[collection_name_saved]

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
        
        
        saved_recipes = list(collection_recipes.find())

 
    if saved_recipes:
        recipe_titles = [(recipe.get('recipe_id'), recipe.get('query', 'Untitled Recipe')) 
                        for recipe in saved_recipes]
        selected_recipe_id = st.selectbox(
            "Select a recipe to view",
            options=[rid for rid, _ in recipe_titles],
            format_func=lambda x: next(title for rid, title in recipe_titles if rid == x),
            key="recipe_selector"
        )
        
        tab1, tab2 = st.tabs(["Chat", "Saved Recipe"])
        
        with tab1:
            display_chat_interface()
            
        with tab2:
            if selected_recipe_id:
                display_saved_recipe(selected_recipe_id)
    else:
        display_chat_interface()

def display_chat_interface():
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
                st.session_state.last_result = result
                
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
                st.error(error_message)
                st.error(f"Traceback: {traceback.format_exc()}")
                st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    if "last_result" in st.session_state and st.button("Save the recipe for later"):
        save_recipe()

def display_saved_recipe(recipe_id):
    recipe_doc = collection_recipes.find_one({"recipe_id": recipe_id})
    if recipe_doc:
        st.subheader("Original Query")
        st.write(recipe_doc['query'])
        
        st.subheader("Recipe Details")
        response = recipe_doc['recipe']['output']
        st.markdown(response)
        
        if 'intermediate_steps' in recipe_doc['recipe']:
            with st.expander("See reasoning steps"):
                for step in recipe_doc['recipe']['intermediate_steps']:
                    st.write(step)
        
        if st.button("Export to Text File"):
            recipe_text = f"""Query: {recipe_doc['query']}\n\nRecipe:\n{response}"""
            st.download_button(
                label="Download Recipe",
                data=recipe_text,
                file_name=f"recipe_{recipe_id}.txt",
                mime="text/plain"
            )

def save_recipe():
    try:
        recipe_id = str(datetime.datetime.now().timestamp())
        collection_recipes.insert_one({
            "recipe_id": recipe_id,
            "recipe": st.session_state.last_result,
            "timestamp": datetime.datetime.now(),
            "query": st.session_state.messages[-2]["content"]  
        })
        st.success("Recipe saved successfully!")
    except Exception as e:
        st.error(f"Error saving recipe: {str(e)}")


if __name__ == "__main__":
    main()
