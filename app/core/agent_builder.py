from langchain.agents import Tool, AgentExecutor, create_openai_tools_agent
from langchain_openai import AzureChatOpenAI
from tavily import TavilyClient

from app.core.config import settings
from app.core.prompts import get_prompt_template
from app.services.vector_store import get_qdrant_retriever, get_embeddings_model
from app.services.database import retrieve_user_history

def build_agent(dietary_restrictions: set = None) -> AgentExecutor:
    """Builds and returns the LangChain agent"""
    llm = AzureChatOpenAI(
        model="gpt-4o-mini",
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT,
        temperature=0.2,
        streaming=True
    )

    embeddings = get_embeddings_model()
    prompt = get_prompt_template(dietary_restrictions)

    #Qdrant Retriever Tool
    retriever = get_qdrant_retriever(embeddings)
    qdrant_tool = Tool(
        name="recipe_search",
        func=retriever.invoke,
        description="Searches a vector database for relevant recipes and cooking information"
    )

    #Tavily
    tavily_client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    web_search_tool = Tool(
        name="web_search",
        func=lambda q: tavily_client.search(query=q, search_depth="basic"),
        description="Searches the web for additional, real-time recipe information and cooking tips"
    )

    #History Retrieval Tool
    history_tool = Tool(
        name="retrieve_history",
        func=lambda _: retrieve_user_history(),
        description="Retrieves the user's recent recipe search history"
    )

    tools = [qdrant_tool, web_search_tool, history_tool]
    agent = create_openai_tools_agent(llm, tools, prompt)

    return AgentExecutor(agent=agent, tools=tools, return_intermediate_steps=False, verbose=True)





