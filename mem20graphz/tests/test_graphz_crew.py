import unittest
from mem20graphz import domain, ecosystem, MEMBERS, __version__

class TestCrew(unittest.TestCase):
    def test_members_preserved(self):
        self.assertEqual(len(MEMBERS), 7)
        self.assertIn("mem20capabilitygapmapperz", MEMBERS)
        self.assertTrue(__version__)

    def test_domain_summary(self):
        s = domain.crew_summary()
        self.assertEqual(s["members"], 7)
        self.assertEqual(s["crew"], "mem20graphz")

    def test_ecosystem_probe_real_integrations(self):
        p = ecosystem.probe()
        self.assertTrue(p["ok"])
        self.assertEqual(p["integration_health"]["ok"], 7)
        self.assertTrue(p["integrations"]["capability_gap"]["ok"])
        self.assertTrue(p["integrations"]["loyalty_graph"]["ok"])
        self.assertTrue(p["integrations"]["semantic_objects"]["ok"])
