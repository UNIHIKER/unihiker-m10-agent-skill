import base64
import hashlib
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('m10_host', ROOT / 'scripts/host/m10.py')
m10 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m10)
ARGS = ['--host', '192.0.2.10', '--user', 'tester']
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/a1kAAAAASUVORK5CYII=')


class HostTests(unittest.TestCase):
    def test_ui_and_hardware_require_confirmation_before_connection(self):
        for cmd in (['screen', 'click', '10', '20'], ['screen', 'move', '10', '20'],
                    ['screen', 'key', 'Return'], ['hw', 'read', 'light'], ['hw', 'blink']):
            with self.subTest(cmd=cmd), patch.object(m10, 'Ssh') as ssh:
                with self.assertRaises(m10.Failure) as exc:
                    m10.dispatch(m10.arguments(ARGS + cmd))
                self.assertEqual(exc.exception.code, 'CONFIRMATION_REQUIRED')
                ssh.assert_not_called()

    def test_invalid_remote_path_and_display(self):
        with patch.object(m10, 'Ssh') as ssh, self.assertRaises(m10.Failure):
            m10.dispatch(m10.arguments(ARGS + ['python', 'run', '--version', '3.12.7', 'desktop.py']))
        ssh.assert_not_called()
        with patch('sys.stderr'), self.assertRaises(SystemExit):
            m10.arguments(ARGS + ['screen', 'shot', '--display', ':0;date', '--output', 'x.png'])

    def test_version_choice_is_per_command(self):
        command = m10.remote_python('3.12.7', ['/tmp/a b.py', 'a; do not execute'])
        self.assertIn('export PYENV_VERSION=3.12.7', command)
        self.assertIn('exec python', command)
        self.assertNotIn('pyenv global', command)
        self.assertTrue(command.startswith('sh -c '))

    def test_python_mismatch_stops_before_script(self):
        args = m10.arguments(ARGS + ['python', 'run', '--version', '3.12.7', '/tmp/test.py'])
        with patch.object(m10, 'Ssh') as ssh:
            remote = ssh.return_value
            remote.run.return_value = b'{"version": "3.8.5", "executable": "/usr/bin/python3"}'
            with self.assertRaises(m10.Failure) as err:
                m10.dispatch(args)
            self.assertEqual(err.exception.code, 'PYTHON_VERSION_MISMATCH')
            self.assertEqual(remote.run.call_count, 1)

    def test_error_classification(self):
        for err, code, status in (
            (b'WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!', 'HOST_KEY_REJECTED', 255),
            (b'FATAL ERROR: Host key not in manually configured list', 'HOST_KEY_REJECTED', 1),
            (b'Permission denied (publickey).', 'AUTH_FAILED', 255),
            (b'Permission denied: opening input device', 'REMOTE_FAILED', 1),
            (b'', 'REMOTE_TIMEOUT', 124),
        ):
            result = subprocess.CompletedProcess([], status, b'', err)
            self.assertEqual(m10.classify_ssh(result).code, code)

    def test_scan_keys_returns_exact_pinnable_row(self):
        blob = b'public-key-blob-test'
        token = base64.b64encode(blob)
        output = b'# ignored\nunexpected-alias ssh-ed25519 ' + token + b'\n'
        expected = 'SHA256:' + base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip('=')
        with patch.object(m10, 'required', return_value='ssh-keyscan'), patch.object(m10, 'invoke') as invoke:
            invoke.return_value = subprocess.CompletedProcess([], 0, output, b'')
            self.assertEqual(m10.scan_keys('192.0.2.10', 2222), {
                expected: b'[192.0.2.10]:2222 ssh-ed25519 ' + token + b'\n'})

    def test_pin_mismatch_stops_before_ssh(self):
        with patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as tmp, patch.object(m10, 'scan_keys', return_value={}):
            args = m10.arguments(ARGS + ['--host-key', 'SHA256:' + 'A' * 43, 'status'])
            with self.assertRaises(m10.Failure) as err:
                m10.Ssh(args, tmp)
            self.assertEqual(err.exception.code, 'HOST_KEY_REJECTED')

    def test_password_requires_pin(self):
        with patch.dict(os.environ, {m10.PASSWORD_ENV: 'test-only-not-a-real-secret'}), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(m10.Failure) as err:
                m10.Ssh(m10.arguments(ARGS + ['status']), tmp)
            self.assertEqual(err.exception.code, 'PIN_REQUIRED')

    def test_save_png_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'sample.png'
            info = m10.save_png(PNG, path)
            self.assertEqual((info['width'], info['height']), (1, 1))
            with self.assertRaises(m10.Failure) as err:
                m10.save_png(PNG, path)
            self.assertEqual(err.exception.code, 'OUTPUT_EXISTS')
            self.assertEqual(path.read_bytes(), PNG)
            with self.assertRaises(m10.Failure) as err:
                m10.save_png(PNG[:-8], Path(tmp) / 'partial.png')
            self.assertEqual(err.exception.code, 'INVALID_PNG')
            self.assertFalse((Path(tmp) / 'partial.png').exists())


if __name__ == '__main__':
    unittest.main()
