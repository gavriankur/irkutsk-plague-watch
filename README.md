# Irkutsk Plague Watch

[Live map](https://gavriankur.github.io/irkutsk-plague-watch/) · [Daily checks and deployments](https://github.com/gavriankur/irkutsk-plague-watch/actions/workflows/update-publish.yml)

## What updates automatically

GitHub Actions checks WHO and CDC every day at **03:17 UTC / 08:47 India time**, and can also be run manually. Scheduled runs may start later when GitHub is busy.

It monitors the WHO incident statement and CDC Russia traveler notice, discovers links from WHO news, disease-outbreak and briefing listings plus CDC travel notices, and publishes updated source excerpts, timestamps, availability and review status to GitHub Pages. This is bounded source monitoring, not comprehensive global case surveillance. It can miss reports outside those listings or content rendered only with JavaScript.

The map's numeric counts are a separately reviewed snapshot, **not automatically inferred from prose**. Newly discovered or changed official wording flags the map as needing review. Quarantined contacts, suspected cases, deaths from unidentified pneumonia and laboratory-confirmed plague must not be pooled. There is no AI extraction, fabricated data, or API-key requirement.

## Review a new report

1. Open the official reports linked on the site and inspect `data/sources.json`. Verify relevance, date, case definition and location.
2. Update `data/reviewed.json` with sourced counts, review date and accurate status. `confirmed_plague_cases: null` means not established, not zero. Record approved report hashes only for sources actually reviewed.
3. Commit the reviewed change to `main`. The workflow fetches sources, tests, builds and publishes automatically.

The initial reviewed incident information comes from [WHO, 7 October 2026](https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing---7-october-2026) and [CDC Russia traveler notice](https://wwwnc.cdc.gov/travel/destinations/traveler/none/russia), checked 8 October 2026. One fatal pneumonia incident is reported, while plague remains unconfirmed in those reviewed sources. About 200 contacts are not cases.

## Reliability

Fetch failures retain previous reports and display a warning. Missing incident wording never resets counts to zero. No usable reports causes the build to fail rather than publish an empty snapshot. Each report has its own last-successful-retrieval timestamp. Source changes are detected from relevant incident paragraphs, not navigation or unrelated disease counts. Snapshots remain in Git history. A recent check timestamp does not imply numeric counts were reviewed recently.

GitHub scheduled workflows in public repositories may be disabled after 60 days without repository activity. Monitor the Actions page for paused schedules or failures.

## Development

Python 3.12; `pip install -r requirements.txt`.

Run `python -m unittest discover -s tests -v`, `python scripts/update_sources.py`, then `python scripts/build.py`. Public files are generated in `site/`. Only `site/` is deployed; scripts and tests are not public website assets.

Map geometry: @d3-maps/atlas 1.0.0 / Natural Earth 110m. Approximate city coordinates from OpenStreetMap via Mapcarta. D3 7.9.0 and TopoJSON Client 3.1.0 are loaded from jsDelivr. Map country shading indicates Russia, not case density or international spread.
