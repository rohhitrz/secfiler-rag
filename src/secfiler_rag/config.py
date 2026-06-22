from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    OPENAI_API_KEY:str
    QDRANT_URL:str="http://localhost:6333"
    QDRANT_API_KEY:str | None = None

settings=Settings()