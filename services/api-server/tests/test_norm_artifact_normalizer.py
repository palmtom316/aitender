import json
from pathlib import Path

from app.services.norm_artifact_normalizer import NormArtifactNormalizer
from app.services.norm_artifact_store import NormArtifactStore


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "norm_artifacts"


def test_normalizer_converts_mineru_payload_to_shared_schema():
    payload = json.loads((FIXTURES_DIR / "mineru.json").read_text())

    normalized = NormArtifactNormalizer().normalize(payload)

    assert normalized.provider == "mineru"
    assert normalized.markdown_text == "# 1 General\nSample clause"
    assert [page.model_dump() for page in normalized.page_texts] == [
        {"page": 1, "text": "1 General Sample clause"}
    ]
    assert normalized.layout_payload == {
        "pages": [{"page": 1, "text": "1 General Sample clause"}]
    }
    assert normalized.metadata == {"source_path": "/tmp/mineru/norm.pdf"}


def test_normalizer_converts_commercial_payload_to_shared_schema():
    payload = json.loads((FIXTURES_DIR / "commercial.json").read_text())

    normalized = NormArtifactNormalizer().normalize(payload)

    assert normalized.provider == "commercial"
    assert normalized.markdown_text == "# 2 Scope\nCommercial sample"
    assert [page.model_dump() for page in normalized.page_texts] == [
        {"page": 2, "text": "2 Scope Commercial sample"}
    ]
    assert normalized.layout_payload == {
        "pages": [{"page": 2, "text": "2 Scope Commercial sample"}]
    }
    assert normalized.metadata == {
        "source_path": "/tmp/commercial/norm.pdf",
        "trace_id": "trace-1",
    }


def test_artifact_store_persists_markdown_and_debug_json(tmp_path: Path):
    payload = json.loads((FIXTURES_DIR / "mineru.json").read_text())
    normalized = NormArtifactNormalizer().normalize(payload)

    store = NormArtifactStore(root_directory=tmp_path)
    stored = store.save(
        document_id="doc-1",
        version_id="doc-version-1",
        artifacts=normalized,
    )

    assert stored.markdown_path.exists()
    assert stored.layout_json_path.exists()
    assert stored.metadata_json_path.exists()
    assert stored.markdown_path.read_text() == "# 1 General\nSample clause"
    assert json.loads(stored.layout_json_path.read_text()) == {
        "pages": [{"page": 1, "text": "1 General Sample clause"}]
    }
