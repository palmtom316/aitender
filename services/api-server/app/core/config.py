from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "aitender-api"
    environment: str = "development"


settings = Settings()
