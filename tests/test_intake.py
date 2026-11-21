import http.client
import json
import re
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from hospital_ops.core import Store, load_config
from hospital_ops.watch import scan

ROOT = Path(__file__).resolve().parent.parent


class IntakeTests(unittest.TestCase):
    def test_folder_intake_duplicates_and_bad_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'morning.vtt').write_text((ROOT / 'examples/morning.vtt').read_text(), encoding='utf-8')
            meeting = {'id': 'example-am', 'kind': 'plan_ahead_am', 'startsAt': '2026-01-05T09:00:00-05:00', 'transcriptFile': 'morning.vtt'}
            (root / 'one.meeting.json').write_text(json.dumps(meeting))
            (root / 'one.review.json').write_text((ROOT / 'templates/review.example.json').read_text())
            store = Store(root / 'ops.sqlite', load_config(ROOT / 'config/site.example.json'))
            try:
                changed, errors = scan(store, root)
                self.assertTrue(changed)
                self.assertEqual(errors, [])
                self.assertFalse(scan(store, root)[0])
                meeting['transcriptFile'] = '../outside.vtt'
                (root / 'bad.meeting.json').write_text(json.dumps(meeting))
                self.assertEqual(len(scan(store, root)[1]), 1)
                self.assertEqual(len(store.records('review')), 1)
            finally:
                store.close()

    def test_local_http_workflow_and_request_guards(self):
        with tempfile.TemporaryDirectory() as folder:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            proc = subprocess.Popen([sys.executable, '-m', 'hospital_ops', '--db', str(Path(folder) / 'ops.sqlite'), 'serve', '--port', str(port)], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            try:
                self.assertIn('Local workbench', proc.stdout.readline())
                def request(path, body=None, token=None, origin=None, host=None):
                    conn = http.client.HTTPConnection('127.0.0.1', port, timeout=5)
                    headers = {'Content-Type': 'application/json'}
                    if token: headers['X-CSRF-Token'] = token
                    if origin: headers['Origin'] = origin
                    if host: headers['Host'] = host
                    conn.request('GET' if body is None else 'POST', path, json.dumps(body) if body is not None else None, headers)
                    response = conn.getresponse()
                    data = response.read().decode()
                    status = response.status
                    conn.close()
                    return status, data
                status, text = request('/')
                self.assertEqual(status, 200)
                token = json.loads(re.search(r'const csrf=("[^"]+");', text).group(1))
                self.assertEqual(request('/api/draft', {}, token=token, origin='https://untrusted.example')[0], 403)
                self.assertEqual(request('/', host='untrusted.example')[0], 403)
                status, text = request('/api/ingest', {'text': (ROOT / 'examples/morning.vtt').read_text(), 'kind': 'plan_ahead_am', 'startsAt': '2026-01-05T09:00:00-05:00', 'sourceLabel': 'Synthetic test'}, token=token)
                self.assertEqual(status, 200)
                mid = json.loads(text)['id']
                self.assertEqual(request('/api/draft', {'meetingId': mid}, token=token)[0], 200)
                review = json.loads((ROOT / 'templates/review.example.json').read_text())
                review['meetingId'] = mid
                self.assertEqual(request('/api/review', review, token=token)[0], 200)
                status, report = request('/report.json?date=2026-01-05')
                self.assertEqual(status, 200)
                self.assertEqual(json.loads(report)['issues'][0]['state'], 'active')
                self.assertEqual(request('/api/review', review)[0], 403)
            finally:
                proc.terminate()
                proc.communicate(timeout=10)


if __name__ == '__main__':
    unittest.main()
