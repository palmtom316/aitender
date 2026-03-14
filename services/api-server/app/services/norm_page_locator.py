from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class NormLocateRequest:
    label: str
    title: str


class NormPageLocator:
    def locate(
        self,
        *,
        label: str,
        title: str,
        page_texts: list[dict],
        page_min: int | None = None,
        page_max: int | None = None,
    ) -> tuple[int | None, int | None]:
        ranges = self.locate_many(
            requests=[NormLocateRequest(label=label, title=title)],
            page_texts=page_texts,
            page_min=page_min,
            page_max=page_max,
        )
        return ranges.get(label, (None, None))

    def locate_many(
        self,
        *,
        requests: list[NormLocateRequest],
        page_texts: list[dict],
        page_min: int | None = None,
        page_max: int | None = None,
    ) -> dict[str, tuple[int | None, int | None]]:
        """
        Locate clause/heading pages in-order and infer page_end using the next start page.

        This is a best-effort heuristic for scanned PDFs without bbox:
        - Start pages are found by matching label/title candidates against per-page OCR text.
        - End pages are inferred as the page before the next start (or same page if equal).
        """
        bounded_pages = self._bounded_pages(page_texts, page_min=page_min, page_max=page_max)
        bounded_pages.sort(key=lambda item: int(item.get("page", 0)))

        start_pages: dict[str, int | None] = {}
        search_start_idx = 0

        for req in requests:
            start_pages[req.label] = self._find_start_page(
                req=req,
                pages=bounded_pages,
                start_idx=search_start_idx,
            )
            if start_pages[req.label] is not None:
                # Move the search window forward so later nodes won't match earlier pages.
                for idx in range(search_start_idx, len(bounded_pages)):
                    if int(bounded_pages[idx]["page"]) == int(start_pages[req.label]):
                        search_start_idx = idx
                        break

        ordered_labels = [req.label for req in requests]
        ranges: dict[str, tuple[int | None, int | None]] = {}

        for idx, label in enumerate(ordered_labels):
            start = start_pages.get(label)
            if start is None:
                ranges[label] = (None, None)
                continue

            next_start = None
            for j in range(idx + 1, len(ordered_labels)):
                candidate = start_pages.get(ordered_labels[j])
                if candidate is not None:
                    next_start = int(candidate)
                    break

            if next_start is None:
                end = start
            elif next_start <= start:
                end = start
            else:
                end = max(start, next_start - 1)

            ranges[label] = (start, end)

        return ranges

    @staticmethod
    def _bounded_pages(
        page_texts: list[dict],
        *,
        page_min: int | None,
        page_max: int | None,
    ) -> list[dict]:
        pages: list[dict] = []
        for page in page_texts:
            try:
                page_number = int(page.get("page"))
            except Exception:
                continue
            if page_min is not None and page_number < page_min:
                continue
            if page_max is not None and page_number > page_max:
                continue
            pages.append({"page": page_number, "text": str(page.get("text", ""))})
        return pages

    def _find_start_page(
        self,
        *,
        req: NormLocateRequest,
        pages: list[dict],
        start_idx: int,
    ) -> int | None:
        candidates = self._build_candidates(req.label, req.title)
        for idx in range(start_idx, len(pages)):
            text = str(pages[idx].get("text", ""))
            normalized = self._normalize(text)
            for candidate in candidates:
                if candidate and candidate in normalized:
                    return int(pages[idx]["page"])
        return None

    @staticmethod
    def _build_candidates(label: str, title: str) -> list[str]:
        label_norm = NormPageLocator._normalize(label)
        title_norm = NormPageLocator._normalize(title)
        title_prefix = title_norm[:24] if title_norm else ""
        return [
            label_norm,
            f"{label_norm}{title_norm}" if label_norm and title_norm else "",
            title_norm,
            title_prefix,
        ]

    @staticmethod
    def _normalize(text: str) -> str:
        # Make matching more robust against OCR spacing/punctuation.
        stripped = re.sub(r"\s+", "", text)
        return stripped.replace("：", ":")
