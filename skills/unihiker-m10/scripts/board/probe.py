#!/usr/bin/env python3
"""M10 task helper, sent over SSH stdin. Compatible with Python 3.7+ on Linux."""
import ast
from contextlib import contextmanager, redirect_stdout
import ctypes as C
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import time

OPT = Path('/opt/unihiker')
HOME_CONFIG = OPT / 'pyboardUI/config.cfg'
REVIEWED_PINPONG = {
    'board.py': 'b5684cad89331c5cb36fb930ac727c9a77b72f72b12de884bb3b424384f97fb7',
    'extension/unihiker.py': '76225aa8e5e0c19e9120dcbcf592518e215956241b2bdc5ba9decd763b5d5690',
}
PACKAGES = ('unihiker', 'pinpong', 'pygame', 'ttkbootstrap', 'PyQt5', 'PySide6', 'pywebview', 'Flask')


class Failure(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def read_file(path, limit=16384):
    try:
        with Path(path).open('rb') as file:
            return file.read(limit).decode('utf-8', errors='replace')
    except OSError:
        return None


def output(argv, env=None, seconds=6):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env, timeout=seconds)


def optional(argv, env=None):
    try:
        result = output(argv, env)
        return result.stdout.decode('utf-8', errors='replace').strip() if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def need_m10():
    version = read_file(OPT / 'Version', 128)
    if version is None or not (OPT / 'pyboardUI').is_dir():
        raise Failure('M10_MARKERS_MISSING', 'This is not a verified product-image layout; do not apply M10-specific operations. Confirm BSP/custom image separately.')
    return version.strip()


