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
        commentary_map = dict(commentary_result.get("commentary_map", {}) or {})
        for clause_id in commentary_map.keys():
            if clause_id not in clause_labels:
                errors.append(f"Commentary references unknown clause: {clause_id}")

        stats = {
            "entry_count": len(entries),
            "tree_node_count": len(tree_labels),
            "clause_count": len(clause_labels),
            "commentary_map_count": len(commentary_map),
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

