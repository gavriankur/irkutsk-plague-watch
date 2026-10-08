"""Build the public snapshot from monitored sources and separately reviewed counts."""
import html
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def build():
    data = json.loads((ROOT / 'data/sources.json').read_text())
    reviewed = json.loads((ROOT / 'data/reviewed.json').read_text())
    def esc(value):
        return html.escape(str(value), quote=True)
    pending = any(reviewed['approved_source_hashes'].get(r['url']) != r['content_hash'] for r in data['reports'])
    failed = [c for c in data['checks'] if not c['ok']]
    panel = '<section class="sources"><h2>Official source monitor</h2>'
    panel += '<p>Daily WHO / CDC checks · Last run: ' + esc(data['checked_at']) + '</p>'
    panel += '<p class="notice">' + ('Official source changes need case-count review. Map counts remain the last reviewed snapshot.' if pending else 'No unreviewed source changes detected. Map counts are the last reviewed snapshot.') + '</p>'
    if failed:
        panel += '<p class="notice">Some source checks failed (' + str(len(failed)) + '). Previously retrieved information is retained; this check does not establish that no new cases exist.</p>'
    for r in data['reports']:
        panel += '<article><a target="_blank" rel="noopener" href="' + esc(r['url']) + '">' + esc(r['agency'] + ' · ' + r['title']) + '</a>'
        panel += '<p>' + (esc(r['quote']) if r['quote'] else 'Incident wording no longer detected on this page. This does not establish zero cases.') + '</p>'
        panel += '<small>Last retrieved: ' + esc(r['checked_at']) + ' · Text last changed: ' + esc(r['changed_at']) + (' · Fetch failed on the latest run' if not r['available'] else '') + '</small></article>'
    panel += '<p><a href="https://github.com/gavriankur/irkutsk-plague-watch/actions/workflows/update-publish.yml">Check history</a> · <a href="sources.json">Source-check data</a> · <a href="reviewed.json">Reviewed map data</a></p></section>'
    template = (ROOT / 'scripts/map-template.html').read_text()
    values = {'{{SOURCES}}':panel, '{{REVIEWED_DATE}}':esc(reviewed['reviewed_at']), '{{NOTE}}':esc(reviewed['note']), '{{STATUS}}':esc(reviewed['status']), '{{COUNT}}':str(reviewed['reported_fatal_pneumonia_incidents']), '{{LON}}':json.dumps(reviewed['longitude']), '{{LAT}}':json.dumps(reviewed['latitude'])}
    for key, value in values.items():
        template = template.replace(key, value)
    assert '{{' not in template, 'Unresolved template fields'
    site = ROOT / 'site'
    site.mkdir(exist_ok=True)
    (site / 'index.html').write_text(template)
    for name in ('sources.json','reviewed.json'):
        (site / name).write_bytes((ROOT / 'data' / name).read_bytes())
    (site / '.nojekyll').touch()
    print('Built site; review pending:', pending)

if __name__ == '__main__':
    build()
