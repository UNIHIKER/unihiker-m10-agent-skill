#!/usr/bin/env python3
"""Check the public stable Skill release; never download or install an update."""
import argparse
from http.client import HTTPException
import json
import os
from pathlib import Path
from queue import Empty, Queue
import re
from threading import Thread
from urllib.request import Request, urlopen

VERSION_FILE = Path(__file__).resolve().parents[2] / 'VERSION'
REPO = 'UNIHIKER/unihiker-m10-agent-skill'
API = f'https://api.github.com/repos/{REPO}/releases/latest'
RELEASES = f'https://github.com/{REPO}/releases'
SKIP_ENV = 'UNIHIKER_M10_SKIP_UPDATE_CHECK'
TIMEOUT = 3.0
MAX_BYTES = 512 * 1024
STABLE_VERSION = re.compile(r'v?(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})\.(0|[1-9][0-9]{0,8})')


def version_tuple(value):
    match = STABLE_VERSION.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError('expected a stable major.minor.patch version')
    return tuple(int(part) for part in match.groups())


def fetch_latest(timeout):
    request = Request(API, headers={'Accept': 'application/vnd.github+json',
                                    'User-Agent': 'unihiker-m10-agent-skill-update-check'})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('release metadata too large')
    release = json.loads(raw)
    if not isinstance(release, dict) or release.get('draft') or release.get('prerelease'):
        raise ValueError('no stable release')
    value = release.get('tag_name')
    version_tuple(value)
    return value.removeprefix('v')


def check(timeout=TIMEOUT):
    try:
        installed = VERSION_FILE.read_text(encoding='ascii').strip()
        current = version_tuple(installed)
    except (OSError, ValueError):
        return {'status': 'unavailable', 'reason': 'invalid_local_version'}

    installed = installed.removeprefix('v')
    if os.environ.get(SKIP_ENV) == '1':
        return {'status': 'skipped', 'installed': installed}

    results = Queue(maxsize=1)

    def lookup():
        try:
            results.put(fetch_latest(timeout))
        except (OSError, ValueError, HTTPException):
            results.put(None)

    # Socket timeouts alone do not bound slow DNS or a series of slow reads.
    Thread(target=lookup, daemon=True).start()
    try:
        latest = results.get(timeout=timeout)
    except Empty:
        return {'status': 'unavailable', 'installed': installed, 'reason': 'timeout'}
    if latest is None:
        return {'status': 'unavailable', 'installed': installed, 'reason': 'release_check_failed'}
    if version_tuple(latest) > current:
        return {'status': 'update_available', 'installed': installed, 'latest': latest, 'url': RELEASES}
    return {'status': 'up_to_date', 'installed': installed, 'latest': latest}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', action='store_true', help='Report all outcomes as JSON for manual troubleshooting.')
    args = parser.parse_args(argv)
    result = check()
    if args.verbose:
        print(json.dumps(result, ensure_ascii=True))
    elif result['status'] == 'update_available':
        print(f"UNIHIKER M10 Control update available: v{result['installed']} -> v{result['latest']}. "
              f"To update: {result['url']}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
