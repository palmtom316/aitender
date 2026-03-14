from __future__ import annotations

import re


NUMERIC_LABEL_PATTERN = re.compile(r"^\d+(?:\.\d+)*$")
APPENDIX_LABEL_PATTERN = re.compile(r"^附录([A-ZＡ-Ｚ])$")
NUMERIC_HEADING_PATTERN = re.compile(r"^(?P<label>\d+(?:\.\d+)*)\s+(?P<title>.+)$")
APPENDIX_HEADING_PATTERN = re.compile(r"^(?P<label>附录[A-ZＡ-Ｚ])(?:\s+(?P<title>.+))?$")
SPECIAL_ROOT_ORDER = {
    "本规范用词说明": 0,
    "引用标准名录": 1,
}


def parse_heading_text(text: str) -> tuple[str, str, str, str | None] | None:
    stripped = text.strip()
    if not stripped:
        return None

    numeric = NUMERIC_HEADING_PATTERN.match(stripped)
    if numeric:
        label = numeric.group("label")
        title = numeric.group("title")
        node_type = "section" if "." in label else "chapter"
        parent_label = label.split(".")[0] if "." in label else None
        return label, title, node_type, parent_label

    appendix = APPENDIX_HEADING_PATTERN.match(stripped)
    if appendix:
        label = appendix.group("label")
        title = appendix.group("title") or label
        return label, title, "appendix", None

    return stripped, stripped, "other", None


def label_sort_key(label: str) -> tuple:
    normalized = str(label or "").strip()
    if not normalized:
        return (9, "")
    if NUMERIC_LABEL_PATTERN.match(normalized):
        return (0, *[int(part) for part in normalized.split(".")])

    appendix = APPENDIX_LABEL_PATTERN.match(normalized)
    if appendix:
        appendix_id = appendix.group(1).upper().translate(str.maketrans("ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ", "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        return (1, appendix_id)

    return (2, SPECIAL_ROOT_ORDER.get(normalized, 99), normalized)
