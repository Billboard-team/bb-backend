from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields import parse_date

import requests
import os

from websrv.models import Bill

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
        parser.add_argument(
                "--number", "-n",
                type=int,
                default=20,
                help="limit of bills requested",
            )

    def handle(self, *args, **options):
        congress_key = os.getenv("CONGRESS_API_KEY")
        if not congress_key:
            raise CommandError("Congress API key is not provived")

        params = {'api_key': congress_key, 'limit': options['number']}
        req = requests.get(congress_url + "bill/", params=params)

        if options["verbose"]:
            self.stdout.write(req.text)

        if options["save"]:
            data = req.json()
            for bill_data in data["bills"]:
                action_date = parse_date(bill_data["latestAction"]["actionDate"])

                try:
                    Bill.objects.get_or_create(
                            title=bill_data["title"],
                            actions=bill_data["latestAction"]["text"],
                            actions_date=action_date,
                            description="",
                            congress=bill_data["congress"],
                            bill_type=bill_data["type"],
                            bill_number=bill_data["number"],
                            url=f"https://www.congress.gov/bill/{bill_data['congress']}th-congress/{bill_data['originChamber'].lower()}-bill/{bill_data['number']}"
                    )
                except Exception as e:
                    self.stdout.write(f"Error storing bill object: {e}")

            self.stdout.write("Saved %d bills to db" % len(data["bills"]))
