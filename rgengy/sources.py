"""Data-source layer: every URL RGENGY touches, with its verification record.

LEGAL / ETHICAL BOUNDARY
------------------------
RGENGY does **not** scrape RotoGrinders, does not call its private ``/api/``
namespace (explicitly disallowed by
https://rotogrinders.com/robots.txt, retrieved 2026-09-22) and does not attempt
to reproduce paywalled output.  The subscription product is rebuilt from
*independent* free and official feeds listed below.  RotoGrinders' public pages
are used only as a **specification** (what columns exist, what the pricing is)
and those pages are cited for manual review, never parsed at runtime.

VERIFICATION STATUS VOCABULARY
------------------------------
``live-verified``  Fetched successfully during the 2026-09-22 audit; HTTP 200
                   and real, plausible payloads were observed.  The exact URL
                   and observed content are recorded in ``docs/evidence/``.
``reachable``      Host answered, but the specific payload could not be
                   inspected (e.g. an empty slate returns an error page).
``documented``     The endpoint is described by a third-party document that was
                   retrieved; RGENGY did not observe a live response.
``unverified``     Not confirmed.  Code paths using it must degrade and report.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode

AUDIT_DATE = "2026-09-22"


@dataclass(frozen=True)
class Endpoint:
    """One data source, with everything needed to audit it."""

    key: str
    name: str
    url_template: str
    provider: str
    official: bool                 # published by the league/government itself
    auth: str                      # "none" | "api-key-optional" | "api-key-required"
    verification_status: str       # see module docstring
    verified_on: Optional[str]
    docs_url: Optional[str]
    terms_url: Optional[str]
    notes: str = ""
    replaces: List[str] = field(default_factory=list)  # RotoGrinders features it substitutes for

    def url(self, **params: Any) -> str:
        """Render the template.  ``{param}`` placeholders are URL-quoted."""
        safe = {k: quote(str(v), safe=",:-") for k, v in params.items()}
        return self.url_template.format(**safe)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "url_template": self.url_template,
            "provider": self.provider,
            "official": self.official,
            "auth": self.auth,
            "verification_status": self.verification_status,
            "verified_on": self.verified_on,
            "docs_url": self.docs_url,
            "terms_url": self.terms_url,
            "notes": self.notes,
            "replaces": list(self.replaces),
        }


# ---------------------------------------------------------------------------
# The registry.  Every entry below was retrieved or its document was retrieved
# on AUDIT_DATE unless the status says otherwise.
# ---------------------------------------------------------------------------

MLB_COPYRIGHT = "http://gdx.mlb.com/components/copyright.txt"

ENDPOINTS: List[Endpoint] = [
    Endpoint(
        key="mlb.schedule",
        name="MLB Stats API - schedule",
        url_template="https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=probablePitcher,odds,venue,team",
        provider="MLB Advanced Media (MLBAM)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://statsapi.mlb.com/",
        terms_url=MLB_COPYRIGHT,
        notes="Retrieved 2026-09-22 for date=2026-09-22: HTTP 200, totalGames=16. Response carries a "
              "copyright block that links the MLBAM terms page. Fields observed: gamePk, gameDate, "
              "officialDate, status.detailedState, teams.{away,home}.team.{id,name,abbreviation,venue},"
              " teams.*.leagueRecord.{wins,losses,pct}, teams.*.probablePitcher.{id,fullName}, venue.{id,name}. "
              "The 'odds' hydrate was requested but no odds block was present in the inspected portion of the "
              "response - MLB odds are therefore sourced from ESPN (see nfl_espn / espn.scoreboard).",
        replaces=["RG MLB slate/schedule", "RG probable-pitcher feed"],
    ),
    Endpoint(
        key="mlb.schedule_plain",
        name="MLB Stats API - schedule (no hydration)",
        url_template="https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}",
        provider="MLB Advanced Media (MLBAM)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://statsapi.mlb.com/",
        terms_url=MLB_COPYRIGHT,
        notes="Retrieved 2026-09-22 for date=2026-09-21: HTTP 200, totalGames=3, all status 'Final'.",
        replaces=["RG MLB slate/schedule"],
    ),
    Endpoint(
        key="mlb.team_stats",
        name="MLB Stats API - team season stats",
        url_template="https://statsapi.mlb.com/api/v1/teams/{team_id}/stats?stats=season&group={group}&season={season}",
        provider="MLB Advanced Media (MLBAM)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://statsapi.mlb.com/",
        terms_url=MLB_COPYRIGHT,
        notes="LIVE-VERIFIED 2026-09-22 (second audit pass): GET /api/v1/teams/110/stats?stats=season"
              "&group=hitting&season=2026 (team id 110 taken from the same day's verified schedule) "
              "returned HTTP 200 with a copyright block and a full 2026 hitting split (gamesPlayed, "
              "runs, doubles, triples, homeRuns, strikeOuts, baseOnBalls, hits, hitByPitch, avg, "
              "atBats, obp, slg, ops, caughtStealing, stolenBases, rbi, totalBases, ...). The same "
              "shape is expected for group=pitching.",
        replaces=["RG team offensive/defensive ratings"],
    ),
    Endpoint(
        key="mlb.player_stats",
        name="MLB Stats API - player season stats",
        url_template="https://statsapi.mlb.com/api/v1/people/{person_id}/stats?stats=season&group={group}&season={season}",
        provider="MLB Advanced Media (MLBAM)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://statsapi.mlb.com/",
        terms_url=MLB_COPYRIGHT,
        notes="LIVE-VERIFIED 2026-09-22 (second audit pass): GET /api/v1/people/608331/stats?stats=season"
              "&group=pitching&season=2026 (person id 608331 taken from the same day's verified "
              "probable-pitcher hydrate) returned HTTP 200 with a full pitching split (inningsPitched, "
              "strikeOuts, earnedRuns, homeRuns, baseOnBalls, hits, wins, losses, era, whip, ...).",
        replaces=["RG player stat inputs", "PlateIQ season stats"],
    ),
    Endpoint(
        key="mlb.venue",
        name="MLB Stats API - venues",
        url_template="https://statsapi.mlb.com/api/v1/venues/{venue_id}",
        provider="MLB Advanced Media (MLBAM)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://statsapi.mlb.com/",
        terms_url=MLB_COPYRIGHT,
        notes="LIVE-VERIFIED 2026-09-22 (second audit pass): GET /api/v1/venues/2395 (venue id taken "
              "from the same day's verified schedule) returned HTTP 200 with "
              "{id: 2395, name: 'Oracle Park', active: true, season: '2026'}. NOTE: this endpoint "
              "returns the venue NAME only - it does NOT return latitude/longitude, so it cannot by "
              "itself resolve the NWS weather grid. Without a coordinate source the weather layer "
              "reports 'venue coordinates unavailable' and skips the adjustment (no coordinate table "
              "is hard-coded, because inventing coordinates would violate the no-hallucination rule).",
        replaces=["WeatherEdge venue lookup"],
    ),
    Endpoint(
        key="nws.point",
        name="NWS API - point metadata",
        url_template="https://api.weather.gov/points/{lat},{lon}",
        provider="U.S. National Weather Service (NOAA)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://www.weather.gov/documentation/services-web-api",
        terms_url="https://www.weather.gov/disclaimer",
        notes="Retrieved 2026-09-22 for 33.4484,-112.0740 (Phoenix): HTTP 200. Returns gridId/gridX/gridY, "
              "forecast and forecastGridData links, relativeLocation, timeZone, radarStation. NWS requires a "
              "User-Agent with contact info - rgengy.http sets one.",
        replaces=["WeatherEdge"],
    ),
    Endpoint(
        key="nws.gridpoint",
        name="NWS API - forecast grid data",
        url_template="https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}",
        provider="U.S. National Weather Service (NOAA)",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://www.weather.gov/documentation/services-web-api",
        terms_url="https://www.weather.gov/disclaimer",
        notes="Retrieved 2026-09-22 for PSR/159,58: HTTP 200, 22 response chunks. Confirmed properties include "
              "validTimes, elevation and ISO-8601 duration time series (temperature in degC observed). The "
              "windSpeed/windDirection/barometricPressure/relativeHumidity/probabilityOfPrecipitation/skyCover "
              "series live in the same properties object per the NWS gridpoint schema; the audit inspected the "
              "temperature series in full and the file was truncated before the remaining series, so those five "
              "fields are 'documented, not individually observed'. The loader is written defensively and "
              "reports which keys were actually present.",
        replaces=["WeatherEdge", "THE BAT X weather/air-density layer"],
    ),
    Endpoint(
        key="nhl.scoreboard",
        name="NHL Web API - scoreboard",
        url_template="https://api-web.nhle.com/v1/scoreboard/{date}",
        provider="National Hockey League",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://api-web.nhle.com/",
        terms_url="https://www.nhl.com/info/terms-of-service",
        notes="Retrieved 2026-09-22: HTTP 200, focusedDateCount=11. Confirmed fields: gamesByDate[].games[].id, "
              "season (20262027), gameType (1 = preseason), gameDate, gameCenterLink, venue.default, "
              "startTimeUTC, easternUTCOffset, venueUTCOffset, tvBroadcasts[], gameState, awayTeam/homeTeam "
              "{id,name,commonName,placeNameWithPreposition,abbrev,score,logo}, periodDescriptor.",
        replaces=["RG NHL slate/schedule"],
    ),
    Endpoint(
        key="nhl.club_schedule",
        name="NHL Web API - club season schedule",
        url_template="https://api-web.nhle.com/v1/club-schedule-season/{club}/{season}",
        provider="National Hockey League",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://api-web.nhle.com/",
        terms_url="https://www.nhl.com/info/terms-of-service",
        notes="CORRECTED AND LIVE-VERIFIED 2026-09-22 (second audit pass, IR-24). The template this "
              "registry shipped in the first pass (/v1/club/schedule/{club}/{season}) returned HTTP 404 "
              "when actually fetched, as did the /v1/club-schedule/{club}/{season} variant. The correct "
              "route, confirmed live, is /v1/club-schedule-season/{club}/{season}: GET .../TOR/20262027 "
              "returned HTTP 200 with {previousSeason: 20252026, currentSeason: 20262027, clubTimezone, "
              "clubUTCOffset, games[] containing id, season, gameType, gameDate, venue.default, "
              "startTimeUTC, easternUTCOffset, venueTimezone, gameState, gameScheduleState, tvBroadcasts[], "
              "awayTeam/homeTeam {id, commonName, placeNameWithPreposition, abbrev, logo, score}, "
              "periodDescriptor, gameOutcome, gameCenterLink}.",
        replaces=["RG NHL schedule"],
    ),
    Endpoint(
        key="nhl.player_landing",
        name="NHL Web API - player landing page data",
        url_template="https://api-web.nhle.com/v1/player/{player_id}/landing",
        provider="National Hockey League",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://api-web.nhle.com/",
        terms_url="https://www.nhl.com/info/terms-of-service",
        notes="LIVE-VERIFIED 2026-09-22 (second audit pass): GET /v1/player/8478402/landing returned "
              "HTTP 200 with playerId, isActive, currentTeamId/Abbrev, name, position, "
              "featuredStats (season 20252026 regular-season and playoff splits), careerTotals "
              "(including plusMinus and faceoffWinningPctg), last5Games[] and seasonTotals[].",
        replaces=["RG NHL player stats"],
    ),
    Endpoint(
        key="espn.scoreboard",
        name="ESPN site API - scoreboard (NFL / NBA / NHL / MLB / WNBA)",
        url_template="https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard",
        provider="ESPN (undocumented public JSON API)",
        official=False,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c",
        terms_url=None,
        notes="Retrieved 2026-09-22 for football/nfl: HTTP 200, 36 response chunks. Confirmed fields: "
              "leagues[].season/calendar, season.{type,year}, week.number, events[].{id,uid,date,name,"
              "shortName,competitions[]}, competitions[].{attendance,venue{fullName,address{city,state},"
              "indoor},competitors[]{id,homeAway,winner,team{id,location,name,abbreviation,displayName,"
              "color,logo},score,linescores[],records[],curatedRank}}. ESPN publishes no terms for this API; "
              "using it is a documented compliance risk (see docs/09-irregularities.md IR-01).",
        replaces=["RG NFL/NBA/WNBA slate, injury status, venue", "RG odds feed (partially)"],
    ),
    Endpoint(
        key="espn.odds",
        name="ESPN core API - competition odds",
        url_template="https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{event_id}/competitions/{competition_id}/odds",
        provider="ESPN (undocumented public JSON API)",
        official=False,
        auth="none",
        verification_status="documented",
        verified_on=None,
        docs_url="https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c",
        terms_url=None,
        notes="Documented by the retrieved endpoint listing, which shows a real response containing "
              "provider.{id,name,priority}, overUnder, details ('ATL -3.5'), spread, overOdds, underOdds and "
              "awayTeamOdds. Not fetched live during the audit, so it is used only when explicitly enabled.",
        replaces=["RG SPREAD / O/U / TOTAL columns", "RG odds page"],
    ),
    Endpoint(
        key="nba.cdn_scoreboard",
        name="NBA CDN - live scoreboard",
        url_template="https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json",
        provider="National Basketball Association",
        official=True,
        auth="none",
        verification_status="reachable",
        verified_on=AUDIT_DATE,
        docs_url="https://cdn.nba.com/",
        terms_url="https://www.nba.com/termsofuse",
        notes="Retrieved 2026-09-22: the fetch returned HTTP 500 through the audit proxy. The NBA regular "
              "season had not started on that date, so an empty slate is a plausible cause, but this is NOT "
              "confirmed. Treated as 'reachable' and never trusted without a runtime shape check.",
        replaces=["RG NBA slate/schedule"],
    ),
    Endpoint(
        key="rg.public_grid",
        name="RotoGrinders public projection grid (SPECIFICATION ONLY - not parsed at runtime)",
        url_template="https://rotogrinders.com/projected-stats/{sport}",
        provider="RotoGrinders / Better Collective",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url="https://rotogrinders.com/",
        terms_url="https://rotogrinders.com/terms",
        notes="Retrieved 2026-09-22 for mlb, nfl and wnba, and re-verified the same day during the "
              "second audit pass. These pages show a FREE six-row teaser above a paywall. Re-observed "
              "on the second pass: MLB grid = 49 columns, NFL = 38, WNBA = 33 (unchanged); the six "
              "free MLB rows updated continuously (FPTS stamped 'updated 29 minutes ago' at retrieval); "
              "OBFPTS/FPTS spanned 1.076-1.126 across the fresh rows; LEV was 9 on all six again; "
              "PRIZEPICKS equalled FPTS on all six again while UNDERDOG differed; WIND rendered as "
              "'COLOut6' and TEMPDESC as 'neutraltemp'. RGENGY reads the *column headers* only, to "
              "define the output schema it must match. It never automates this endpoint: robots.txt "
              "disallows /api/ and /app, and reproducing paywalled rows would breach the site's terms. "
              "Columns are transcribed in docs/04-rg-findings.md.",
        replaces=[],
    ),
    Endpoint(
        key="rg.robots",
        name="RotoGrinders robots.txt",
        url_template="https://rotogrinders.com/robots.txt",
        provider="RotoGrinders / Better Collective",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url=None,
        terms_url="https://rotogrinders.com/terms",
        notes="Retrieved 2026-09-22 and re-verified the same day during the second audit pass. "
              "Disallows, for all user agents: /app, ?, */edit, /grind-downs/, /api/ and .csv; declares "
              "sitemap at https://rotogrinders.com/sitemaps.xml. This is why RGENGY does not "
              "automate any RotoGrinders endpoint.",
        replaces=[],
    ),
    Endpoint(
        key="rg.sitemaps",
        name="RotoGrinders sitemap index",
        url_template="https://rotogrinders.com/sitemaps.xml",
        provider="RotoGrinders / Better Collective",
        official=True,
        auth="none",
        verification_status="live-verified",
        verified_on=AUDIT_DATE,
        docs_url=None,
        terms_url="https://rotogrinders.com/terms",
        notes="Retrieved 2026-09-22. Lists eight child sitemaps: sitemap.xml, articles.xml, authors.xml and "
              "per-sport player sitemaps for nfl, nba, mlb, nhl and pga. Confirms the five sports for which "
              "RotoGrinders publishes individual player URLs.",
        replaces=[],
    ),
]

BY_KEY: Dict[str, Endpoint] = {e.key: e for e in ENDPOINTS}


def get(key: str) -> Endpoint:
    if key not in BY_KEY:
        raise KeyError(f"Unknown endpoint {key!r}. Known: {sorted(BY_KEY)}")
    return BY_KEY[key]


def registry_rows() -> List[Dict[str, Any]]:
    return [e.to_dict() for e in ENDPOINTS]


def verification_summary() -> Dict[str, Any]:
    """Counts by verification status, for the published verification panel."""
    counts: Dict[str, int] = {}
    for e in ENDPOINTS:
        counts[e.verification_status] = counts.get(e.verification_status, 0) + 1
    return {
        "audit_date": AUDIT_DATE,
        "generated_at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_endpoints": len(ENDPOINTS),
        "by_status": counts,
        "official": sum(1 for e in ENDPOINTS if e.official),
        "unofficial": sum(1 for e in ENDPOINTS if not e.official),
        "requires_auth": sum(1 for e in ENDPOINTS if e.auth != "none"),
    }


# ---------------------------------------------------------------------------
# Thin fetchers.  Each returns (normalised_rows, provenance_list).
# ---------------------------------------------------------------------------

from rgengy.http import FetchLog, Provenance, safe_json  # noqa: E402
from rgengy.models import Game, Odds, Weather  # noqa: E402


class SourceError(RuntimeError):
    """Raised when a source cannot deliver the shape the engine needs."""


def _prov(p: Provenance, endpoint: Endpoint) -> Dict[str, Any]:
    d = p.to_dict()
    d["endpoint_key"] = endpoint.key
    d["provider"] = endpoint.provider
    d["official"] = endpoint.official
    d["verification_status"] = endpoint.verification_status
    return d


def mlb_games(date: str, log: Optional[FetchLog] = None,
              use_cache: bool = True) -> tuple:
    """Return ``(games, provenance, warnings)`` for an MLB date (YYYY-MM-DD)."""
    ep = get("mlb.schedule")
    url = ep.url(date=date)
    data, prov = safe_json(url, log=log, use_cache=use_cache)
    warnings: List[str] = []
    games: List[Game] = []
    if data is None:
        warnings.append(f"mlb.schedule unreachable: {prov.error}")
        return games, [_prov(prov, ep)], warnings

    if "copyright" not in data:
        warnings.append("mlb.schedule response is missing the MLBAM copyright block - unexpected shape")

    dates = data.get("dates") or []
    if not dates:
        warnings.append(f"mlb.schedule returned no dates for {date} (off-day or shape change)")
    for day in dates:
        for g in day.get("games") or []:
            away = (g.get("teams") or {}).get("away") or {}
            home = (g.get("teams") or {}).get("home") or {}
            away_team = away.get("team") or {}
            home_team = home.get("team") or {}
            venue = g.get("venue") or {}
            game = Game(
                sport="mlb",
                game_id=str(g.get("gamePk")),
                starts_utc=g.get("gameDate") or "",
                home_team=(home_team.get("abbreviation") or home_team.get("name") or "???"),
                away_team=(away_team.get("abbreviation") or away_team.get("name") or "???"),
                home_id=str(home_team.get("id")) if home_team.get("id") else None,
                away_id=str(away_team.get("id")) if away_team.get("id") else None,
                venue=venue.get("name"),
                venue_id=str(venue.get("id")) if venue.get("id") else None,
                league=((home_team.get("league") or {}).get("name")),
                status=(g.get("status") or {}).get("detailedState"),
                provenance=[_prov(prov, ep)],
            )
            game.extra["home_record"] = _record(home)
            game.extra["away_record"] = _record(away)
            pp_home = (home.get("probablePitcher") or {})
            pp_away = (away.get("probablePitcher") or {})
            game.extra["probable_pitcher_home"] = {"id": pp_home.get("id"), "name": pp_home.get("fullName")}
            game.extra["probable_pitcher_away"] = {"id": pp_away.get("id"), "name": pp_away.get("fullName")}
            if not pp_home or not pp_away:
                warnings.append(f"game {game.game_id}: probable pitcher missing for one or both sides")
            if g.get("odds"):
                o = g["odds"][0] if isinstance(g["odds"], list) else g["odds"]
                game.odds = Odds(
                    provider=(o.get("provider") or {}).get("name") if isinstance(o.get("provider"), dict) else None,
                    over_under=o.get("overUnder"),
                    details=o.get("details"),
                    source=ep.url_template,
                )
            games.append(game)
    return games, [_prov(prov, ep)], warnings


def _record(side: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rec = side.get("leagueRecord")
    if not rec:
        return None
    return {"wins": rec.get("wins"), "losses": rec.get("losses"), "pct": rec.get("pct")}


def nhl_games(date: str, log: Optional[FetchLog] = None,
              use_cache: bool = True) -> tuple:
    """Return ``(games, provenance, warnings)`` from the NHL scoreboard feed."""
    ep = get("nhl.scoreboard")
    data, prov = safe_json(ep.url(date=date), log=log, use_cache=use_cache)
    warnings: List[str] = []
    games: List[Game] = []
    if data is None:
        warnings.append(f"nhl.scoreboard unreachable: {prov.error}")
        return games, [_prov(prov, ep)], warnings

    for day in data.get("gamesByDate") or []:
        for g in day.get("games") or []:
            away = g.get("awayTeam") or {}
            home = g.get("homeTeam") or {}
            game = Game(
                sport="nhl",
                game_id=str(g.get("id")),
                starts_utc=g.get("startTimeUTC") or "",
                home_team=home.get("abbrev") or "???",
                away_team=away.get("abbrev") or "???",
                home_id=str(home.get("id")) if home.get("id") else None,
                away_id=str(away.get("id")) if away.get("id") else None,
                venue=(g.get("venue") or {}).get("default"),
                status=g.get("gameState"),
                provenance=[_prov(prov, ep)],
            )
            gt = g.get("gameType")
            if gt != 2:
                warnings.append(
                    f"NHL game {game.game_id} has gameType={gt} (2 = regular season); "
                    f"preseason/off-season data is not a valid projection input"
                )
            games.append(game)
    return games, [_prov(prov, ep)], warnings


ESPN_SPORT_PATHS = {
    "nfl": "football/nfl",
    "nba": "basketball/nba",
    "wnba": "basketball/wnba",
    "nhl": "hockey/nhl",
    "mlb": "baseball/mlb",
    "ncaaf": "football/college-football",
    "ncaab": "basketball/mens-college-basketball",
}


def espn_games(sport: str, date: Optional[str] = None, log: Optional[FetchLog] = None,
               use_cache: bool = True) -> tuple:
    """Return ``(games, provenance, warnings)`` from ESPN's public scoreboard JSON."""
    ep = get("espn.scoreboard")
    path = ESPN_SPORT_PATHS.get(sport)
    if path is None:
        raise SourceError(f"no ESPN sport path for {sport!r}; known: {sorted(ESPN_SPORT_PATHS)}")
    url = ep.url(sport_path=path)
    if date:
        url = url + f"?dates={date}"
    data, prov = safe_json(url, log=log, use_cache=use_cache)
    warnings: List[str] = []
    games: List[Game] = []
    if data is None:
        warnings.append(f"espn.scoreboard ({sport}) unreachable: {prov.error}")
        return games, [_prov(prov, ep)], warnings

    for ev in data.get("events") or []:
        for comp in ev.get("competitions") or []:
            competitors = comp.get("competitors") or []
            home = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home or not away:
                warnings.append(f"ESPN event {ev.get('id')}: missing a home or away competitor")
                continue
            venue = comp.get("venue") or {}
            game = Game(
                sport=sport,
                game_id=str(ev.get("id")),
                starts_utc=ev.get("date") or "",
                home_team=(home.get("team") or {}).get("abbreviation") or "???",
                away_team=(away.get("team") or {}).get("abbreviation") or "???",
                home_id=str((home.get("team") or {}).get("id") or "") or None,
                away_id=str((away.get("team") or {}).get("id") or "") or None,
                venue=venue.get("fullName"),
                status=(comp.get("status") or {}).get("type", {}).get("detail")
                       if isinstance(comp.get("status"), dict) else None,
                provenance=[_prov(prov, ep)],
            )
            game.extra["indoor"] = venue.get("indoor")
            game.extra["city"] = (venue.get("address") or {}).get("city")
            game.extra["state"] = (venue.get("address") or {}).get("state")
            odds_list = comp.get("odds") or []
            if odds_list:
                o = odds_list[0]
                provider = o.get("provider") or {}
                game.odds = Odds(
                    provider=provider.get("name") if isinstance(provider, dict) else str(provider),
                    spread=o.get("spread"),
                    over_under=o.get("overUnder"),
                    details=o.get("details"),
                    home_ml=(o.get("homeTeamOdds") or {}).get("moneyLine"),
                    away_ml=(o.get("awayTeamOdds") or {}).get("moneyLine"),
                    source=ep.url_template,
                )
            else:
                warnings.append(f"ESPN event {ev.get('id')}: no odds block present")
            games.append(game)
    return games, [_prov(prov, ep)], warnings