def package_versions():
    try:
        from importlib import metadata
    except ImportError:
        result = dict.fromkeys(PACKAGES)
        current = None
        for line in (optional([sys.executable, '-m', 'pip', '--disable-pip-version-check', 'show', *PACKAGES]) or '').splitlines():
            key, _, value = line.partition(': ')
            if key == 'Name':
                current = next((name for name in PACKAGES if name.lower() == value.lower()), None)
            elif key == 'Version' and current:
                result[current] = value
        return result
    result = {}
    for name in PACKAGES:
        try:
            result[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            result[name] = None
    return result


def python_info():
    pyenv = shutil.which('pyenv') or Path.home() / '.pyenv/bin/pyenv'
    tools = [str(pyenv)]
    return {
        'active_python': {'version': '.'.join(map(str, sys.version_info[:3])), 'executable': sys.executable,
                          'packages': package_versions()},
        'system_python': {'executable': '/usr/bin/python3', 'reported_version': optional(['/usr/bin/python3', '-V'])},
        'pyenv': {'version': optional(tools + ['--version']), 'selection': optional(tools + ['version-name']),
                  'installed': (optional(tools + ['versions', '--bare']) or '').splitlines()},
    }


def home_info():
    # Do not expose raw config: it can contain the AP password and paths.
    try:
        config = json.loads(read_file(HOME_CONFIG) or '{}')
    except ValueError:
        return {}
    if not isinstance(config, dict):
        return {}
    fields = ('language', 'AutoStart', 'Jupyter', 'SIoT', 'siotVersion', 'FileShare', 'ScreenShare', 'ap')
    return {key: config[key] for key in fields if key in config and isinstance(config[key], (str, bool, int))}


def wifi_info():
    devices = []
    nm = optional(['nmcli', '-t', '-f', 'DEVICE,TYPE,STATE', 'device', 'status'], dict(os.environ, LC_ALL='C'))
    if nm:
        for line in nm.splitlines():
            parts = line.split(':', 2)
            if len(parts) == 3 and parts[1] in ('wifi', 'wifi-p2p', 'bridge', 'ethernet'):
                devices.append(dict(zip(('interface', 'type', 'state'), parts)))
    try:
        addrs = json.loads(optional(['ip', '-j', 'address', 'show']) or '[]')
    except ValueError:
        addrs = []
    return {'nmcli_available': bool(shutil.which('nmcli')), 'nmcli_status_read': nm is not None, 'devices': devices,
            'interfaces': [{'interface': x.get('ifname'), 'state': x.get('operstate'),
                            'ipv4': [a['local'] + '/' + str(a['prefixlen']) for a in x.get('addr_info', []) if a.get('family') == 'inet']}
                           for x in addrs if x.get('ifname') != 'lo']}


def status():
    version = read_file(OPT / 'Version', 128)
    os_id = (read_file('/etc/os-release', 4096) or '').splitlines()
    return {'m10_product_layout_detected': version is not None and (OPT / 'pyboardUI').is_dir(),
            'image_version': version.strip() if version is not None else None,
            'linux': {**{k: v.strip('"\'') for k, v in (line.split('=', 1) for line in os_id if '=' in line)
                         if k in ('ID', 'PRETTY_NAME', 'VERSION_ID')}, 'kernel': os.uname().release,
                      'arch': os.uname().machine, 'glibc': optional(['getconf', 'GNU_LIBC_VERSION']),
                      'device_tree_model': (read_file('/proc/device-tree/model', 256) or '').rstrip('\0\n') or None},
            'home': home_info(), **python_info(), 'network': wifi_info(),
            'screen': {'x11_sockets': sorted(p.name for p in Path('/tmp/.X11-unix').glob('X*')),
                       'xdpyinfo': bool(shutil.which('xdpyinfo')), 'ffmpeg': bool(shutil.which('ffmpeg'))},
            'calibration_tool_present': bool(shutil.which('ts_calibrate'))}


def x11_env(display):
    need_m10()
    if not re.fullmatch(r':\d{1,3}', display):
        raise Failure('BAD_DISPLAY', 'Use a verified local X11 display number.')
    if not Path('/tmp/.X11-unix', 'X' + display[1:]).exists():
        raise Failure('NO_DISPLAY', 'No local X11 socket for this display. Do not start a new session just to fabricate a capture.')
    return dict(os.environ, DISPLAY=display, LC_ALL='C')


def screenshot(display):
    env = x11_env(display)
    if not all(shutil.which(tool) for tool in ('xdpyinfo', 'ffmpeg')):
        raise Failure('MISSING_CAPTURE_TOOL', 'Required on the board: xdpyinfo and ffmpeg with x11grab. Use the official screen-sharing route if unavailable.')
    info = optional(['xdpyinfo'], env) or ''
    dim = re.search(r'dimensions:\s+(\d+)x(\d+)', info)
    if not dim:
        raise Failure('DISPLAY_ACCESS', 'Could not query the X11 dimensions as the current SSH user; verify the physical session and authorization.')
    w, h = map(int, dim.groups())
    if not (0 < w <= 4096 and 0 < h <= 4096):
        raise Failure('DISPLAY_SIZE', 'Unexpected X11 screen dimensions.')
    r = output(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-f', 'x11grab', '-video_size',
                '{}x{}'.format(w, h), '-i', display, '-frames:v', '1', '-threads', '1', '-c:v', 'png',
                '-f', 'image2pipe', 'pipe:1'], env, seconds=10)
    if r.returncode or not r.stdout.startswith(b'\x89PNG\r\n\x1a\n'):
        raise Failure('CAPTURE_FAILED', 'ffmpeg x11grab failed: ' + r.stderr.decode('utf-8', errors='replace').strip()[:400])
    return r.stdout


def bind(lib, name, returns, *args):
    fn = getattr(lib, name)
    fn.restype, fn.argtypes = returns, args
    return fn


