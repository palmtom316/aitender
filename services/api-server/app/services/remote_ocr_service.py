import json
import mimetypes
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.models.project_ai_settings import ProviderApiConfig


class RemoteOCRService:
    def extract(
        self,
        *,
        document_path: Path,
        config: ProviderApiConfig,
    ) -> dict:
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


remote_ocr_service = RemoteOCRService()
