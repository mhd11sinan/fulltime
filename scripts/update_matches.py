"""Add newly finished Champions League matches to index.html.

Fetches finished matches from football-data.org and appends any that are
missing to the RAW array. Existing entries are never changed or reordered,
because match ids come from their position in RAW and saved ratings use them.

Usage:
    FOOTBALL_DATA_TOKEN=... python3 scripts/update_matches.py
    python3 scripts/update_matches.py --file sample.json   # offline test
"""
import json
import os
import re
import sys
import unicodedata
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, 'index.html')
NOTES = os.path.join(ROOT, 'CLAUDE.md')
SEASON = os.environ.get('SEASON', '2026')
API = 'https://api.football-data.org/v4/competitions/CL/matches?season=%s&status=FINISHED' % SEASON
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


def fetch(args):
    if '--file' in args:
        with open(args[args.index('--file') + 1], encoding='utf-8-sig') as f:
            return json.load(f)
    token = os.environ.get('FOOTBALL_DATA_TOKEN')
    if not token:
        sys.exit('FOOTBALL_DATA_TOKEN is not set. Add it as a repository secret.')
    req = urllib.request.Request(API, headers={'X-Auth-Token': token})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def goals(score):
    # Use the score after 90 or 120 minutes, never the penalty shoot-out.
    rt, et = score.get('regularTime'), score.get('extraTime') or {}
    if rt and rt.get('home') is not None:
        return rt['home'] + (et.get('home') or 0), rt['away'] + (et.get('away') or 0)
    ft = score['fullTime']
    return ft['home'], ft['away']


def js_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def label(md):
    return 'the knockouts' if md == KNOCKOUTS else 'matchday %d' % md


def main(args):
    html = open(INDEX, encoding='utf-8').read()
    teams = re.findall(r"'([^']+)'", re.search(r'var TEAMS=\[(.*?)\];', html, re.S).group(1))
    raw = re.search(r'var RAW=\[\n(.*?)\n\];', html, re.S)
    existing = [(int(md), d, h, a) for md, d, h, a in
                re.findall(r"\[(\d+),'([\d-]+)','((?:[^'\\]|\\.)*)',\d+,'((?:[^'\\]|\\.)*)',\d+\]", raw.group(1))]
    seen = set()
    for md, d, h, a in existing:
        seen.add((md, frozenset((h, a))) if md != KNOCKOUTS else (d, frozenset((h, a))))

    resolve = resolver(teams)
    new, unknown = [], set()
    data = fetch(args)
    for m in sorted(data.get('matches', []), key=lambda m: (m['utcDate'], m['id'])):
        if m.get('status') != 'FINISHED':
            continue
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
        seen.add(key)
        hs, as_ = goals(m['score'])
        new.append((md, date, home, hs, away, as_))

    if unknown:
        sys.exit('Unrecognised club names: %s. Add them to ALIASES in scripts/update_matches.py.'
                 % ', '.join(sorted(unknown)))
    if not new:
        print('No new results.')
        return

    lines = ' [%d,%s,%s,%d,%s,%d]'
    added = ',\n'.join(lines % (md, js_str(d), js_str(h), hs, js_str(a), as_) for md, d, h, hs, a, as_ in new)
    html = html[:raw.end(1)] + ',\n' + added + html[raw.end(1):]

    latest = max([e[0] for e in existing] + [n[0] for n in new])
    total = len(existing) + len(new)
    html = re.sub(r'/\* ---------- data: .*? ---------- \*/',
                  '/* ---------- data: results through %s of 2026/27, appended by scripts/update_matches.py ---------- */'
                  % label(latest), html, count=1)
    html = re.sub(r'Results here run through (?:matchday \d+|the knockouts)\.',
                  'Results here run through %s.' % label(latest), html, count=1)
    with open(INDEX, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)

    notes = open(NOTES, encoding='utf-8').read()
    notes = re.sub(r'^- Matches seeded:.*$',
                   '- Matches seeded: %d results through %s. New results are added weekly by '
                   '`.github/workflows/update-matches.yml` from football-data.org.' % (total, label(latest)),
                   notes, count=1, flags=re.M)
    with open(NOTES, 'w', encoding='utf-8', newline='\n') as f:
        f.write(notes)

    mds = sorted({n[0] for n in new})
    msg = 'Add results: %s (%d matches)' % (', '.join(label(md) for md in mds), len(new))
    for md, d, h, hs, a, as_ in new:
        print('%s  %s %d-%d %s  (%s)' % (d, h, hs, as_, a, label(md)))
    print(msg)
    out = os.environ.get('GITHUB_OUTPUT')
    if out:
        with open(out, 'a', encoding='utf-8') as f:
            f.write('message=%s\n' % msg)


if __name__ == '__main__':
    main(sys.argv[1:])