def x_input(display, action, *args):
    x11_env(display)
    try:
        x = C.CDLL('libX11.so.6')
    except OSError:
        raise Failure('X11_MISSING', 'libX11.so.6 not found.')
    ptr, int_, uint, ulong = C.c_void_p, C.c_int, C.c_uint, C.c_ulong
    open_display = bind(x, 'XOpenDisplay', ptr, C.c_char_p)
    close_display = bind(x, 'XCloseDisplay', int_, ptr)
    d = open_display(display.encode('ascii'))
    if not d:
        raise Failure('DISPLAY_ACCESS', 'Cannot open the verified local X11 session.')
    try:
        screen = bind(x, 'XDefaultScreen', int_, ptr)(d)
        width = bind(x, 'XDisplayWidth', int_, ptr, int_)(d, screen)
        height = bind(x, 'XDisplayHeight', int_, ptr, int_)(d, screen)
        root = bind(x, 'XDefaultRootWindow', ulong, ptr)(d)
        sync = bind(x, 'XSync', int_, ptr, int_)
        query = bind(x, 'XQueryPointer', int_, ptr, ulong, C.POINTER(ulong), C.POINTER(ulong),
                     C.POINTER(int_), C.POINTER(int_), C.POINTER(int_), C.POINTER(int_), C.POINTER(uint))

        def position():
            a, b, rx, ry, wx, wy, mask = ulong(), ulong(), int_(), int_(), int_(), int_(), uint()
            if not query(d, root, C.byref(a), C.byref(b), C.byref(rx), C.byref(ry), C.byref(wx), C.byref(wy), C.byref(mask)):
                raise Failure('POINTER_QUERY', 'Could not read pointer position on this X11 screen.')
            return rx.value, ry.value, mask.value

        if action == 'pointer':
            px, py, _ = position()
            return {'display': display, 'x': px, 'y': py, 'width': width, 'height': height}
        if action in ('move', 'click'):
            xp, yp = map(int, args)
            if not (0 <= xp < width and 0 <= yp < height):
                raise Failure('COORDINATES', 'Coordinates are outside the active screen.')
            if action == 'click' and position()[2]:
                raise Failure('INPUT_BUSY', 'A modifier, lock key or button is active. Do not inject a click.')
            # XTEST fake motion can be accepted but not update the core pointer on this image.
            warp = bind(x, 'XWarpPointer', int_, ptr, ulong, ulong, int_, int_, uint, uint, int_, int_)
            warp(d, 0, root, 0, 0, 0, 0, xp, yp)
            sync(d, 0)
            read_x, read_y, mask = position()
            if (read_x, read_y) != (xp, yp):
                raise Failure('POINTER_NOT_MOVED', 'The pointer did not reach the requested coordinates; no click was sent.')
            if action == 'move':
                return {'display': display, 'event': action, 'x': read_x, 'y': read_y, 'position_verified': True}
            if mask:
                raise Failure('INPUT_BUSY', 'A modifier, lock key or button is active; no click was sent.')
        try:
            xt = C.CDLL('libXtst.so.6')
        except OSError:
            raise Failure('XTEST_UNAVAILABLE', 'libXtst.so.6 is unavailable; use the remote desktop manually.')
        query_extension = bind(xt, 'XTestQueryExtension', int_, ptr, *([C.POINTER(int_)] * 4))
        vals = [int_() for _ in range(4)]
        if not query_extension(d, *(C.byref(z) for z in vals)):
            raise Failure('XTEST_UNAVAILABLE', 'Display has no XTEST extension.')
        if action == 'click':
            button = bind(xt, 'XTestFakeButtonEvent', int_, ptr, uint, int_, ulong)
            pressed = button(d, 1, 1, 0)
            released = button(d, 1, 0, 0)
            if not pressed or not released:
                raise Failure('INPUT_FAILED', 'XTEST did not accept the full click; inspect the screen.')
        elif action == 'key' and re.fullmatch(r'[A-Za-z0-9_]{1,32}', args[0]):
            sym = bind(x, 'XStringToKeysym', ulong, C.c_char_p)(args[0].encode('ascii'))
            code = bind(x, 'XKeysymToKeycode', C.c_ubyte, ptr, ulong)(d, sym)
            primary = bind(x, 'XKeycodeToKeysym', ulong, ptr, C.c_ubyte, int_)(d, code, 0) if code else 0
            if not sym or sym != primary:
                raise Failure('UNMAPPED_KEY', 'Use a directly mapped keysym; shifted characters and key chords are not supported.')
            if position()[2]:
                raise Failure('INPUT_BUSY', 'A modifier, lock key or button is active. Do not inject a key.')
            key = bind(xt, 'XTestFakeKeyEvent', int_, ptr, uint, int_, ulong)
            pressed = key(d, code, 1, 0)
            released = key(d, code, 0, 0)
            if not pressed or not released:
                raise Failure('INPUT_FAILED', 'XTEST did not accept the full key event; inspect the screen.')
        else:
            raise Failure('UNKNOWN_INPUT', 'Unsupported input action.')
        sync(d, 0)
        return {'display': display, 'event': action, 'event_sent': True, 'application_effect_verified': False}
    finally:
        close_display(d)


