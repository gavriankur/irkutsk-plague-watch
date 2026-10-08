"""Collect official incident reports; never infer medical case counts from prose."""
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
WHO = 'https://www.who.int/news-room/speeches/item/who-director-general-s-opening-remarks-at-the-media-briefing---7-october-2026'
CDC = 'https://wwwnc.cdc.gov/travel/destinations/traveler/none/russia'
INDEXES = ['https://www.who.int/news-room/speeches', 'https://www.who.int/news', 'https://www.who.int/emergencies/disease-outbreak-news', 'https://wwwnc.cdc.gov/travel/notices']
HOSTS = {'www.who.int', 'wwwnc.cdc.gov', 'www.cdc.gov'}
PLACE = re.compile(r'irkutsk|shelekhov|russi(?:a|an)', re.I)
TOPIC = re.compile(r'\bplague\b|pneumonia', re.I)

def fetch(url):
    if urlparse(url).hostname not in HOSTS or not url.startswith('https://'):
        raise ValueError('Non-official source URL')
    error = None
    for attempt in range(3):
        try:
            req = Request(url, headers={'User-Agent': 'IrkutskPlagueWatch/1.0 (official-source monitoring; daily)'})
            with urlopen(req, timeout=25) as res:
                if urlparse(res.url).hostname not in HOSTS:
                    raise ValueError('Non-official redirect')
                raw = res.read(4_000_001)
            if len(raw) > 4_000_000:
                raise ValueError('Oversized response')
            soup = BeautifulSoup(raw, 'html.parser')
            if not soup.title or len(soup.get_text(' ', strip=True)) < 300 or any(t in soup.title.get_text().lower() for t in ('access denied', 'just a moment')):
                raise ValueError('Missing page heading; possible error or blocked response')
            return soup
        except Exception as exc:
            error = exc
            if attempt < 2:
                time.sleep(attempt + 1)
    raise error

def incident_text(soup):
    for node in soup(['script', 'style', 'nav', 'footer', 'header']):
        node.decompose()
    scope = soup.find('main') or soup
    paragraphs = [' '.join(p.get_text(' ', strip=True).split()) for p in scope.find_all('p')]
    # Only nearby incident paragraphs; never entire pages containing unrelated outbreaks.
    selected = set()
    for i, p in enumerate(paragraphs):
        if PLACE.search(p) and TOPIC.search(p):
            selected.add(i)
            for j in (i-1, i+1):
                if 0 <= j < len(paragraphs) and re.search(r'plague|pneumonia|contacts|laboratory tests|verification', paragraphs[j], re.I):
                    selected.add(j)
    return '\n'.join(paragraphs[i] for i in sorted(selected))

def short_quote(text):
    # At most 25 quoted words per source, with no automated interpretation.
    line = next((p for p in text.splitlines() if PLACE.search(p) and TOPIC.search(p)), '')
    words = line.split()
    return ' '.join(words[:25]) + (' …' if len(words) > 25 else '')

def main():
    path = ROOT / 'data/sources.json'
    old = json.loads(path.read_text()) if path.exists() else {'reports': [], 'checks': []}
    reports = {r['url']: r for r in old['reports']}
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    checks, candidates = [], {WHO, CDC, *reports}
    # Discover recent WHO briefing statements even when their titles do not name plague.
    for index in INDEXES:
        try:
            soup = fetch(index)
            found = []
            for a in soup.select('a[href]'):
                url = urljoin(index, a['href']).split('#')[0]
                title = a.get_text(' ', strip=True)
                if urlparse(url).hostname not in HOSTS:
                    continue
                if PLACE.search(title + ' ' + url) and TOPIC.search(title + ' ' + url):
                    if '/item/' in url or '/notices/' in url:
                        found.append(url)
                elif '/speeches/item/' in url and ('2026' in url or '2027' in url):
                    found.append(url)
            # WHO listings use their own public CMS API rather than HTML article links.
            if 'who.int' in index:
                api_paths = re.findall(r'[\"\'](/api/(?:hubs|news)/[^\"\']+)[\"\']', str(soup))
                for api_path in dict.fromkeys(api_paths):
                    if not any(x in api_path.lower() for x in ('speeches', 'diseaseoutbreak', 'newsitems')):
                        continue
                    if '/speeches' in index and 'speeches' not in api_path:
                        continue
                    if 'disease-outbreak-news' in index and 'diseaseoutbreak' not in api_path.lower():
                        continue
                    api_url = quote(urljoin(index, html.unescape(api_path)), safe='/:?&=$,()%')
                    api_url = re.sub(r'([?&])\$top=\d+', r'\1$top=25', api_url)
                    if '$top=' not in api_url:
                        api_url += '&$top=25'
                    with urlopen(Request(api_url, headers={'User-Agent': 'IrkutskPlagueWatch/1.0'}), timeout=25) as response:
                        if urlparse(response.url).hostname not in HOSTS:
                            raise ValueError('Non-official API redirect')
                        listing = json.loads(response.read(4_000_000))
                    for item in listing.get('value', []):
                        title = item.get('Title', '')
                        relative = item.get('ItemDefaultUrl', '')
                        if not relative:
                            continue
                        if relative.startswith('/news-room/') or relative.startswith('/emergencies/'):
                            article_url = urljoin(index, relative)
                        else:
                            base = 'https://www.who.int/news-room/speeches/item/' if 'speeches' in api_path else ('https://www.who.int/emergencies/disease-outbreak-news/item/' if 'diseaseoutbreak' in api_path.lower() else 'https://www.who.int/news/item/')
                            article_url = base + relative.lstrip('/')
                        if PLACE.search(title) and TOPIC.search(title):
                            found.append(article_url)
                        elif 'speeches' in api_path and ('media briefing' in title.lower()):
                            found.append(article_url)
            candidates.update(dict.fromkeys(found[:12]))
            checks.append({'url': index, 'ok': True, 'checked_at': now})
        except Exception as exc:
            checks.append({'url': index, 'ok': False, 'error': str(exc)[:180], 'checked_at': now})
    for url in sorted(candidates):
        try:
            soup = fetch(url)
            title = (soup.h1 or soup.title).get_text(' ', strip=True)
            text = incident_text(soup)
            digest = hashlib.sha256(text.encode()).hexdigest()
            previous = reports.get(url)
            if text or previous:
                changed = previous is None or previous['content_hash'] != digest
                reports[url] = {'url': url, 'agency': 'WHO' if 'who.int' in url else 'CDC', 'title': title,
                    'quote': short_quote(text), 'content_hash': digest, 'checked_at': now,
                    'changed_at': now if changed else previous['changed_at'], 'available': True,
                    'relevant_notice_present': bool(text)}
            checks.append({'url': url, 'ok': True, 'checked_at': now})
        except Exception as exc:
            if url in reports:
                reports[url]['available'] = False
            checks.append({'url': url, 'ok': False, 'error': str(exc)[:180], 'checked_at': now})
    result = {'checked_at': now, 'reports': sorted(reports.values(), key=lambda r: r['changed_at'], reverse=True), 'checks': checks}
    path.write_text(json.dumps(result, indent=2) + '\n')
    failures = sum(not c['ok'] for c in checks)
    print(f'Checked {len(checks)} sources; {len(reports)} incident reports; {failures} fetch failures.')
    # Never overwrite reviewed case counts here. A disappeared notice is not evidence of zero cases.
    if not reports:
        raise SystemExit('No usable incident reports; refusing an empty publication')

if __name__ == '__main__':
    main()
