# Fulltime

Letterboxd-style site for football fans. Users log matches, rate them (0.5 to 5 stars), write short takes, rate players, and show a top four of matches and players on a profile that friends can visit. This is opinion-based: there is no crowd "rating" and fan bias is part of the point.

## Current scope
- Competition: UEFA Champions League 2026/27 league phase only.
- Players: names only, no photos or club crests (avoids licensing problems).
- Matches seeded: 54 results through matchday 3. New results are added weekly by `.github/workflows/update-matches.yml` from football-data.org.
- One fixture (Slavia Praha v Lens, 10 Sep 2026) had home and away order that differed between sources. Verify against UEFA before relying on it.

## Current implementation
- Single page: `index.html` (vanilla JS, no build step), hosted on GitHub Pages. Its only dependency is supabase-js 2.45.4 from jsDelivr.
- Accounts and storage: Supabase (Postgres + Auth), set up as described in SUPABASE.md. Schema and row-level security rules are in `supabase/schema.sql`; everything is publicly readable and users can only write their own rows. `config.js` holds the project URL and publishable key (public by design; never the secret key).
- Sign-in: username + password only (no email, no OAuth). Supabase Auth still needs an email, so `authEmail()` maps a username to `<username>@<config.authEmailDomain>` (default `users.fulltime.invalid`); "Confirm email" must be off. Sign-up sends the username as user metadata and the `on_auth_user_created` trigger creates the `profiles` row in the same transaction. Usernames (`^[a-z0-9_]{3,20}$`) can't change, because the sign-in address is derived from them, and there's no self-service password reset; see SUPABASE.md. `openUsername` remains only as a fallback for an account with no profile.
- Signed out (or `config.js` empty): data lives in `localStorage` under `fulltime.v1`, as before. Signed in: data is loaded from Supabase into `S` and every change is written through by `putLog`/`delLog`/`putPlayer`/`delPlayer`/`putCustom`/`delCustom`/`putFavs`. Never write `localStorage` while signed in.
- Import: when signed in, the Profile tab offers to copy browser-only ratings into the account (`importable`, `doImport`); `fulltime.v1.imported.<user id>` remembers it was done or dismissed.
- Routes: `#/m/<id>` match page, `#/u/<username>[/diary|likes|watchlist|lists|stats][/<list id>]` public profile, `#/people` the People list. Everything else (tabs, own profile section `V.psub`, open list `V.listId`) is in-memory state.
- `UPCOMING` holds scheduled fixtures `[md, date, home, away]`; the update script rewrites it every run. Upcoming matches have ids `u_<fixture key>`. A fixture key is `date_homeslug_awayslug` (`fkey()`); the watchlist stores keys, not ids, so an entry survives the match moving from `UPCOMING` to `RAW`.
- Profiles have sections: Profile (top fours, recent diary), Diary, Likes, Watchlist, Lists, Stats. Stats charts are plain HTML/CSS bars in `--accent`, one series each, with hover tooltips.
- Match pages show your log and, when Supabase is on, other fans' rating spread (no average, per the opinion-first scope), like count and reviews.
- `RAW` is append-only: match ids are `'m'+(index+1)`, so never reorder or remove entries. `scripts/update_matches.py` appends finished matches from football-data.org; `.github/workflows/update-matches.yml` runs it every Friday 06:00 UTC (and on demand) using the `FOOTBALL_DATA_TOKEN` repository secret, then commits and pushes. If it fails on an unrecognised club name, add the name to `ALIASES` in the script.
- All data loaded from Supabase (including other users') goes through `clean()` before rendering and is escaped with `esc()`. Keep that when adding queries.

## Data model
- Match: `{id, md, date, home, hs, away, as}` (custom matches have ids starting with `c`).
- Log (per match): `{rating, mode, review, ts}` where mode is live, replay, attended or highlights.
- Player: `{id, name, team, rating, note}`, id = slug(name)|slug(team). Prefer the provider's player ID once an API is added.
- Profile: `{logs, players, favM[4], favP[4], custom[]}`.
- Profile also has `likes[]` (match ids, newest first), `watch[]` (fixture keys) and `lists[]` (`{id:'l…', name, desc, items:[match ids], ts}`, up to 50 lists of 100 matches).
- Supabase tables: `profiles` (id, username, fav_matches, fav_players), `match_logs`, `player_ratings`, `custom_matches` (home_goals/away_goals, match_date), `match_likes`, `watchlist` (fixture), `lists` (description, items text[]), all keyed by user.

## Roadmap (in rough priority order)
1. Done (phase 1): accounts, usernames, public profiles, People list, browser import. Still to do here: account deletion and username changes.
2. Import fixtures, results and squads from football-data.org (free tier includes the Champions League; verify limits on their official pricing page; 10 calls/min, delayed scores). Cache responses server-side.
3. Follow system and a feed of friends' recent logs.
4. Done: match pages, likes, watchlist, lists, stats. Still to do: per-match player ratings.
5. Expand beyond the Champions League.

## Conventions
- No build step; add libraries only from a CDN with an exact version.
- Use sentence case and plain wording in the UI.
- Light and dark themes both supported via CSS variables; keep both working.