def pinpong_root():
    from importlib.machinery import PathFinder
    spec = PathFinder.find_spec('pinpong')  # top-level lookup, no library import
    locations = spec.submodule_search_locations if spec else None
    if not locations:
        raise Failure('PINPONG_MISSING', 'PinPong package not found in this interpreter.')
    return Path(next(iter(locations))).resolve()


def normalized(text):
    return re.sub('[^a-z0-9]', '', text.lower())


def lookup_api(query):
    if not re.fullmatch(r'[A-Za-z0-9_.-]{2,48}', query):
        raise Failure('BAD_QUERY', 'Provide a library symbol or module model.')
    root = pinpong_root()
    q = normalized(query)
    if len(q) < 2:
        raise Failure('BAD_QUERY', 'Provide a module model or symbol name.')
    candidates = [root / 'board.py']
    for folder in ('extension', 'libs'):
        candidates.extend(sorted((root / folder).rglob('*.py')))
    results = []

    def sig(node):
        if hasattr(ast, 'unparse'):
            return '(' + ast.unparse(node.args) + ')'
        return None  # Python 3.7/3.8: return source line, not a reconstructed signature.

    for path in candidates:
        if path.is_symlink():
            continue
        try:
            if path.stat().st_size > 1024 * 1024:
                continue
            tree = ast.parse(path.read_bytes())
        except (OSError, SyntaxError, ValueError):
            continue
        module = 'pinpong.' + '.'.join(path.relative_to(root).with_suffix('').parts)
        modmatch = q in normalized(module.rsplit('.', 1)[-1])
        for node in tree.body:
            name = getattr(node, 'name', '')
            name_match = q in normalized(name)
            if isinstance(node, ast.ClassDef):
                methods = [{'name': m.name, 'signature': sig(m), 'line': m.lineno} for m in node.body
                           if isinstance(m, ast.FunctionDef) and (m.name == '__init__' or not m.name.startswith('_'))
                           and (modmatch or name_match or q in normalized(m.name))]
                if (modmatch or name_match or methods) and not name.startswith('_'):
                    results.append({'module': module, 'name': name, 'kind': 'class', 'line': node.lineno, 'methods': methods[:16]})
            elif isinstance(node, ast.FunctionDef) and (modmatch or name_match) and not name.startswith('_'):
                results.append({'module': module, 'name': name, 'kind': 'function', 'signature': sig(node), 'line': node.lineno})
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and normalized(target.id) == q:
                        results.append({'module': module, 'name': target.id, 'kind': 'binding', 'line': node.lineno})
    results.sort(key=lambda row: (normalized(row['name']) != q, 'unihiker' not in row['module'], row['module'], row['line']))
    ex = root / 'examples'
    examples = [p.relative_to(root).as_posix() for p in sorted(ex.rglob('*.py'))
                if q in normalized(p.relative_to(ex).as_posix())][:12]
    return {'query': query, 'found': bool(results or examples), 'pinpong_root': str(root),
            'pinpong_version': package_versions().get('pinpong'), 'interpreter': sys.executable,
            'matches': results[:20], 'examples': examples, 'matches_truncated': len(results) > 20,
            'note': 'Static source lookup only; check M10 applicability before running an example.'}


