from dotenv import load_dotenv 
import os
from prompt import prompt, question_examples

#langchain
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

load_dotenv()


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
        set_debug(True)
        set_verbose(True)

    def prompt_template(self):
        prompt_format = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful AI assistant specialized in retrieving and explaining recipes."),
            ("user", "{question}"),
            ("assistant", "{answer}")
        ])

        few_shots_prompt = FewShotChatMessagePromptTemplate(
            example_prompt=prompt_format,
            examples=question_examples
        )

        instructions = ChatPromptTemplate.from_messages(
            prompt + [few_shots_prompt]
        )

        base_prompt = hub.pull("langchain-ai/openai-functions-template")
        prompt_template = base_prompt.partial(instructions=instructions)
        return prompt_template

    def set_qdrant_tool(self, collection_name: str):
        
        client = QdrantClient("localhost", port=6333)
        
 
        embeddings = self.embeddings_model
        
      
        qdrant = Qdrant(
            client=client,
            collection_name=collection_name,
            embeddings=embeddings
        )
        
        retriever = qdrant.as_retriever()

        return Tool(
            name="qdrant_search",
            func=retriever.get_relevant_documents,
            description="Searches the Qdrant vector database for relevant recipe information"
        )

    def set_web_search_tool(self):
        tavily_key = os.getenv("TAVILY_API_KEY")
        tavily_client = TavilyClient(api_key=tavily_key)

        def tavily_search(query: str) -> str:
            """Perform a web search using Tavily API."""
            try:
                search_result = tavily_client.search(query=query, search_depth="basic")
                formatted_result = "\n".join([f"- {result['title']}: {result['content']}" 
                                              for result in search_result['results'][:3]])
                return formatted_result
            except Exception as e:
                return f"An error occurred during the web search: {str(e)}"

        return Tool(
            name="web_search",
            func=tavily_search,
            description="Searches the web for additional recipe information and cooking tips using Tavily"
        )
    
    def set_mongo_tool(self):
        def retrieve_history(query: str = None) -> list[str]:
            recipes = []
            for item in collection.find():
                recipes.append(item["question"])
            return recipes
        
        return Tool(
            name="retrieve_history",
            func=retrieve_history,
            description="Retrieves the user's favorite recipes"
        )


    def set_agent(self):
        qdrant_tool = self.set_qdrant_tool(collection_name=os.getenv("QDRANT_COLLECTION_NAME"))
        web_search_tool = self.set_web_search_tool()
        mongo_tool = self.set_mongo_tool()

        tools = [qdrant_tool, web_search_tool, mongo_tool]

        agent = create_openai_tools_agent(self.smart_llm, tools, self.prompt_template())
        return AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=False, verbose=True)
    




    
if __name__ == "__main__":
    retriever = Retriever()
    agent = retriever.set_agent()
    agent.invoke({"input": "What is the recipe for a chocolate cake?"})
    


    



