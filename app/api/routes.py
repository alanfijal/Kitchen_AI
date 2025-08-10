from fastapi import APIRouter, HTTPException
from app.api.schemas import Query, Response
from app.core.agent_builder import build_agent
from app.services.database import save_user_query

router = APIRouter()

@router.post("/ask", response_model=Response)
async def ask_question(query: Query):
    try:
        save_user_query(query.question)
        agent = build_agent(dietary_restrictions=set(query.dietary_restrictions))
        result = await agent.ainvoke({"input": query.question})
        return Response(answer=result["output"])
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
