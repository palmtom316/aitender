class NormSearchService:
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

        for entry in clause_index.get("entries", []):
            if entry.get("document_id") != document_id:
                continue
            if entry.get("node_type") != "clause":
                continue
            if clause_id and entry.get("label") != clause_id:
                continue

            path_labels = self._build_path_labels(entry, entry_by_label)
            if path_prefix and path_prefix not in path_labels:
                continue

            commentary_text = commentary_map.get(entry["label"], "")
            if query and not self._matches_query(entry, commentary_text, query):
                continue

            items.append(
                {
                    "label": entry["label"],
                    "title": entry["title"],
                    "page_start": entry["page_start"],
                    "page_end": entry["page_end"],
                    "summary_text": entry["summary_text"],
                    "commentary_summary": commentary_text,
                    "path_labels": path_labels,
                }
            )

        items.sort(key=lambda item: item["label"])
        return {"items": items}

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
    def _matches_query(entry: dict, commentary_text: str, query: str) -> bool:
        haystack = " ".join(
            [
                entry.get("title", ""),
                entry.get("summary_text", ""),
                commentary_text,
            ]
        ).lower()
        tokens = [token for token in query.lower().split() if token]
        return all(token in haystack for token in tokens)


norm_search_service = NormSearchService()
