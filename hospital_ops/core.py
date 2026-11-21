"""Standard-library core. Transcripts are evidence, never executable instructions."""
from __future__ import annotations

import hashlib
import html
import json
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

MAX_TEXT = 2_000_000


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def instant(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp must be ISO text with Z or an explicit UTC offset.")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Invalid ISO timestamp.") from None
    if d.tzinfo is None or "T" not in value:
        raise ValueError("Timestamp requires T and Z or a UTC offset.")
    return d.astimezone(timezone.utc)


def timestamp(value):
    return instant(value).isoformat().replace("+00:00", "Z")


def digest(value):
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def load_config(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    validate_config(cfg)
    return cfg


def validate_config(cfg):
    if cfg.get("version") != 1 or cfg.get("datasetMode") not in ("synthetic", "operational"):
        raise ValueError("Use config version 1 and datasetMode operational or synthetic.")
    for group in ("meetings", "signals", "outcomes", "rules"):
        keys = [x["key"] for x in cfg[group]]
        if len(keys) != len(set(keys)) or not all(re.fullmatch(r"[a-z][a-z0-9_]{0,63}", k) for k in keys):
            raise ValueError("Configuration keys must be unique lowercase identifiers: " + group)
    for rule in cfg["rules"]:
        if rule["checkpoint"] not in {x["key"] for x in cfg["meetings"]}:
            raise ValueError("Unknown checkpoint.")
        if not rule["allSignals"] or not set(rule["allSignals"]) <= {x["key"] for x in cfg["signals"]}:
            raise ValueError("Unknown rule signals.")
        if rule["outcome"] not in {x["key"] for x in cfg["outcomes"]}:
            raise ValueError("Unknown outcome.")
    if not 1 <= cfg["minimumHistory"] <= 10000 or not 1 <= cfg["historyDays"] <= 3650:
        raise ValueError("Invalid history limits.")
    if not 0 <= cfg["watchRate"] <= 1:
        raise ValueError("watchRate must be between 0 and 1.")
    return cfg


def parse_vtt(text):
    """Parse timestamped WebVTT, preserving voice tags and cue offsets."""
    if len(text) > MAX_TEXT:
        raise ValueError("Transcript exceeds 2 million characters.")
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("WEBVTT"):
        raise ValueError("Expected a WEBVTT transcript.")
    cues = []
    time_re = r"(?:\d{2,}:)?\d{2}:\d{2}\.\d{3}"
    def millis(s):
        parts = s.split(":")
        h, m, seconds = ("0", *parts) if len(parts) == 2 else parts
        if int(m) > 59 or float(seconds) >= 60:
            raise ValueError("Invalid cue timestamp.")
        return round((int(h) * 3600 + int(m) * 60 + float(seconds)) * 1000)
    for block in re.split(r"\n\s*\n", text):
        lines = block.strip().splitlines()
        if not lines or lines[0].startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if index is None:
            continue
        match = re.fullmatch(rf"({time_re})\s+-->\s+({time_re})(?:\s+.*)?", lines[index].strip())
        if not match:
            raise ValueError("Invalid cue timing line.")
        start, end = match.groups()
        if millis(end) < millis(start):
            raise ValueError("Cue ends before it starts.")
        raw = "\n".join(lines[index + 1:])
        speakers = list(dict.fromkeys(re.findall(r"<v(?:\.[^ >]+)*\s+([^>]+)>", raw)))
        body = html.unescape(re.sub(r"<[^>]+>", "", raw)).strip()
        if body:
            cues.append({"id": "c" + str(len(cues) + 1), "start": start, "end": end,
                         "startMs": millis(start), "speaker": "; ".join(speakers) or "Not attributed", "text": body})
    if not cues:
        raise ValueError("No timestamped transcript cues found.")
    return cues


class Store:
    def __init__(self, path, config):
        self.config = validate_config(config)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY,value TEXT NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS records (kind TEXT NOT NULL,id TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(kind,id))")
        mode = self.db.execute("SELECT value FROM metadata WHERE key='datasetMode'").fetchone()
        if mode and mode[0] != config["datasetMode"]:
            self.db.close()
            raise ValueError("Synthetic and operational records must use separate databases.")
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO metadata VALUES ('datasetMode',?)", (config["datasetMode"],))

    def close(self):
        self.db.close()

    def records(self, kind):
        return [json.loads(r[0]) for r in self.db.execute("SELECT data FROM records WHERE kind=?", (kind,))]

    def get(self, kind, identifier):
        row = self.db.execute("SELECT data FROM records WHERE kind=? AND id=?", (kind, identifier)).fetchone()
        if not row:
            raise ValueError("Record not found: " + identifier)
        return json.loads(row[0])

    def _put(self, kind, record):
        previous = self.db.execute("SELECT data FROM records WHERE kind=? AND id=?", (kind, record["id"])).fetchone()
        encoded = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if previous:
            if previous[0] == encoded:
                return False
            raise ValueError("An immutable record already uses this ID. Create a new revision ID.")
        with self.db:
            self.db.execute("INSERT INTO records VALUES (?,?,?)", (kind, record["id"], encoded))
        return True

    def ingest_vtt(self, text, kind, starts_at, source_label, meeting_id=None, received_at=None):
        if kind not in {x["key"] for x in self.config["meetings"]}:
            raise ValueError("Unknown meeting kind.")
        instant(starts_at)
        local_date = starts_at[:10]
        date.fromisoformat(local_date)
        received = timestamp(received_at or utcnow())
        if instant(received) < instant(starts_at):
            raise ValueError("A transcript cannot be received before the meeting starts.")
        record_id = meeting_id or digest([kind, starts_at, source_label, text])[:24]
        existing = next((m for m in self.records("meeting") if m["id"] == record_id), None)
        if existing:
            if existing["contentHash"] == digest(text) and existing["kind"] == kind and existing["startsAt"] == starts_at:
                return existing
            raise ValueError("Meeting ID already contains different content. Use a new revision ID.")
        m = {"id": record_id, "kind": kind, "startsAt": starts_at, "date": local_date,
             "receivedAt": received, "sourceLabel": str(source_label)[:300], "contentHash": digest(text), "cues": parse_vtt(text)}
        self._put("meeting", m)
        return m

    def draft_review(self, meeting_id):
        m = self.get("meeting", meeting_id)
        hits = []
        for signal in self.config["signals"]:
            for cue in m["cues"]:
                if any(word.casefold() in cue["text"].casefold() for word in signal["keywords"]):
                    hits.append({"signal": signal["key"], "cueId": cue["id"], "text": cue["text"],
                                 "note": "Mention only. Confirm meaning, negation, timing and relevance before adding an observation."})
        return {"meetingId": meeting_id, "suggestedMentions": hits, "reviewTemplate": {
            "id": meeting_id + "-review-1", "meetingId": meeting_id, "reviewerRole": "REPLACE_WITH_ROLE",
            "observations": [], "outcomes": []}}

    def add_review(self, review, received_at=None):
        review = json.loads(json.dumps(review))
        m = self.get("meeting", review["meetingId"])
        if not isinstance(review.get("id"), str) or not review["id"].strip():
            raise ValueError("Review requires a stable unique id.")
        if not review.get("reviewerRole") or review["reviewerRole"] == "REPLACE_WITH_ROLE":
            raise ValueError("A reviewer role is required.")
        # Normalize documented optional fields before comparing a repeated import.
        review.setdefault("observations", [])
        review.setdefault("outcomes", [])
        for observation in review["observations"]:
            observation.setdefault("owner", "Not stated")
            observation.setdefault("action", "Not stated")
            observation.setdefault("due", "Not stated")
        prior = next((r for r in self.records("review") if r["id"] == review["id"]), None)
        if prior:
            compare = {k: v for k, v in prior.items() if k not in ("availableAt", "receivedAt", "reviewedAt")}
            incoming = {k: v for k, v in review.items() if k not in ("availableAt", "receivedAt", "reviewedAt")}
            if compare == incoming:
                return prior
            raise ValueError("Review ID already exists. Use a new revision ID to correct it.")
        received = timestamp(received_at or utcnow())
        reviewed = timestamp(review.get("reviewedAt", received))
        if instant(reviewed) < instant(m["startsAt"]) or instant(reviewed) > instant(received):
            raise ValueError("Review time must be after meeting start and no later than receipt.")
        cues = {x["id"] for x in m["cues"]}
        observations = review.setdefault("observations", [])
        outcomes = review.setdefault("outcomes", [])
        if not observations and not outcomes:
            raise ValueError("Review must contain at least one observation or outcome.")
        if len({o["signal"] for o in observations}) != len(observations):
            raise ValueError("Only one state per signal in a review.")
        if len({o["key"] for o in outcomes}) != len(outcomes):
            raise ValueError("Only one value per outcome in a review.")
        for o in observations + outcomes:
            if not isinstance(o.get("summary"), str) or not o["summary"].strip():
                raise ValueError("Every entry needs a factual summary.")
            if not o.get("cueIds") or not set(o["cueIds"]) <= cues:
                raise ValueError("Every entry needs valid evidence cueIds from its meeting.")
        for o in observations:
            if o["signal"] not in {s["key"] for s in self.config["signals"]} or o.get("state") not in ("active", "cleared", "unknown"):
                raise ValueError("Invalid observation signal or state.")
            if not o.get("issueId"):
                raise ValueError("Use a stable issueId to carry an issue between meetings.")
            o.setdefault("owner", "Not stated")
            o.setdefault("action", "Not stated")
            o.setdefault("due", "Not stated")
        for o in outcomes:
            if o["key"] not in {s["key"] for s in self.config["outcomes"]} or not (o.get("value") is None or type(o.get("value")) is bool):
                raise ValueError("Outcome value must be true, false, or null (unknown).")
        review.update({"reviewedAt": reviewed, "receivedAt": received,
                       "availableAt": max((received, reviewed, m["receivedAt"]), key=instant)})
        self._put("review", review)
        return review

    def add_snapshot(self, kind, payload, received_at=None):
        if payload.get("version") != 1 or kind not in ("staffing", "handoff"):
            raise ValueError("Use a version 1 staffing or handoff snapshot.")
        if kind == "staffing":
            date.fromisoformat(payload["staffingDate"])
            instant(payload["capturedUtc"])
            values = payload["values"]
            if len(values) != 46 or any(len(row) != 12 or any(not isinstance(x, str) for x in row) for row in values):
                raise ValueError("Staffing snapshot must contain A1:L46 as 46 rows of 12 strings.")
        else:
            headers = payload["headers"]
            if not headers or not all(isinstance(h, str) for h in headers) or len(set(headers)) != len(headers):
                raise ValueError("Handoff headers must be unique strings.")
            if len(payload["rows"]) > 5000 or any(len(row) != len(headers) for row in payload["rows"]):
                raise ValueError("Invalid handoff row dimensions.")
            if any(not isinstance(v, (str, int, float, bool)) for row in payload["rows"] for v in row):
                raise ValueError("Handoff cells must be scalar values.")
        if len(json.dumps(payload)) > MAX_TEXT:
            raise ValueError("Snapshot exceeds the supported size.")
        sid = digest([kind, payload])[:24]
        existing = next((s for s in self.records("snapshot") if s["id"] == sid), None)
        if existing:
            return existing
        received = timestamp(received_at or utcnow())
        if kind == "staffing" and instant(payload["capturedUtc"]) > instant(received):
            raise ValueError("Snapshot capture time is in the future.")
        record = {"id": sid, "kind": kind, "receivedAt": received, "payload": payload}
        self._put("snapshot", record)
        return record

    def entries(self, as_of):
        cutoff = instant(as_of)
        meetings = {m["id"]: m for m in self.records("meeting") if instant(m["receivedAt"]) <= cutoff and instant(m["startsAt"]) <= cutoff}
        # Later review revisions replace that meeting's earlier interpretation, not its source.
        latest = {}
        for r in sorted(self.records("review"), key=lambda r: (instant(r["availableAt"]), r["id"])):
            if r["meetingId"] in meetings and instant(r["availableAt"]) <= cutoff:
                latest[r["meetingId"]] = r
        return sorted([(meetings[mid], r) for mid, r in latest.items()], key=lambda pair: (instant(pair[0]["startsAt"]), instant(pair[1]["availableAt"])))

    def states(self, day, as_of):
        states = {}
        for m, r in self.entries(as_of):
            if m["date"] == day:
                for o in r["observations"]:
                    states[o["signal"]] = o["state"]
        return states

    def checkpoint(self, day, kind, as_of):
        found = [(m, r) for m, r in self.entries(as_of) if m["date"] == day and m["kind"] == kind]
        if not found:
            return None
        # First available confirmed checkpoint, immutable for prospective comparisons.
        m, _ = min(found, key=lambda pair: instant(pair[1]["availableAt"]))
        rs = [r for r in self.records("review") if r["meetingId"] == m["id"] and instant(r["availableAt"]) <= instant(as_of)]
        return min(rs, key=lambda r: (instant(r["availableAt"]), r["id"]))["availableAt"]

    def outcome(self, day, key, after, as_of):
        result = None
        for m, r in self.entries(as_of):
            if m["date"] == day and instant(m["startsAt"]) > instant(after):
                for o in r["outcomes"]:
                    if o["key"] == key:
                        result = o["value"]
        return result

    def cohort(self, rule, day, as_of):
        start = date.fromisoformat(day) - timedelta(days=self.config["historyDays"])
        days = sorted({m["date"] for m, _ in self.entries(as_of) if start <= date.fromisoformat(m["date"]) < date.fromisoformat(day)})
        matched, events, baseline, unknown = 0, 0, [], 0
        for past_day in days:
            cut = self.checkpoint(past_day, rule["checkpoint"], as_of)
            if not cut:
                continue
            outcome = self.outcome(past_day, rule["outcome"], cut, as_of)
            states = self.states(past_day, cut)
            if not all(states.get(key) in ("active", "cleared") for key in rule["allSignals"]):
                continue
            if outcome is None:
                unknown += 1
                continue
            baseline.append(outcome)
            if all(states.get(k) == "active" for k in rule["allSignals"]):
                matched += 1
                events += int(outcome)
        return {"matchedDays": matched, "events": events, "baselineDays": len(baseline),
                "baselineEvents": sum(baseline), "unknownOutcomeDays": unknown,
                "rate": events / matched if matched else None}

    def warnings(self, day, as_of):
        states = self.states(day, as_of)
        result = []
        for rule in self.config["rules"]:
            if not self.checkpoint(day, rule["checkpoint"], as_of):
                continue
            if not all(states.get(k) == "active" for k in rule["allSignals"]):
                continue
            history = self.cohort(rule, day, as_of)
            sufficient = history["matchedDays"] >= self.config["minimumHistory"]
            result.append({"rule": rule["key"], "label": rule["label"], "action": rule["action"],
                           "outcome": rule["outcome"], "history": history,
                           "status": "Historical watch" if sufficient and history["rate"] >= self.config["watchRate"] else "Rule-based review",
                           "interpretation": "Exploratory association, not a calibrated prediction." if sufficient else "Insufficient comparable history. No probability is estimated."})
        return result

    def report(self, day, as_of=None):
        date.fromisoformat(day)
        as_of = timestamp(as_of or utcnow())
        meetings = sorted([m for m in self.records("meeting") if m["date"] == day and instant(m["receivedAt"]) <= instant(as_of) and instant(m["startsAt"]) <= instant(as_of)], key=lambda m: instant(m["startsAt"]))
        entries = self.entries(as_of)
        reviewed = {m["id"] for m, _ in entries}
        issues = {}
        for m, r in entries:
            if m["date"] > day:
                continue
            cue_map = {c["id"]: c for c in m["cues"]}
            for o in r["observations"]:
                issues[o["issueId"]] = dict(o, meetingId=m["id"], meetingKind=m["kind"], date=m["date"],
                    reviewedAt=r["reviewedAt"], evidence=[{"cueId": cid, "start": cue_map[cid]["start"], "text": cue_map[cid]["text"]} for cid in o["cueIds"]])
        snapshots = {}
        for s in sorted(self.records("snapshot"), key=lambda s: (instant(s["receivedAt"]), s["id"])):
            if instant(s["receivedAt"]) <= instant(as_of):
                previous = snapshots.get(s["kind"])
                if s["kind"] == "staffing" and previous and instant(s["payload"]["capturedUtc"]) < instant(previous["payload"]["capturedUtc"]):
                    continue
                snapshots[s["kind"]] = s
        return {"version": 1, "siteLabel": self.config["siteLabel"], "datasetMode": self.config["datasetMode"], "configHash": digest(self.config),
                "date": day, "asOfUtc": as_of, "generatedUtc": utcnow(),
                "meetings": [{k: m[k] for k in ("id", "kind", "startsAt", "sourceLabel")} | {"reviewed": m["id"] in reviewed} for m in meetings],
                "missingMeetings": [m["label"] for m in self.config["meetings"] if m["key"] not in {x["kind"] for x in meetings}],
                "issues": list(issues.values()), "warnings": self.warnings(day, as_of), "snapshots": snapshots}

    def evaluate(self, as_of=None):
        """Walk forward: build each warning using only records available at its checkpoint."""
        as_of = timestamp(as_of or utcnow())
        results = []
        days = sorted({m["date"] for m, _ in self.entries(as_of)})
        for rule in self.config["rules"]:
            counts = {"scored": 0, "unscored": 0, "insufficientHistory": 0, "truePositive": 0, "falsePositive": 0, "trueNegative": 0, "falseNegative": 0}
            for day in days:
                cut = self.checkpoint(day, rule["checkpoint"], as_of)
                if not cut:
                    continue
                truth = self.outcome(day, rule["outcome"], cut, as_of)
                state = self.states(day, cut)
                if truth is None or not all(state.get(k) in ("active", "cleared") for k in rule["allSignals"]):
                    counts["unscored"] += 1
                    continue
                hist = self.cohort(rule, day, cut)
                if hist["matchedDays"] < self.config["minimumHistory"]:
                    counts["insufficientHistory"] += 1
                    continue
                prediction = all(state.get(k) == "active" for k in rule["allSignals"]) and hist["rate"] >= self.config["watchRate"]
                counts["scored"] += 1
                counts[("true" if prediction == truth else "false") + ("Positive" if prediction else "Negative")] += 1
            tp, fp, fn = counts["truePositive"], counts["falsePositive"], counts["falseNegative"]
            results.append({"rule": rule["key"], **counts, "precision": tp / (tp + fp) if tp + fp else None,
                            "recall": tp / (tp + fn) if tp + fn else None})
        return {"datasetMode": self.config["datasetMode"], "asOfUtc": as_of,
                "note": "Exploratory walk-forward evaluation. Synthetic results demonstrate software behavior, not clinical or operational accuracy.", "rules": results}


def staffing_date(local_date, mode="next-business-day", explicit_date=None, holidays=()):
    d = date.fromisoformat(local_date)
    if mode == "explicit-date":
        return date.fromisoformat(explicit_date).isoformat()
    if mode == "same-date":
        return d.isoformat()
    if mode != "next-business-day":
        raise ValueError("Unknown staffing date mode.")
    closed = {date.fromisoformat(x) for x in holidays}
    d += timedelta(days=1)
    while d.weekday() > 4 or d in closed:
        d += timedelta(days=1)
    return d.isoformat()
