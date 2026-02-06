from pydantic import BaseModel

class Settings(BaseModel):
    app_name: str = "Background Remover API"
    version: str = "1.0.0"

settings = Settings()