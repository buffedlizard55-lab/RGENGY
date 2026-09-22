"""Minimal, dependency-free HTTP layer with on-disk caching and provenance.

Every fetch performed by RGENGY goes through :func:`get_json` / :func:`get_text`
so that we can:

* apply a real ``User-Agent`` (NWS *requires* one - see
  https://www.weather.gov/documentation/services-web-api),
* rate-limit politely per host,
* cache responses to disk so a run is reproducible and re-runnable offline,
* record **provenance** - the exact URL, HTTP status and fetch time - which is
  what makes the published artefacts auditable.

The module never fabricates a response.  On failure it raises
:class:`FetchError` carrying the HTTP status so callers can decide whether to
degrade (and say so) or abort.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

# NWS asks for a descriptive UA with contact info.  We use a generic one that
# identifies the project; the operator can override with RGENGY_USER_AGENT.
DEFAULT_USER_AGENT = (
    "RGENGY/0.1 (+https://github.com/buffedlizard55-lab/RGENGY; "
    "open-source sports projection research)"
)

DEFAULT_TIMEOUT = float(os.environ.get("RGENGY_TIMEOUT", "20"))
CACHE_DIR = Path(os.environ.get("RGENGY_CACHE", ".rgengy-cache"))
MIN_INTERVAL = float(os.environ.get("RGENGY_MIN_INTERVAL", "0.35"))


class FetchError(RuntimeError):
    """Raised when a fetch fails.  Carries the HTTP status when available."""

    def __init__(self, url: str, reason: str, status: Optional[int] = None) -> None:
        super().__init__(f"{reason} (status={status}) for {url}")
        self.url = url
        self.reason = reason
        self.status = status


@dataclass
class Provenance:
    """Where a piece of data came from.  Serialised into every artefact."""

    url: str
    status: Optional[int] = None
    fetched_at: Optional[str] = None
    from_cache: bool = False
    elapsed_ms: Optional[int] = None
    error: Optional[str] = None
    note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "status": self.status,
            "fetched_at": self.fetched_at,
            "from_cache": self.from_cache,
            "elapsed_ms": self.elapsed_ms,
            "error": self.error,
            "note": self.note,
        }

    @property
    def ok(self) -> bool:
        return self.status is not None and 200 <= self.status < 300 and self.error is None


@dataclass
class FetchLog:
    """Accumulated provenance for a whole pipeline run."""

    entries: list = field(default_factory=list)

    def add(self, prov: Provenance) -> Provenance:
        self.entries.append(prov)
        return prov

    def summary(self) -> Dict[str, Any]:
        ok = [p for p in self.entries if p.ok]
        failed = [p for p in self.entries if not p.ok]
        hosts: Dict[str, int] = {}
        for p in self.entries:
            host = urllib.parse.urlparse(p.url).netloc
            hosts[host] = hosts.get(host, 0) + 1
        return {
            "total_requests": len(self.entries),
            "ok": len(ok),
            "failed": len(failed),
            "from_cache": sum(1 for p in self.entries if p.from_cache),
            "hosts": hosts,
            "failures": [
                {"url": p.url, "status": p.status, "error": p.error} for p in failed
            ],
        }


_log_lock = threading.Lock()
_last_request: Dict[str, float] = {}
GLOBAL_LOG = FetchLog()


def _throttle(host: str) -> None:
    with _log_lock:
        last = _last_request.get(host, 0.0)
        wait = MIN_INTERVAL - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        _last_request[host] = time.time()


def _cache_path(url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    host = urllib.parse.urlparse(url).netloc or "local"
    return CACHE_DIR / host / f"{digest}.json"


def _build_request(url: str, headers: Optional[Dict[str, str]] = None) -> urllib.request.Request:
    hdrs = {
        "User-Agent": os.environ.get("RGENGY_USER_AGENT", DEFAULT_USER_AGENT),
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "identity",
    }
    if headers:
        hdrs.update(headers)
    return urllib.request.Request(url, headers=hdrs)


def fetch(url: str, *, use_cache: bool = True, log: Optional[FetchLog] = None,
          headers: Optional[Dict[str, str]] = None, timeout: float = DEFAULT_TIMEOUT) -> tuple:
    """Return ``(raw_bytes, Provenance)`` for ``url``.

    Raises :class:`FetchError` on network/HTTP failure.  Never returns invented
    content.
    """
    log = log if log is not None else GLOBAL_LOG
    host = urllib.parse.urlparse(url).netloc
    path = _cache_path(url)

    if use_cache and path.exists():
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
            prov = Provenance(
                url=url,
                status=blob.get("status"),
                fetched_at=blob.get("fetched_at"),
                from_cache=True,
            )
            log.add(prov)
            return blob["body"].encode("utf-8") if isinstance(blob["body"], str) else blob["body"], prov
        except Exception:  # corrupt cache entry -> refetch
            path.unlink(missing_ok=True)

    _throttle(host)
    started = time.time()
    try:
        with urllib.request.urlopen(_build_request(url, headers), timeout=timeout) as resp:
            body = resp.read()
            status = getattr(resp, "status", None) or resp.getcode()
        prov = Provenance(
            url=url, status=status,
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            elapsed_ms=int((time.time() - started) * 1000),
        )
        log.add(prov)
        if use_cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "url": url,
                        "status": status,
                        "fetched_at": prov.fetched_at,
                        "body": body.decode("utf-8", errors="replace"),
                    }
                ),
                encoding="utf-8",
            )
        return body, prov
    except urllib.error.HTTPError as exc:
        prov = Provenance(
            url=url, status=exc.code,
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            error=f"HTTPError: {exc.reason}",
            elapsed_ms=int((time.time() - started) * 1000),
        )
        log.add(prov)
        raise FetchError(url, f"HTTPError: {exc.reason}", exc.code) from exc
    except Exception as exc:  # URLError, timeout, TLS, DNS...
        prov = Provenance(
            url=url, status=None,
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            error=f"{type(exc).__name__}: {exc}",
            elapsed_ms=int((time.time() - started) * 1000),
        )
        log.add(prov)
        raise FetchError(url, f"{type(exc).__name__}: {exc}", None) from exc


def get_json(url: str, *, use_cache: bool = True, log: Optional[FetchLog] = None,
             headers: Optional[Dict[str, str]] = None, timeout: float = DEFAULT_TIMEOUT):
    """Fetch ``url`` and decode it as JSON.  Returns ``(obj, Provenance)``."""
    body, prov = fetch(url, use_cache=use_cache, log=log, headers=headers, timeout=timeout)
    try:
        return json.loads(body.decode("utf-8")), prov
    except json.JSONDecodeError as exc:
        prov.error = f"invalid JSON: {exc}"
        raise FetchError(url, f"invalid JSON: {exc}", prov.status) from exc


def get_text(url: str, *, use_cache: bool = True, log: Optional[FetchLog] = None,
             headers: Optional[Dict[str, str]] = None, timeout: float = DEFAULT_TIMEOUT):
    """Fetch ``url`` as text.  Returns ``(text, Provenance)``."""
    body, prov = fetch(url, use_cache=use_cache, log=log, headers=headers, timeout=timeout)
    return body.decode("utf-8", errors="replace"), prov


def safe_json(url: str, *, log: Optional[FetchLog] = None, use_cache: bool = True,
              headers: Optional[Dict[str, str]] = None):
    """Like :func:`get_json` but returns ``(None, provenance_with_error)`` on failure.

    Used by the pipeline so that one unreachable endpoint degrades the run
    (and is *reported*) instead of aborting it.
    """
    try:
        return get_json(url, use_cache=use_cache, log=log, headers=headers)
    except FetchError as exc:
        prov = Provenance(url=url, status=exc.status, error=str(exc.reason),
                          fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        if log is not None:
            log.add(prov)
        return None, prov
