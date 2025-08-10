from fastapi import FastAPI
from app.api.routes import router as api_router 
import uvicorn 

app = FastAPI(
    title="Recipe Assistant API",
    version="1.0.0",
    description="An AI-powered assistant for recipes and kitchen management"
)

app.include_router(api_router, prefix="/api", tags=["Recipe Assistant"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Recipe Assistant API"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)