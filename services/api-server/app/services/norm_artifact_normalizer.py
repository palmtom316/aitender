from app.schemas.norm_artifacts import NormalizedNormArtifacts, PageText


class NormArtifactNormalizer:
    def normalize(self, payload: dict) -> NormalizedNormArtifacts:
        provider = str(payload["provider"])

        if provider == "mineru":
            markdown_text = str(payload.get("markdown_text", ""))
            layout_payload = dict(payload.get("layout_payload", {"pages": []}))
            metadata = dict(payload.get("metadata", {}))
            page_texts = [
                PageText(page=int(page["page"]), text=str(page["text"]))
                for page in layout_payload.get("pages", [])
            ]
        else:
            markdown_text = str(payload.get("markdown", ""))
            pages = [
                {
                    "page": int(page["page_number"]),
                    "text": str(page["content"]),
                }
                for page in payload.get("pages", [])
            ]
            layout_payload = {"pages": pages}
            metadata = dict(payload.get("meta", {}))
            page_texts = [
                PageText(page=page["page"], text=page["text"]) for page in pages
            ]

        return NormalizedNormArtifacts(
            provider=provider,
            markdown_text=markdown_text,
            layout_payload=layout_payload,
            page_texts=page_texts,
            metadata=metadata,
        )
