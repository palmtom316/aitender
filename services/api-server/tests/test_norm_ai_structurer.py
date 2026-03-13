from app.models.project_ai_settings import ProviderApiConfig
from app.services.norm_ai_structurer import NormAIStructurer


class FakeNormAIStructurer(NormAIStructurer):
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def _post_json(self, **kwargs) -> dict:
        return self.payload


def test_norm_ai_structurer_normalizes_openai_style_json_response():
    structurer = FakeNormAIStructurer(
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"clause_index":{"summary_text":"Doc summary","entries":['
                            '{"label":"1","title":"General","node_type":"chapter",'
                            '"parent_label":null,"page_start":1,"page_end":1,'
                            '"summary_text":"General summary","commentary_summary":"",'
                            '"tags":[]},{"label":"1.0.1","title":"Clause text",'
                            '"node_type":"clause","parent_label":"1","page_start":1,'
                            '"page_end":1,"summary_text":"Clause summary",'
                            '"commentary_summary":"Commentary summary",'
                            '"tags":["mandatory"]}],"tree":[]},'
                            '"commentary_result":{"summary_text":"Commentary doc summary",'
                            '"entries":[{"label":"1.0.1","title":"1.0.1",'
                            '"node_type":"clause","parent_label":"1","page_start":1,'
                            '"page_end":1,"commentary_text":"Detailed commentary",'
                            '"summary_text":"Commentary summary","tags":["mandatory"]}],'
                            '"commentary_map":{"1.0.1":"Detailed commentary"},"errors":[]}}'
                        )
                    }
                }
            ]
        }
    )

    clause_index, commentary_result = structurer.generate(
        document_id="doc-1",
        markdown_text="# 1 General\n1.0.1 Clause text",
        page_texts=[{"page": 1, "text": "1 General 1.0.1 Clause text"}],
        baseline_clause_index={
            "entries": [
                {
                    "document_id": "doc-1",
                    "label": "1",
                    "title": "General",
                    "node_type": "chapter",
                    "parent_label": None,
                    "path_labels": ["1"],
                    "page_start": 1,
                    "page_end": 1,
                    "summary_text": "General",
                    "commentary_summary": "",
                    "tags": [],
                },
                {
                    "document_id": "doc-1",
                    "label": "1.0.1",
                    "title": "Clause text",
                    "node_type": "clause",
                    "parent_label": "1",
                    "path_labels": ["1", "1.0.1"],
                    "page_start": 1,
                    "page_end": 1,
                    "summary_text": "Clause text",
                    "commentary_summary": "",
                    "tags": [],
                },
            ],
            "tree": [],
        },
        config=ProviderApiConfig(
            base_url="https://ai.example.test/v1",
            api_key="secret",
            model="deepseek-chat",
        ),
    )

    assert clause_index["summary_text"] == "Doc summary"
    assert clause_index["entries"][1]["tags"] == ["mandatory"]
    assert clause_index["entries"][1]["commentary_summary"] == "Commentary summary"
    assert commentary_result["commentary_map"]["1.0.1"] == "Detailed commentary"
