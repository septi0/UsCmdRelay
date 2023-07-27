# UsCmdRelay

## Description

**UsCmdRelay** is a lightweight socket server, which allows controlled remote execution of commands on the host system based on authentication keys and command cluster definitions.

It is intended to be used as a command executor, not as a remote shell and to be used in a controlled environment, where the clients are trusted (internal network, VPN, etc.).

Communication between clients and the server is done over TCP sockets where the server listens on the specified port and the clients connect to it. Data is exchanged in JSON format. Before executing commands, the server employs auth_keys for client authentication, providing controlled access to the command clusters.

## Features
- Remote command execution
- Client authentication using auth_keys
- Granular authentication control over command clusters
- Command clustering

## Software requirements

- python3


## Installation

#### 1. As a package

```
pip install --upgrade <git-repo>
```

or 

```
git clone <git-repo>
cd <git-repo>
python setup.py install
```

#### 2. As a standalone script

```
git clone <git-repo>
```

## Server Usage

The UsCmdRelay server can be started in 3 ways (depending on the instalation method):

#### 1. As a package (if installed globally)

```
/usr/bin/uscmdrelay <parameters>
```

#### 2. As a package (if installed in a virtualenv)

```
<path-to-venv>/bin/uscmdrelay <parameters>
```

#### 3. As a standalone script

```
<git-clone-dir>/run.py <parameters>
```

Check "Server command line arguments" section for more information about the available parameters.

## Client Usage

Clients can connect to the server using any method, as long as they can communicate over TCP sockets and exchange data in JSON format. The following example is a simple request using bash, netcat and jq:

```
echo '{"auth_key": "my_auth_key", "command": "command-name"}' | nc <server-ip> <server-port> | jq
```

## Server command line arguments

```
uscmdrelay [-h] [--host HOST] [--port PORT] [--log LOG_FILE] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]
              [--shell-exec] [--version]
              {configtest} ...

options:
  -h, --help            show this help message and exit
  --host HOST           Host to listen on
  --port PORT           Port to listen on
  --log LOG_FILE        Log file where to write logs
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Log level
  --shell-exec          Use shell to execute commands (not recommended)
  --version             show program's version number and exit

Commands:
  {configtest}
    configtest          Test configuration file
```

## Client data format:

The client must send the data as a JSON encoded string with the following keys:
    
```
{
    "auth_key": "my_auth_key",
    "command": "command-name",
    "arguments": ["arg1", "arg2", "arg3"]
}
```

- `auth_key` - Auth key to use for authentication
- `command` - Command to execute. It can be the command name when using the `default` relay cluster or the command name prefixed with the relay cluster name (e.g. `cluster1::command-name`)
- `arguments` - List of arguments to pass to the command

## Server response format:

```
{
    "status": "command_status",
    "message": "return message
    "code": "return code"
}
```

- `status` - Response status. Can be one of the following:
    - `success` - Command executed successfully
    - `error` - Command execution failed
- `message` - Return message from the command / error message
- `code` - Response status code. Can be one of the following:
    - `0` - success
    - `10xx` - authentication errors
    - `20xx` - client data errors
    - `30xx` - command execution errors
    - `9999` - server error

## Configuration files
For sample configuration files see `auth.sample.conf` and `relays.sample.conf`. Aditionally, you can copy theese files to `/etc/uscmdrelay/`, `/etc/opt/uscmdrelay/` or `~/.config/uscmdrelay/` and adjust the values to your needs.

#### Configuring auth (auth.conf)
Each section in the configuration file is an auth key. The name of the section is the auth key that will be specified with the `auth_key` property by the client.

Section properties:
- `description` - Description of the auth key
- `auth_clusters`- List of auth clusters that the auth key is allowed to use. Use `*` to allow all auth clusters.

#### Configuring relays (relays.conf)
Each section in the configuration file is a relay cluster. The name of the section is the name of the relay cluster that will be specified as a prefix with the `command` property by the client.

Relay definition:
```
<command-name>=<command>
```

## Systemd service

To run UsCmdRelay as a service, have it start on boot and restart on failure, create a systemd service file in `/etc/systemd/system/uscmdrelay.service` and copy the content from `uscmdrelay.sample.service` file, adjusting the `ExecStart` parameter based on the installation method.

After that, run the following commands:

```
systemctl daemon-reload
systemctl enable uscmdrelay.service
systemctl start uscmdrelay.service
```
## Disclaimer

This software is provided as is, without any warranty. Use at your own risk. The author is not responsible for any damage caused by this software.

## License

This software is licensed under the GNU GPL v3 license. See the LICENSE file for more information.