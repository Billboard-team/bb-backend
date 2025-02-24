from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields import parse_date, parse_datetime
from dotenv import load_dotenv

import requests
import os

from websrv.models import Bill

load_dotenv()

congress_url = "https://api.congress.gov/v3/"

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
        req = requests.get(congress_url + "bill/", params=params)

        if options["verbose"]:
            self.stdout.write(req.text)

        if options["save"]:
            data = req.json()
            for bill_data in data["bills"]:
                action_date = parse_date(bill_data["latestAction"]["actionDate"])

                try:
                    b = Bill(
                            title=bill_data["title"],
                            actions=bill_data["latestAction"]["text"],
                            actions_date=action_date,
                            description="",
                            congress=bill_data["congress"],
                            bill_type=bill_data["type"],
                            bill_number=bill_data["number"],
                            url=bill_data["url"]
                        )
                    b.save()
                except Exception as e:
                    self.stdout.write(f"Error storing bill object: {e}")

            self.stdout.write("Saved %d bills to db" % len(data["bills"]))
