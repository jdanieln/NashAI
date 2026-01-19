from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DB_PATH: str = os.path.join("data", "nash_finance.db")
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
