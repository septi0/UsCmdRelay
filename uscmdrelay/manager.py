import os
import logging
import signal
import asyncio
import shlex
from configparser import ConfigParser
from uscmdrelay.client_request import ClientRequest
from uscmdrelay.client_response import ClientResponse
from uscmdrelay.cmd_exec import exec_cmd
from uscmdrelay.exceptions import UsCMdRelayConfigError, ClientRequestError, ProcessError, GracefulExit

__all__ = ['UsCmdRelayManager']

class UsCmdRelayManager:
    def __init__(self, params: dict) -> None:
        self._pid_filepath: str = self._gen_pid_filepath()

        self._shell_exec = params.get('shell_exec', False)

        self._logger: logging.Logger = self._gen_logger(params.get('log_file', ''), params.get('log_level', 'INFO'))

        auth_config = self._parse_config('auth')

        self._auth_config: dict = self._gen_auth_config(auth_config)

        relays_config = self._parse_config('relays')

        self._relays_config: dict = self._gen_relays_config(relays_config)

        self._stats = {
            'connected_clients': 0,
            'total_clients': 0,
            'total_requests': 0,
            'total_errors': 0,
        }

    def run(self, options: dict) -> None:
        pid = str(os.getpid())

        if os.path.isfile(self._pid_filepath):
            self._logger.error("Server is already running")
            return

        with open(self._pid_filepath, 'w') as f:
            f.write(pid)

        self._logger.info("Starting server")

        host = options.get('host', '0.0.0.0')
        port = options.get('port', 7777)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.add_signal_handler(signal.SIGTERM, self._sigterm_handler)
        loop.add_signal_handler(signal.SIGINT, self._sigterm_handler)
        loop.add_signal_handler(signal.SIGQUIT, self._sigterm_handler)

        try:
            loop.run_until_complete(self._start_server(host=host, port=port))
        except (GracefulExit) as e:
            self._logger.info("Received termination signal")
        except (Exception) as e:
            self._logger.exception(e, exc_info=True)
        finally:
            try:
                self._logger.info("Shutting down server")

                # print stats
                self._logger.info(f"Total clients: {self._stats['total_clients']}")
                self._logger.info(f"Total requests: {self._stats['total_requests']}")
                self._logger.info(f"Total errors: {self._stats['total_errors']}")

                os.unlink(self._pid_filepath)

                self._cancel_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
            finally:
                asyncio.set_event_loop(None)
                loop.close()

    def _sigterm_handler(self) -> None:
        raise GracefulExit
    
    def _cancel_tasks(self, loop: asyncio.AbstractEventLoop) -> None:
        tasks = asyncio.all_tasks(loop=loop)

        if not tasks:
            return

        for task in tasks:
            task.cancel()

        loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))

        for task in tasks:
            if task.cancelled():
                continue

            if task.exception() is not None:
                loop.call_exception_handler({
                    'message': 'Unhandled exception during task cancellation',
                    'exception': task.exception(),
                    'task': task,
                })

    def _gen_pid_filepath(self) -> str:
        if os.getuid() == 0:
            return '/var/run/uscmdrelay.pid'
        else:
            return '/tmp/uscmdrelay.pid'
    
    def _gen_logger(self, log_file: str, log_level: str) -> logging.Logger:
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        if not log_level in levels:
            log_level = "INFO"

        logger = logging.getLogger()
        logger.setLevel(levels[log_level])

        if log_file:
            handler = logging.FileHandler(log_file)
        else:
            handler = logging.StreamHandler()

        handler.setLevel(levels[log_level])
        handler.setFormatter(logging.Formatter(format))

        logger.addHandler(handler)

        return logger
    
    def _parse_config(self, config_type: str) -> dict:
        config_files = [
            f'/etc/uscmdrelay/{config_type}.conf',
            f'/etc/opt/uscmdrelay/{config_type}.conf',
            os.path.expanduser(f'~/.config/uscmdrelay/{config_type}.conf'),
        ]

        if config_type == 'auth':
            for config_file in config_files:
                if os.path.isfile(config_file):
                    stat = os.stat(config_file)

                    # check if file is owned by user that is running the server
                    if stat.st_uid != os.getuid():
                        raise UsCMdRelayConfigError(f'"{config_file}" must be owned by {os.getuid()}')

                    # check if file has proper permissions (only user can read/write)
                    if stat.st_mode & 0o077 != 0:
                        raise UsCMdRelayConfigError(f'"{config_file}" must have permissions 600')

        config_inst = ConfigParser()
        config_inst.read(config_files)

        # check if any config was found
        if not config_inst.sections():
            raise UsCMdRelayConfigError("No config found")

        config = {}

        for section in config_inst.sections():
            section_data = {}

            for key, value in config_inst.items(section):
                section_data[key] = value

            config[section] = section_data

        return config
    
    def _gen_auth_config(self, config: dict) -> dict:
        parsed_config = {}

        for section, section_data in config.items():
            parsed_config[section] = {}

            if 'auth_clusters' in section_data:
                if not section_data['auth_clusters']:
                    raise UsCMdRelayConfigError(f'"auth_clusters" must have a value for "{section}" key')

                clusters = shlex.split(section_data['auth_clusters'])

                if '*' in clusters and len(clusters) > 1:
                    raise UsCMdRelayConfigError(f'when "*" is used in "auth_clusters" for "{section}" key, no other clusters can be defined')
                
                parsed_config[section]['clusters'] = clusters
            else:
                raise UsCMdRelayConfigError(f'"auth_clusters" is required for "{section}" key')
            
            if 'description' in section_data:
                parsed_config[section]['description'] = section_data['description']

        return parsed_config

    def _gen_relays_config(self, config: dict) -> dict:
        parsed_config = {}

        for section, section_data in config.items():
            parsed_config[section] = {}

            for name, command in section_data.items():
                if not command:
                    raise UsCMdRelayConfigError(f'no command definition for "{section}::{name}"')
                
                parsed_config[section][name] = shlex.split(command)

        return parsed_config

    async def _start_server(self, *, host: str = '0.0.0.0', port: int = 7777):
        server = await asyncio.start_server(self._handle_client, host, port)
        self._logger.info(f"Server is listening on {host}:{port}")

        async with server:
            await server.serve_forever()

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')

        self._logger.info(f"New client connected {addr[0]}:{addr[1]}")

        self._stats['connected_clients'] += 1
        self._stats['total_clients'] += 1

        data = await self._read_stream_data(reader)

        try:
            message = data.decode('utf-8').strip()

            self._stats['total_requests'] += 1

            self._logger.debug(f"Client {addr[0]}:{addr[1]} sent message: {message}")

            if message:
                reply = await self._process_client_message(message)

                # encode reply and send it to client
                writer.write((str(reply) + "\n").encode())
                await writer.drain()
        except (Exception) as e:
            self._logger.exception(e, exc_info=True)
            self._stats['total_errors'] += 1

        writer.close()
        await writer.wait_closed()

        self._logger.info(f"Client {addr[0]}:{addr[1]} disconnected")
        self._stats['connected_clients'] -= 1

    async def _read_stream_data(self, reader: asyncio.StreamReader) -> bytes:
        data = b''

        while True:
            chunk = await reader.read(1024)

            if not chunk:
                break

            data += chunk

            # end of message
            if data.endswith(b'\n'):
                break

        return data

    async def _process_client_message(self, message: str) -> ClientResponse:
        try:
            request = ClientRequest(message)
        except (ClientRequestError) as e:
            self._logger.error(f'Client error: Could not create ClientRequest instance. Reason: {e}')
            return ClientResponse(str(e), 'error', code=2099)

        # auth client
        if not self._auth_client(request):
            self._logger.error(f'Client error: authentication failed')
            return ClientResponse('Authentication failed', 'error', code=1000)
        
        if not request.cluster in self._relays_config:
            self._logger.error(f'Client error: Unknown cluster "{request.cluster}"')
            return ClientResponse(f'Unknown cluster provided', 'error', code=2000)

        if not request.command in self._relays_config[request.cluster]:
            self._logger.error(f'Client error: Command "{request.cluster}::{request.command}" not found')
            return ClientResponse(f'Command "{request.cluster}::{request.command}" not found', 'error', code=2001)
        
        command = self._relays_config[request.cluster][request.command]

        # split command into list parts
        cmd_with_args = command
        cmd_with_args += request.arguments

        self._logger.info(f'Relaying command "{request.cluster}::{request.command}"')

        try:
            out = await exec_cmd(cmd_with_args, shell_exec=self._shell_exec)
        except ProcessError as e:
            self._logger.error(f'Client error: Could not execute cmd. Reason: {e}')
            return ClientResponse(str(e), 'error', code=3001)
        except (Exception) as e:
            self._logger.exception(e, exc_info=True)
            self._stats['total_errors'] += 1
            return ClientResponse('Server error', 'error', code=9999)
        
        return ClientResponse(out, 'ok', code=0)
    
    def _auth_client(self, request: ClientRequest) -> bool:
        if not request.auth_key in self._auth_config:
            return False
        
        self._logger.debug(f'Authenticating client with key "{request.auth_key}"')
        
        key_config = self._auth_config[request.auth_key]

        if '*' in key_config['clusters']:
            return True
        
        if request.cluster in key_config['clusters']:
            return True
            
        return False
