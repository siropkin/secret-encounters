#!/usr/bin/env python3
"""Triple-check gender classification over the full checkpoint corpus.
Independent re-derivation + false-positive traps + distribution stability."""
import json, re, glob
from pathlib import Path
from collections import Counter
import scrape

RAW = scrape.RAW if scrape.RAW.exists() else Path(__file__).parent / 'data' / 'raw'
posts = [p for f in glob.glob(str(RAW / '*.json')) for p in json.load(open(f))]
N = len(posts)
print(f"posts: {N:,}\n")

def text_of(p): return f"{p.get('title') or ''}\n{p.get('selftext') or ''}"

TAG = scrape.TAG
TAG_BARE = scrape.TAG_BARE
PAIR = scrape.PAIR
# independent extractor: first-person contexts only, different strategy
FP = re.compile(r"(?:i(?:'m| am|’m)?\s*(?:a\s*)?\(?(18|[2-6]\d|7[0-5])\s*([MF])\b|\((18|[2-6]\d|7[0-5])([MF])\)\s*(?:here|,|\.|-|—|$))", re.I)
SPOUSE = re.compile(r"(husband|wife|spouse|partner|girlfriend|boyfriend|\bgf\b|\bbf\b|\bap\b)[^.]{0,40}?$", re.I)

cur = Counter(); ind = Counter(); disagree = []
fp45 = m4motor = f22 = bmw = spouse_first = lowercase_only = covid_age = 0
fp45_ex, spouse_ex, lower_ex = [], [], []

for p in posts:
    text = text_of(p); title = p.get('title') or ''
    r = scrape.parse_post(p)
    g_cur = r['gender'] or 'NONE'
    cur[g_cur] += 1

    # independent derivation
    tag = TAG.search(text) or TAG_BARE.search(title)
    g_ind = None
    if tag and tag.group(1).upper() in 'MF': g_ind = tag.group(1).upper()
    if g_ind is None:
        m = FP.search(text)
        if m: g_ind = (m.group(2) or m.group(4)).upper()
    ind[g_ind or 'NONE'] += 1
    if g_cur != g_ind and g_ind != 'NONE' and g_cur != 'NONE' and len(disagree) < 6:
        disagree.append((g_cur, g_ind, title[:80]))

    low = text.lower()
    if re.search(r'\bf45\b', low):
        fp45 += 1
        if r['gender'] == 'F' and r['age'] == 45 and len(fp45_ex) < 3: fp45_ex.append(title[:90])
    if TAG_BARE.search(title) and 'motorway' in low: m4motor += 1
    if re.search(r'\bf[- ]?22\b', low): f22 += 1
    if 'bmw' in low and re.search(r'\bm\s?4\b', low): bmw += 1
    first = PAIR.search(text)
    if first and SPOUSE.search(text[:first.start()]):
        spouse_first += 1
        if len(spouse_ex) < 3: spouse_ex.append(title[:90])
    if r['gender'] is None:
        m = re.search(r"\b(1[89]|[2-6]\d|7[0-5])\s*([mf])\b", text)
        if m and not m.group(2).isupper():
            lowercase_only += 1
            if len(lower_ex) < 3: lower_ex.append((title or '')[:90])
    if r['age'] in (19, 20) and 'covid' in low: covid_age += 1

print("== current parser ==", dict(cur))
print("== independent    ==", dict(ind))
print(f"\ndisagreements (both assigned, different): {len(disagree)} examples shown of sample")
for c, i, t in disagree: print(f"  cur={c} ind={i} :: {t}")

print("\n== false-positive traps (full corpus) ==")
print(f"  'f45' (gym chain) mentions: {fp45}", fp45_ex or '')
print(f"  M4x tag + 'motorway' in text: {m4motor}")
print(f"  'f-22/f 22' (jet) mentions: {f22}")
print(f"  'bmw' + 'm4' mentions: {bmw}")
print(f"  spouse-first age-pair (husband (35M)…): {spouse_first}", spouse_ex or '')
print(f"  genderless but lowercase '37m/28f' present: {lowercase_only}", lower_ex or '')
print(f"  age 19/20 + 'covid' in text: {covid_age}")

# distribution stability: strict (tags only) vs current
strictM = strictF = 0
for p in posts:
    tag = TAG.search(text_of(p)) or TAG_BARE.search(p.get('title') or '')
    if tag and tag.group(1).upper() == 'M': strictM += 1
    if tag and tag.group(1).upper() == 'F': strictF += 1
print(f"\n== stability ==")
print(f"  current M share of gendered: {100*cur['M']/(cur['M']+cur['F']):.1f}%")
print(f"  strict tags-only M share:    {100*strictM/(strictM+strictF):.1f}%  (n={strictM+strictF:,})")