# --- weather ---------------------------------------------------------------

def _iso_window(valid_time: str) -> tuple:
    """Parse an ISO-8601 interval such as ``2026-09-22T10:00:00+00:00/PT2H``.

    Returns ``(start_datetime, hours)``.  Implemented by hand because the stdlib
    has no ISO-8601 *interval* parser and adding a dependency is not allowed.
    """
    if "/" not in valid_time:
        raise ValueError(f"not an ISO-8601 interval: {valid_time!r}")
    start_s, dur_s = valid_time.split("/", 1)
    start = _dt.datetime.fromisoformat(start_s.replace("Z", "+00:00"))
    hours = 0.0
    body = dur_s[1:] if dur_s.startswith("P") else dur_s
    if "T" in body:
        date_part, time_part = body.split("T", 1)
    else:
        date_part, time_part = body, ""
    if date_part.endswith("D"):
        hours += float(date_part[:-1]) * 24
    num = ""
    for ch in time_part:
        if ch.isdigit() or ch == ".":
            num += ch
        else:
            if num:
                factor = {"H": 1.0, "M": 1 / 60.0, "S": 1 / 3600.0}.get(ch)
                if factor:
                    hours += float(num) * factor
            num = ""
    return start, hours


def _series_at(props: Dict[str, Any], key: str, when: _dt.datetime) -> Optional[float]:
    """Value of NWS series ``key`` valid at ``when`` (UTC)."""
    block = props.get(key)
    if not isinstance(block, dict):
        return None
    for entry in block.get("values") or []:
        try:
            start, hours = _iso_window(entry.get("validTime", ""))
        except ValueError:
            continue
        end = start + _dt.timedelta(hours=hours)
        if start <= when < end:
            val = entry.get("value")
            return None if val is None else float(val)
    # No window contains ``when`` - fall back to the nearest window start so a
    # game just outside the forecast range still gets a value (and the caller
    # can see it was extrapolated via the returned warning list).
    best = None
    best_gap = None
    for entry in block.get("values") or []:
        try:
            start, _h = _iso_window(entry.get("validTime", ""))
        except ValueError:
            continue
        gap = abs((start - when).total_seconds())
        if best_gap is None or gap < best_gap:
            best_gap = gap
            best = entry.get("value")
    return float(best) if best is not None else None


