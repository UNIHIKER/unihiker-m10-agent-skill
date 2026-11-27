#!/usr/bin/env python3
"""Controller-side CLI. Python 3.9+, standard library, and system SSH tools."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import struct
import subprocess
import sys
import tempfile

BOARD = Path(__file__).resolve().parents[1] / 'board' / 'probe.py'
PASSWORD_ENV = 'UNIHIKER_SSH_PASSWORD'
HOST = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,252}\Z')
USER = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]{0,63}\Z')
FINGERPRINT = re.compile(r'SHA256:[A-Za-z0-9+/]{43}\Z')
VERSION = re.compile(r'(?:system|3\.\d+\.\d+)\Z')
DISPLAY = re.compile(r':\d{1,3}\Z')
PNG = b'\x89PNG\r\n\x1a\n'


class Failure(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def invoke(argv, *, data=None, timeout=15, env=None):
    try:
        if data is None:
            return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, env=env)
        return subprocess.run(argv, input=data, capture_output=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise Failure('TIMEOUT', 'Timed out; if this was a write action, verify its effect before retrying.') from None
    except OSError as exc:
        raise Failure('LOCAL_TOOL_ERROR', str(exc)) from None


def required(name):
    path = shutil.which(name)
    if not path:
        raise Failure('MISSING_HOST_TOOL', f'{name} was not found on the controller.')
    return path


def scan_keys(host, port):
    scan = invoke([required('ssh-keyscan'), '-T', '4', '-p', str(port), host], timeout=9)
    rows = {}
    for line in scan.stdout.splitlines():
        fields = line.split()
        if len(fields) != 3 or fields[0].startswith(b'#'):
            continue
        try:
            key = base64.b64decode(fields[2], validate=True)
        except ValueError:
            continue
        fingerprint = 'SHA256:' + base64.b64encode(hashlib.sha256(key).digest()).decode().rstrip('=')
        # Write only the selected key with the requested hostname, not scan-supplied aliases.
        name = host if port == 22 else f'[{host}]:{port}'
        rows[fingerprint] = b' '.join([name.encode('ascii'), *fields[1:]]) + b'\n'
    if not rows:
        raise Failure('NO_HOST_KEY', 'No SSH host key received from the specified target.')
    return rows


def classify_ssh(result):
    text = result.stderr.decode('utf-8', errors='replace').strip()
    lower = text.lower()
    if any(s in lower for s in ('host key verification failed', 'host identification has changed',
                               'host key is not cached', 'host key did not appear', 'host key does not match',
                               'host key not in manually configured list', 'host key fingerprint is')):
        return Failure('HOST_KEY_REJECTED', 'SSH host key is unknown or changed; verify it with a trusted source.')
    if any(s in lower for s in ('access denied', 'permission denied (', 'wrong password', 'no supported authentication methods', 'authentication failed')):
        return Failure('AUTH_FAILED', 'SSH authentication failed for the selected target and account.')
    if result.returncode == 124:
        return Failure('REMOTE_TIMEOUT', 'Remote action reached its time limit; verify before retrying.')
    if 'unable to open connection' in lower or 'connection refused' in lower or 'connection timed out' in lower:
        return Failure('CONNECT_FAILED', text[:450])
    if result.returncode in (126, 127):
        return Failure('REMOTE_COMMAND_UNAVAILABLE', text[:450] or 'Remote command or Python not available.')
    return Failure('REMOTE_FAILED', text[:650] or f'Remote exit status {result.returncode}.')


class Ssh:
    def __init__(self, args, directory):
        self.args = args
        self.directory = Path(directory)
        password = os.environ.get(PASSWORD_ENV)
        self.env = dict(os.environ)
        self.env.pop(PASSWORD_ENV, None)
        target = f'{args.user}@{args.host}'
        plink = shutil.which('plink')
        if not plink and os.name == 'nt':
            candidate = Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'PuTTY' / 'plink.exe'
            plink = str(candidate) if candidate.is_file() else None
        if password and args.identity:
            raise Failure('AUTH_OPTIONS', f'Unset {PASSWORD_ENV} before using --identity.')
        if password and not args.host_key:
            raise Failure('PIN_REQUIRED', 'Password automation requires a verified --host-key fingerprint.')
        if password and os.name == 'nt' and plink:
            file = self.directory / 'password'
            file.write_text(password + '\n', encoding='utf-8')
            self.argv = [plink, '-batch', '-ssh', '-T', '-P', str(args.port), '-hostkey', args.host_key,
                         '-pwfile', str(file), target]
            return
        prefix = []
        mode = ['-o', 'BatchMode=yes']
        if password:
            sshpass = shutil.which('sshpass')
            if not sshpass:
                raise Failure('MISSING_HOST_TOOL', 'Password automation needs PuTTY plink on Windows or sshpass with OpenSSH. Prefer SSH keys.')
            self.env['SSHPASS'] = password
            prefix = [sshpass, '-e']
            mode = ['-o', 'PubkeyAuthentication=no', '-o', 'PreferredAuthentications=password']
        opts = ['-o', 'StrictHostKeyChecking=yes', '-o', 'ConnectTimeout=5', '-o', 'RequestTTY=no',
                '-o', 'ForwardAgent=no', '-o', 'ClearAllForwardings=yes']
        if args.host_key:
            rows = scan_keys(args.host, args.port)
            if args.host_key not in rows:
                raise Failure('HOST_KEY_REJECTED', 'SSH fingerprint did not match the verified pin.')
            known = self.directory / 'known_hosts'
            known.write_bytes(rows[args.host_key])
            empty = self.directory / 'global_known_hosts'
            empty.touch()
            opts += ['-F', 'none', '-o', 'CheckHostIP=no', '-o', f'UserKnownHostsFile="{known.as_posix()}"',
                     '-o', f'GlobalKnownHostsFile="{empty.as_posix()}"']
        if args.identity:
            opts += ['-o', 'IdentitiesOnly=yes', '-i', str(Path(args.identity).expanduser())]
        self.argv = prefix + [required('ssh'), '-T', '-p', str(args.port)] + opts + mode + [target]

    def run(self, command, *, data=None, timeout=25):
        result = invoke(self.argv + [command], data=data, timeout=timeout, env=self.env)
        if result.returncode:
            raise classify_ssh(result)
        return result.stdout

    def board(self, task, values=(), *, version=None):
        shell = remote_python(version, ['-I', '-B', '-', task, *map(str, values)])
        # Feed the local helper over stdin; the helper itself is never installed on the board.
        raw = self.run('timeout -k 2s 18s ' + shell, data=BOARD.read_bytes(), timeout=25)
        if task == 'shot' and raw.startswith(PNG):
            return raw
        try:
            answer = json.loads(raw.decode('utf-8'))
        except (ValueError, UnicodeError):
            raise Failure('UNEXPECTED_BOARD_OUTPUT', 'Expected structured helper output or an X11 PNG; check SSH startup output.') from None
        if not isinstance(answer, dict) or answer.get('ok') not in (True, False):
            raise Failure('UNEXPECTED_BOARD_OUTPUT', 'Unexpected helper response.')
        if not answer['ok']:
            raise Failure(answer['code'], answer['message'])
        return answer


def remote_python(version, args):
    tail = ' ' + shlex.join(args)
    if version is None:
        # Use the active interpreter for diagnostics rather than reporting the preferred one as active.
        return 'python3' + tail
    quoted = shlex.quote(version)
    command = ('if command -v pyenv >/dev/null 2>&1; then p=$(command -v pyenv); '
               'elif [ -x "$HOME/.pyenv/bin/pyenv" ]; then p="$HOME/.pyenv/bin/pyenv"; '
               'else echo "pyenv not found" >&2; exit 127; fi; '
               f'export PYENV_VERSION={quoted}; exec "$p" exec python' + tail)
    return 'sh -c ' + shlex.quote(command)


def save_png(raw, output):
    if len(raw) < 33 or not raw.startswith(PNG) or raw[8:16] != b'\0\0\0\rIHDR' or raw[-8:-4] != b'IEND':
        raise Failure('INVALID_PNG', 'Board output is not a complete PNG.')
    w, h = struct.unpack('>II', raw[16:24])
    if not (0 < w <= 4096 and 0 < h <= 4096):
        raise Failure('INVALID_PNG', 'Board returned invalid PNG dimensions.')
    path = Path(output).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('xb') as file:
            file.write(raw)
    except FileExistsError:
        raise Failure('OUTPUT_EXISTS', 'Choose a new output path; the existing file was not overwritten.') from None
    return {'path': str(path), 'width': w, 'height': h, 'bytes': len(raw), 'capture': 'board X11 via ffmpeg'}


def tcp_check(host, port):
    try:
        with socket.create_connection((host, port), timeout=4):
            return
    except OSError as exc:
        raise Failure('CONNECT_FAILED', f'{host}:{port} TCP check failed: {exc}') from None


def pattern(regex, label):
    def parse(value):
        if not regex.fullmatch(value):
            raise argparse.ArgumentTypeError(f'invalid {label}: {value!r}')
        return value
    return parse


def bounded(low, high):
    def parse(value):
        n = int(value)
        if not low <= n <= high:
            raise argparse.ArgumentTypeError(f'must be in {low}..{high}')
        return n
    return parse


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True, type=pattern(HOST, 'host (IPv4 or hostname)'))
    parser.add_argument('--user', type=pattern(USER, 'SSH account'), help='Explicit SSH account; required for all SSH actions.')
    parser.add_argument('--port', type=bounded(1, 65535), default=22)
    parser.add_argument('--host-key', type=pattern(FINGERPRINT, 'SHA256 fingerprint'))
    parser.add_argument('--identity', help='Path to a private key (prefer the SSH agent).')
    command = parser.add_subparsers(dest='group', required=True)
    command.add_parser('discover-key', help='Discover untrusted fingerprints; does not authenticate.')
    command.add_parser('status', help='Read-only image/runtime probe.')
    ssh = command.add_parser('ssh').add_subparsers(dest='action', required=True)
    ssh.add_parser('tcp', help='Only check the specified TCP port.')
    ssh.add_parser('check', help='Check SSH authentication and remote command execution.')
    run = ssh.add_parser('run', help='Run an explicit remote shell command; review authorization first.')
    run.add_argument('command'); run.add_argument('--seconds', type=bounded(1, 120), default=15)
    python = command.add_parser('python').add_subparsers(dest='action', required=True)
    python.add_parser('list')
    py_run = python.add_parser('run', help='Run an existing absolute .py path on the board.')
    py_run.add_argument('--version', required=True, type=pattern(VERSION, 'installed Python version'))
    py_run.add_argument('--seconds', type=bounded(1, 120), default=15)
    py_run.add_argument('path')
    py_run.add_argument('script_args', nargs=argparse.REMAINDER)
    wifi = command.add_parser('wifi').add_subparsers(dest='action', required=True)
    wifi.add_parser('status', help='No Wi-Fi changes or scanning.')
    screen = command.add_parser('screen').add_subparsers(dest='action', required=True)
    shot = screen.add_parser('shot'); shot.add_argument('--output', required=True)
    pos = screen.add_parser('pointer', help='Read the current cursor position.')
    move = screen.add_parser('move'); click = screen.add_parser('click')
    key = screen.add_parser('key')
    for p in (shot, pos, move, click, key):
        p.add_argument('--display', default=':0', type=pattern(DISPLAY, 'local X11 display'))
    for p in (move, click):
        p.add_argument('x', type=bounded(0, 4095)); p.add_argument('y', type=bounded(0, 4095))
    key.add_argument('key', type=pattern(re.compile(r'[A-Za-z0-9_]{1,32}\Z'), 'single X11 keysym'))
    for p in (move, click, key):
        p.add_argument('--confirm', action='store_true', help='Explicitly permit this UI event.')
    command.add_parser('calibration-guide', help='Read calibration availability and return the board menu route.')
    hw = command.add_parser('hw').add_subparsers(dest='action', required=True)
    api = hw.add_parser('api', help='Find symbols without executing PinPong modules.')
    api.add_argument('query', type=pattern(re.compile(r'[A-Za-z0-9_.-]{2,48}\Z'), 'module or sensor identifier'))
    read = hw.add_parser('read', help='Read an onboard input on the reviewed PinPong build.')
    read.add_argument('sensor', choices=['light', 'button-a', 'button-b'])
    blink = hw.add_parser('blink', help='Blink the onboard L LED (not an external GPIO).')
    blink.add_argument('--count', type=bounded(1, 5), default=3)
    for p in (api, read, blink):
        p.add_argument('--version', type=pattern(VERSION, 'installed Python version'))
    for p in (read, blink):
        p.add_argument('--confirm', action='store_true', help='Confirm the board is free for PinPong access.')
    return parser.parse_args(argv)


def dispatch(a):
    if a.group == 'discover-key':
        return {'verified': False, 'fingerprints': list(scan_keys(a.host, a.port))}
    group, action = a.group, getattr(a, 'action', None)
    if group == 'ssh' and action in ('tcp', 'check'):
        tcp_check(a.host, a.port)
        if action == 'tcp':
            return {'tcp_reachable': True, 'authenticated': False}
    if not a.user:
        raise Failure('ACCOUNT_REQUIRED', 'Provide the verified SSH account via --user.')
    if (group == 'screen' and action in ('move', 'click', 'key') or group == 'hw' and action in ('read', 'blink')) and not a.confirm:
        raise Failure('CONFIRMATION_REQUIRED', 'Verify the target, requested action and state, then supply --confirm.')
    if group == 'python' and action == 'run' and (not a.path.startswith('/') or not a.path.endswith('.py') or any(c in a.path for c in '\r\n')):
        raise Failure('REMOTE_SCRIPT_PATH', 'Provide an existing absolute Linux .py path on the board.')
    with tempfile.TemporaryDirectory(prefix='m10-ssh-') as directory:
        ssh = Ssh(a, directory)
        if group == 'ssh':
            if action == 'check':
                raw = ssh.run("printf '%s\\n' 'm10-ssh-ok'", timeout=10)
                if raw.splitlines()[-1:] != [b'm10-ssh-ok']:
                    raise Failure('SSH_MISSING_MARKER', 'SSH returned unexpected output.')
                return {'tcp_reachable': True, 'authenticated': True, 'm10_identity_checked': False}
            raw = ssh.run(f'timeout -k 2s {a.seconds}s sh -c ' + shlex.quote(a.command), timeout=a.seconds + 12)
            return {'stdout': raw.decode('utf-8', errors='replace')}
        if group == 'status' or group == 'python' and action == 'list':
            return ssh.board('status' if group == 'status' else 'python')
        if group == 'python':
            identity = ('import json,sys; print(json.dumps({"version": ".".join(map(str, sys.version_info[:3])), '
                        '"executable": sys.executable}))')
            command = remote_python(a.version, ['-I', '-B', '-c', identity])
            raw = ssh.run('timeout -k 2s 8s ' + command, timeout=14)
            try:
                actual = json.loads(raw.decode('utf-8'))
                if not isinstance(actual['version'], str) or not isinstance(actual['executable'], str):
                    raise ValueError
            except (ValueError, KeyError, TypeError):
                raise Failure('PYTHON_PROBE_OUTPUT', 'Cannot verify the selected Python interpreter; script was not run.') from None
            if a.version != 'system' and actual['version'] != a.version:
                raise Failure('PYTHON_VERSION_MISMATCH', 'The selected interpreter reported a different version; script was not run.')
            command = remote_python(a.version, [a.path, *a.script_args])
            raw = ssh.run(f'timeout -k 2s {a.seconds}s ' + command, timeout=a.seconds + 12)
            return {'requested_version': a.version, 'reported_version': 'Python ' + actual['version'],
                    'executable': actual['executable'], 'remote_path': a.path,
                    'stdout': raw.decode('utf-8', errors='replace')}
        if group in ('wifi', 'calibration-guide'):
            return ssh.board('wifi' if group == 'wifi' else 'calibration')
        if group == 'screen':
            if action == 'shot':
                output = Path(a.output).expanduser()
                if output.exists():
                    raise Failure('OUTPUT_EXISTS', 'Choose a new output path.')
                return {**save_png(ssh.board('shot', [a.display]), output), 'display': a.display}
            values = [a.display, action]
            values += [a.x, a.y] if action in ('move', 'click') else [a.key] if action == 'key' else []
            return ssh.board('input', values)
        if group == 'hw':
            value = {'api': lambda: a.query, 'read': lambda: a.sensor, 'blink': lambda: a.count}[action]()
            return ssh.board(action, [value], version=a.version)
    raise AssertionError('unhandled command')


def main(argv=None):
    a = arguments(argv)
    try:
        result = dispatch(a)
        print(json.dumps({'ok': True, 'host': a.host, 'port': a.port, **result}, ensure_ascii=True))
        return 0
    except (Failure, OSError) as exc:
        print(json.dumps({'ok': False, 'host': a.host, 'error': getattr(exc, 'code', 'LOCAL_IO_ERROR'), 'message': str(exc)}, ensure_ascii=True))
        return 1


if __name__ == '__main__':
    sys.exit(main())
