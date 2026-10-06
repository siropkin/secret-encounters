#!/usr/bin/env python3
"""Audit scrape.py's classification against raw checkpoints.
Usage: python3 validate.py [sample-size]"""
import random, re, sys
from collections import Counter
import scrape

N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
random.seed(7)

files = scrape.checkpoint_files()
if not files:
    sys.exit(f"no checkpoints found in {scrape.RAW} or {scrape.LEGACY_RAW}")
posts = [p for f in files for p in scrape.load_json_posts(f)]
print(f"total checkpointed posts: {len(posts):,}\n")

parsed = [(p, scrape.parse_post(p)) for p in posts]
R = [r for _, r in parsed]

# ---- coverage ----
def pct(x, total): return f"{100 * x / total:.0f}%"
print("== coverage ==")
print(f"gender: {pct(sum(1 for r in R if r['gender']), len(R))}   age: {pct(sum(1 for r in R if r['age']), len(R))}"
      f"   seeking: {pct(sum(1 for r in R if r['seeking']), len(R))}   city: {pct(sum(1 for r in R if r['cities']), len(R))}"
      f"   any motive: {pct(sum(1 for r in R if r['motives']), len(R))}")

# ---- gender: tag vs age-pair consistency ----
print("\n== gender cross-check (tag gender vs age-pair gender) ==")
PAIR = scrape.PAIR
TAGS = re.compile(r"\[\s*([mfta])\s*4\s*([mfta])\s*\]", re.I)
BARE = re.compile(r"\b([mfta])\s*4\s*([mfta])\b", re.I)
disagree = 0
for p, r in random.sample(parsed, min(N, len(parsed))):
    tag = TAGS.search(f"{p.get('title','')}\n{p.get('selftext','')}") or BARE.search(p.get('title') or '')
    if not tag: continue
    tg = tag.group(1).upper()
    pairs = [(int(m.group(1) or m.group(4)), (m.group(2) or m.group(3)).upper()) for m in PAIR.finditer(f"{p.get('title','')}\n{p.get('selftext','')}")]
    pairs = [(a, g) for a, g in pairs if 18 <= a <= 75]
    if pairs and pairs[0][1] in 'MF' and tg in 'MF' and pairs[0][1] != tg:
        disagree += 1
        if disagree <= 3: print("  MISMATCH:", (p.get('title') or '')[:90])
print(f"  disagreements: {disagree}/{N} sampled tagged posts")

# ---- missed gender: phrasing we don't capture ----
print("\n== gender patterns we miss (sample of genderless posts) ==")
probes = {"i'm a NN yo man/woman": re.compile(r"\bi'?m (?:a )?(\d{2})[ -]?(?:yo|yr|year[s ]?old)? ?(man|woman|guy|male|female)\b", re.I),
          "my (NNM/F) husband/wife": re.compile(r"my \((\d{2})([MF])\) (?:hus|wife|so|partner)", re.I),
          "NN year old man/woman": re.compile(r"(\d{2})[ -]year[ -]old (man|woman)", re.I)}
miss = [p for p, r in parsed if not r['gender']]
print(f"genderless posts: {len(miss):,} ({pct(len(miss), len(R))})")
for name, rx in probes.items():
    hits = [p for p in miss if rx.search(f"{p.get('title','')}\n{p.get('selftext','')}")]
    print(f"  recoverable via '{name}': {len(hits):,}")
    for p in hits[:2]: print("    e.g.:", (p.get('title') or '')[:90])

# ---- motives: snippet eyeball + known FP traps ----
print("\n== motive spot-check (random matched snippets) ==")
for key, kws in scrape.MOTIFS.items():
    bucket = [p for p, r in parsed if key in r['motives']]
    print(f"  {key}: {len(bucket):,} posts")
    for p in random.sample(bucket, min(2, len(bucket))):
        low = f"{p.get('title','')} {p.get('selftext','')}".lower()
        kw = next(k for k in kws if k in low)
        i = low.find(kw)
        print(f"    [{kw}] …{low[max(0,i-35):i+len(kw)+35].strip()}…")
print("\n  'alone' contexts (FP check):")
alone = [p for p, r in parsed if 'loneliness' in r['motives'] and 'alone' in f"{p.get('title','')} {p.get('selftext','')}".lower()]
fp = [p for p in alone if re.search(r"(leave|let|left|leaves|leaving|alone time|time alone|be alone)\S* ?\S* alone", f"{p.get('title','')} {p.get('selftext','')}".lower())]
print(f"  posts matching 'alone': {len(alone):,}; 'leave/let ... alone'-ish among them: {len(fp):,}")

# ---- cities: name-collision audit ----
print("\n== city audit (#tag-backed vs free-text, name-collision risk) ==")
hashtag = re.compile(r"#([A-Za-z][A-Za-z .']+)")
city_hits = Counter(); city_tagged = Counter(); examples = {}
for p in posts:
    low = f"{p.get('title','')} {p.get('selftext','')}".lower()
    tags = ' '.join(hashtag.findall(p.get('title') or '')).lower()
    for name, rx in scrape.CITY_RES:
        if rx.search(low):
            city_hits[name] += 1
            if any(rx.search(a) for a in tags.split()): pass
            if rx.search(tags): city_tagged[name] += 1
            examples.setdefault(name, (p.get('title') or '')[:80])
for name, n in city_hits.most_common(15):
    print(f"  {name:14s} {n:5,}  (#-tagged: {city_tagged[name]:5,})  e.g. {examples[name]}")
print("\n  risky-name cities (all their matches):")
for risky in ("Austin", "Charlotte", "Dallas", "Paris", "Washington"):
    hits = [p for p in posts if dict(scrape.CITY_RES)[risky].search(f"{p.get('title','')} {p.get('selftext','')}".lower())]
    taggy = [p for p in hits if dict(scrape.CITY_RES)[risky].search(' '.join(hashtag.findall(p.get('title') or '')).lower())]
    print(f"  {risky:10s} total {len(hits):4,}  #-tagged {len(taggy):4,}")
    for p in random.sample(hits, min(2, len(hits))): print("      e.g.:", (p.get('title') or '')[:90])
