#!/usr/bin/env python3
"""Scrape r/Affairs submissions from the Arctic Shift archive and bake an
aggregated data/data.json for the Secret Encounters infographic.
(PullPush is edge-blocked/backend-down; Arctic Shift is the Pushshift-successor
that side-project-census already uses successfully.)

Usage:  python3 scrape.py [days]      # history window, default 365
        python3 scrape.py demo        # parser self-check
    python3 scrape.py rebuild     # aggregate existing checkpoints only
Stdlib only. Output is aggregates only — no usernames or post IDs are stored.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, urllib.error
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
API = "https://arctic-shift.photon-reddit.com/api/posts/search"
OUT = ROOT / "data" / "data.json"
LEGACY_RAW = ROOT / "data" / "raw"
RAW = Path(os.environ.get("SECRET_ENCOUNTERS_RAW_DIR", str(ROOT / ".checkpoints" / "raw"))).expanduser()
UA = {"User-Agent": "secret-encounters/1.0 (vintage data-viz research)"}

TAG = re.compile(r"\[\s*([mfta])\s*4\s*([mfta])\w*\s*\]", re.I)  # [M4F] [F4M] [M4A] [M4MF]
TAG_BARE = re.compile(r"\b([mfta])\s*4\s*([mfta])\b", re.I)    # 37 m4f #Missouri (title only)
PAIR = re.compile(r"\b(\d{2})\s*[-/–—]?\s*([MF])\b|\b([MF])\s*[-/–—]?\s*(\d{2})\b", re.I)

MOTIFS = {
    "dead_bedroom":   ["dead bedroom", "dead-bedroom", "sexless", "no sex", "no intimacy",
                       "lack of intimacy", "touch starved", "touch-starved"],
    "thrill_variety": ["thrill", "excitement", "exciting", "variety", "spark", "adrenaline",
                       "bored", "boredom", "adventure", "naughty", "forbidden"],
    "emotional_gap":  ["emotional connection", "emotionally", "unappreciated", "neglected",
                       "ignored", "taken for granted", "understood", "validation"],
    "loneliness":     ["lonely", "loneliness", "alone", "isolated", "no one to talk"],
    "desired":        ["feel wanted", "feel desired", "feeling wanted", "feeling desired",
                       "desired", "attractive", "attention", "craved", "adored"],
    "escape":         ["escape", "stress", "unhappy", "resentment", "checked out",
                       "roommate", "miserable", "trapped"],
}

CITIES = {  # name: (lat, lon, [aliases])
    "New York":      (40.71,  -74.00, ["new york", "newyork", "nyc", "ny", "manhattan", "brooklyn"]),
    "Los Angeles":   (34.05, -118.24, ["los angeles", "losangeles", "la"]),
    "Chicago":       (41.88,  -87.63, ["chicago"]),
    "Toronto":       (43.65,  -79.38, ["toronto", "gta"]),
    "London":        (51.51,   -0.13, ["london"]),
    "Houston":       (29.76,  -95.37, ["houston", "htx"]),
    "Seattle":       (47.61, -122.33, ["seattle"]),
    "San Francisco": (37.77, -122.42, ["san francisco", "sanfrancisco", "sf bay", "bay area", "sf", "bayarea"]),
    "Boston":        (42.36,  -71.06, ["boston"]),
    "Atlanta":       (33.75,  -84.39, ["atlanta", "atl"]),
    "Denver":        (39.74, -104.99, ["denver"]),
    "Austin":        (30.27,  -97.74, ["austin", "atx"]),
    "Portland":      (45.52, -122.68, ["portland", "pdx"]),
    "Las Vegas":     (36.17, -115.14, ["las vegas", "lasvegas", "vegas"]),
    "Miami":         (25.76,  -80.19, ["miami", "south florida", "soflo", "broward",
                                       "fort lauderdale", "ft lauderdale", "ft. lauderdale", "west palm"]),
    "Philadelphia":  (39.95,  -75.17, ["philadelphia", "philly"]),
    "San Diego":     (32.72, -117.16, ["san diego", "sandiego"]),
    "Dallas":        (32.78,  -96.80, ["dallas", "dfw"]),
    "Phoenix":       (33.45, -112.07, ["phoenix", "phx", "scottsdale"]),
    "Minneapolis":   (44.98,  -93.27, ["minneapolis", "twin cities"]),
    "Vancouver":     (49.28, -123.12, ["vancouver"]),
    "Montreal":      (45.50,  -73.57, ["montreal", "mtl"]),
    "Sydney":        (-33.87, 151.21, ["sydney"]),
    "Melbourne":     (-37.81, 144.96, ["melbourne"]),
    "Dublin":        (53.35,   -6.26, ["dublin"]),
    "Manchester":    (53.48,   -2.24, ["manchester"]),
    "Amsterdam":     (52.37,    4.90, ["amsterdam"]),
    "Berlin":        (52.52,   13.40, ["berlin"]),
    "Paris":         (48.86,    2.35, ["paris"]),
    "Washington":    (38.91,  -77.04, ["washington dc", "dc area", "dmv", "dc", "nova"]),
    "Nashville":     (36.16,  -86.78, ["nashville"]),
    "New Orleans":   (29.95,  -90.07, ["new orleans", "neworleans", "nola"]),
    "Calgary":       (51.05, -114.07, ["calgary"]),
    "Columbus":      (39.96,  -83.00, ["columbus"]),
    "Charlotte":     (35.23,  -80.84, ["charlotte"]),
    "Kansas City":   (39.10,  -94.58, ["kansas city", "kansascity", "kc mo", "kcmo"]),
    "San Jose":      (37.34, -121.89, ["san jose", "sanjose"]),
    "Tampa":         (27.95,  -82.46, ["tampa"]),
    "Orlando":       (28.54,  -81.38, ["orlando"]),
    "Detroit":       (42.33,  -83.05, ["detroit"]),
    "Baltimore":     (39.29,  -76.61, ["baltimore"]),
    "Pittsburgh":    (40.44,  -80.00, ["pittsburgh"]),
    "St. Louis":     (38.63,  -90.20, ["st. louis", "st louis", "stlouis", "stl"]),
    "Sacramento":    (38.58, -121.49, ["sacramento"]),
    "Indianapolis":  (39.77,  -86.16, ["indianapolis", "indy"]),
    "Raleigh":       (35.78,  -78.64, ["raleigh", "rdu"]),
    "Salt Lake City": (40.76, -111.89, ["salt lake city", "salt lake", "slc"]),
    "Brisbane":      (-27.47, 153.03, ["brisbane"]),
    "Ottawa":        (45.42,  -75.70, ["ottawa"]),
    "Edmonton":      (53.55, -113.49, ["edmonton"]),
}
CITY_RES = [(name, re.compile(r"\b(?:" + "|".join(map(re.escape, aliases)) + r")\b"))
            for name, (_, _, aliases) in CITIES.items()]

def checkpoint_sort_key(path):
    try:
        return (0, int(path.stem))
    except ValueError:
        return (1, path.stem)

def checkpoint_files():
    files = sorted(RAW.glob("*.json"), key=checkpoint_sort_key)
    if files:
        return files
    legacy = sorted(LEGACY_RAW.glob("*.json"), key=checkpoint_sort_key)
    if legacy:
        print(f"using legacy checkpoints from {LEGACY_RAW}; set SECRET_ENCOUNTERS_RAW_DIR to keep checkpoints outside web data/", flush=True)
    return legacy

def load_json_posts(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  skipping {path.name}: {type(e).__name__}: {e}", flush=True)
        return []
    if isinstance(payload, list):
        return payload
    print(f"  skipping {path.name}: expected a JSON array", flush=True)
    return []

def dedupe_posts(posts):
    seen = set()
    unique = []
    dropped = 0
    for post in posts:
        pid = post.get("id") if isinstance(post, dict) else None
        key = ("id", pid) if pid else ("fallback", post.get("created_utc") if isinstance(post, dict) else None,
                                        post.get("title") if isinstance(post, dict) else None,
                                        post.get("selftext") if isinstance(post, dict) else None)
        if key in seen:
            dropped += 1
            continue
        seen.add(key)
        unique.append(post)
    return unique, dropped

def age_bucket(a):
    return "18-24" if a < 25 else "25-34" if a < 35 else "35-44" if a < 45 else "45-54" if a < 55 else "55+"

def parse_post(p):
    title = p.get('title') or ''
    text = f"{title}\n{p.get('selftext') or ''}"
    tag = TAG.search(text) or TAG_BARE.search(title)
    gender = tag.group(1).upper() if tag else None
    tgender = tag.group(2).upper() if tag else None
    if gender not in ("M", "F"):  gender = None
    if tgender not in ("M", "F"): tgender = None
    pairs = [(int(m.group(1) or m.group(4)), (m.group(2) or m.group(3)).upper())
             for m in PAIR.finditer(text)]
    pairs = [(a, g) for a, g in pairs if 18 <= a <= 75]
    age = next((a for a, g in pairs if gender and g == gender), None)
    if age is None and tag:  # "34 [M4F]" — bare number next to the tag
        bare = re.search(r"\b(\d{2})\b", text)
        if bare and 18 <= int(bare.group(1)) <= 75: age = int(bare.group(1))
    if age is None and pairs:    age = pairs[0][0]
    if gender is None and pairs: gender = pairs[0][1]
    tage = next((a for a, g in pairs if tgender and g == tgender and a != age), None)
    low = text.lower()
    return {
        "gender": gender, "age": age, "tage": tage,
        "seeking": f"{gender}4{tgender}" if gender and tgender else None,
        "motives": [k for k, kws in MOTIFS.items() if any(kw in low for kw in kws)],
        "cities":  [name for name, rx in CITY_RES if rx.search(low)],
    }

def fetch(after):
    q = {"subreddit": "affairs", "after": after, "sort": "asc", "limit": "auto",
         "fields": "id,title,selftext,created_utc"}
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(q), headers=UA)
    for attempt in range(8):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.load(r).get("data") or []
                if data: return data
                print(f"  empty page; retry {attempt + 1}/8", flush=True)
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}; slowing down (retry {attempt + 1}/8)", flush=True)
        except Exception as e:
            print(f"  {type(e).__name__}: {e}; retry {attempt + 1}/8", flush=True)
        time.sleep(15 * (attempt + 1))  # archive rate-limits bursts: "Timeout. Maybe slow down a bit"
    return []  # exhausted retries — caller skips the cursor forward

def main(days):
    posts = []
    now = int(time.time())
    RAW.mkdir(parents=True, exist_ok=True)
    saved = checkpoint_files()
    if saved:  # resume from checkpoints
        for p in saved:
            posts.extend(load_json_posts(p))
        cursors = [p.get("created_utc") for p in posts if isinstance(p, dict) and isinstance(p.get("created_utc"), (int, float))]
        cursor = int(max(cursors)) if cursors else now - days * 86400
        print(f"resuming: {len(posts)} posts from {len(saved)} saved pages", flush=True)
    else:
        cursor = now - days * 86400
    skips = 0
    for i in range(len(saved), 1500):  # safety cap
        batch = fetch(cursor)
        if not batch:  # cursor the archive keeps choking on — step past it (negligible loss)
            skips += 1
            if skips > 10: sys.exit("archive kept refusing — rerun to resume from checkpoints")
            cursor += 5
            print(f"  skipping cursor (+{skips * 5}s)", flush=True)
            continue
        skips = 0
        posts.extend(batch)
        (RAW / f"{i + 1}.json").write_text(json.dumps(batch), encoding="utf-8")
        cursor = batch[-1].get("created_utc", now)
        print(f"page {i + 1}: {len(posts)} posts (up to {time.strftime('%Y-%m-%d', time.gmtime(cursor))})", flush=True)
        if cursor >= now - 1800 or len(batch) < 50: break  # caught up to ~now
        time.sleep(1.2)  # polite cadence
    if not posts:
        sys.exit("no posts collected")
    posts, dropped = dedupe_posts(posts)
    if dropped:
        print(f"deduped {dropped} repeated posts by id/fingerprint", flush=True)
    data = aggregate(posts)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {OUT} — {len(posts)} posts, {data['gendered']} gendered, {data['seeking_tagged']} seeking-tags")

def analyze_posts(records):
    buckets = ['18-24', '25-34', '35-44', '45-54', '55+']
    coverage = {gender: Counter() for gender in ('M', 'F')}
    age_values = {gender: [] for gender in coverage}
    strata = {gender: {bucket: Counter() for bucket in buckets} for gender in coverage}
    cities = {city: {'gender': Counter(), 'single': Counter(), 'title': Counter(),
                     'specific': Counter(), 'ages': {gender: Counter() for gender in coverage}}
              for city in CITIES}
    specific_patterns = {city: re.compile(r'\b(?:' + '|'.join(re.escape(alias) for alias in aliases if len(alias) > 3) + r')\b')
                         for city, (_, _, aliases) in CITIES.items()}
    months = {}
    authors_available = 0
    for post, parsed in records:
        gender = parsed['gender']
        if gender not in coverage:
            continue
        counts = coverage[gender]
        counts['posts'] += 1
        counts['age'] += parsed['age'] is not None
        counts['city'] += bool(parsed['cities'])
        counts['seeking'] += parsed['seeking'] is not None
        counts['reason'] += bool(parsed['motives'])
        counts['multiple_cities'] += len(parsed['cities']) > 1
        author = post.get('author')
        authors_available += isinstance(author, str) and author.lower() not in ('', '[deleted]', '[removed]')
        bucket = age_bucket(parsed['age']) if parsed['age'] else None
        if bucket:
            age_values[gender].append(parsed['age'])
            strata[gender][bucket]['posts'] += 1
            strata[gender][bucket]['city'] += bool(parsed['cities'])
            for motif in parsed['motives']:
                strata[gender][bucket][motif] += 1
        timestamp = post.get('created_utc')
        month = time.strftime('%Y-%m', time.gmtime(timestamp)) if isinstance(timestamp, (int, float)) else None
        if month:
            monthly = months.setdefault(month, {'gender': Counter(), 'coverage': {group: Counter() for group in coverage}, 'cities': {}})
            monthly['gender'][gender] += 1
            for field in ('age', 'city', 'seeking', 'reason'):
                monthly['coverage'][gender][field] += {'age': bucket is not None, 'city': bool(parsed['cities']),
                    'seeking': parsed['seeking'] is not None, 'reason': bool(parsed['motives'])}[field]
        title = (post.get('title') or '').lower()
        text = title + '\n' + (post.get('selftext') or '').lower()
        for city in parsed['cities']:
            city_counts = cities[city]
            city_counts['gender'][gender] += 1
            city_counts['single'][gender] += len(parsed['cities']) == 1
            city_counts['title'][gender] += next(pattern for name, pattern in CITY_RES if name == city).search(title) is not None
            city_counts['specific'][gender] += specific_patterns[city].search(text) is not None
            if bucket:
                city_counts['ages'][gender][bucket] += 1
            if month:
                monthly['cities'].setdefault(city, Counter())[gender] += 1
    pooled = sum(counts['posts'] for groups in strata.values() for counts in groups.values())
    weights = {bucket: sum(strata[gender][bucket]['posts'] for gender in coverage) / pooled if pooled else 0 for bucket in buckets}
    complete_strata = pooled > 0 and all(strata[gender][bucket]['posts'] for gender in coverage for bucket in buckets)
    def standardized(gender, counts):
        if not complete_strata:
            return None
        return 100 * sum(weights[bucket] * counts[bucket] / strata[gender][bucket]['posts'] for bucket in buckets)
    for gender, counts in coverage.items():
        counts['no_reason'] = counts['posts'] - counts['reason']
        counts['median_age'] = statistics.median(age_values[gender]) if age_values[gender] else None
        counts['mean_age'] = statistics.mean(age_values[gender]) if age_values[gender] else None
    sorted_months = sorted(months)
    full_months = sorted_months[1:-1]
    city_results = []
    for city, counts in cities.items():
        if not sum(counts['gender'].values()):
            continue
        rates = {gender: standardized(gender, counts['ages'][gender]) for gender in coverage}
        eligible = []
        men_rate = counts['gender']['M'] / coverage['M']['posts'] if coverage['M']['posts'] else 0
        women_rate = counts['gender']['F'] / coverage['F']['posts'] if coverage['F']['posts'] else 0
        for month in full_months:
            monthly = months[month]
            hits = monthly['cities'].get(city, Counter())
            if hits['M'] >= 20 and hits['F'] >= 5:
                relative = (hits['F'] / monthly['gender']['F']) / (hits['M'] / monthly['gender']['M'])
                eligible.append(relative)
        city_results.append({'city': city, **{field: dict(counts[field]) for field in ('gender', 'single', 'title', 'specific')},
            'age_standardized_rate': rates, 'relative_rate': women_rate / men_rate if men_rate else None,
            'monthly_checks': {'eligible': len(eligible), 'same_direction': sum((relative >= 1) == (women_rate >= men_rate) for relative in eligible),
                               'relative_rate_min': min(eligible) if eligible else None, 'relative_rate_max': max(eligible) if eligible else None}})
    return {'coverage': {gender: dict(counts) for gender, counts in coverage.items()},
        'age_buckets': {gender: {bucket: dict(counts) for bucket, counts in groups.items()} for gender, groups in strata.items()},
        'age_weights': weights,
        'age_standardized': {field: {gender: standardized(gender, {bucket: strata[gender][bucket][field] for bucket in buckets}) for gender in coverage}
                             for field in ['city', *MOTIFS]},
        'cities': sorted(city_results, key=lambda row: sum(row['gender'].values()), reverse=True),
        'months': [{'month': month, 'full_month': month in full_months, 'gender': dict(months[month]['gender']),
                    'coverage': {gender: dict(counts) for gender, counts in months[month]['coverage'].items()}} for month in sorted_months],
        'author_available_posts': authors_available,
        'method': {'age_adjustment': 'Pooled stated-age distribution across five age buckets; only available when both groups have every bucket.',
                   'monthly_checks': 'Boundary months excluded; city direction checked only with at least 20 male and 5 female posts per month.',
                   'specific_aliases': 'Excludes aliases of three characters or fewer. Longer aliases can still be ambiguous.',
                   'interpretation': 'Exploratory post-level comparisons, not population estimates or independent-author significance tests.'}}

def aggregate(posts):

    gender_c, seeking_c, cities_c = Counter(), Counter(), Counter()
    ages    = {"M": Counter(), "F": Counter()}
    motives = {"M": Counter(), "F": Counter(), "all": Counter()}
    tagged = 0
    records = [(post, parse_post(post)) for post in posts]
    for p, r in records:
        g = r["gender"]
        if g:
            gender_c[g] += 1
            if r["age"]: ages[g][age_bucket(r["age"])] += 1
            for m in r["motives"]: motives[g][m] += 1
        for m in r["motives"]: motives["all"][m] += 1
        if r["seeking"]: seeking_c[r["seeking"]] += 1; tagged += 1
        for c in r["cities"]: cities_c[c] += 1

    timestamps = [int(p.get("created_utc")) for p in posts if isinstance(p, dict) and isinstance(p.get("created_utc"), (int, float))]
    if not timestamps:
        now = int(time.time())
        timestamps = [now]

    data = {
        "generated": time.strftime("%Y-%m-%d"),
        "period": {"from": time.strftime("%b %Y", time.gmtime(min(timestamps))),
                   "to":   time.strftime("%b %Y", time.gmtime(max(timestamps)))},
        "posts": len(posts), "gendered": sum(gender_c.values()), "seeking_tagged": tagged,
        "gender": dict(gender_c),
        "seeking": dict(seeking_c.most_common()),
        "ages": {g: dict(c) for g, c in ages.items()},
        "motives": {g: dict(c) for g, c in motives.items()},
        "cities": [{"city": n, "lat": CITIES[n][0], "lon": CITIES[n][1], "n": c}
                   for n, c in cities_c.most_common(15)],
        "analysis": analyze_posts(records),
    }
    return data

def rebuild():
    files = checkpoint_files()
    posts = [p for f in files for p in load_json_posts(f)]
    if not posts: sys.exit(f"no checkpoints in {RAW} or {LEGACY_RAW}")
    posts, dropped = dedupe_posts(posts)
    if dropped:
        print(f"deduped {dropped} repeated posts by id/fingerprint", flush=True)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(aggregate(posts), indent=1), encoding="utf-8")
    print(f"rebuilt {OUT} from {len(files)} pages ({len(posts)} posts)")

def demo():
    p = parse_post({"title": "34 [M4F] #Chicago - married, dead bedroom, looking for excitement",
                    "selftext": "feeling lonely and unappreciated"})
    assert p["gender"] == "M" and p["age"] == 34 and p["seeking"] == "M4F", p
    assert "dead_bedroom" in p["motives"] and "loneliness" in p["motives"], p
    assert "Chicago" in p["cities"], p
    p2 = parse_post({"title": "42F - he made me feel wanted again", "selftext": ""})
    assert p2["gender"] == "F" and p2["age"] == 42 and "desired" in p2["motives"], p2
    p3 = parse_post({"title": "Update: my wife found out", "selftext": "I (38M) messed up"})
    assert p3["gender"] == "M" and p3["age"] == 38, p3
    p4 = parse_post({"title": "F 45, thinking about taking the leap", "selftext": ""})
    assert p4["gender"] == "F" and p4["age"] == 45, p4
    p5 = parse_post({"title": "37 m4f #Missouri looking for a secret fwb", "selftext": ""})
    assert p5["gender"] == "M" and p5["seeking"] == "M4F" and p5["age"] == 37, p5
    city_posts = [{"title": aliases[0], "selftext": "", "created_utc": index + 1}
                  for index, (_, _, aliases) in enumerate(list(CITIES.values())[:16])]
    city_data = aggregate(city_posts)
    assert len(city_data["cities"]) == 15, city_data["cities"]
    fixtures = []
    for gender in ('M', 'F'):
        for age in (21, 29, 39, 49, 59):
            fixtures.append({'title': f'{age} [{gender}4M] Chicago lonely', 'created_utc': 1700000000})
    fixture_data = aggregate(fixtures)['analysis']
    assert fixture_data['coverage']['M']['age'] == 5, fixture_data
    assert fixture_data['coverage']['F']['no_reason'] == 0, fixture_data
    assert fixture_data['age_standardized']['city'] == {'M': 100.0, 'F': 100.0}, fixture_data
    assert fixture_data['cities'][0]['gender'] == {'M': 5, 'F': 5}, fixture_data
    assert aggregate([])['analysis']['age_standardized']['city'] == {'M': None, 'F': None}
    unequal_ages = []
    for gender in ('M', 'F'):
        for age in (21, 29, 39, 49, 59):
            total = 10 if (gender == 'M' and age == 21) or (gender == 'F' and age == 59) else 1
            for index in range(total):
                unequal_ages.append({'title': f'{age} [{gender}4M] ' + ('Chicago' if age == 59 else 'online')})
    adjusted_ages = aggregate(unequal_ages)['analysis']
    assert adjusted_ages['coverage']['M']['city'] != adjusted_ages['coverage']['F']['city'], adjusted_ages
    assert abs(adjusted_ages['age_standardized']['city']['M'] - adjusted_ages['age_standardized']['city']['F']) < 1e-10, adjusted_ages
    city_fixtures = aggregate([
        {'title': '29 [F4M] Chicago New York', 'selftext': '', 'created_utc': 1700000000},
        {'title': '39 [M4F] #NY', 'selftext': 'Chicago', 'created_utc': 1700000000},
        {'title': '49 [F4M] online', 'selftext': '', 'created_utc': 1700000000},
    ])['analysis']
    assert city_fixtures['coverage']['F']['multiple_cities'] == 1, city_fixtures
    assert city_fixtures['coverage']['F']['no_reason'] == 2, city_fixtures
    new_york = next(city for city in city_fixtures['cities'] if city['city'] == 'New York')
    assert new_york['specific'].get('M', 0) == 0 and new_york['specific']['F'] == 1, new_york
    assert new_york['title']['M'] == 1 and new_york['single'].get('M', 0) == 0, new_york
    month_fixtures = []
    for month in (1, 2, 3):
        timestamp = int(time.mktime((2026, month, 15, 12, 0, 0, 0, 0, -1)))
        for gender, total, city_posts in [('M', 40, 20), ('F', 10, 5)]:
            for index in range(total):
                month_fixtures.append({'title': f'39 [{gender}4M] ' + ('Chicago' if index < city_posts else 'online'), 'created_utc': timestamp})
    monthly_analysis = aggregate(month_fixtures)['analysis']
    assert [month['full_month'] for month in monthly_analysis['months']] == [False, True, False], monthly_analysis
    assert monthly_analysis['cities'][0]['monthly_checks']['eligible'] == 1, monthly_analysis
    assert monthly_analysis['cities'][0]['monthly_checks']['same_direction'] == 1, monthly_analysis
    print("demo ok")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    elif len(sys.argv) > 1 and sys.argv[1] == "rebuild":
        rebuild()  # aggregate data/raw checkpoints without fetching
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 365)  # days of history
