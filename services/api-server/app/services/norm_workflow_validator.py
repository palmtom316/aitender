from __future__ import annotations


class NormWorkflowValidator:
    def validate(
        self,
        *,
        clause_index: dict,
        commentary_result: dict,
        expected_chapters: list[str] | None = None,
        expected_sections: list[str] | None = None,
    ) -> dict:
        errors: list[str] = []
        warnings: list[str] = []

        entries = list(clause_index.get("entries", []))
        tree = clause_index.get("tree", [])

        duplicate_clause_labels = sorted(
            {
                str(entry.get("label"))
                for entry in entries
                if entry.get("label")
                and sum(
                    1 for other in entries if other.get("label") == entry.get("label")
                )
                > 1
            }
        )
        if duplicate_clause_labels:
            errors.append(f"Duplicate clause labels: {duplicate_clause_labels}")

        labels_in_entries = {entry.get("label") for entry in entries if entry.get("label")}
        tree_labels = self._collect_labels_from_tree(tree)

        missing_from_entries = sorted(label for label in tree_labels - labels_in_entries)
        missing_from_tree = sorted(label for label in labels_in_entries - tree_labels)
        if missing_from_entries:
            errors.append(
                f"Tree nodes missing from clause_index.entries: {missing_from_entries}"
            )
        if missing_from_tree:
            errors.append(
                f"clause_index.entries contains labels not present in tree: {missing_from_tree}"
            )

        # Require the three-level structure when TOC expects sections.
        node_types = {entry.get("node_type") for entry in entries}
        if expected_sections:
            if "chapter" not in node_types:
                errors.append("clause_index.entries does not contain chapter nodes.")
            if "section" not in node_types:
                errors.append("clause_index.entries does not contain section nodes.")
            if "clause" not in node_types:
                errors.append("clause_index.entries does not contain clause nodes.")

        if expected_chapters:
            missing_chapters = [label for label in expected_chapters if label not in labels_in_entries]
            if missing_chapters:
                errors.append(f"Missing expected chapter labels from TOC: {missing_chapters}")

        if expected_sections:
            missing_sections = [label for label in expected_sections if label not in labels_in_entries]
            if missing_sections:
                errors.append(f"Missing expected section labels from TOC: {missing_sections}")

        clause_labels = {
            entry.get("label")
            for entry in entries
            if entry.get("node_type") == "clause" and entry.get("label")
        }
        for entry in entries:
            page_start = entry.get("page_start")
            page_end = entry.get("page_end")
            if (
                isinstance(page_start, int)
                and isinstance(page_end, int)
                and page_start > page_end
            ):
                errors.append(
                    f"Invalid clause page range for {entry.get('label')}: "
                    f"{page_start}>{page_end}"
                )
        commentary_map = dict(commentary_result.get("commentary_map", {}) or {})
        for clause_id in commentary_map.keys():
            if clause_id not in clause_labels:
                errors.append(f"Commentary references unknown clause: {clause_id}")

        commentary_entries = list(commentary_result.get("entries", []) or [])
        duplicate_commentary_labels = sorted(
            {
                str(entry.get("label"))
                for entry in commentary_entries
                if entry.get("label")
                and sum(
                    1
                    for other in commentary_entries
                    if other.get("label") == entry.get("label")
                )
                > 1
            }
        )
        if duplicate_commentary_labels:
            errors.append(
                f"Duplicate commentary labels: {duplicate_commentary_labels}"
            )
        commentary_clause_entries = [
            entry for entry in commentary_entries if entry.get("node_type") == "clause"
        ]
        commentary_structural_entries = [
            entry
            for entry in commentary_entries
            if entry.get("node_type") in {"chapter", "section"}
        ]
        if commentary_structural_entries and not commentary_clause_entries:
            errors.append(
                "Commentary contains structural nodes but no clause-level commentary nodes."
            )
        for entry in commentary_clause_entries:
            label = entry.get("label")
            page_start = entry.get("page_start")
            page_end = entry.get("page_end")
            if (
                isinstance(page_start, int)
                and isinstance(page_end, int)
                and page_start > page_end
            ):
                errors.append(
                    f"Invalid commentary page range for {label}: "
                    f"{page_start}>{page_end}"
                )
            if label and label not in commentary_map:
                errors.append(
                    f"Commentary clause entry is missing commentary_map text: {label}"
                )
            if not str(entry.get("commentary_text", "")).strip():
                errors.append(
                    f"Commentary clause entry is missing commentary_text: {label}"
                )

        stats = {
            "entry_count": len(entries),
            "tree_node_count": len(tree_labels),
            "clause_count": len(clause_labels),
            "commentary_map_count": len(commentary_map),
            "commentary_entry_count": len(commentary_entries),
            "commentary_clause_count": len(commentary_clause_entries),
        }

        if expected_sections and len(entries) < 30:
            warnings.append("clause_index.entries count is suspiciously low.")

        return {
            "ok": not errors,
            "errors": errors,
            "warnings": warnings,
            "stats": stats,
        }

    def _collect_labels_from_tree(self, nodes: list[dict]) -> set[str]:
        labels: set[str] = set()
        for node in nodes or []:
            label = node.get("label")
            if label:
                labels.add(label)
            labels.update(self._collect_labels_from_tree(node.get("children", [])))
        return labels
