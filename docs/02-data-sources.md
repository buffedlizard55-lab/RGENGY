<!-- GENERATED FILE - DO NOT EDIT: rendered by scripts/build_docs.py from the committed registries. Edit the source and re-run the generator. -->

# 02 - Data sources

Every external input RGENGY uses, with the provider, whether that provider is the league/official body itself, the authentication it needs, and what was actually verified on **2026-09-22**. Generated from `rgengy/sources.py` by `scripts/build_docs.py` - edit the registry, not this file.

**16 endpoints**: 14 official / 2 unofficial, 0 requiring an API key.

| verification status | count | meaning |
| --- | ---: | --- |
| `live-verified` | 9 | retrieved and its response shape confirmed by inspection |
| `unverified` | 3 | NOT retrieved during the audit - listed for completeness only |
| `documented` | 3 | the provider documents it; it was not retrieved during the audit |
| `reachable` | 1 | reached successfully; response shape not fully confirmed |

> **L-02.** The audit environment had no outbound network access for raw fetches, so
> *no scoring value in this repository is marked `confirmed_by_operator`* - both
> operators keep their authoritative scoring pages inside their logged-in apps.
> `rgengy probe` and `rgengy verify` exist to be run from a networked machine and stamp
> each endpoint with its live status.

## ESPN (undocumented public JSON API)

Third-party feed.

### `espn.odds` - ESPN core API - competition odds

| | |
| --- | --- |
| status | `documented` (the provider documents it; it was not retrieved during the audit) |
| verified on | never |
| provider | ESPN (undocumented public JSON API) (unofficial) |
| auth | `none` |
| url | `https://sports.core.api.espn.com/v2/sports/{sport}/leagues/{league}/events/{event_id}/competitions/{competition_id}/odds` |
| docs | [https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c](https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c) |
| terms | **none published** - see IR-01 |
| replaces (RotoGrinders) | RG SPREAD / O/U / TOTAL columns, RG odds page |

> Documented by the retrieved endpoint listing, which shows a real response containing provider.{id,name,priority}, overUnder, details ('ATL -3.5'), spread, overOdds, underOdds and awayTeamOdds. Not fetched live during the audit, so it is used only when explicitly enabled.

