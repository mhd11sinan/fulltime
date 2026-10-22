"""Update Fulltime's match and squad data from football-data.org.

- Finished matches missing from the RAW array in index.html are appended to it.
  Existing entries are never changed or reordered, because match ids come from
  their position in RAW and saved ratings use them.
- Scheduled fixtures replace the UPCOMING array on every run.
- Club squads are written to squads.json (only when they changed).

Usage:
    FOOTBALL_DATA_TOKEN=... python3 scripts/update_matches.py
    python3 scripts/update_matches.py --file matches.json [--squads-file teams.json]   # offline test
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
NOTES = os.path.join(ROOT, 'CLAUDE.md')
SQUADS = os.path.join(ROOT, 'squads.json')
SEASON = os.environ.get('SEASON', '2026')
API = 'https://api.football-data.org/v4/competitions/CL/matches?season=%s' % SEASON
TEAMS_API = 'https://api.football-data.org/v4/competitions/CL/teams?season=%s' % SEASON
KNOCKOUTS = 9

# football-data.org names that don't reduce to a site name on their own.
# Keys are normalised (see norm); values must be in TEAMS in index.html.
ALIASES = {
    'internazionale milano': 'Inter',
    'inter milan': 'Inter',
    'linzer ask': 'LASK',
    'sporting clube portugal': 'Sporting CP',
    'sporting lisbon': 'Sporting CP',
    'atleti': 'Atlético Madrid',
    'psg': 'Paris Saint-Germain',
    'pae aek': 'AEK Athens',
}
# Club-type words dropped before comparing names.
STOP = {'fc', 'cf', 'afc', 'sc', 'sk', 'fk', 'kv', 'ac', 'as', 'ss', 'ssc', 'osc', 'bv', 'vfb', 'pae',
        'club', 'de', 'cd', 'rc', 'racing', 'balompie', '1907', '09', 'calcio', 'futbol'}
POS_ORDER = {'GK': 0, 'DEF': 1, 'MID': 2, 'FWD': 3, '': 4}


def norm(name):
    name = name.lower()
    for a, b in (('ø', 'o'), ('ł', 'l'), ('đ', 'd'), ('ß', 'ss'), ('ı', 'i')):
        name = name.replace(a, b)
    name = ''.join(c for c in unicodedata.normalize('NFKD', name) if not unicodedata.combining(c))
    return ' '.join(t for t in re.findall(r'[a-z0-9]+', name) if t not in STOP)


def resolver(teams):
    by_norm = {norm(t): t for t in teams}

    def resolve(*names):
        for name in names:
            if not name:
                continue
            n = norm(name)
            if n in ALIASES:
                return ALIASES[n]
            if n in by_norm:
                return by_norm[n]
            words = set(n.split())
            hits = [t for k, t in by_norm.items() if set(k.split()) <= words or words <= set(k.split())]
            if len(hits) == 1:
                return hits[0]
        return None
    return resolve


def get(url):
    token = os.environ.get('FOOTBALL_DATA_TOKEN')
    if not token:
        sys.exit('FOOTBALL_DATA_TOKEN is not set. Add it as a repository secret.')
    req = urllib.request.Request(url, headers={'X-Auth-Token': token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def read_json(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def goals(score):
    # Use the score after 90 or 120 minutes, never the penalty shoot-out.
    rt, et = score.get('regularTime'), score.get('extraTime') or {}
    if rt and rt.get('home') is not None:
        return rt['home'] + (et.get('home') or 0), rt['away'] + (et.get('away') or 0)
    ft = score['fullTime']
    return ft['home'], ft['away']


def position(p):
    p = (p or '').lower()
    if 'goal' in p:
        return 'GK'
    if 'mid' in p:  # before 'def', so "Defensive Midfield" is a midfielder
        return 'MID'
    if 'def' in p or 'back' in p:
        return 'DEF'
    if any(w in p for w in ('off', 'attack', 'forward', 'wing', 'striker')):
        return 'FWD'
    return ''


def js_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def label(md):
    return 'the knockouts' if md == KNOCKOUTS else 'matchday %d' % md


def write(path, text):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def update_matches(html, data, resolve):
    """Returns (html, messages, new_count, latest_md, total)."""
    raw = re.search(r'var RAW=\[\n(.*?)\n\];', html, re.S)
    existing = [(int(md), d, h, a) for md, d, h, a in
                re.findall(r"\[(\d+),'([\d-]+)','((?:[^'\\]|\\.)*)',\d+,'((?:[^'\\]|\\.)*)',\d+\]", raw.group(1))]
    seen = set()
    for md, d, h, a in existing:
        seen.add((md, frozenset((h, a))) if md != KNOCKOUTS else (d, frozenset((h, a))))

    new, upcoming, unknown = [], [], set()
    for m in sorted(data.get('matches', []), key=lambda m: (m['utcDate'], m['id'])):
        status = m.get('status')
        if status not in ('FINISHED', 'SCHEDULED', 'TIMED'):
            continue
        if not m['homeTeam'].get('name') or not m['awayTeam'].get('name'):
            continue  # knockout tie whose teams aren't decided yet
        md = m['matchday'] if m.get('stage') == 'LEAGUE_STAGE' else KNOCKOUTS
        date = m['utcDate'][:10]
        home = resolve(m['homeTeam'].get('name'), m['homeTeam'].get('shortName'))
        away = resolve(m['awayTeam'].get('name'), m['awayTeam'].get('shortName'))
        if not home or not away:
            unknown.update(t['name'] for t, r in ((m['homeTeam'], home), (m['awayTeam'], away)) if not r)
            continue
        key = (md, frozenset((home, away))) if md != KNOCKOUTS else (date, frozenset((home, away)))
        if key in seen:
            continue
        if status != 'FINISHED':
            upcoming.append((md, date, home, away))
            continue
        seen.add(key)
        hs, as_ = goals(m['score'])
        new.append((md, date, home, hs, away, as_))

    if unknown:
        sys.exit('Unrecognised club names: %s. Add them to ALIASES in scripts/update_matches.py.'
                 % ', '.join(sorted(unknown)))

    messages = []
    if new:
        added = ',\n'.join(' [%d,%s,%s,%d,%s,%d]' % (md, js_str(d), js_str(h), hs, js_str(a), as_)
                           for md, d, h, hs, a, as_ in new)
        html = html[:raw.end(1)] + ',\n' + added + html[raw.end(1):]
        for md, d, h, hs, a, as_ in new:
            print('%s  %s %d-%d %s  (%s)' % (d, h, hs, as_, a, label(md)))
        mds = sorted({n[0] for n in new})
        messages.append('add results: %s (%d matches)' % (', '.join(label(md) for md in mds), len(new)))

    # UPCOMING is rewritten in full each run; RAW is only ever appended to.
    up_block = 'var UPCOMING=[\n' + ',\n'.join(
        ' [%d,%s,%s,%s]' % (md, js_str(d), js_str(h), js_str(a)) for md, d, h, a in upcoming) + ('\n' if upcoming else '') + '];'
    old_up = re.search(r'var UPCOMING=\[\n.*?\];', html, re.S)
    if old_up is not None and old_up.group(0) != up_block:
        html = html[:old_up.start()] + up_block + html[old_up.end():]
        messages.append('update upcoming fixtures (%d)' % len(upcoming))

    latest = max([e[0] for e in existing] + [n[0] for n in new])
    return html, messages, len(new), latest, len(existing) + len(new)


def update_squads(data, resolve):
    """Returns a message if squads.json changed, else None."""
    teams, unknown = {}, set()
    for t in data.get('teams', []):
        name = resolve(t.get('name'), t.get('shortName'))
        if not name:
            unknown.add(t.get('name'))
            continue
        players = []
        for p in t.get('squad') or []:
            if p.get('name'):
                players.append({'id': p.get('id'), 'name': p['name'], 'pos': position(p.get('position'))})
        if players:
            players.sort(key=lambda p: (POS_ORDER[p['pos']], p['name']))
            teams[name] = players
    if unknown:
        sys.exit('Unrecognised club names in squads: %s. Add them to ALIASES in scripts/update_matches.py.'
                 % ', '.join(sorted(n for n in unknown if n)))
    if not teams:
        print('No squads returned; squads.json left as it is.')
        return None
    # One club per line keeps the file small but the git diffs readable.
    text = '{"season":"2026/27","teams":{\n' + ',\n'.join(
        json.dumps(t, ensure_ascii=False) + ':' + json.dumps(ps, ensure_ascii=False, separators=(',', ':'))
        for t, ps in sorted(teams.items())) + '\n}}\n'
    old = open(SQUADS, encoding='utf-8').read() if os.path.exists(SQUADS) else ''
    if text == old:
        return None
    write(SQUADS, text)
    return 'update squads (%d clubs, %d players)' % (len(teams), sum(len(v) for v in teams.values()))


def main(args):
    html = open(INDEX, encoding='utf-8').read()
    teams = re.findall(r"'([^']+)'", re.search(r'var TEAMS=\[(.*?)\];', html, re.S).group(1))
    resolve = resolver(teams)
    offline = '--file' in args

    matches = read_json(args[args.index('--file') + 1]) if offline else get(API)
    html, messages, new_count, latest, total = update_matches(html, matches, resolve)

    if new_count:
        html = re.sub(r'/\* ---------- data: .*? ---------- \*/',
                      '/* ---------- data: results through %s of 2026/27, appended by scripts/update_matches.py ---------- */'
                      % label(latest), html, count=1)
        html = re.sub(r'Results here run through (?:matchday \d+|the knockouts)\.',
                      'Results here run through %s.' % label(latest), html, count=1)
        notes = open(NOTES, encoding='utf-8').read()
        notes = re.sub(r'^- Matches seeded:.*$',
                       '- Matches seeded: %d results through %s. New results are added weekly by '
                       '`.github/workflows/update-matches.yml` from football-data.org.' % (total, label(latest)),
                       notes, count=1, flags=re.M)
        write(NOTES, notes)
    if messages:
        write(INDEX, html)

    squads = None
    if '--squads-file' in args:
        squads = read_json(args[args.index('--squads-file') + 1])
    elif not offline:
        time.sleep(7)  # free plan allows 10 requests a minute
        squads = get(TEAMS_API)
    if squads is not None:
        msg = update_squads(squads, resolve)
        if msg:
            messages.append(msg)

    if not messages:
        print('No changes.')
        return
    msg = '; '.join(messages)
    msg = msg[0].upper() + msg[1:]
    print(msg)
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a', encoding='utf-8') as f:
            f.write('message=%s\n' % msg)


if __name__ == '__main__':
    main(sys.argv[1:])
