from app.models.project_ai_settings import ProviderApiConfig
from app.services.project_ai_settings_service import ProjectAiSettingsService


def test_project_ai_settings_service_persists_across_reloads(tmp_path):
    state_path = tmp_path / "project-ai-settings.json"
    initial = ProjectAiSettingsService(state_path=state_path)
    initial.update_settings(
        "project-alpha",
        initial.get_settings("project-alpha").model_copy(
            update={
                "ocr": ProviderApiConfig(
                    base_url="https://ocr.example.test/extract",
                    api_key="ocr-secret",
                    model="mineru-remote",
                ),
                "analysis": ProviderApiConfig(
                    base_url="https://ai.example.test/v1",
                    api_key="ai-secret",
                    model="deepseek-chat",
                ),
            }
        ),
    )

    reloaded = ProjectAiSettingsService(state_path=state_path)
    saved = reloaded.get_settings("project-alpha")

    assert saved.ocr.base_url == "https://ocr.example.test/extract"
    assert saved.ocr.api_key == "ocr-secret"
    assert saved.analysis.model == "deepseek-chat"
