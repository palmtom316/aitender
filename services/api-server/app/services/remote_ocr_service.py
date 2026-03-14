import json
import mimetypes
import time
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zipfile import ZipFile

from app.models.project_ai_settings import ProviderApiConfig


class RemoteOCRService:
    def extract(
        self,
        *,
        document_path: Path,
        config: ProviderApiConfig,
    ) -> dict:
        if self._uses_mineru_async(config.base_url):
            return self._extract_mineru_async(
                document_path=document_path,
                config=config,
            )

        response = self._post_multipart(
            url=config.base_url,
            model=config.model,
            api_key=config.api_key,
            document_path=document_path,
        )
        payload = self._unwrap_payload(response)

        if "markdown_text" in payload or "layout_payload" in payload:
            metadata = dict(payload.get("metadata", {}))
            metadata.setdefault("source_path", str(document_path))
            return {
                "provider": str(payload.get("provider", "remote")),
                "markdown_text": str(payload.get("markdown_text", "")),
                "layout_payload": dict(payload.get("layout_payload", {"pages": []})),
                "metadata": metadata,
            }

        if "markdown" in payload or "pages" in payload:
            meta = dict(payload.get("meta", {}))
            meta.setdefault("source_path", str(document_path))
            return {
                "provider": str(payload.get("provider", "commercial")),
                "markdown": str(payload.get("markdown", "")),
                "pages": list(payload.get("pages", [])),
                "meta": meta,
            }

        raise RuntimeError(
            "OCR API response must contain either markdown_text/layout_payload "
            "or markdown/pages fields"
        )

    def _extract_mineru_async(
        self,
        *,
        document_path: Path,
        config: ProviderApiConfig,
    ) -> dict:
        api_root = self._mineru_api_root(config.base_url)
        data_id = uuid.uuid4().hex
        create_payload = self._post_json(
            url=f"{api_root}/file-urls/batch",
            api_key=config.api_key,
            body={
                "enable_formula": False,
                "model_version": config.model,
                "files": [
                    {
                        "name": document_path.name,
                        "is_ocr": True,
                        "data_id": data_id,
                    }
                ],
            },
        )
        batch_id, upload_url = self._parse_mineru_batch_create_response(
            create_payload,
            expected_name=document_path.name,
        )
        self._put_bytes(
            url=upload_url,
            content=document_path.read_bytes(),
            mime_type=mimetypes.guess_type(document_path.name)[0] or "application/pdf",
        )
        result_payload = self._poll_mineru_batch_result(
            api_root=api_root,
            api_key=config.api_key,
            batch_id=batch_id,
        )
        full_zip_url = self._parse_mineru_result_zip_url(
            result_payload,
            expected_name=document_path.name,
        )
        archive_bytes = self._download_bytes(
            url=full_zip_url,
            api_key=config.api_key,
        )
        markdown_text, layout_payload = self._extract_mineru_zip_payload(archive_bytes)
        return {
            "provider": "mineru",
            "markdown_text": markdown_text,
            "layout_payload": layout_payload,
            "metadata": {
                "source_path": str(document_path),
                "provider_batch_id": batch_id,
                "provider_model": config.model,
                "provider_result_url": full_zip_url,
            },
        }

    def _post_multipart(
        self,
        *,
        url: str,
        model: str,
        api_key: str,
        document_path: Path,
    ) -> dict:
        boundary = f"aitender-{uuid.uuid4().hex}"
        mime_type = mimetypes.guess_type(document_path.name)[0] or "application/pdf"
        file_bytes = document_path.read_bytes()
        body = b"".join(
            [
                self._field_part(boundary, "model", model),
                self._file_part(
                    boundary=boundary,
                    field_name="file",
                    filename=document_path.name,
                    mime_type=mime_type,
                    content=file_bytes,
                ),
                f"--{boundary}--\r\n".encode(),
            ]
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }
        if api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"

        request = Request(url=url, data=body, headers=headers, method="POST")
        try:
            with urlopen(request, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OCR API request failed: {exc.code} {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"OCR API request failed: {exc.reason}") from exc

    def _post_json(
        self,
        *,
        url: str,
        api_key: str,
        body: dict,
    ) -> dict:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"
        request = Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(request, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OCR API request failed: {exc.code} {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"OCR API request failed: {exc.reason}") from exc

    def _get_json(
        self,
        *,
        url: str,
        api_key: str,
    ) -> dict:
        headers = {"Accept": "application/json"}
        if api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=300) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OCR API request failed: {exc.code} {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"OCR API request failed: {exc.reason}") from exc

    def _put_bytes(
        self,
        *,
        url: str,
        content: bytes,
        mime_type: str,
    ) -> None:
        request = Request(
            url,
            data=content,
            headers={"Content-Type": ""},
            method="PUT",
        )
        try:
            with urlopen(request, timeout=300):
                return
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OCR upload failed: {exc.code} {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"OCR upload failed: {exc.reason}") from exc

    def _download_bytes(
        self,
        *,
        url: str,
        api_key: str = "",
    ) -> bytes:
        headers = {}
        if api_key.strip():
            headers["Authorization"] = f"Bearer {api_key.strip()}"
        request = Request(url, headers=headers, method="GET")
        try:
            with urlopen(request, timeout=300) as response:
                return response.read()
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OCR download failed: {exc.code} {details}") from exc
        except URLError as exc:
            raise RuntimeError(f"OCR download failed: {exc.reason}") from exc

    @staticmethod
    def _field_part(boundary: str, name: str, value: str) -> bytes:
        return (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n"
        ).encode("utf-8")

    @staticmethod
    def _file_part(
        *,
        boundary: str,
        field_name: str,
        filename: str,
        mime_type: str,
        content: bytes,
    ) -> bytes:
        header = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
        return b"".join([header, content, b"\r\n"])

    def _unwrap_payload(self, payload: dict) -> dict:
        current = payload
        while isinstance(current, dict):
            if any(
                key in current
                for key in ("markdown_text", "layout_payload", "markdown", "pages")
            ):
                return current

            for key in ("data", "result", "output"):
                child = current.get(key)
                if isinstance(child, dict):
                    current = child
                    break
            else:
                return current

        raise RuntimeError("OCR API response body must be a JSON object")

    @staticmethod
    def _uses_mineru_async(base_url: str) -> bool:
        return "mineru.net/api/v4/extract/task" in base_url.rstrip("/")

    @staticmethod
    def _mineru_api_root(base_url: str) -> str:
        if "/api/v4/" in base_url:
            prefix = base_url.split("/api/v4/")[0]
            return f"{prefix}/api/v4"
        parts = urlsplit(base_url)
        return f"{parts.scheme}://{parts.netloc}/api/v4"

    def _parse_mineru_batch_create_response(
        self,
        payload: dict,
        *,
        expected_name: str,
    ) -> tuple[str, str]:
        if isinstance(payload, dict) and payload.get("code") not in (None, 0, "0"):
            raise RuntimeError(
                f"MinerU batch create failed: {payload.get('msg', 'unknown error')}"
            )
        current = (
            dict(payload.get("data", {}))
            if isinstance(payload, dict) and isinstance(payload.get("data"), dict)
            else self._unwrap_payload(payload)
        )
        batch_id = str(current.get("batch_id", "")).strip()
        file_urls = list(current.get("file_urls", []) or [])
        if not batch_id or not file_urls:
            raise RuntimeError("MinerU batch create response is missing batch_id or file_urls")
        first_string = next((item for item in file_urls if isinstance(item, str) and item.strip()), None)
        if first_string is not None:
            return batch_id, first_string
        for item in file_urls:
            if not isinstance(item, dict):
                continue
            if str(item.get("name", "")).strip() == expected_name and str(item.get("url", "")).strip():
                return batch_id, str(item["url"])
        first = file_urls[0]
        upload_url = str(first.get("url", "")).strip() if isinstance(first, dict) else ""
        if not upload_url:
            raise RuntimeError("MinerU batch create response did not provide an upload URL")
        return batch_id, upload_url

    def _poll_mineru_batch_result(
        self,
        *,
        api_root: str,
        api_key: str,
        batch_id: str,
        timeout_seconds: int = 300,
        poll_interval_seconds: float = 2.0,
    ) -> dict:
        deadline = time.monotonic() + timeout_seconds
        url = f"{api_root}/extract-results/batch/{batch_id}"
        while time.monotonic() < deadline:
            payload = self._get_json(url=url, api_key=api_key)
            state = self._extract_mineru_batch_state(payload)
            if state == "done":
                return payload
            if state in {"failed", "error"}:
                raise RuntimeError(f"MinerU batch failed: {json.dumps(payload, ensure_ascii=False)}")
            time.sleep(poll_interval_seconds)
        raise RuntimeError(f"MinerU batch did not finish within {timeout_seconds} seconds")

    def _extract_mineru_batch_state(self, payload: dict) -> str:
        current = self._unwrap_payload(payload)
        results = list(current.get("extract_result", []) or [])
        if not results:
            return str(current.get("state", "")).strip().lower()
        states = {str(item.get("state", "")).strip().lower() for item in results if item.get("state") is not None}
        if states == {"done"}:
            return "done"
        if "failed" in states or "error" in states:
            return "failed"
        if "running" in states or "pending" in states:
            return "running"
        return next(iter(states), "")

    def _parse_mineru_result_zip_url(
        self,
        payload: dict,
        *,
        expected_name: str,
    ) -> str:
        current = self._unwrap_payload(payload)
        results = list(current.get("extract_result", []) or [])
        for item in results:
            if str(item.get("file_name", "")).strip() == expected_name and str(item.get("full_zip_url", "")).strip():
                return str(item["full_zip_url"])
        for item in results:
            full_zip_url = str(item.get("full_zip_url", "")).strip()
            if full_zip_url:
                return full_zip_url
        raise RuntimeError("MinerU batch result did not provide full_zip_url")

    def _extract_mineru_zip_payload(self, archive_bytes: bytes) -> tuple[str, dict]:
        with ZipFile(BytesIO(archive_bytes)) as archive:
            markdown_text = ""
            layout_payload = {}
            for name in archive.namelist():
                lowered = name.lower()
                if lowered.endswith("/full.md") or lowered.endswith("full.md"):
                    markdown_text = archive.read(name).decode("utf-8")
                elif lowered.endswith("/layout.json") or lowered.endswith("layout.json"):
                    layout_payload = json.loads(archive.read(name).decode("utf-8"))
            if not markdown_text:
                raise RuntimeError("MinerU result archive is missing full.md")
            if not layout_payload:
                layout_payload = {"pages": [{"page": 1, "text": markdown_text}]}
            else:
                layout_payload = {"pages": self._build_page_texts_from_layout(layout_payload)}
            return markdown_text, layout_payload

    def _build_page_texts_from_layout(self, layout_payload: dict) -> list[dict]:
        pages: dict[int, list[str]] = {}

        def append(page: int | None, text: str) -> None:
            if page is None:
                return
            cleaned = str(text).strip()
            if not cleaned:
                return
            bucket = pages.setdefault(page, [])
            if cleaned not in bucket:
                bucket.append(cleaned)

        def walk(node, page_hint: int | None = None) -> None:
            if isinstance(node, dict):
                current_page = page_hint
                for key in ("page", "page_no", "page_idx", "page_id", "page_number"):
                    value = node.get(key)
                    if isinstance(value, int):
                        current_page = int(value)
                        break
                for key in ("text", "content"):
                    value = node.get(key)
                    if isinstance(value, str):
                        append(current_page, value)
                for value in node.values():
                    walk(value, current_page)
            elif isinstance(node, list):
                for item in node:
                    walk(item, page_hint)

        walk(layout_payload)
        return [
            {"page": page, "text": " ".join(chunks)}
            for page, chunks in sorted(pages.items())
        ]


remote_ocr_service = RemoteOCRService()
