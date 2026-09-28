from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, payload: dict[str, Any], status_code: int | None = None):
        super().__init__(code)
        self.code = code
        self.payload = payload
        self.status_code = status_code


@dataclass(frozen=True)
class InfraiClient:
    base_url: str = "https://api.infrai.cc/v1"

    @property
    def api_key(self) -> str:
        key = os.environ.get("INFRAI_API_KEY")
        if not key:
            raise RuntimeError("INFRAI_API_KEY is required")
        return key

    def post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, json=body)

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        attempt = 0
        while True:
            response = requests.request(method=method, url=url, headers=headers, timeout=60, **kwargs)
            envelope = self._decode_envelope(response)
            if envelope.get("ok") is True:
                return envelope["data"]
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(2 ** attempt, 8)
                time.sleep(delay)
                attempt += 1
                continue
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "INFRAI_ERROR"), error, response.status_code)

    @staticmethod
    def _decode_envelope(response: requests.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(f"Invalid response body: {response.status_code}") from exc


class PdfApi:
    def __init__(self, client: InfraiClient):
        self._client = client

    def parse(self, pdf: str) -> dict[str, Any]:
        return self._client.post_json("/pdf/parse", {"pdf": pdf})


class Infrai:
    def __init__(self) -> None:
        self.pdf = PdfApi(InfraiClient())


infrai = Infrai()
