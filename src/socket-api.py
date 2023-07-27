#!/usr/bin/python3

import socket, threading, sys, json, subprocess, logging, shlex
from configparser import ConfigParser

vendor = 'uscentral'
app_name = 'socket-api'
app_version='1.0.0'

config_dir = '/etc/opt/{}/{}/'.format(vendor, app_name)
var_dir = '/var/opt/{}/{}/'.format(vendor, app_name)
log_dir = "{}/logs/".format(var_dir)

config = ConfigParser()
config.read(config_dir + '/socket-api.conf')

host = config.get('server', 'host', fallback='127.0.0.1')
port = config.getint('server', 'port', fallback=7777)
log_file = config.get('server', 'log_file', fallback='')
log_stdout = config.getboolean('server', 'log_stdout', fallback=True)
log_level = config.getint('server', 'log_level', fallback=logging.DEBUG)

ThreadCount = 0

# configure logging
logger = logging.getLogger(app_name)
logger.setLevel(log_level)
log_formatter = logging.Formatter('[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')

# if log file exists, add it as an additional handler
if log_file:
    log_file_handler = logging.FileHandler(filename=log_dir + '/socket-api.log')
    log_file_handler.setFormatter(log_formatter)
    logger.addHandler(log_file_handler)

# if log stdout is true, add it as an additional handler
if log_stdout:
    log_console_handler = logging.StreamHandler(stream=sys.stdout)
    log_console_handler.setFormatter(log_formatter)
    logger.addHandler(log_console_handler)

def clientHandler(connection, address):
    buff_size = 1024
    data = b''

    # read client data from buffer (with len of 1024)
    while True:
        chunk_data = connection.recv(buff_size)
        # if no data left, break
        if not chunk_data: break

        data += chunk_data

        # if return sent, break
        if data.endswith(b'\r\n'): break
    
    # convert message to utf8 and strip it
    message = data.decode('utf-8').strip()

    if message:
        logger.info('Client ' + address[0] + ':' + str(address[1]) + ' said: ' + message)

        reply = processClientMessage(message)

        logger.debug('Server responded with: ' + json.dumps(reply))

        # send response to client
        connection.send(str.encode(json.dumps(reply) + "\n"))

    # close client connection
    connection.close()

    logger.info('Client ' + address[0] + ':' + str(address[1]) + ' disconnected')

def processClientMessage(message):
    if not message: return {'status': 'error', 'reason': 'No command provided'}

    try:
        # attempt to parse client message as json
        payload = json.loads(message)
    except Exception as e:
        # client message is in raw format
        payload = {'command': message}

    # make sure we have a command in our payload dictionary
    if not 'command' in payload: return {'status': 'error', 'reason': 'No command provided'}

    arguments = []

    # if arguments were provided in our dictionary, add them to our arguments list
    if 'arguments' in payload:
        if type(payload['arguments']) is str: arguments = [payload['arguments']]
        elif type(payload['arguments']) is list: arguments = payload['arguments']

    # retrieve command from config 
    command = config.get('commands', payload['command'], fallback='')

    if not command: return {'status': 'error', 'reason': 'Unknown command provided'}

    # split command into list parts
    command_list = shlex.split(command)
    command_list += arguments

    logger.debug('Executing command: ' + str(command_list))

    try:
        cmd = subprocess.run(command_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.exception(str(e))
        cmd = False

    logger.debug('Command output: ' + repr(cmd))

    if not cmd: return {'status': 'error', 'reason': 'Inexistent command'}
    elif cmd.returncode == 0: return {'status': 'ok', 'resp': cmd.stdout.decode('utf-8')}
    else: return {'status': 'error', 'reason': cmd.stderr.decode('utf-8'), 'code': cmd.returncode}

def acceptConnections(ServerSocket):
    connection, address = ServerSocket.accept()
    # timeout client after 60s
    connection.settimeout(60)

    logger.info('Client ' + address[0] + ':' + str(address[1]) + ' connected')

    # start new thread with accepted connection
    threading.Thread(target=clientHandler, args=(connection, address)).start()

def startServer(host, port):
    ServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # bind hostname and port to socket
        ServerSocket.bind((host, port))
    except Exception as e:
        logger.exception(str(e))
        sys.exit(1)

    logger.info('Server is listening on ' + host + ':' + str(port))

    # start listening
    ServerSocket.listen()

    while True:
        # accept connections
        acceptConnections(ServerSocket)

if __name__ == "__main__":
    try:
        # start server
        startServer(host, port)
    except KeyboardInterrupt:
        pass
    finally:
        # quit
        sys.exit(0)