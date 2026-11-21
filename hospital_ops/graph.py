"""Optional read-only Microsoft Graph transcript adapter. No token storage."""
import json
import os
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward an access token to a redirected host.


def get(url, accept="application/json"):
    if urlparse(url).scheme != "https" or urlparse(url).netloc != "graph.microsoft.com":
        raise ValueError("Only the global Microsoft Graph HTTPS endpoint is supported.")
    token = os.environ.get("GRAPH_ACCESS_TOKEN")
    if not token:
        raise ValueError("Set GRAPH_ACCESS_TOKEN using your organization's approved sign-in process.")
    request = Request(url, headers={"Authorization": "Bearer " + token, "Accept": accept})
    try:
        with build_opener(NoRedirect()).open(request, timeout=60) as response:
            payload = response.read(2_000_001)
            if len(payload) > 2_000_000:
                raise ValueError("Graph response exceeds 2 MB. Use a scoped manual export.")
            return payload.decode("utf-8-sig")
    except HTTPError as err:
        # Never echo headers, tokens or full Graph error bodies.
        if err.code == 403:
            raise ValueError("Graph denied access. Check consent, access policy, transcript access and speaker-attribution settings; manual VTT upload remains available.") from None
        if err.code == 429:
            raise ValueError("Graph throttled this request. Retry after " + str(err.headers.get("Retry-After", "the indicated interval")) + " seconds.") from None
        raise ValueError("Graph request failed with HTTP " + str(err.code)) from None


def pull(store, organizer, meeting_id, kind, starts_at):
    root = "https://graph.microsoft.com/v1.0/users/" + quote(organizer, safe='') + "/onlineMeetings/" + quote(meeting_id, safe='') + "/transcripts"
    page = root
    found = []
    seen_pages = set()
    while page:
        if page in seen_pages or len(seen_pages) >= 50:
            raise ValueError("Unexpected Graph pagination. Narrow the meeting request.")
        seen_pages.add(page)
        data = json.loads(get(page))
        for item in data.get("value", []):
            transcript_id = item["id"]
            text = get(root + "/" + quote(transcript_id, safe='') + "/content", "text/vtt")
            # Each transcript segment has its own source identity; reruns deduplicate.
            found.append(store.ingest_vtt(text, kind, starts_at, "Teams transcript", "graph-" + __import__('hashlib').sha256((meeting_id + ':' + transcript_id).encode()).hexdigest()[:24])["id"])
        page = data.get("@odata.nextLink")
    return {"status": "imported" if found else "transcript_not_available", "meetingIds": found}
