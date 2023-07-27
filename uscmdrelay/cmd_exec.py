import logging
import subprocess
from uscmdrelay.exceptions import ProcessError

__all__ = ['exec_cmd']

def exec_cmd(cmd: list, *, input: str = None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell_exec: bool = False):
    logging.debug(f'Executing command: {[*cmd]}')

    kwargs = {}

    if shell_exec:
        cmd = ' '.join(cmd)
        kwargs['shell'] = True

    out = subprocess.run(cmd, input=input, stdout=stdout, stderr=stderr, **kwargs)

    logging.debug(f'Command output: {out}')

    if out.returncode != 0:
        raise ProcessError(out.stderr.decode('utf-8').strip(), out.returncode)

    if out.stdout:
        return out.stdout.decode('utf-8').strip()
    
    return ''