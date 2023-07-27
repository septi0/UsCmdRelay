import json
from uscmdrelay.exceptions import ClientRequestError

__all__ = ['ClientRequest']

class ClientRequest:
    def __init__(self, message: str) -> None:
        payload = self._parse_message(message)

        self._auth_key: str = payload['auth_key']
        self._command: str = payload['command']
        self._cluster: str = payload['cluster']
        self._arguments: list[str] = payload['arguments']

    def _parse_message(self, message: str) -> dict:
        payload = {}

        try:
            # attempt to parse client message as json
            payload = json.loads(message)
        except json.JSONDecodeError:
            # client message is in raw format
            raise ClientRequestError('Unknown message format')

        if not 'auth_key' in payload:
            raise ClientRequestError('auth_key is required')
        else:
            if type(payload['auth_key']) is not str:
                raise ClientRequestError('auth_key must be a string')
        
        if not 'command' in payload:
            raise ClientRequestError('command is required')
        else:
            if type(payload['command']) is not str:
                raise ClientRequestError('command must be a string')

            # check if command contains cluster
            if '::' in payload['command']:
                cluster, command = payload['command'].split('::', 1)
                payload['cluster'] = cluster
                payload['command'] = command
            else:
                payload['cluster'] = 'default'

        if not 'arguments' in payload:
            payload['arguments'] = []
        else:
            if type(payload['arguments']) is str:
                payload['arguments'] = [payload['arguments']]
            elif type(payload['arguments']) is list:
                pass
            else:
                raise ClientRequestError('arguments must be a string or list of strings')

        return payload
    
    @property
    def auth_key(self) -> str:
        return self._auth_key

    @property
    def command(self) -> str:
        return self._command
    
    @property
    def cluster(self) -> str:
        return self._cluster
    
    @property
    def arguments(self) -> list:
        return self._arguments
    
    def __bool__(self) -> bool:
        return bool(self._command)