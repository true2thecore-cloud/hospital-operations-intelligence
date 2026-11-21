"""Escaped, self-contained leadership reports. No external scripts or fonts."""
import csv
import html
import io
import json


def esc(value):
    return html.escape(str(value))


STYLE = """
:root{color-scheme:light;--navy:#17344c;--teal:#087f8c;--muted:#526577;--line:#dce5ed}
*{box-sizing:border-box}body{margin:0;background:#f2f6f9;color:#20354a;font:15px/1.5 system-ui,Segoe UI,sans-serif}
main{max-width:1280px;margin:auto;padding:30px}header{background:var(--navy);color:white;padding:32px;border-radius:18px}
h1{font-size:32px;margin:5px 0 10px;line-height:1.15}h2{font-size:20px;margin:0 0 14px}h3{font-size:16px;margin:0 0 8px}
.eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase}.sub{color:#d5e6f1}.muted{color:var(--muted);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:20px 0}.two{grid-template-columns:1.3fr 1fr}
.card{background:white;border:1px solid var(--line);border-radius:14px;padding:22px;overflow-wrap:anywhere}.number{font-size:36px;font-weight:750;color:var(--teal)}
.pill{display:inline-block;border-radius:20px;background:#e8f5f4;color:#12605d;padding:4px 10px;font-size:12px;font-weight:650}
.amber{background:#fff1cc;color:#795407}.gray{background:#edf1f5;color:#526577}.item{border-top:1px solid var(--line);padding:14px 0}.item:first-of-type{border:0}
table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-weight:650;background:#f5f8fa}
.scroll{overflow:auto}details{margin:10px 0}summary{cursor:pointer;color:var(--teal);font-weight:600}blockquote{border-left:3px solid #93b7c8;padding-left:12px;margin:10px 0;color:var(--muted)}
button,.button{background:var(--teal);color:white;border:0;border-radius:8px;padding:10px 16px;font:inherit;cursor:pointer;text-decoration:none;display:inline-block}
input,select,textarea{font:inherit;padding:9px;border:1px solid #aabcca;border-radius:6px;width:100%;margin:5px 0 12px}label{display:block;font-weight:600}textarea{min-height:120px}
footer{color:var(--muted);font-size:12px;margin-top:20px}.banner{margin-top:12px;background:#fff1cc;color:#694d0d;border-radius:7px;padding:10px}.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
@media(max-width:800px){main{padding:14px}.grid,.two{grid-template-columns:1fr}header{padding:22px}h1{font-size:27px}}
@media print{body{background:white}main{padding:0}.card,header{break-inside:avoid}.no-print{display:none}}
"""


