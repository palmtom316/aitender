from app.repositories.factory import get_norm_structure_repository
from app.repositories.norm_structure_repository import NormStructureRepository
from app.services.norm_label_utils import label_sort_key


class NormSearchService:
    def __init__(
        self,
        structure_repository: NormStructureRepository | None = None,
    ) -> None:
        self._structure_repository = structure_repository or get_norm_structure_repository()

    def search(
        self,
        *,
        document_id: str,
        clause_index: dict,
        commentary_result: dict,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> dict:
        entry_by_label = {
            entry["label"]: entry
            for entry in clause_index.get("entries", [])
        }
        commentary_map = commentary_result.get("commentary_map", {})
        items: list[dict] = []
        commentary_items: list[dict] = []

        for entry in clause_index.get("entries", []):
            if entry.get("document_id") != document_id:
                continue
            if entry.get("node_type") != "clause":
                continue
            if clause_id and entry.get("label") != clause_id:
                continue

            path_labels = entry.get("path_labels") or self._build_path_labels(
                entry,
                entry_by_label,
            )
            if path_prefix and path_prefix not in path_labels:
                continue

            commentary_text = commentary_map.get(entry["label"], "")
            if query and not self._matches_clause_query(entry, query):
                continue

            items.append(
                {
                    "label": entry["label"],
                    "title": entry["title"],
                    "page_start": entry["page_start"],
                    "page_end": entry["page_end"],
                    "summary_text": entry["summary_text"],
                    "commentary_summary": commentary_text,
                    "content_preview": entry.get("content_preview", ""),
                    "path_labels": path_labels,
                    "tags": entry.get("tags", []),
                }
            )

        items.sort(key=lambda item: label_sort_key(item["label"]))
        if query:
            for entry in clause_index.get("entries", []):
                if entry.get("document_id") != document_id:
                    continue
                if entry.get("node_type") != "clause":
                    continue
                if clause_id and entry.get("label") != clause_id:
                    continue

                path_labels = entry.get("path_labels") or self._build_path_labels(
                    entry,
                    entry_by_label,
                )
                if path_prefix and path_prefix not in path_labels:
                    continue

                commentary_text = commentary_map.get(entry["label"], "")
                if not commentary_text or not self._matches_commentary_query(
                    commentary_text,
                    query,
                ):
                    continue

                commentary_items.append(
                    {
                        "label": entry["label"],
                        "title": entry["title"],
                        "page_start": entry["page_start"],
                        "page_end": entry["page_end"],
                        "summary_text": entry["summary_text"],
                        "commentary_summary": commentary_text,
                        "content_preview": entry.get("content_preview", ""),
                        "path_labels": path_labels,
                        "tags": entry.get("tags", []),
                    }
                )

        commentary_items.sort(key=lambda item: label_sort_key(item["label"]))
        commentary_label_set = {item["label"] for item in items}
        commentary_items = [
            item for item in commentary_items if item["label"] not in commentary_label_set
        ]
        return {"items": items, "commentary_items": commentary_items}

    def search_document(
        self,
        *,
        document_id: str,
        query: str | None = None,
        clause_id: str | None = None,
        path_prefix: str | None = None,
    ) -> dict | None:
        items = self._structure_repository.search_clause_results(
            document_id=document_id,
            query=query,
            clause_id=clause_id,
            path_prefix=path_prefix,
        )
        if items is None:
            return None
        commentary_items = (
            self._structure_repository.search_commentary_results(
                document_id=document_id,
                query=query,
                clause_id=clause_id,
                path_prefix=path_prefix,
            )
            if query
            else []
        )
        normalized = []
        for item in items:
            normalized.append(
                {
                    "label": item.get("label", ""),
                    "title": item.get("title", ""),
                    "page_start": item.get("page_start"),
                    "page_end": item.get("page_end"),
                    "summary_text": item.get("summary_text", ""),
                    "commentary_summary": item.get("commentary_summary", ""),
                    "content_preview": item.get("content_preview", ""),
                    "path_labels": list(item.get("path_labels") or []),
                    "tags": list(item.get("tags") or []),
                }
            )
        normalized.sort(key=lambda item: label_sort_key(item["label"]))
        normalized_commentary = []
        for item in commentary_items or []:
            normalized_commentary.append(
                {
                    "label": item.get("label", ""),
                    "title": item.get("title", ""),
                    "page_start": item.get("page_start"),
                    "page_end": item.get("page_end"),
                    "summary_text": item.get("summary_text", ""),
                    "commentary_summary": item.get("commentary_summary", ""),
                    "content_preview": item.get("content_preview", ""),
                    "path_labels": list(item.get("path_labels") or []),
                    "tags": list(item.get("tags") or []),
                }
            )
        normalized_commentary.sort(key=lambda item: label_sort_key(item["label"]))
        commentary_label_set = {item["label"] for item in normalized}
        normalized_commentary = [
            item
            for item in normalized_commentary
            if item["label"] not in commentary_label_set
        ]
        return {
            "items": normalized,
            "commentary_items": normalized_commentary,
        }

    def _build_path_labels(
        self,
        entry: dict,
        entry_by_label: dict[str, dict],
    ) -> list[str]:
        path_labels: list[str] = []
        current = entry

        while current:
            path_labels.append(current["label"])
            parent_label = current.get("parent_label")
            current = entry_by_label.get(parent_label) if parent_label else None

        return list(reversed(path_labels))

    @staticmethod
    def _matches_clause_query(entry: dict, query: str) -> bool:
        haystack = " ".join(
            [
                entry.get("title", ""),
                entry.get("summary_text", ""),
                entry.get("content_preview", ""),
            ]
        ).lower()
        tokens = [token for token in query.lower().split() if token]
        return all(token in haystack for token in tokens)

    @staticmethod
    def _matches_commentary_query(commentary_text: str, query: str) -> bool:
        haystack = commentary_text.lower()
        tokens = [token for token in query.lower().split() if token]
        return all(token in haystack for token in tokens)

norm_search_service = NormSearchService()
