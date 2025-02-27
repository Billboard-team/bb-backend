from django.test import TestCase
from websrv.models import Bill
from websrv.utils.llm import Summarizer

# Create your tests here.
class SummarizerTestCase(TestCase):
    def setUp(self) -> None:
        self.summarizer = Summarizer()

    def test_clean_html(self):
        self.assertTrue(True)
