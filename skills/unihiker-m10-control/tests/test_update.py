from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('m10_update', ROOT / 'scripts/host/check_update.py')
update = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(update)


class UpdateTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.version = Path(directory.name) / 'VERSION'
        self.version.write_text('0.9.0\n', encoding='ascii')
        for patcher in (patch.object(update, 'VERSION_FILE', self.version),
                        patch.dict(os.environ, {update.SKIP_ENV: '0'})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            self.assertEqual(update.main(list(args)), 0)
        self.assertEqual(err.getvalue(), '')
        return out.getvalue()

    def test_notice_for_numerically_newer_stable_release(self):
        payload = {'tag_name': 'v0.10.0', 'html_url': 'https://example.invalid', 'body': 'Not forwarded.'}
        with patch.object(update, 'urlopen', return_value=io.BytesIO(json.dumps(payload).encode())) as fetch:
            output = self.cli()
        self.assertIn('v0.9.0 -> v0.10.0', output)
        self.assertIn(update.RELEASES, output)
        self.assertNotIn('example.invalid', output)
        self.assertNotIn('Not forwarded.', output)
        self.assertEqual(fetch.call_args.args[0].full_url, update.API)

    def test_equal_or_older_release_is_silent(self):
        for latest in ('0.9.0', '0.8.9'):
            with self.subTest(latest=latest), patch.object(update, 'fetch_latest', return_value=latest):
                self.assertEqual(self.cli(), '')
                self.assertEqual(json.loads(self.cli('--verbose'))['status'], 'up_to_date')

    def test_offline_or_no_release_is_silent(self):
        for failure in (URLError('offline'), HTTPError(update.API, 404, 'Not Found', {}, None)):
            with self.subTest(failure=failure), patch.object(update, 'urlopen', side_effect=failure):
                self.assertEqual(self.cli(), '')
                self.assertEqual(json.loads(self.cli('--verbose'))['status'], 'unavailable')

    def test_bad_versions_and_prereleases_are_ignored(self):
        for payload in ({'tag_name': 'v1.0.0-rc.1'}, {'tag_name': 'v1.0.0', 'prerelease': True},
                        {'tag_name': 'v1.0.0', 'draft': True}, {'tag_name': None}, []):
            with self.subTest(payload=payload), patch.object(update, 'urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
                self.assertEqual(self.cli(), '')

    def test_skip_does_not_fetch(self):
        with patch.dict(os.environ, {update.SKIP_ENV: '1'}), patch.object(update, 'urlopen') as fetch:
            self.assertEqual(self.cli(), '')
            self.assertEqual(json.loads(self.cli('--verbose'))['status'], 'skipped')
            fetch.assert_not_called()

    def test_missing_local_version_does_not_fetch(self):
        self.version.unlink()
        with patch.object(update, 'urlopen') as fetch:
            self.assertEqual(self.cli(), '')
            self.assertEqual(json.loads(self.cli('--verbose'))['reason'], 'invalid_local_version')
            fetch.assert_not_called()

    def test_deadline_does_not_wait_for_stalled_lookup(self):
        with patch.object(update, 'Thread') as worker:
            self.assertEqual(update.check(timeout=0.02)['reason'], 'timeout')
            self.assertTrue(worker.call_args.kwargs['daemon'])
            worker.return_value.start.assert_called_once()


if __name__ == '__main__':
    unittest.main()
