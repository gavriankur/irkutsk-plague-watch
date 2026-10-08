# Irkutsk Plague Watch

A sourced world map of the reported October 2026 Irkutsk pneumonia incident, with pneumonic plague explicitly marked as unconfirmed.

## Data snapshot

Checked 8 October 2026. Latest cited WHO statement: 7 October 2026.

- One reported fatal pneumonia incident. Pneumonic plague has not been publicly verified in the sources reviewed.
- Russia reported no recent plague cases in Irkutsk to WHO.
- A second pneumonia report remained unverified in the cited WHO statement.
- Approximately 200 quarantined contacts are **not case counts**.

This is a static snapshot, not a live surveillance feed. Country shading identifies Russia, not disease density. The location marker is approximate.

## Sources

- [WHO statement, 7 October 2026](https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing---7-october-2026)
- [ECDC statement, 6 October 2026](https://www.ecdc.europa.eu/en/news-events/ecdc-closely-monitoring-situation-following-case-pneumonia-unknown-origin-russia)
- Map geometry: @d3-maps/atlas 1.0.0, world countries 110m (Natural Earth). Approximate Irkutsk coordinates: OpenStreetMap via Mapcarta.

## GitHub Pages

Serve the root of the `main` branch. The site is a standalone static `index.html`; no build is required. D3 and TopoJSON load from jsDelivr.
