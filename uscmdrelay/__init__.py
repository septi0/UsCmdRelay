import sys
import argparse
from uscmdrelay.manager import UsCmdRelayManager
from uscmdrelay.exceptions import UsCMdRelayConfigError
from uscmdrelay.info import APP_NAME, APP_VERSION, APP_DESCRIPTION

def main():
    # get args from command line
    parser = argparse.ArgumentParser(description=APP_DESCRIPTION)

    parser.add_argument('--host', dest='host', help='Host to listen on', default='0.0.0.0')
    parser.add_argument('--port', dest='port', help='Port to listen on', type=int, default=7777)
    parser.add_argument('--log', dest='log_file', help='Log file where to write logs')
    parser.add_argument('--log-level', dest='log_level', help='Log level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO')
    parser.add_argument('--shell-exec', dest='shell_exec', help='Use shell to execute commands (not recommended)', action='store_true')
    parser.add_argument('--version', action='version', version=f'{APP_NAME} {APP_VERSION}')

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    configtest_parser = subparsers.add_parser('configtest', help='Test configuration file')
    
    args = parser.parse_args()

    options = {}

    options['host'] = args.host
    options['port'] = args.port
    options['log_file'] = args.log_file
    options['log_level'] = args.log_level
    options['shell_exec'] = args.shell_exec
    
    try:
        uscmdrelay = UsCmdRelayManager(options)
    except UsCMdRelayConfigError as e:
        print(f"Config error: {e}\nCheck documentation for more information on how to configure uscmdrelay")
        sys.exit(2)

    if args.command == 'configtest':
        print("Config OK")
    else:
        uscmdrelay.run()
