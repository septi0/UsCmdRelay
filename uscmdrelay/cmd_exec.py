import logging
import asyncio
from uscmdrelay.exceptions import ProcessError

__all__ = ['exec_cmd']

async def exec_cmd(cmd: list, *, input: str = None, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, shell_exec: bool = False) -> str:
    logging.debug(f'Executing command: {[*cmd]}')
    
    if shell_exec:
        cmd = ' '.join(cmd)

    if shell_exec:
        process = await asyncio.create_subprocess_shell(cmd, stdin=stdin, stdout=stdout, stderr=stderr)
    else:
        process = await asyncio.create_subprocess_exec(*cmd, stdin=stdin, stdout=stdout, stderr=stderr)

    if input:
        process.stdin.write(input.encode('utf-8'))
        process.stdin.close()

    out, err = await process.communicate()

    if process.returncode != 0:
        raise ProcessError(err.decode('utf-8').strip(), process.returncode)

    result = ''

    if out:
        return out.decode('utf-8').strip()
    
    return result