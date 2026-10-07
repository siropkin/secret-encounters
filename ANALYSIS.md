# What We Can Learn From These Posts

Exploratory analysis of 125,668 archived r/Affairs posts, Oct 2025 to Oct 2026.
These findings describe detected patterns in posts, not people, residents, or the prevalence of affairs.

## Information In Posts

The denominator is all posts identified by the parser as men or women, separately: 106,230 and 8,212 posts. Another 11,226 posts are not identified as either group and are excluded from these comparisons.

| Detected information | Men's posts | Women's posts |
| --- | ---: | ---: |
| Age | 98.8% (104,913) | 98.0% (8,048) |
| City-group name or alias | 49.5% (52,629) | 36.0% (2,953) |
| Seeking-men-or-women tag | 97.2% (103,266) | 93.0% (7,634) |
| At least one reason keyword | 59.0% (62,717) | 48.5% (3,982) |
| No reason keyword detected | 41.0% (43,513) | 51.5% (4,230) |

Age detection is mostly a similarity, not a large gender difference. Median detected ages are 40 for men and 34 for women. These are ages extracted from posts, not verified ages of unique authors.

City detection has a larger gap: 13.6 percentage points. Giving both groups the same broad age distribution leaves a gap of 11.8 points (49.3% versus 37.5%). This makes age mix an incomplete explanation, but does not identify the actual cause.

Missing detection is not the same as withholding information. Subreddit formatting conventions, online-only requests, unrecognized cities, parser failures, wording, and other factors can all influence these rates. Reason keywords may express wishes rather than explain an affair, and multiple categories can match a post.

## Gender And City Together

Women account for 7.2% of all gender-identified posts, but only 5.3% of gender-identified posts with at least one detected city group. The city subset is therefore not a neutral sample of the entire dataset.

The city table includes groups with at least 500 gender-identified posts and 50 posts identified as women in the full dataset. This is a display threshold, not a statistical significance threshold. Counts can overlap between city groups.

| City group | Men's posts | Women's posts | Women's share |
| --- | ---: | ---: | ---: |
| Boston | 3,598 | 100 | 2.7% |
| New York | 8,409 | 529 | 5.9% |
| Los Angeles | 2,631 | 200 | 7.1% |
| San Francisco | 2,295 | 97 | 4.1% |
| Toronto | 1,982 | 75 | 3.6% |
| Vancouver | 493 | 66 | 11.8% |
| Charlotte | 443 | 59 | 11.8% |

The useful question is whether the mix of posts differs between city mention groups, not which city has more affairs or offers better odds of finding a partner.

### Sensitivity Checks

An F/M mention-rate ratio divides the share of women's posts mentioning a city by the share of men's posts mentioning it. It uses all gender-identified posts in each group as the raw denominator. A value of 1 means equal mention rates; it is not a women-to-men headcount ratio.

| City group | Raw F/M mention rate | Same age mix | Same direction / eligible months |
| --- | ---: | ---: | ---: |
| Boston | 0.36 | 0.34 | 8 / 8 |
| San Francisco | 0.55 | 0.57 | 9 / 9 |
| Toronto | 0.49 | 0.47 | 6 / 6 |
| Denver | 0.54 | 0.52 | 7 / 7 |
| Vancouver | 1.73 | 1.56 | 5 / 5 |
| Charlotte | 1.72 | 1.88 | 6 / 6 |

Monthly checks use each month's gender totals as denominators. The first and last months are excluded; a city-month qualifies only with at least 20 men's posts and 5 women's posts. These restrictions can exclude months in which a pattern is weaker. A repeated direction is exploratory evidence, not a significance test or a guarantee of stability. For example, Vancouver's eligible ratios range from 1.43 to 5.32, despite all being on the same side of 1.

As a research sensitivity check, there are 2,395 gender-identified posts matching multiple city groups. Removing them leaves 53,187 posts, with a women's share of 5.4%. This is a narrower subset, not necessarily a cleaner estimate of home locations. The page instead shows two independent top-15 city lists ranked by matched-post count, with percentages based on all posts in each gender group, and no additional comparison controls.

### Automated Alias Audit

Two additional checks count matches in titles only, and matches using aliases longer than three characters. No city definitions or original counts were changed.

| City group | All matched posts, M / F | Title matches, M / F | Longer-alias matches, M / F |
| --- | ---: | ---: | ---: |
| New York | 8,409 / 529 | 7,864 / 508 | 1,359 / 63 |
| Washington | 3,988 / 237 | 3,666 / 221 | 1,679 / 91 |
| Los Angeles | 2,631 / 200 | 2,293 / 170 | 1,583 / 105 |
| Chicago | 3,741 / 246 | 3,503 / 233 | 3,741 / 246 |

The large New York sensitivity is a warning: abbreviations such as NY can refer to a state, not New York City. LA, SF, GTA, NOVA, and other aliases can also be ambiguous or regional. Longer aliases still have namesakes and geographic ambiguities. Title-only matching can exclude valid body mentions and retain invalid title mentions.

This is an automated sensitivity audit, not a manually labeled accuracy evaluation. It does not establish that excluded matches were wrong, or that retained matches were correct. A stratified, privately reviewed sample is still needed before calling these precise city locations. No raw post text or identifiers are included in the published analysis output.

