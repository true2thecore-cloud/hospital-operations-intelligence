"""Loopback-only local workbench. Not an enterprise hosted service."""
import json
import secrets
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from .core import Store, load_config
from .render import STYLE, esc, render_report


def page(config, token):
    options = ''.join('<option value="' + esc(m['key']) + '">' + esc(m['label']) + '</option>' for m in config['meetings'])
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Operations Workbench</title><style>''' + STYLE + '''</style><main>
<header><div class="eyebrow">Hospital operations intelligence</div><h1>Turn meeting evidence into follow-through.</h1><div class="sub">Local workbench | Upload, review, connect, brief</div></header>
<div class="grid two"><section class="card"><h2>1. Import a meeting</h2><label>Meeting<select id="kind">''' + options + '''</select></label>
<label>Meeting start, local time with UTC offset<input id="starts" placeholder="2027-01-04T09:00:00-05:00"></label><label>VTT transcript<input id="vtt" type="file" accept=".vtt"></label><button id="ingest">Import transcript</button>
<p class="muted">The import retains source cues. Mentions become suggestions for your review, not confirmed risks.</p></section>
<section class="card"><h2>2. Review the evidence</h2><label>Meeting ID<input id="meetingId"></label><button id="draft">Get review draft</button><p class="muted">Review the suggestions below. Edit the reviewTemplate into a standalone JSON file using the example in templates/review.example.json, then import it here.</p><input id="review" type="file" accept=".json"><button id="saveReview">Import reviewed observations</button></section></div>
<div class="grid two"><section class="card"><h2>3. Connect staffing or handoff</h2><select id="snapshotKind"><option value="staffing">Staffing A1:L46</option><option value="handoff">Forms handoff responses</option></select><input id="snapshot" type="file" accept=".json"><button id="saveSnapshot">Import companion snapshot</button><p class="muted">Use the export scripts in the companion repository. Dates and capture times remain visible.</p></section>
<section class="card"><h2>4. Open the leadership brief</h2><label>Report date<input id="day" type="date" value="''' + date.today().isoformat() + '''"></label><button id="report">Open brief</button><p><a id="jsonLink" href="#">Download report JSON for Excel</a></p></section></div>
<section class="card"><h2>Result and evidence</h2><pre id="result" style="white-space:pre-wrap;overflow-wrap:anywhere">Ready.</pre></section><footer>Use an organization-approved device and storage location. This local service does not send transcripts to an AI provider.</footer></main>
<script>
const csrf=''' + json.dumps(token) + ''';
const el=id=>document.getElementById(id);
async function file(id){if(!el(id).files.length)throw Error('Choose a file first.');return el(id).files[0].text()}
async function send(path,body){let r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify(body)});let v=await r.json();if(!r.ok)throw Error(v.error);el('result').textContent=JSON.stringify(v,null,2);return v}
function action(id,fn){el(id).onclick=()=>fn().catch(e=>el('result').textContent=e.message)}
action('ingest',async()=>{let v=await send('/api/ingest',{text:await file('vtt'),kind:el('kind').value,startsAt:el('starts').value,sourceLabel:el('vtt').files[0].name});el('meetingId').value=v.id});
action('draft',()=>send('/api/draft',{meetingId:el('meetingId').value}));
action('saveReview',async()=>send('/api/review',JSON.parse(await file('review'))));
action('saveSnapshot',async()=>send('/api/snapshot',{kind:el('snapshotKind').value,payload:JSON.parse(await file('snapshot'))}));
el('report').onclick=()=>window.open('/report?date='+encodeURIComponent(el('day').value),'_blank','noopener');
el('jsonLink').onclick=()=>{el('jsonLink').href='/report.json?date='+encodeURIComponent(el('day').value)};
</script></html>'''


def serve(db_path, config_path, port=8765):
    config = load_config(config_path)
    token = secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def allowed(self):
            return self.headers.get('Host') in (f'127.0.0.1:{port}', f'localhost:{port}')

        def reply(self, status, content, content_type='application/json; charset=utf-8'):
            data = content.encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('X-Frame-Options', 'DENY')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if not self.allowed():
                return self.reply(403, '{"error":"Invalid host"}')
            route = urlparse(self.path)
            if route.path == '/':
                return self.reply(200, page(config, token), 'text/html; charset=utf-8')
            if route.path not in ('/report', '/report.json'):
                return self.reply(404, '{"error":"Not found"}')
            store = Store(db_path, config)
            try:
                day = parse_qs(route.query).get('date', [date.today().isoformat()])[0]
                report = store.report(day)
                self.reply(200, render_report(report) if route.path == '/report' else json.dumps(report), 'text/html; charset=utf-8' if route.path == '/report' else 'application/json; charset=utf-8')
            except (ValueError, KeyError, TypeError) as err:
                self.reply(400, json.dumps({'error': str(err)}))
            finally:
                store.close()

        def do_POST(self):
            origin = self.headers.get('Origin')
            if not self.allowed() or self.headers.get('X-CSRF-Token') != token or origin not in (None, f'http://127.0.0.1:{port}', f'http://localhost:{port}'):
                return self.reply(403, '{"error":"Invalid local request"}')
            store = Store(db_path, config)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 3_000_000:
                    raise ValueError('Request must be under 3 MB.')
                body = json.loads(self.rfile.read(length))
                if self.path == '/api/ingest':
                    m = store.ingest_vtt(body['text'], body['kind'], body['startsAt'], body['sourceLabel'])
                    result = {'id': m['id'], 'cues': len(m['cues']), 'status': 'awaiting_review'}
                elif self.path == '/api/draft':
                    result = store.draft_review(body['meetingId'])
                elif self.path == '/api/review':
                    r = store.add_review(body)
                    result = {'id': r['id'], 'status': 'reviewed'}
                elif self.path == '/api/snapshot':
                    s = store.add_snapshot(body['kind'], body['payload'])
                    result = {'id': s['id'], 'status': 'imported'}
                else:
                    return self.reply(404, '{"error":"Not found"}')
                self.reply(200, json.dumps(result))
            except (ValueError, KeyError, TypeError, AttributeError) as err:
                self.reply(400, json.dumps({'error': str(err)}))
            finally:
                store.close()

        def log_message(self, *_):
            pass  # Do not log transcript contents or URLs.
    server = HTTPServer(('127.0.0.1', port), Handler)
    print(f'Local workbench: http://127.0.0.1:{port} (Ctrl+C to stop)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
