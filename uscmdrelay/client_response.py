import json

__all__ = ['ClientResponse']

class ClientResponse:
    def __init__(self, message: str | dict, status: str, *, code = 0) -> None:
        self._message: str | dict = message
        self._status: str = status
        self._code: int = code

    def __str__(self) -> str:
        return json.dumps({'status': self._status, 'message': self._message, 'code': self._code})