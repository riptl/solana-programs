from dataclasses import dataclass
from typing import Any, Optional

import requests


class RPCError(Exception):
    """JSON-RPC 2.0 error.
    https://www.jsonrpc.org/specification#error_object"""

    def __init__(self, code: int, message: str = "", data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)

    @staticmethod
    def from_json(obj: Optional[dict]) -> Optional["RPCError"]:
        if obj is None:
            return None
        return RPCError(
            code=obj["code"], message=obj.get("message"), data=obj.get("data")
        )


@dataclass
class RPCResponse:
    """JSON-RPC 2.0 result.
    https://www.jsonrpc.org/specification#response_object"""

    id: int
    result: Optional[Any] = None
    error: Optional[RPCError] = None

    def is_error(self) -> bool:
        return self.error is not None

    def raise_for_result(self):
        if self.error is not None:
            raise self.error

    @staticmethod
    def from_json(obj: dict) -> "RPCResponse":
        return RPCResponse(
            id=obj["id"],
            result=obj.get("result"),
            error=RPCError.from_json(obj.get("error")),
        )


class RPCClient:
    """JSON-RPC 2.0 HTTP client"""

    def __init__(self, url: str):
        self.session = requests.Session()
        self.counter = 0
        self.url = url

    def request(self, method: str, *params) -> Any:
        """Sends an RPC request and returns the result, or raises an error."""
        res = self.request_response(method, *params)
        res.raise_for_result()
        return res.result

    def request_response(self, method: str, *params) -> RPCResponse:
        """Sends an RPC request and returns the response object."""
        request = {
            "jsonrpc": "2.0",
            "id": self.nonce(),
            "method": method,
            "params": list(params),
        }
        res = self.session.post(self.url, json=request)
        res.raise_for_status()
        return RPCResponse.from_json(res.json())

    def nonce(self) -> int:
        """Increments the request ID nonce."""
        self.counter += 1
        return self.counter
