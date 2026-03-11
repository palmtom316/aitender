from app.services.norm_structure_validator import NormStructureValidator


def test_structure_validator_accepts_matching_clause_tree_and_commentary_map():
    validator = NormStructureValidator()

    result = validator.validate(
        clause_index={
            "entries": [
                {"label": "1", "node_type": "chapter"},
                {"label": "1.0.1", "node_type": "clause"},
                {"label": "1.1", "node_type": "section"},
                {"label": "1.1.1", "node_type": "clause"},
            ],
            "tree": [
                {
                    "label": "1",
                    "children": [
                        {"label": "1.0.1", "children": []},
                        {
                            "label": "1.1",
                            "children": [{"label": "1.1.1", "children": []}],
                        },
                    ],
                }
            ],
        },
        commentary_result={
            "commentary_map": {
                "1.0.1": "Commentary for general clause.",
                "1.1.1": "Commentary for scope clause.",
            }
        },
    )

    assert result == {"ok": True, "errors": []}


def test_structure_validator_reports_unknown_commentary_clause():
    validator = NormStructureValidator()

    result = validator.validate(
        clause_index={
            "entries": [
                {"label": "1", "node_type": "chapter"},
                {"label": "1.0.1", "node_type": "clause"},
            ],
            "tree": [{"label": "1", "children": [{"label": "1.0.1", "children": []}]}],
        },
        commentary_result={
            "commentary_map": {
                "9.9.9": "Invalid clause commentary.",
            }
        },
    )

    assert result == {
        "ok": False,
        "errors": ["Commentary references unknown clause: 9.9.9"],
    }


def test_structure_validator_reports_clause_tree_mismatch():
    validator = NormStructureValidator()

    result = validator.validate(
        clause_index={
            "entries": [
                {"label": "1", "node_type": "chapter"},
                {"label": "1.0.1", "node_type": "clause"},
            ],
            "tree": [{"label": "1", "children": []}],
        },
        commentary_result={
            "commentary_map": {
                "1.0.1": "Commentary for general clause.",
            }
        },
    )

    assert result == {
        "ok": False,
        "errors": ["Clause tree is missing clause entry: 1.0.1"],
    }


def test_structure_validator_reports_tree_clause_missing_from_entries():
    validator = NormStructureValidator()

    result = validator.validate(
        clause_index={
            "entries": [
                {"label": "1", "node_type": "chapter"},
            ],
            "tree": [
                {
                    "label": "1",
                    "children": [{"label": "1.0.1", "children": []}],
                }
            ],
        },
        commentary_result={"commentary_map": {}},
    )

    assert result == {
        "ok": False,
        "errors": ["Clause tree contains unmapped clause entry: 1.0.1"],
    }
