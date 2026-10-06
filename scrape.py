#!/usr/bin/env python3
"""Scrape r/Affairs submissions from the Arctic Shift archive and bake an
aggregated data/data.json for the Secret Encounters infographic.
(PullPush is edge-blocked/backend-down; Arctic Shift is the Pushshift-successor
that side-project-census already uses successfully.)

Usage:  python3 scrape.py [days]      # history window, default 365
        python3 scrape.py demo        # parser self-check
Stdlib only. Output is aggregates only — no usernames or post IDs are stored.
"""
import json, re, sys, time, urllib.parse, urllib.request, urllib.error
from collections import Counter
from pathlib import Path

API = "https://arctic-shift.photon-reddit.com/api/posts/search"
OUT = Path(__file__).resolve().parent / "data" / "data.json"
UA = {"User-Agent": "secret-encounters/1.0 (vintage data-viz research)"}

TAG = re.compile(r"\[\s*([mfta])\s*4\s*([mfta])\s*\]", re.I)   # [M4F] [F4M] [M4A]
PAIR = re.compile(r"\b(\d{2})\s*[-/–—]?\s*([MF])\b|\b([MF])\s*[-/–—]?\s*(\d{2})\b")

MOTIFS = {
    "dead_bedroom":   ["dead bedroom", "dead-bedroom", "sexless", "no sex", "no intimacy",
                       "lack of intimacy", "touch starved", "touch-starved"],
    "thrill_variety": ["thrill", "excitement", "exciting", "variety", "spark", "adrenaline",
                       "bored", "boredom", "adventure", "naughty", "forbidden", "rush"],
    "emotional_gap":  ["emotional connection", "emotionally", "unappreciated", "neglected",
                       "ignored", "taken for granted", "understood", "validation"],
    "loneliness":     ["lonely", "loneliness", "alone", "isolated", "no one to talk"],
    "desired":        ["feel wanted", "feel desired", "feeling wanted", "feeling desired",
                       "desired", "attractive", "attention", "craved", "adored"],
    "escape":         ["escape", "stress", "unhappy", "resentment", "checked out",
                       "roommate", "miserable", "trapped"],
}

CITIES = {  # name: (lat, lon, [aliases])
    "New York":      (40.71,  -74.00, ["new york", "nyc", "manhattan", "brooklyn"]),
    "Los Angeles":   (34.05, -118.24, ["los angeles", "la"]),
    "Chicago":       (41.88,  -87.63, ["chicago"]),
    "Toronto":       (43.65,  -79.38, ["toronto"]),
    "London":        (51.51,   -0.13, ["london"]),
    "Houston":       (29.76,  -95.37, ["houston"]),
    "Seattle":       (47.61, -122.33, ["seattle"]),
    "San Francisco": (37.77, -122.42, ["san francisco", "sf bay", "bay area"]),
    "Boston":        (42.36,  -71.06, ["boston"]),
    "Atlanta":       (33.75,  -84.39, ["atlanta"]),
    "Denver":        (39.74, -104.99, ["denver"]),
    "Austin":        (30.27,  -97.74, ["austin"]),
    "Portland":      (45.52, -122.68, ["portland"]),
    "Las Vegas":     (36.17, -115.14, ["las vegas", "vegas"]),
    "Miami":         (25.76,  -80.19, ["miami"]),
    "Philadelphia":  (39.95,  -75.17, ["philadelphia", "philly"]),
    "San Diego":     (32.72, -117.16, ["san diego"]),
    "Dallas":        (32.78,  -96.80, ["dallas"]),
    "Phoenix":       (33.45, -112.07, ["phoenix", "scottsdale"]),
    "Minneapolis":   (44.98,  -93.27, ["minneapolis", "twin cities"]),
    "Vancouver":     (49.28, -123.12, ["vancouver"]),
    "Montreal":      (45.50,  -73.57, ["montreal"]),
    "Sydney":        (-33.87, 151.21, ["sydney"]),
    "Melbourne":     (-37.81, 144.96, ["melbourne"]),
    "Dublin":        (53.35,   -6.26, ["dublin"]),
    "Manchester":    (53.48,   -2.24, ["manchester"]),
    "Amsterdam":     (52.37,    4.90, ["amsterdam"]),
    "Berlin":        (52.52,   13.40, ["berlin"]),
    "Paris":         (48.86,    2.35, ["paris"]),
    "Washington":    (38.91,  -77.04, ["washington dc", "dc area", "dmv"]),
    "Nashville":     (36.16,  -86.78, ["nashville"]),
    "New Orleans":   (29.95,  -90.07, ["new orleans"]),
    "Calgary":       (51.05, -114.07, ["calgary"]),
    "Columbus":      (39.96,  -83.00, ["columbus"]),
    "Charlotte":     (35.23,  -80.84, ["charlotte"]),
    "Kansas City":   (39.10,  -94.58, ["kansas city", "kc mo", "kcmo"]),
    "San Jose":      (37.34, -121.89, ["san jose"]),
    "Tampa":         (27.95,  -82.46, ["tampa"]),
    "Orlando":       (28.54,  -81.38, ["orlando"]),
    "Detroit":       (42.33,  -83.05, ["detroit"]),
    "Baltimore":     (39.29,  -76.61, ["baltimore"]),
    "Pittsburgh":    (40.44,  -80.00, ["pittsburgh"]),
    "St. Louis":     (38.63,  -90.20, ["st. louis", "st louis", "stl"]),
    "Sacramento":    (38.58, -121.49, ["sacramento"]),
    "Indianapolis":  (39.77,  -86.16, ["indianapolis", "indy"]),
}
CITY_RES = [(name, re.compile(r"\b(?:" + "|".join(map(re.escape, aliases)) + r")\b"))
            for name, (_, _, aliases) in CITIES.items()]