@contextmanager
def pinpong_lock():
    fd = os.open('/run/lock/unihiker-m10-skill-pin.dat', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_uid != os.geteuid():
            raise Failure('PINPONG_LOCK', 'Unexpected owner or type on the Skill lock file.')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Failure('PINPONG_BUSY', 'Another Skill hardware command is active.')
        yield
    finally:
        os.close(fd)


def hardware(action, value):
    need_m10()
    root = pinpong_root()
    try:
        reviewed = package_versions().get('pinpong') == '0.6.2' and all(
            hashlib.sha256((root / name).read_bytes()).hexdigest() == digest for name, digest in REVIEWED_PINPONG.items())
    except OSError:
        reviewed = False
    if not reviewed:
        raise Failure('PINPONG_UNREVIEWED', 'This build was not reviewed for non-flashing initialization. Use hw api to inspect it; do not auto-upgrade or flash.')
    def stop(_signal, _frame):
        raise Failure('ACTION_INTERRUPTED', 'Hardware action was interrupted; verify the board state.')
    signal.signal(signal.SIGTERM, stop)
    with pinpong_lock(), redirect_stdout(io.StringIO()):
        from pinpong.board import Board, Pin
        from pinpong.extension.unihiker import button_a, button_b, light
        board = Board('UNIHIKER')
        if board.boardname != 'UNIHIKER':
            raise Failure('WRONG_BOARD', 'PinPong did not resolve UNIHIKER.')
        board.begin(0)  # For the reviewed build only: never pass firmware=1.
        if action == 'read':
            if value == 'light':
                reading = light.read()
                if not 0 <= reading <= 4095:
                    raise Failure('SENSOR_RANGE', 'Light reading is outside the expected raw range.')
                return {'sensor': value, 'value': int(reading), 'unit': 'raw', 'range': [0, 4095]}
            button = {'button-a': button_a, 'button-b': button_b}.get(value)
            if button is None:
                raise Failure('UNKNOWN_SENSOR', 'Unsupported sensor.')
            return {'sensor': value, 'pressed': bool(button.is_pressed())}
        count = int(value)
        if not 1 <= count <= 5:
            raise Failure('BLINK_COUNT', 'Blink count must be 1..5.')
        led = Pin(Pin.P25, Pin.OUT)
        try:
            for _ in range(count):
                led.write_digital(1)
                time.sleep(0.3)
                led.write_digital(0)
                time.sleep(0.3)
        finally:
            led.write_digital(0)
        return {'led': 'onboard L/P25', 'cycles_completed': count, 'off_command_sent': True, 'physical_effect_verified': False}


def main(task, values):
    if task == 'status':
        return status()
    if task == 'python':
        return python_info()
    if task == 'wifi':
        return wifi_info()
    if task == 'shot':
        return screenshot(*values)
    if task == 'input':
        return x_input(*values)
    if task == 'api':
        return lookup_api(*values)
    if task in ('read', 'blink'):
        return hardware(task, *values)
    if task == 'calibration':
        need_m10()
        return {'tool_present': bool(shutil.which('ts_calibrate')), 'performed': False,
                'menu': 'Home > 校准触摸屏', 'physical_interaction_required': True, 'may_reboot': True}
    raise Failure('UNKNOWN_TASK', 'Unsupported board task.')


if __name__ == '__main__':
    try:
        result = main(sys.argv[1], sys.argv[2:])
        if isinstance(result, bytes):
            sys.stdout.buffer.write(result)
        else:
            print(json.dumps({'ok': True, **result}, ensure_ascii=True))
    except (Failure, subprocess.TimeoutExpired, OSError, ValueError, ImportError) as exc:
        print(json.dumps({'ok': False, 'code': getattr(exc, 'code', 'BOARD_PROBE_FAILED'), 'message': str(exc)}, ensure_ascii=True))
