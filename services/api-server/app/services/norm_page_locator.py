class NormPageLocator:
    def locate(
        self,
        *,
        label: str,
        title: str,
        page_texts: list[dict],
    ) -> tuple[int | None, int | None]:
        for page in page_texts:
            text = str(page.get("text", ""))
            if label in text or title in text:
                page_number = int(page["page"])
                return page_number, page_number

        return None, None
