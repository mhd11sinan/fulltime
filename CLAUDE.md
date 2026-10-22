# Fulltime

Letterboxd-style site for football fans. Users log matches, rate them (0.5 to 5 stars), write short takes, rate players, and show a top four of matches and players on a profile that friends can visit. This is opinion-based: there is no crowd "rating" and fan bias is part of the point.

## Current scope
- Competition: UEFA Champions League 2026/27 league phase only.
- Players: names only, no photos or club crests (avoids licensing problems).
- Matches seeded: 54 results through matchday 3. New results are added weekly by `.github/workflows/update-matches.yml` from football-data.org.
- One fixture (Slavia Praha v Lens, 10 Sep 2026) had home and away order that differed between sources. Verify against UEFA before relying on it.

## Current implementation
- Single file: `index.html` (vanilla JS, no build step, no dependencies).
- Per-user data lives in `localStorage` under key `fulltime.v1`.
- The Friends tab uses Claude artifact runtime capabilities (`claude.use('db')`, `claude.use('user')`). These only exist when the page is hosted on claude.ai. Outside that, the code falls back to local-only mode and the Friends tab explains this. To run it elsewhere, replace that block (`initCaps`, `pushNow`, `removeShared`) with a real backend.
- `RAW` is append-only: match ids are `'m'+(index+1)`, so never reorder or remove entries. `scripts/update_matches.py` appends finished matches from football-data.org; `.github/workflows/update-matches.yml` runs it every Friday 06:00 UTC (and on demand) using the `FOOTBALL_DATA_TOKEN` repository secret, then commits and pushes. If it fails on an unrecognised club name, add the name to `ALIASES` in the script.
- All data from other users is sanitised by `clean()` before rendering and escaped with `esc()`. Keep that when changing the sync code.

## Data model
- Match: `{id, md, date, home, hs, away, as}` (custom matches have ids starting with `c`).
- Log (per match): `{rating, mode, review, ts}` where mode is live, replay, attended or highlights.
- Player: `{id, name, team, rating, note}`, id = slug(name)|slug(team). Prefer the provider's player ID once an API is added.
- Profile: `{logs, players, favM[4], favP[4], custom[]}`.

## Roadmap (in rough priority order)
1. Real backend with accounts, so profiles are public and followable (Postgres or SQLite plus auth).
2. Import fixtures, results and squads from football-data.org (free tier includes the Champions League; verify limits on their official pricing page; 10 calls/min, delayed scores). Cache responses server-side.
3. Follow system and a feed of friends' recent logs.
4. Lists (for example "greatest comebacks") and per-match player ratings.
5. Expand beyond the Champions League.

## Conventions
- Keep it dependency-free until a backend exists.
- Use sentence case and plain wording in the UI.
- Light and dark themes both supported via CSS variables; keep both working.
