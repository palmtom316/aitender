class NormStructureValidator:
    def validate(
        self,
        *,
        clause_index: dict,
        commentary_result: dict,
    ) -> dict:
        errors: list[str] = []

        labels = {
            entry["label"]
            for entry in clause_index.get("entries", [])
            if entry.get("node_type") == "clause"
        }
        tree_labels = self._collect_clause_labels_from_tree(clause_index.get("tree", []))

        for clause_id in labels - tree_labels:
            errors.append(f"Clause tree is missing clause entry: {clause_id}")
        for clause_id in tree_labels - labels:
            errors.append(f"Clause tree contains unmapped clause entry: {clause_id}")

        for clause_id in commentary_result.get("commentary_map", {}):
            if clause_id not in labels:
                errors.append(f"Commentary references unknown clause: {clause_id}")

        return {"ok": not errors, "errors": errors}

    def _collect_clause_labels_from_tree(self, nodes: list[dict]) -> set[str]:
        labels: set[str] = set()
        for node in nodes:
            label = node.get("label")
            if label and label.count(".") >= 2:
                labels.add(label)
            labels.update(self._collect_clause_labels_from_tree(node.get("children", [])))
        return labels
