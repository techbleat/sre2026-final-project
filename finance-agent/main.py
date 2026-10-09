"""Start with: uvicorn main:app --reload --port 9001"""
import logging
from dotenv import load_dotenv
load_dotenv()
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from openai import OpenAIError
from agent import run_agent
from auth import require_user, UserContext

app = FastAPI(title="FinanceAgent — basic banking demo")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

    @field_validator("message")
    @classmethod
    def nonempty(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank")
        return value

@app.get("/health")
def health():
    return {"status": "ok", "mock_data": True}

@app.get("/me")
def me(user: UserContext = Depends(require_user)):
    return {"user_id": user.user_id}

@app.post("/chat")
def chat(request: ChatRequest, user: UserContext = Depends(require_user)):
    try:
        # Pass user context to tools so they can call backend APIs
        return run_agent(request.message, tool_context={"user_id": user.user_id, "token": user.get("token")})
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIError as exc:
        logging.getLogger(__name__).warning("Model API request failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Model API request failed. Check your API key, model access, billing and connectivity.") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
