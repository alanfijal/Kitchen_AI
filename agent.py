from dotenv import load_dotenv 
import os
from prompt import prompt, question_examples

# langchain
from langchain import hub
from langchain_core.tools import create_retriever_tool
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain.agents import Tool, AgentExecutor, create_openai_tools_agent
from langchain.globals import set_debug, set_verbose
from langchain.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.tools import tool
from langchain_qdrant import Qdrant

from tavily import TavilyClient
from qdrant_client import QdrantClient

from pymongo import MongoClient

from typing import List, Dict
from enum import Enum

load_dotenv()

class DietaryRestriciton(Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten-free"
    DAIRY_FREE = "dairy-free"
    NUT_FREE = "nut-free"
    HALAL = "halal"
    KOSHER = "kosher"

# MongoDB setup
cosmos_mongo_uri = os.getenv("COSMOS_MONGO_URI")
database_name = os.getenv("DATABASE_NAME")
collection_name = os.getenv("COLLECTION_NAME")

client = MongoClient(cosmos_mongo_uri)
db = client[database_name]
collection = db[collection_name]

class Retriever:
    def __init__(self):
        self.smart_llm = AzureChatOpenAI(
            model="gpt-4o-mini",
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            temperature=0.2,
            streaming=True,
            api_version=os.getenv("OPENAI_API_VERSION")
        )
        self.embeddings_model = AzureOpenAIEmbeddings(
            model='text-embedding-ada-002',
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_ADA"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT_ADA"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION_ADA"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY_ADA")
        )
        self.dietary_restrictions = set()
        set_debug(True)
        set_verbose(True)

    def prompt_template(self):
        prompt_format = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant specializing in retrieving and explaining recipes."),
            ("user", "{question}"),
            ("assistant", "{answer}")
        ])

        few_shots_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=prompt_format,
            examples=question_examples
        )

        # Merge your base prompt lines + few shots
        instructions = ChatPromptTemplate.from_messages(prompt + [few_shots_prompt])

        # Now you must provide a value for `dietary_restrictions`:
        filled_instructions = instructions.format(
            dietary_restrictions=", ".join(self.dietary_restrictions) or "None set"
        )

        # Alternatively, you could do partial variables:
        # instructions = ChatPromptTemplate.from_messages(
        #     prompt + [few_shots_prompt],
        #     partial_variables={
        #         "dietary_restrictions": ", ".join(self.dietary_restrictions) or "None set"
        #     }
        # )
        # filled_instructions = instructions.format()

        # Then feed `filled_instructions` into your final prompt:
        base_prompt = hub.pull("langchain-ai/openai-functions-template")
        # partial() merges your final instructions with the base template
        prompt_template = base_prompt.partial(instructions=filled_instructions)
        return prompt_template

    
    def set_dietary_restrictions(self, restrictions: str) -> str:
        """Updates the local set of dietary restrictions based on the user's selection."""
        try:
            if not restrictions or restrictions.isspace():
                self.dietary_restrictions = set()
                return "Dietary restrictions cleared"
            
            # Split on commas, normalize to lowercase
            restrictions_list = [r.strip().lower() for r in restrictions.split(',')]

            valid_restrictions = {
                r for r in restrictions_list
                if r in [v.value for v in DietaryRestriciton]
            }

            self.dietary_restrictions = valid_restrictions

            return f"Successfully set dietary restrictions: {', '.join(valid_restrictions)}"
        
        except Exception as e:
            return f"Error setting dietary restrictions: {str(e)}"

    def set_qdrant_tool(self, collection_name: str):
        """Sets up the Qdrant search tool for retrieving documents from the vector DB."""
        qdrant_client = QdrantClient("localhost", port=6333)
        qdrant = Qdrant(
            client=qdrant_client,
            collection_name=collection_name,
            embeddings=self.embeddings_model
        )
        base_retriever = qdrant.as_retriever()
        
        return Tool(
            name="qdrant_search",
            func=base_retriever.get_relevant_documents,
            description="Searches the Qdrant vector database for relevant recipe information."
        )

    def set_web_search_tool(self):
        """Sets up the Tavily web search tool (if you need to search the web)."""
        tavily_key = os.getenv("TAVILY_API_KEY")
        tavily_client = TavilyClient(api_key=tavily_key)

        def tavily_search(query: str) -> str:
            try:
                search_result = tavily_client.search(query=query, search_depth="basic")
                formatted = "\n".join([
                    f"- {res['title']}: {res['content']}"
                    for res in search_result['results'][:3]
                ])
                return formatted
            except Exception as e:
                return f"An error occurred during the web search: {str(e)}"

        return Tool(
            name="web_search",
            func=tavily_search,
            description="Searches the web for additional recipe information and cooking tips using Tavily."
        )
    
    def set_mongo_tool(self):
        """Retrieves the user's favorite recipes from MongoDB."""
        def retrieve_history(query: str = None) -> list[str]:
            recipes = []
            for item in collection.find():
                recipes.append(item["question"])
            return recipes
        
        return Tool(
            name="retrieve_history",
            func=retrieve_history,
            description="Retrieves the user's favorite recipes from MongoDB."
        )

    def set_agent(self):
        """Build the agent with all the relevant tools and the updated prompt template."""
        qdrant_tool = self.set_qdrant_tool(collection_name=os.getenv("QDRANT_COLLECTION_NAME"))
        web_search_tool = self.set_web_search_tool()
        mongo_tool = self.set_mongo_tool()

        # This function allows the LLM to set the restrictions itself if it calls "set_dietary_restrictions"
        dietary_tool = Tool(
            name="set_dietary_restrictions",
            func=self.set_dietary_restrictions,
            description="Sets dietary restrictions for recipe filtering based on the user's preferences"
        )

        tools = [qdrant_tool, web_search_tool, mongo_tool, dietary_tool]

        # Get final prompt template (with the updated dietary restrictions notice)
        final_prompt = self.prompt_template()

        # Create the agent using that final prompt
        agent = create_openai_tools_agent(
            llm=self.smart_llm,
            tools=tools,
            prompt=final_prompt
        )
        return AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=False, verbose=True)


if __name__ == "__main__":
    retriever = Retriever()
    # Example: Manually set some dietary restrictions here just to test:
    # retriever.set_dietary_restrictions("vegan, gluten-free")
    agent = retriever.set_agent()

    # Try an example query
    response = agent.invoke({"input": "What is the recipe for a chocolate cake?"})
    print("Agent Response:", response["output"])
