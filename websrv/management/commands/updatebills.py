from sys import stdout
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields import parse_date
from dotenv import load_dotenv

from urllib.parse import urlparse

import requests
import os

from websrv.models import Bill

load_dotenv()

test_url = "https://api.congress.gov/v3/bill/119/hres/148?format=json"

class Command(BaseCommand):
    help = "Fetch bills from Congress.gov API"

    def add_arguments(self, parser):
        parser.add_argument(
                "--verbose",
                action="store_true",
                help="Output data to stdout",
            )
        parser.add_argument(
                "--save", "-s",
                action="store_true",
                help="Storing data to the database",
            )

    def handle(self, *args, **options):
        congress_key = os.getenv("CONGRESS_API_KEY")
        if not congress_key:
            raise CommandError("Congress API key is not provived")

        params = {'api_key': congress_key}

        parsed = urlparse(test_url)
        parsed.path = parsed.path + "/text"

        print(parsed)

