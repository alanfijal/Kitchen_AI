from fastapi import FastAPI, HTTPException
from pydantic import BaseModel 
from agent import Retriever
import uvicorn

app = FastAPI(title="Recipe Assistant API")

#Initialise the agent that then will be wrapped into an API
retriever = Retriever()
agent = retriever.set_agent()

#Validators
class Query(BaseModel):
    question: str

class Response(BaseModel):
    answer: str

#add the post request to obtain the answer 
@app.post("/ask", response_model=Response)
async def ask_question(query: Query):
    try:
        result = agent.invoke({"input": query.question})
        return Response(answer=result["output"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#check the status of the API
@app.get("/health")
async def health_check():
    return {"status": "healthy"}



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
 