### `espn.scoreboard` - ESPN site API - scoreboard (NFL / NBA / NHL / MLB / WNBA)

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | ESPN (undocumented public JSON API) (unofficial) |
| auth | `none` |
| url | `https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard` |
| docs | [https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c](https://gist.github.com/nntrn/ee26cb2a0716de0947a0a4e9a157bc1c) |
| terms | **none published** - see IR-01 |
| replaces (RotoGrinders) | RG NFL/NBA/WNBA slate, injury status, venue, RG odds feed (partially) |

> Retrieved 2026-09-22 for football/nfl: HTTP 200, 36 response chunks. Confirmed fields: leagues[].season/calendar, season.{type,year}, week.number, events[].{id,uid,date,name,shortName,competitions[]}, competitions[].{attendance,venue{fullName,address{city,state},indoor},competitors[]{id,homeAway,winner,team{id,location,name,abbreviation,displayName,color,logo},score,linescores[],records[],curatedRank}}. ESPN publishes no terms for this API; using it is a documented compliance risk (see docs/09-irregularities.md IR-01).

## MLB Advanced Media (MLBAM)

Official league/government feed.

### `mlb.player_stats` - MLB Stats API - player season stats

| | |
| --- | --- |
| status | `unverified` (NOT retrieved during the audit - listed for completeness only) |
| verified on | never |
| provider | MLB Advanced Media (MLBAM) (OFFICIAL) |
| auth | `none` |
| url | `https://statsapi.mlb.com/api/v1/people/{person_id}/stats?stats=season&group={group}&season={season}` |
| docs | [https://statsapi.mlb.com/](https://statsapi.mlb.com/) |
| terms | [http://gdx.mlb.com/components/copyright.txt](http://gdx.mlb.com/components/copyright.txt) |
| replaces (RotoGrinders) | RG player stat inputs, PlateIQ season stats |

> Same caveat as mlb.team_stats.

### `mlb.schedule` - MLB Stats API - schedule

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | MLB Advanced Media (MLBAM) (OFFICIAL) |
| auth | `none` |
| url | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}&hydrate=probablePitcher,odds,venue,team` |
| docs | [https://statsapi.mlb.com/](https://statsapi.mlb.com/) |
| terms | [http://gdx.mlb.com/components/copyright.txt](http://gdx.mlb.com/components/copyright.txt) |
| replaces (RotoGrinders) | RG MLB slate/schedule, RG probable-pitcher feed |

> Retrieved 2026-09-22 for date=2026-09-22: HTTP 200, totalGames=16. Response carries a copyright block that links the MLBAM terms page. Fields observed: gamePk, gameDate, officialDate, status.detailedState, teams.{away,home}.team.{id,name,abbreviation,venue}, teams.*.leagueRecord.{wins,losses,pct}, teams.*.probablePitcher.{id,fullName}, venue.{id,name}. The 'odds' hydrate was requested but no odds block was present in the inspected portion of the response - MLB odds are therefore sourced from ESPN (see nfl_espn / espn.scoreboard).

### `mlb.schedule_plain` - MLB Stats API - schedule (no hydration)

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | MLB Advanced Media (MLBAM) (OFFICIAL) |
| auth | `none` |
| url | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}` |
| docs | [https://statsapi.mlb.com/](https://statsapi.mlb.com/) |
| terms | [http://gdx.mlb.com/components/copyright.txt](http://gdx.mlb.com/components/copyright.txt) |
| replaces (RotoGrinders) | RG MLB slate/schedule |

> Retrieved 2026-09-22 for date=2026-09-21: HTTP 200, totalGames=3, all status 'Final'.

### `mlb.team_stats` - MLB Stats API - team season stats

| | |
| --- | --- |
| status | `unverified` (NOT retrieved during the audit - listed for completeness only) |
| verified on | never |
| provider | MLB Advanced Media (MLBAM) (OFFICIAL) |
| auth | `none` |
| url | `https://statsapi.mlb.com/api/v1/teams/{team_id}/stats?stats=season&group={group}&season={season}` |
| docs | [https://statsapi.mlb.com/](https://statsapi.mlb.com/) |
| terms | [http://gdx.mlb.com/components/copyright.txt](http://gdx.mlb.com/components/copyright.txt) |
| replaces (RotoGrinders) | RG team offensive/defensive ratings |

> Endpoint family confirmed present at statsapi.mlb.com, but this exact path/parameter set was NOT retrieved during the audit. The pipeline calls it through safe_json() and reports a degraded run if the shape differs. MUST be confirmed before the engine output is trusted.

### `mlb.venue` - MLB Stats API - venues

| | |
| --- | --- |
| status | `unverified` (NOT retrieved during the audit - listed for completeness only) |
| verified on | never |
| provider | MLB Advanced Media (MLBAM) (OFFICIAL) |
| auth | `none` |
| url | `https://statsapi.mlb.com/api/v1/venues/{venue_id}` |
| docs | [https://statsapi.mlb.com/](https://statsapi.mlb.com/) |
| terms | [http://gdx.mlb.com/components/copyright.txt](http://gdx.mlb.com/components/copyright.txt) |
| replaces (RotoGrinders) | WeatherEdge venue lookup |

> Needed for ballpark latitude/longitude so the NWS weather grid can be resolved. Not retrieved during the audit; a hard-coded venue coordinate table is NOT shipped, because inventing coordinates would violate the no-hallucination rule. Without this endpoint the weather layer reports 'venue coordinates unavailable' and skips the adjustment.

## National Basketball Association

Official league/government feed.

### `nba.cdn_scoreboard` - NBA CDN - live scoreboard

| | |
| --- | --- |
| status | `reachable` (reached successfully; response shape not fully confirmed) |
| verified on | 2026-09-22 |
| provider | National Basketball Association (OFFICIAL) |
| auth | `none` |
| url | `https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` |
| docs | [https://cdn.nba.com/](https://cdn.nba.com/) |
| terms | [https://www.nba.com/termsofuse](https://www.nba.com/termsofuse) |
| replaces (RotoGrinders) | RG NBA slate/schedule |

> Retrieved 2026-09-22: the fetch returned HTTP 500 through the audit proxy. The NBA regular season had not started on that date, so an empty slate is a plausible cause, but this is NOT confirmed. Treated as 'reachable' and never trusted without a runtime shape check.

## National Hockey League

Official league/government feed.

### `nhl.club_schedule` - NHL Web API - club schedule

| | |
| --- | --- |
| status | `documented` (the provider documents it; it was not retrieved during the audit) |
| verified on | never |
| provider | National Hockey League (OFFICIAL) |
| auth | `none` |
| url | `https://api-web.nhle.com/v1/club/schedule/{club}/{season}` |
| docs | [https://api-web.nhle.com/](https://api-web.nhle.com/) |
| terms | [https://www.nhl.com/info/terms-of-service](https://www.nhl.com/info/terms-of-service) |
| replaces (RotoGrinders) | RG NHL schedule |

> Same API family as the verified scoreboard endpoint but not individually retrieved during the audit.

### `nhl.player_landing` - NHL Web API - player landing page data

| | |
| --- | --- |
| status | `documented` (the provider documents it; it was not retrieved during the audit) |
| verified on | never |
| provider | National Hockey League (OFFICIAL) |
| auth | `none` |
| url | `https://api-web.nhle.com/v1/player/{player_id}/landing` |
| docs | [https://api-web.nhle.com/](https://api-web.nhle.com/) |
| terms | [https://www.nhl.com/info/terms-of-service](https://www.nhl.com/info/terms-of-service) |
| replaces (RotoGrinders) | RG NHL player stats |

> Not individually retrieved during the audit.

### `nhl.scoreboard` - NHL Web API - scoreboard

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | National Hockey League (OFFICIAL) |
| auth | `none` |
| url | `https://api-web.nhle.com/v1/scoreboard/{date}` |
| docs | [https://api-web.nhle.com/](https://api-web.nhle.com/) |
| terms | [https://www.nhl.com/info/terms-of-service](https://www.nhl.com/info/terms-of-service) |
| replaces (RotoGrinders) | RG NHL slate/schedule |

> Retrieved 2026-09-22: HTTP 200, focusedDateCount=11. Confirmed fields: gamesByDate[].games[].id, season (20262027), gameType (1 = preseason), gameDate, gameCenterLink, venue.default, startTimeUTC, easternUTCOffset, venueUTCOffset, tvBroadcasts[], gameState, awayTeam/homeTeam {id,name,commonName,placeNameWithPreposition,abbrev,score,logo}, periodDescriptor.

## RotoGrinders / Better Collective

Official league/government feed.

### `rg.public_grid` - RotoGrinders public projection grid (SPECIFICATION ONLY - not parsed at runtime)

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | RotoGrinders / Better Collective (OFFICIAL) |
| auth | `none` |
| url | `https://rotogrinders.com/projected-stats/{sport}` |
| docs | [https://rotogrinders.com/](https://rotogrinders.com/) |
| terms | [https://rotogrinders.com/terms](https://rotogrinders.com/terms) |

> Retrieved 2026-09-22 for mlb, nfl and wnba. These pages show a FREE six-row teaser above a paywall. RGENGY reads the *column headers* only, to define the output schema it must match. It never automates this endpoint: robots.txt disallows /api/ and /app, and reproducing paywalled rows would breach the site's terms. Columns are transcribed in docs/04-data-schema-catalog.md.

### `rg.robots` - RotoGrinders robots.txt

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | RotoGrinders / Better Collective (OFFICIAL) |
| auth | `none` |
| url | `https://rotogrinders.com/robots.txt` |
| terms | [https://rotogrinders.com/terms](https://rotogrinders.com/terms) |

> Retrieved 2026-09-22. Disallows /app, /grind-downs/, /api/ and *.csv for all user agents; declares sitemap at https://rotogrinders.com/sitemaps.xml. This is why RGENGY does not automate any RotoGrinders endpoint.

### `rg.sitemaps` - RotoGrinders sitemap index

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | RotoGrinders / Better Collective (OFFICIAL) |
| auth | `none` |
| url | `https://rotogrinders.com/sitemaps.xml` |
| terms | [https://rotogrinders.com/terms](https://rotogrinders.com/terms) |

> Retrieved 2026-09-22. Lists eight child sitemaps: sitemap.xml, articles.xml, authors.xml and per-sport player sitemaps for nfl, nba, mlb, nhl and pga. Confirms the five sports for which RotoGrinders publishes individual player URLs.

## U.S. National Weather Service (NOAA)

Official league/government feed.

### `nws.gridpoint` - NWS API - forecast grid data

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | U.S. National Weather Service (NOAA) (OFFICIAL) |
| auth | `none` |
| url | `https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}` |
| docs | [https://www.weather.gov/documentation/services-web-api](https://www.weather.gov/documentation/services-web-api) |
| terms | [https://www.weather.gov/disclaimer](https://www.weather.gov/disclaimer) |
| replaces (RotoGrinders) | WeatherEdge, THE BAT X weather/air-density layer |

> Retrieved 2026-09-22 for PSR/159,58: HTTP 200, 22 response chunks. Confirmed properties include validTimes, elevation and ISO-8601 duration time series (temperature in degC observed). The windSpeed/windDirection/barometricPressure/relativeHumidity/probabilityOfPrecipitation/skyCover series live in the same properties object per the NWS gridpoint schema; the audit inspected the temperature series in full and the file was truncated before the remaining series, so those five fields are 'documented, not individually observed'. The loader is written defensively and reports which keys were actually present.

### `nws.point` - NWS API - point metadata

| | |
| --- | --- |
| status | `live-verified` (retrieved and its response shape confirmed by inspection) |
| verified on | 2026-09-22 |
| provider | U.S. National Weather Service (NOAA) (OFFICIAL) |
| auth | `none` |
| url | `https://api.weather.gov/points/{lat},{lon}` |
| docs | [https://www.weather.gov/documentation/services-web-api](https://www.weather.gov/documentation/services-web-api) |
| terms | [https://www.weather.gov/disclaimer](https://www.weather.gov/disclaimer) |
| replaces (RotoGrinders) | WeatherEdge |

> Retrieved 2026-09-22 for 33.4484,-112.0740 (Phoenix): HTTP 200. Returns gridId/gridX/gridY, forecast and forecastGridData links, relativeLocation, timeZone, radarStation. NWS requires a User-Agent with contact info - rgengy.http sets one.