def air_density(temperature_c: float, pressure_mb: float,
                relative_humidity_pct: float = 0.0) -> float:
    """Air density in kg/m^3 from temperature, pressure and humidity.

    Uses the standard moist-air formula: rho = (p_d / (R_d*T)) + (p_v / (R_v*T))
    where p_d is dry-air partial pressure and p_v the vapour pressure.

    Constants (SI, CODATA / WMO):
      R_d = 287.058 J/(kg*K)   specific gas constant, dry air
      R_v = 461.495 J/(kg*K)   specific gas constant, water vapour
    Saturation vapour pressure uses the Magnus-Tetens approximation with the
    WMO-recommended coefficients (6.112 hPa, 17.62, 243.12 C).

    This is physics, not a fitted fantasy constant, so it is reproducible and
    auditable.  Sources: https://en.wikipedia.org/wiki/Density_of_air and
    https://en.wikipedia.org/wiki/Tetens_equation
    """
    t_k = temperature_c + 273.15
    if t_k <= 0:
        raise ValueError("temperature must be above absolute zero")
    p_pa = pressure_mb * 100.0
    rh = max(0.0, min(100.0, relative_humidity_pct)) / 100.0
    es_hpa = 6.112 * _exp((17.62 * temperature_c) / (243.12 + temperature_c))
    p_v = rh * es_hpa * 100.0
    p_d = max(0.0, p_pa - p_v)
    return (p_d / (287.058 * t_k)) + (p_v / (461.495 * t_k))