## The Gap Changes Over Time

Men's posts have a higher detected-city rate in all 11 interior months, November 2025 through September 2026. But the magnitude changes:

| Month | Men's city-detection rate | Women's city-detection rate | Gap |
| --- | ---: | ---: | ---: |
| November 2025 | 46.3% | 31.0% | 15.3 points |
| September 2026 | 49.8% | 45.6% | 4.2 points |

Monthly city-detection data is retained in the aggregate JSON, not charted on the page. Comparing these endpoints is descriptive, not a fitted trend or evidence of behavioral change. Possible explanations include changing poster composition, repeat campaigns, wording, and archive coverage. An interior calendar month is not a guarantee of complete collection.

## Gender Mix And Calendar Groups

The page now shows two aligned monthly activity charts: average men's and women's posts per calendar day. Each uses a separate labeled vertical scale that does not start at zero, so compare the timing of changes, not line heights or apparent amplitudes. Both groups' highest daily posting average occurs in January 2026: 309.0 men's posts and 28.2 women's posts per day.

As a research observation, across the 11 interior months men's share ranges from 91.6% to 93.8% and women's share from 6.2% to 8.4%. Women's share is 7.7% in November 2025 (726 posts) and 7.2% in September 2026 (689 posts), with no steady increase. A share can rise because one group's count increases or the other group's count decreases. Shares are not the metric used in the activity charts.

Calendar comparisons divide post counts by the actual calendar days in the included months. The page's seasonal table contains only Season, Men / day, and Women / day; the additional share below is retained for research. Both groups posted more per day in winter than summer in this snapshot, not evidence of a recurring seasonal effect.

| Calendar group | Included months | Days | Men's posts / day | Women's posts / day | Women's share |
| --- | --- | ---: | ---: | ---: | ---: |
| Winter | Dec 2025-Feb 2026 | 90 | 301.8 | 24.7 | 7.6% |
| Spring | Mar-May 2026 | 92 | 292.2 | 21.8 | 6.9% |
| Summer | Jun-Aug 2026 | 92 | 279.5 | 20.1 | 6.7% |
| Autumn, incomplete | Nov 2025 and Sep 2026 | 60 | 291.8 | 23.6 | 7.5% |

These are northern-calendar labels, not local seasons for every poster. Autumn combines noncontiguous months from two different years and excludes October. One annual cycle cannot establish recurring seasonality. Normalizing by calendar days does not correct missing archive coverage or repeated authors.

An exploratory Pearson correlation between men's and women's monthly daily posting averages is 0.745 across the 11 interior months. Volumes tend to move together in this snapshot, but this is not a significance or causality claim. Shared audience changes, archive coverage, repeated posting, and time dependence can contribute. This remains a research observation, not a headline chart.

## Reasons With The Same Age Mix

These research-only observed and age-adjusted comparisons use posts with a stated age: 104,913 men's posts and 8,048 women's posts. Differences arise from weighting, not from changing the sample. The age-adjusted chart has been removed from the page; its calculations remain in the aggregate analysis data.

Within each of five age buckets, we calculate the reason-match rate for each gender. We then apply the same pooled stated-age weights to both groups: 2.32%, 24.37%, 47.27%, 21.59%, and 4.44% for ages 18-24, 25-34, 35-44, 45-54, and 55+, respectively. The pooled distribution is male-heavy; it is an internal reference, not a population standard.

| Keyword category | Men's adjusted rate | Women's adjusted rate |
| --- | ---: | ---: |
| Excitement and variety | 32.4% | 22.3% |
| Feeling desired | 21.6% | 22.9% |
| Lack of closeness | 12.0% | 16.7% |
| Lack of sex | 9.9% | 6.6% |
| Escape | 12.9% | 6.6% |
| Loneliness | 5.8% | 6.0% |

These are broad keyword classifications, not validated psychological measures. For example, a request for an emotional connection need not demonstrate a lack of closeness in a relationship. Age adjustment does not account for city, language, audience selection, repeat authors, or differences within age buckets. Percentages can overlap and need not total 100%.

## What We Cannot Establish

- The checkpoint records contain timestamps, IDs, titles, and text, but no usable author information. Duplicate post IDs are removed; repeat authors are not.
- We cannot infer how common affairs are, how men or women generally approach fidelity, or where posters live.
- Gender, age, city, and reason are parser outputs, not verified attributes. The parser primarily recognizes M/F formats; unrecognized and other formats are not represented as equivalent groups here.
- No independent-author confidence intervals, significance claims, or corrections for multiple exploratory comparisons are provided.
- We have not normalized against Reddit demographics or city populations. That would require a suitable reference population and a defensible sampling model.

## Reproduce

Run `python3 scrape.py demo` for fixture checks, then `python3 scrape.py rebuild` to regenerate the aggregate JSON from local checkpoints without fetching new data. The new `analysis` object contains coverage, age strata and weights, all city-group cross-tabs, sensitivity counts, monthly coverage, and the method definitions. The original chart totals are preserved.

The strongest defensible summary is: **age is present in nearly all gender-identified posts, while detected city mentions and the gender mix of city groups differ; those differences vary over time and are sensitive to how locations are matched.**