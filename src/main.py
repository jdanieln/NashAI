from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.core.engine import NashNeuralEngine

app = FastAPI(title="NashAI API")

# Initialize Engine
# In production, we might want to do this lazily or in a dependency
engine = NashNeuralEngine()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: dict

@app.get("/")
def read_root():
    return {"status": "ok", "message": "NashAI is running"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        result = engine.process_query(request.message)
        return ChatResponse(response=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
