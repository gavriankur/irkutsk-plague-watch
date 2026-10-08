import sys
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_sources import incident_text, short_quote

class SourceIsolation(unittest.TestCase):
    def test_unrelated_counts_are_excluded(self):
        soup=BeautifulSoup('<main><p>A laboratory worker in Irkutsk died of pneumonia suspected to be plague.</p><p>About 200 contacts were quarantined.</p><p>Now to Ebola.</p><p>8665 confirmed cases of Ebola in Congo.</p></main>', 'html.parser')
        text=incident_text(soup)
        self.assertIn('200 contacts',text)
        self.assertNotIn('8665',text)
    def test_generic_plague_is_not_russian_incident(self):
        self.assertEqual('',incident_text(BeautifulSoup('<main><p>Plague occurs in Madagascar.</p><p>Russia recommends routine vaccines.</p></main>','html.parser')))
    def test_absence_is_not_zero(self):
        self.assertEqual('',incident_text(BeautifulSoup('<main><p>Russia traveler advice.</p></main>','html.parser')))
    def test_quote_is_bounded(self):
        self.assertLessEqual(len(short_quote('Irkutsk plague '+'word '*100).replace(' …','').split()),25)

if __name__ == '__main__': unittest.main()

class ReviewedCounts(unittest.TestCase):
    def test_updater_has_no_write_path_to_reviewed_counts(self):
        import tempfile
        from unittest.mock import patch
        import update_sources
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'data').mkdir()
            reviewed=root/'data/reviewed.json'
            original='{"confirmed_plague_cases": null, "contacts": 200}'
            reviewed.write_text(original)
            page=BeautifulSoup('<html><title>Official incident report</title><h1>Irkutsk</h1><main><p>Irkutsk pneumonia suspected to be plague.</p><p>200 contacts quarantined.</p></main></html>','html.parser')
            with patch.object(update_sources,'ROOT',root), patch.object(update_sources,'fetch',return_value=page), patch.object(update_sources,'INDEXES',[]):
                update_sources.main()
            self.assertEqual(original,reviewed.read_text())