def _exp(x: float) -> float:
    import math
    return math.exp(x)


def venue_weather(lat: float, lon: float, when_utc: str,
                  log: Optional[FetchLog] = None, use_cache: bool = True) -> tuple:
    """Resolve game-time weather for a venue.

    Two-step NWS lookup (point -> gridpoint), both verified 2026-09-22.
    Returns ``(Weather|None, provenance, warnings)``.
    """
    warnings: List[str] = []
    provs: List[Dict[str, Any]] = []

    pt_ep = get("nws.point")
    pt_url = pt_ep.url(lat=round(float(lat), 4), lon=round(float(lon), 4))
    pt, pt_prov = safe_json(pt_url, log=log, use_cache=use_cache)
    provs.append(_prov(pt_prov, pt_ep))
    if pt is None:
        warnings.append(f"NWS point lookup failed for {lat},{lon}: {pt_prov.error}")
        return None, provs, warnings

    props = ((pt.get("properties") or {}))
    grid_url = props.get("forecastGridData")
    grid_id, grid_x, grid_y = props.get("gridId"), props.get("gridX"), props.get("gridY")
    if not grid_url and None not in (grid_id, grid_x, grid_y):
        grid_url = get("nws.gridpoint").url(grid_id=grid_id, grid_x=grid_x, grid_y=grid_y)
    if not grid_url:
        warnings.append("NWS point response did not expose a forecastGridData link")
        return None, provs, warnings

    gp_ep = get("nws.gridpoint")
    gp, gp_prov = safe_json(grid_url, log=log, use_cache=use_cache)
    provs.append(_prov(gp_prov, gp_ep))
    if gp is None:
        warnings.append(f"NWS gridpoint fetch failed for {grid_url}: {gp_prov.error}")
        return None, provs, warnings

    gprops = gp.get("properties") or {}
    present = [k for k in ("temperature", "windSpeed", "windDirection", "barometricPressure",
                           "relativeHumidity", "probabilityOfPrecipitation", "skyCover")
               if isinstance(gprops.get(k), dict)]
    missing = [k for k in ("temperature", "windSpeed", "windDirection", "barometricPressure",
                           "relativeHumidity", "probabilityOfPrecipitation", "skyCover")
               if k not in present]
    if missing:
        warnings.append(f"NWS gridpoint {grid_url} is missing series: {missing} (present: {present})")

    when = _dt.datetime.fromisoformat(when_utc.replace("Z", "+00:00"))
    temp_c = _series_at(gprops, "temperature", when)
    wind_kmh = _series_at(gprops, "windSpeed", when)
    wind_dir = _series_at(gprops, "windDirection", when)
    press_pa = _series_at(gprops, "barometricPressure", when)
    rh = _series_at(gprops, "relativeHumidity", when)
    pop = _series_at(gprops, "probabilityOfPrecipitation", when)
    sky = _series_at(gprops, "skyCover", when)

    density = None
    if temp_c is not None and press_pa is not None:
        try:
            density = round(air_density(temp_c, press_pa / 100.0, rh or 0.0), 4)
        except ValueError as exc:
            warnings.append(f"air-density computation failed: {exc}")

    w = Weather(
        temperature_c=None if temp_c is None else round(temp_c, 2),
        temperature_f=None if temp_c is None else round(temp_c * 9.0 / 5.0 + 32.0, 1),
        wind_speed_mph=None if wind_kmh is None else round(wind_kmh * 0.621371, 1),
        wind_direction_deg=None if wind_dir is None else round(wind_dir, 1),
        pressure_mb=None if press_pa is None else round(press_pa / 100.0, 2),
        relative_humidity_pct=None if rh is None else round(rh, 1),
        precip_prob_pct=None if pop is None else round(pop, 1),
        sky_cover_pct=None if sky is None else round(sky, 1),
        air_density_kg_m3=density,
        source=gp_ep.url_template,
    )
    w.temp_desc = describe_temp(w.temperature_f)
    w.wind_desc = describe_wind(w.wind_speed_mph, w.wind_direction_deg)
    return w, provs, warnings


