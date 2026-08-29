
import unittest
from location_service import Location
from company_search import Company
from run_job_application import filter_companies_by_keywords

class TestJobApplication(unittest.TestCase):

    def setUp(self):
        self.dummy_location = Location(0, 0, "Test Address")
        self.tech_keywords = [
            'software', 'technology', 'tech', 'systems', 'solutions', 'labs',
            'infotech', 'digital', 'consulting', 'services', 'data', 'cloud',
            'security', 'cyber', 'network', 'electronics', 'communications',
            'global', 'technologies', 'innovation', 'engineering', 'saas', 'mnc'
        ]

    def test_filter_tech_companies(self):
        companies = [
            Company("Tech Corp", self.dummy_location, "Software Development", "Addr1"),
            Company("Bakery", self.dummy_location, "Food", "Addr2"),
            Company("CyberSec Ltd", self.dummy_location, "Security", "Addr3"),
            Company("Construction Co", self.dummy_location, "Construction", "Addr4"),
            Company("Data Systems", self.dummy_location, "IT Services", "Addr5"),
        ]

        filtered = filter_companies_by_keywords(companies, self.tech_keywords)

        # Expected: Tech Corp, CyberSec Ltd, Data Systems
        self.assertEqual(len(filtered), 3)
        self.assertEqual(filtered[0].name, "Tech Corp")
        self.assertEqual(filtered[1].name, "CyberSec Ltd")
        self.assertEqual(filtered[2].name, "Data Systems")

    def test_filter_no_match(self):
        companies = [
            Company("Bakery", self.dummy_location, "Food", "Addr1"),
            Company("Farm", self.dummy_location, "Agriculture", "Addr2"),
        ]
        filtered = filter_companies_by_keywords(companies, self.tech_keywords)
        self.assertEqual(len(filtered), 0)

    def test_filter_case_insensitive(self):
        companies = [
            Company("tech startup", self.dummy_location, "Business", "Addr1"),
            Company("Old School", self.dummy_location, "SOFTWARE", "Addr2"),
        ]
        filtered = filter_companies_by_keywords(companies, self.tech_keywords)
        self.assertEqual(len(filtered), 2)

if __name__ == '__main__':
    unittest.main()
