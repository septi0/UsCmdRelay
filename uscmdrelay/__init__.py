import sys
import argparse
from uscmdrelay.manager import UsCmdRelayManager
from uscmdrelay.exceptions import UsCMdRelayConfigError
from uscmdrelay.info import __app_name__, __version__, __description__, __author__, __author_email__, __author_url__, __license__

def main():
    # get args from command line
    parser = argparse.ArgumentParser(description=__description__)

    parser.add_argument('--host', dest='host', help='Host to listen on', default='0.0.0.0')
    parser.add_argument('--port', dest='port', help='Port to listen on', type=int, default=7777)
    parser.add_argument('--log', dest='log_file', help='Log file where to write logs')
    parser.add_argument('--log-level', dest='log_level', help='Log level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO')
    parser.add_argument('--shell-exec', dest='shell_exec', help='Use shell to execute commands (not recommended)', action='store_true')
    parser.add_argument('--version', action='version', version=f'{__app_name__} {__version__}')

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    configtest_parser = subparsers.add_parser('configtest', help='Test configuration file')
    
    args = parser.parse_args()

    options = {
        'log_file': args.log_file,
        'log_level': args.log_level,
        'shell_exec': args.shell_exec,
    }
    
    try:
        uscmdrelay = UsCmdRelayManager(options)
    except UsCMdRelayConfigError as e:
        print(f"Config error: {e}\nCheck documentation for more information on how to configure uscmdrelay")
        sys.exit(2)

    if args.command == 'configtest':
        print("Config OK")
    else:
        options = {
            'host': args.host,
            'port': args.port,
        }

        uscmdrelay.run(options)