import ast
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/board/probe.py'
SPEC = importlib.util.spec_from_file_location('m10_probe', SCRIPT)
probe = importlib.util.module_from_spec(SPEC)
if os.name == 'nt':
    with patch.dict(sys.modules, {'fcntl': Mock()}):
        SPEC.loader.exec_module(probe)
else:
    SPEC.loader.exec_module(probe)


class BoardTests(unittest.TestCase):
    def test_board_source_parses_on_python_37(self):
        ast.parse(SCRIPT.read_text(encoding='utf-8'), feature_version=(3, 7))

    def test_home_config_minimizes_sensitive_fields(self):
        config = {'language': 'zh-cn.json', 'AutoStart': False, 'apPassword': 'secret', 'path': '/private/notes.py'}
        with patch.object(probe, 'read_file', return_value=json.dumps(config)):
            self.assertEqual(probe.home_info(), {'language': 'zh-cn.json', 'AutoStart': False})

    def test_api_lookup_uses_ast_instead_of_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for folder in ('libs', 'extension', 'examples/UNIHIKER'):
                (root / folder).mkdir(parents=True)
            (root / 'libs/sample_sensor.py').write_text('raise RuntimeError("do not execute")\nclass SampleSensor:\n    def read(self, n=3):\n        pass\n', encoding='utf-8')
            (root / 'examples/UNIHIKER/sample_sensor.py').touch()
            with patch.object(probe, 'pinpong_root', return_value=root), patch.object(probe, 'package_versions', return_value={'pinpong': 'test'}):
                info = probe.lookup_api('SampleSensor')
                self.assertTrue(info['found'])
                self.assertEqual(info['matches'][0]['module'], 'pinpong.libs.sample_sensor')
                self.assertEqual(info['matches'][0]['methods'][0]['signature'], '(self, n=3)')
                self.assertEqual(info['examples'], ['examples/UNIHIKER/sample_sensor.py'])
                self.assertFalse(probe.lookup_api('NoSuchSensor')['found'])

    def test_unreviewed_pinpong_is_blocked_before_lock_or_import(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(probe, 'need_m10'), \
                patch.object(probe, 'pinpong_root', return_value=Path(tmp)), \
                patch.object(probe, 'package_versions', return_value={'pinpong': '0.6.2'}), patch.object(probe, 'pinpong_lock') as lock:
            with self.assertRaises(probe.Failure) as err:
                probe.hardware('read', 'light')
            self.assertEqual(err.exception.code, 'PINPONG_UNREVIEWED')
            lock.assert_not_called()

    def test_unknown_calibration_layout_is_not_touched(self):
        with patch.object(probe, 'read_file', return_value=None):
            with self.assertRaises(probe.Failure) as err:
                probe.main('calibration', [])
            self.assertEqual(err.exception.code, 'M10_MARKERS_MISSING')


if __name__ == '__main__':
    unittest.main()
