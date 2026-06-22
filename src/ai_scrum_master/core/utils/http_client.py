from __future__ import annotations

import base64
import json
import socket
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# Force IPv4 resolution to prevent TimeoutError/ConnectionResetError in environments where IPv6 is broken
_original_getaddrinfo = socket.getaddrinfo
def _ipv4_getaddrinfo(*args, **kwargs):
    responses = _original_getaddrinfo(*args, **kwargs)
    return [response for response in responses if response[0] == socket.AF_INET]

socket.getaddrinfo = _ipv4_getaddrinfo


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    json_body: dict[str, Any] | None = None
    text: str = ""


class HttpClient(Protocol):
    def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        pass

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        pass

    def delete_request(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        pass


class UrllibHttpClient:
    def get_json(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        request = Request(
            url,
            headers=self._build_headers(headers=headers, basic_auth=basic_auth),
            method="GET",
        )
        return self._open(request, timeout)

    def post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._build_headers(headers={"Content-Type": "application/json", **(headers or {})}, basic_auth=basic_auth),
            method="POST",
        )
        return self._open(request, timeout)

    def delete_request(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
        timeout: int = 30,
    ) -> HttpResponse:
        request = Request(
            url,
            headers=self._build_headers(headers=headers, basic_auth=basic_auth),
            method="DELETE",
        )
        return self._open(request, timeout)

    def _build_headers(
        self,
        headers: dict[str, str] | None = None,
        basic_auth: tuple[str, str] | None = None,
    ) -> dict[str, str]:
        request_headers = dict(headers or {})
        if basic_auth:
            token = base64.b64encode(f"{basic_auth[0]}:{basic_auth[1]}".encode()).decode()
            request_headers["Authorization"] = f"Basic {token}"
        return request_headers

    def _open(self, request: Request, timeout: int) -> HttpResponse:
        try:
            with urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", errors="replace")
                return HttpResponse(
                    status_code=response.status,
                    json_body=_decode_json(text),
                    text=text,
                )
        except HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace")
            return HttpResponse(
                status_code=exc.code,
                json_body=_decode_json(text),
                text=text,
            )
        except URLError as exc:
            return HttpResponse(status_code=0, text=f"{type(exc.reason).__name__}: {exc.reason}")
        except TimeoutError as exc:
            return HttpResponse(status_code=0, text=f"TimeoutError: {exc}")


def _decode_json(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None
