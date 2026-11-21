import argparse
import json
import sys
from pathlib import Path
from .core import Store, load_config, staffing_date
from .render import render_report, issues_csv


def write_json(value, path=None):
    text = json.dumps(value, indent=2, ensure_ascii=False)
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        print(text)


def main():
    p = argparse.ArgumentParser(description="Hospital operations meeting memory and evidence-backed briefs")
    p.add_argument('--config', default='config/site.example.json')
    p.add_argument('--db', default='data/operations.sqlite')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('init')
    ingest = sub.add_parser('ingest')
    ingest.add_argument('file')
    ingest.add_argument('--kind', required=True)
    ingest.add_argument('--starts-at', required=True, help='Local ISO date/time with offset, e.g. 2027-01-04T09:00:00-05:00')
    ingest.add_argument('--meeting-id')
    draft = sub.add_parser('draft')
    draft.add_argument('meeting_id')
    draft.add_argument('--out')
    review = sub.add_parser('review')
    review.add_argument('file')
    snap = sub.add_parser('snapshot')
    snap.add_argument('kind', choices=['staffing', 'handoff'])
    snap.add_argument('file')
    report = sub.add_parser('report')
    report.add_argument('--date', required=True)
    report.add_argument('--as-of')
    report.add_argument('--out', default='data/latest')
    evaluate = sub.add_parser('evaluate')
    evaluate.add_argument('--as-of')
    evaluate.add_argument('--out')
    serve = sub.add_parser('serve')
    serve.add_argument('--port', type=int, default=8765)
    watcher = sub.add_parser('watch')
    watcher.add_argument('--inbox', required=True)
    watcher.add_argument('--out', required=True)
    watcher.add_argument('--interval', type=int, default=60)
    watcher.add_argument('--once', action='store_true')
    demo = sub.add_parser('demo')
    demo.add_argument('--out', default='data/demo')
    choose = sub.add_parser('staffing-date')
    choose.add_argument('date')
    choose.add_argument('--mode', default='next-business-day', choices=['next-business-day', 'same-date', 'explicit-date'])
    choose.add_argument('--explicit-date')
    choose.add_argument('--holiday', action='append', default=[])
    graph = sub.add_parser('graph-pull')
    graph.add_argument('--organizer', required=True)
    graph.add_argument('--meeting-id', required=True)
    graph.add_argument('--kind', required=True)
    graph.add_argument('--starts-at', required=True)
    args = p.parse_args()
    if args.command == 'staffing-date':
        print(staffing_date(args.date, args.mode, args.explicit_date, args.holiday))
        return
    if args.command == 'demo':
        from .demo import create_demo
        print(create_demo(args.out))
        return
    if args.command == 'serve':
        from .server import serve
        serve(args.db, args.config, args.port)
        return
    if args.command == 'watch':
        from .watch import watch
        watch(args.db, args.config, args.inbox, args.out, args.interval, args.once)
        return
    store = Store(args.db, load_config(args.config))
    try:
        if args.command == 'init':
            print('Operational database ready: ' + args.db)
        elif args.command == 'ingest':
            write_json(store.ingest_vtt(Path(args.file).read_text(encoding='utf-8-sig'), args.kind, args.starts_at, Path(args.file).name, args.meeting_id))
        elif args.command == 'draft':
            write_json(store.draft_review(args.meeting_id), args.out)
        elif args.command == 'review':
            write_json(store.add_review(json.loads(Path(args.file).read_text(encoding='utf-8-sig'))))
        elif args.command == 'snapshot':
            value = store.add_snapshot(args.kind, json.loads(Path(args.file).read_text(encoding='utf-8-sig')))
            write_json({'id': value['id'], 'kind': value['kind'], 'receivedAt': value['receivedAt']})
        elif args.command == 'report':
            result = store.report(args.date, args.as_of)
            base = Path(args.out)
            base.parent.mkdir(parents=True, exist_ok=True)
            write_json(result, str(base) + '.json')
            Path(str(base) + '.html').write_text(render_report(result), encoding='utf-8')
            Path(str(base) + '.csv').write_text(issues_csv(result), encoding='utf-8-sig', newline='')
            print('Created ' + str(base) + '.html, .json and .csv')
        elif args.command == 'evaluate':
            write_json(store.evaluate(args.as_of), args.out)
        elif args.command == 'graph-pull':
            from .graph import pull
            write_json(pull(store, args.organizer, args.meeting_id, args.kind, args.starts_at))
    finally:
        store.close()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, OSError, TypeError) as error:
        print('Error: ' + str(error), file=sys.stderr)
        sys.exit(1)
