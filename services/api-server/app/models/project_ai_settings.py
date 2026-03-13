from pydantic import BaseModel, Field


class ProviderApiConfig(BaseModel):
    base_url: str = ""
    api_key: str = ""
    model: str = ""

    def is_configured(self) -> bool:
        return bool(self.base_url.strip() and self.model.strip())


class ProjectAiSettings(BaseModel):
    project_id: str
    ocr: ProviderApiConfig = Field(default_factory=ProviderApiConfig)
    analysis: ProviderApiConfig = Field(default_factory=ProviderApiConfig)
