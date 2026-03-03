from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.agent import NashAgent

app = FastAPI(title="NashAI API")

# Initialize Agent
# In production, we might want to do this lazily or in a dependency
agent = NashAgent()

from typing import List, Dict, Optional

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = []

class ChatResponse(BaseModel):
    response: dict

@app.get("/")
def read_root():
    return {"status": "ok", "message": "NashAI is running"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        result = agent.process_query(request.message, request.history)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
