from __future__ import annotations

from pathlib import Path

import httpx

from tender_crawler.settings import get_settings


class DifyClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def is_dataset_upload_configured(self) -> bool:
        return bool(
            self.settings.dify_base_url
            and self.settings.dify_api_key
            and self.settings.dify_dataset_id
        )

    def upload_file_to_dataset(self, file_path: str | Path) -> str:
        if not self.is_dataset_upload_configured():
            return "Dify knowledge upload is not configured. Set DIFY_BASE_URL, DIFY_API_KEY, and DIFY_DATASET_ID."

        path = Path(file_path)
        url = self._url(f"/v1/datasets/{self.settings.dify_dataset_id}/document/create-by-file")
        headers = {"Authorization": f"Bearer {self.settings.dify_api_key}"}
        data = {
            "data": (
                '{"indexing_technique":"high_quality","process_rule":{"mode":"automatic"}}'
            )
        }

        with path.open("rb") as file:
            files = {"file": (path.name, file, "text/csv")}
            with httpx.Client(timeout=120) as client:
                response = client.post(url, headers=headers, data=data, files=files)
                response.raise_for_status()
                return response.text

    def _url(self, path: str) -> str:
        return f"{self.settings.dify_base_url.rstrip('/')}/{path.lstrip('/')}"