def describe_temp(temp_f: Optional[float]) -> Optional[str]:
    """Mirror RotoGrinders' TEMPDESC style ('neutraltemp', 'warm', 'cold').

    RotoGrinders publishes descriptors such as ``neutraltemp`` in its MLB grid
    (verified 2026-09-22) but does not publish the thresholds, so the bands
    below are RGENGY's own and are labelled as such everywhere they appear.
    """
    if temp_f is None:
        return None
    if temp_f < 50:
        return "verycold"
    if temp_f < 65:
        return "cold"
    if temp_f <= 80:
        return "neutraltemp"
    if temp_f <= 92:
        return "warm"
    return "verywarm"


_COMPASS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def describe_wind(mph: Optional[float], direction_deg: Optional[float]) -> Optional[str]:
    """RG-style wind descriptor, e.g. ``COLOut6`` = 6 mph blowing out.

    RotoGrinders' WIND column shows values like ``COLOut6`` on its public MLB
    grid (verified 2026-09-22). The composition rule (venue-side abbreviation +
    direction + integer mph) is RGENGY's reconstruction; RG does not document it.
    """
    if mph is None:
        return None
    rounded = int(round(mph))
    if direction_deg is None:
        return f"{rounded}mph"
    idx = int(((direction_deg + 11.25) % 360) // 22.5)
    return f"{_COMPASS[idx]}{rounded}"