def age_bucket(a):
    return "18-24" if a < 25 else "25-34" if a < 35 else "35-44" if a < 45 else "45-54" if a < 55 else "55+"

def parse_post(p):
    text = f"{p.get('title') or ''}\n{p.get('selftext') or ''}"
    tag = TAG.search(text)
    gender = tag.group(1).upper() if tag else None
    tgender = tag.group(2).upper() if tag else None
    if gender not in ("M", "F"):  gender = None
    if tgender not in ("M", "F"): tgender = None
    pairs = [(int(m.group(1) or m.group(3)), (m.group(2) or m.group(4)).upper())
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
    sys.exit("Arctic Shift never served a page — rerun later.")

def main(days):
    posts = []
    now = int(time.time())
    cursor = now - days * 86400
    for i in range(1500):  # safety cap
        batch = fetch(cursor)
        posts.extend(batch)
        cursor = batch[-1].get("created_utc", now)
        print(f"page {i + 1}: {len(posts)} posts (up to {time.strftime('%Y-%m-%d', time.gmtime(cursor))})", flush=True)
        if cursor >= now - 1800 or len(batch) < 50: break  # caught up to ~now
        time.sleep(1.2)  # polite cadence
    if not posts:
        sys.exit("no posts collected")

    gender_c, seeking_c, cities_c = Counter(), Counter(), Counter()
    ages    = {"M": Counter(), "F": Counter()}
    motives = {"M": Counter(), "F": Counter(), "all": Counter()}
    tagged = 0
    for p in posts:
        r = parse_post(p)
        g = r["gender"]
        if g:
            gender_c[g] += 1
            if r["age"]: ages[g][age_bucket(r["age"])] += 1
            for m in r["motives"]: motives[g][m] += 1
        for m in r["motives"]: motives["all"][m] += 1
        if r["seeking"]: seeking_c[r["seeking"]] += 1; tagged += 1
        for c in r["cities"]: cities_c[c] += 1

    data = {
        "generated": time.strftime("%Y-%m-%d"),
        "period": {"from": time.strftime("%b %Y", time.gmtime(min(p["created_utc"] for p in posts))),
                   "to":   time.strftime("%b %Y", time.gmtime(max(p["created_utc"] for p in posts)))},
        "posts": len(posts), "gendered": sum(gender_c.values()), "seeking_tagged": tagged,
        "gender": dict(gender_c),
        "seeking": dict(seeking_c.most_common()),
        "ages": {g: dict(c) for g, c in ages.items()},
        "motives": {g: dict(c) for g, c in motives.items()},
        "cities": [{"city": n, "lat": CITIES[n][0], "lon": CITIES[n][1], "n": c}
                   for n, c in cities_c.most_common(12)],
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"wrote {OUT} — {len(posts)} posts, {data['gendered']} gendered, {tagged} seeking-tags")

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
    print("demo ok")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo()
    else:
        main(int(sys.argv[1]) if len(sys.argv) > 1 else 365)  # days of history