def render_report(report):
    active = [i for i in report["issues"] if i["state"] == "active"]
    unknown = [i for i in report["issues"] if i["state"] == "unknown"]
    synthetic = report["datasetMode"] == "synthetic"
    out = [f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Operations Brief</title><style>{STYLE}</style><main>',
           f'<header><div class="eyebrow">{esc(report["siteLabel"])} / Operations intelligence</div><h1>The plan. The changes. The follow-through.</h1><div class="sub">{esc(report["date"])} | Evidence available through {esc(report["asOfUtc"])}</div>',
           '<div class="banner">SYNTHETIC DEMONSTRATION. All meetings, issues and outcomes are invented.</div>' if synthetic else '', '</header>',
           '<div class="grid">',
           f'<div class="card"><div class="muted">Confirmed open issues, including carry-forward</div><div class="number">{len(active)}</div><span class="pill amber">{len(unknown)} uncertain status</span></div>',
           f'<div class="card"><div class="muted">Meetings available today</div><div class="number">{len(report["meetings"])}</div><span class="pill">{sum(m["reviewed"] for m in report["meetings"])} reviewed</span></div>',
           f'<div class="card"><div class="muted">Patterns to review</div><div class="number">{len(report["warnings"])}</div><span class="pill gray">Evidence, then leadership judgment</span></div></div>',
           '<div class="grid two"><section class="card"><h2>Meeting sequence</h2>']
    for m in report["meetings"]:
        out.append(f'<div class="item"><span class="pill {"" if m["reviewed"] else "amber"}">{"Reviewed" if m["reviewed"] else "Awaiting review"}</span><h3>{esc(m["kind"].replace("_", " ").title())}</h3><div>{esc(m["startsAt"])}</div><div class="muted">{esc(m["sourceLabel"])}</div></div>')
    if not report["meetings"]:
        out.append('<p>No meeting evidence available for this date.</p>')
    out.append('<p class="muted">Not yet imported: ' + esc(", ".join(report["missingMeetings"]) or "None") + '. This can include future meetings.</p></section><section class="card"><h2>Early-warning review</h2>')
    for w in report["warnings"]:
        h = w["history"]
        out.append(f'<div class="item"><span class="pill amber">{esc(w["status"])}</span><h3>{esc(w["label"])}</h3><p>{esc(w["action"])}</p><p class="muted">{h["events"]} of {h["matchedDays"]} comparable earlier days had the configured outcome. Baseline: {h["baselineEvents"]} of {h["baselineDays"]}. Unknown outcomes: {h["unknownOutcomeDays"]}.</p><p class="muted">{esc(w["interpretation"])}</p></div>')
    if not report["warnings"]:
        out.append('<p>No configured pattern is currently supported by the reviewed inputs. Missing evidence is not an all-clear.</p>')
    out.append('</section></div><section class="card"><h2>Issues and accountable follow-through</h2>')
    for issue in sorted(report["issues"], key=lambda x: (x["state"] == "cleared", x["date"], x["issueId"])):
        evidence = ''.join(f'<blockquote>{esc(e["start"])}: {esc(e["text"])}</blockquote>' for e in issue["evidence"])
        out.append(f'<div class="item"><span class="pill {"amber" if issue["state"] == "active" else "gray"}">{esc(issue["state"].title())}</span> <strong>{esc(issue["summary"])}</strong><p>Owner: {esc(issue["owner"])} | Due: {esc(issue["due"])}</p><p>{esc(issue["action"])}</p><div class="muted">{esc(issue["issueId"])} | Last evidence: {esc(issue["date"])} / {esc(issue["meetingKind"])}</div><details><summary>Show source evidence</summary>{evidence}</details></div>')
    if not report["issues"]:
        out.append('<p>No reviewed issues yet. Upload a transcript, review its evidence, then import a review.</p>')
    out.append('</section><div class="grid two"><section class="card"><h2>Staffing connection</h2>')
    staffing = report["snapshots"].get("staffing")
    if staffing:
        p = staffing["payload"]
        out.append(f'<p><strong>Assignment date: {esc(p["staffingDate"])}</strong><br>Source tab: {esc(p["sourceSheet"])}<br><span class="muted">Captured {esc(p["capturedUtc"])} | Imported {esc(staffing["receivedAt"])}</span></p>')
        if p["staffingDate"] != report["date"]:
            out.append('<span class="pill amber">Different assignment date from this brief</span>')
        out.append('<details><summary>View complete A1:L46 staffing snapshot</summary><div class="scroll"><table>')
        for n, row in enumerate(p["values"], 1):
            out.append('<tr><th>' + str(n) + '</th>' + ''.join('<td>' + esc(x) + '</td>' for x in row) + '</tr>')
        out.append('</table></div></details>')
    else:
        out.append('<p>No staffing snapshot imported. Export from the companion workbook to connect it.</p>')
    out.append('</section><section class="card"><h2>Charge nurse handoff</h2>')
    handoff = report["snapshots"].get("handoff")
    if handoff:
        p = handoff["payload"]
        out.append(f'<p>{len(p["rows"])} response rows in the imported snapshot.</p><p class="muted">Imported {esc(handoff["receivedAt"])}</p><details><summary>Review response records</summary><div class="scroll"><table><tr>' + ''.join('<th>' + esc(x) + '</th>' for x in p["headers"]) + '</tr>')
        # Preserve source order. Do not claim the last row is the latest submission.
        for row in p["rows"][-30:]:
            out.append('<tr>' + ''.join('<td>' + esc(x) + '</td>' for x in row) + '</tr>')
        out.append('</table></div><p class="muted">Showing up to 30 rows in source order, not timestamp order. Snapshots are context, not confirmed meeting observations.</p></details>')
    else:
        out.append('<p>No handoff snapshot imported.</p>')
    out.append('</section></div><footer>Operational decision support. Records show available evidence and review status. Missing information stays unknown. Generated ' + esc(report["generatedUtc"]) + '.</footer></main></html>')
    return ''.join(out)


def issues_csv(report):
    out = io.StringIO(newline='')
    writer = csv.writer(out)
    fields = ['issueId', 'state', 'summary', 'owner', 'action', 'due', 'date', 'meetingId']
    writer.writerow(fields)
    for issue in report['issues']:
        # Prevent formula interpretation when opened directly in Excel.
        writer.writerow([("'" + str(issue[k])) if str(issue[k]).lstrip().startswith(('=', '+', '-', '@')) else issue[k] for k in fields])
    return out.getvalue()
