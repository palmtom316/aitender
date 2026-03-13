import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models.norm_clause_entry import NormClauseEntry
from app.models.norm_commentary_entry import NormCommentaryEntry
from app.models.project_ai_settings import ProviderApiConfig


class NormAIStructurer:
    def generate(
        self,
        *,
        document_id: str,
        markdown_text: str,
        page_texts: list[dict],
        baseline_clause_index: dict,
        config: ProviderApiConfig,
    ) -> tuple[dict, dict]:
        payload = self._post_json(
            url=self._normalize_ai_url(config.base_url),
            api_key=config.api_key,
            body=self._build_request_body(
                model=config.model,
                document_id=document_id,
                markdown_text=markdown_text,
                page_texts=page_texts,
                baseline_clause_index=baseline_clause_index,
            ),
        )
        data = self._extract_json_payload(payload)
        clause_index = self._normalize_clause_index(document_id, data, baseline_clause_index)
        commentary_result = self._normalize_commentary_result(document_id, data)
        return clause_index, commentary_result

    def _build_request_body(
        self,
        *,
        model: str,
        document_id: str,
        markdown_text: str,
        page_texts: list[dict],
        baseline_clause_index: dict,
    ) -> dict:
        return {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You convert OCR markdown of Chinese engineering norms into "
                        "structured JSON. Return valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "task": (
                                "Use the provided baseline clause tree as the canonical "
                                "structure. Improve summaries, add tags, and add commentary "
                                "entries when the OCR text contains commentary-like content. "
                                "Return JSON with keys clause_index and commentary_result. "
                                "For each clause_index entry include label, title, node_type, "
                                "parent_label, page_start, page_end, summary_text, "
                                "commentary_summary, tags. For commentary_result include "
                                "entries, commentary_map, summary_text, errors."
                            ),
                            "document_id": document_id,
                            "markdown_text": markdown_text,
                            "page_texts": page_texts,
                            "baseline_clause_index": baseline_clause_index,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        }

    def _post_json(
        self,
        *,
        url: str,
        api_key: str,
        body: dict,
    ) -> dict:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"

        request = Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"AI API request failed: {exc.code} {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"AI API request failed: {exc.reason}") from exc

    @staticmethod
    def _normalize_ai_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")
        if normalized.endswith("/chat/completions"):
            return normalized
        return f"{normalized}/chat/completions"

    def _extract_json_payload(self, payload: dict) -> dict:
        if "clause_index" in payload and "commentary_result" in payload:
            return payload

        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("AI API response is missing choices")

        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict)
            ]
            content = "".join(parts)

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("AI API response content is empty")

        return json.loads(self._strip_json_fence(content))

    @staticmethod
    def _strip_json_fence(content: str) -> str:
        text = content.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return text

    def _normalize_clause_index(
        self,
        document_id: str,
        payload: dict,
        baseline_clause_index: dict,
    ) -> dict:
        raw_clause_index = payload.get("clause_index") or {}
        raw_entries = raw_clause_index.get("entries") or baseline_clause_index.get("entries", [])
        baseline_by_label = {
            entry["label"]: entry
            for entry in baseline_clause_index.get("entries", [])
        }
        entries: list[dict] = []

        for raw_entry in raw_entries:
            label = str(raw_entry.get("label", "")).strip()
            if not label:
                continue
            baseline = baseline_by_label.get(label, {})
            entry = NormClauseEntry.model_validate(
                {
                    "document_id": document_id,
                    "label": label,
                    "title": raw_entry.get("title", baseline.get("title", "")),
                    "node_type": raw_entry.get("node_type", baseline.get("node_type", "clause")),
                    "parent_label": raw_entry.get(
                        "parent_label",
                        baseline.get("parent_label"),
                    ),
                    "path_labels": raw_entry.get(
                        "path_labels",
                        baseline.get("path_labels", []),
                    ),
                    "page_start": raw_entry.get(
                        "page_start",
                        baseline.get("page_start"),
                    ),
                    "page_end": raw_entry.get("page_end", baseline.get("page_end")),
                    "summary_text": raw_entry.get(
                        "summary_text",
                        baseline.get("summary_text", ""),
                    ),
                    "commentary_summary": raw_entry.get(
                        "commentary_summary",
                        baseline.get("commentary_summary", ""),
                    ),
                    "tags": raw_entry.get("tags", baseline.get("tags", [])),
                }
            )
            entries.append(entry.model_dump())

        tree = raw_clause_index.get("tree")
        if not isinstance(tree, list):
            tree = baseline_clause_index.get("tree", [])

        return {
            "summary_text": str(raw_clause_index.get("summary_text", "")),
            "entries": entries,
            "tree": tree,
        }

    def _normalize_commentary_result(
        self,
        document_id: str,
        payload: dict,
    ) -> dict:
        raw_commentary = payload.get("commentary_result") or {}
        entries: list[dict] = []
        for raw_entry in raw_commentary.get("entries", []):
            entry = NormCommentaryEntry.model_validate(
                {
                    "document_id": document_id,
                    "label": raw_entry.get("label", ""),
                    "title": raw_entry.get("title", raw_entry.get("label", "")),
                    "node_type": raw_entry.get("node_type", "clause"),
                    "parent_label": raw_entry.get("parent_label"),
                    "page_start": raw_entry.get("page_start"),
                    "page_end": raw_entry.get("page_end"),
                    "commentary_text": raw_entry.get("commentary_text", ""),
                    "summary_text": raw_entry.get("summary_text", ""),
                    "tags": raw_entry.get("tags", []),
                }
            )
            entries.append(entry.model_dump())

        commentary_map = {
            str(label): str(text)
            for label, text in dict(raw_commentary.get("commentary_map", {})).items()
        }
        return {
            "summary_text": str(raw_commentary.get("summary_text", "")),
            "entries": entries,
            "commentary_map": commentary_map,
            "errors": [str(item) for item in raw_commentary.get("errors", [])],
        }


norm_ai_structurer = NormAIStructurer()
