"""Process a local or approved synced folder. The database stays local."""
import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from .core import Store, load_config
from .render import render_report, issues_csv


def scan(store, inbox):
    inbox = Path(inbox).resolve()
    before = store.db.total_changes
    errors = []
    # Transcript metadata first, reviews second, snapshots third.
    for suffix in ('meeting', 'review', 'staffing', 'handoff'):
        for file in sorted(inbox.glob('*.' + suffix + '.json')):
            try:
                if file.stat().st_size > 3_000_000:
                    raise ValueError('File is too large.')
                value = json.loads(file.read_text(encoding='utf-8-sig'))
                if suffix == 'meeting':
                    transcript = (inbox / value['transcriptFile']).resolve()
                    if transcript.parent != inbox or transcript.suffix.lower() != '.vtt':
                        raise ValueError('Transcript must be a VTT directly inside the intake folder.')
                    store.ingest_vtt(transcript.read_text(encoding='utf-8-sig'), value['kind'], value['startsAt'], value.get('sourceLabel', transcript.name), value['id'])
                elif suffix == 'review':
                    store.add_review(value)
                else:
                    store.add_snapshot(suffix, value)
            except (ValueError, KeyError, TypeError, OSError) as err:
                errors.append({'file': file.name, 'error': str(err)})
    return store.db.total_changes > before, errors


def watch(db, config_path, inbox, out, interval=60, once=False):
    cfg = load_config(config_path)
    try:
        zone = ZoneInfo(cfg['timezone'])
    except ZoneInfoNotFoundError:
        raise ValueError('Time-zone database missing. On Windows, install tzdata with your approved Python package process, or use explicit-date CLI commands.') from None
    inbox, out = Path(inbox), Path(out)
    inbox.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    store = Store(db, cfg)
    last_day = None
    last_errors = None
    try:
        while True:
            day = datetime.now(zone).date().isoformat()
            changed, errors = scan(store, inbox)
            if changed or day != last_day or not (out / 'operations.json').exists():
                report = store.report(day)
                for name, text in [('operations.json', json.dumps(report, indent=2)), ('operations.html', render_report(report)), ('operations.csv', issues_csv(report))]:
                    # Atomic rename prevents a consumer from reading a partial JSON file.
                    temp = out / (name + '.tmp')
                    temp.write_text(text, encoding='utf-8')
                    temp.replace(out / name)
                print('Updated operations brief for ' + day, flush=True)
            if errors != last_errors:
                (out / 'intake-errors.json').write_text(json.dumps(errors, indent=2), encoding='utf-8')
                if errors:
                    print(str(len(errors)) + ' intake file(s) need attention. See intake-errors.json.', flush=True)
                last_errors = errors
            last_day = day
            if once:
                break
            time.sleep(max(5, interval))
    except KeyboardInterrupt:
        pass
    finally:
        store.close()
