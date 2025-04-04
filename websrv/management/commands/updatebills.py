from django.core.management.base import BaseCommand, CommandError
from urllib.parse import urlparse
import os

from websrv.models import Bill, Cosponsor
from websrv.utils.congress import fetch_cosponsors

class Command(BaseCommand):
    help = "Fetch bills from Congress.gov API"

    def add_arguments(self, parser):
        parser.add_argument(
                "--cosponsor", "-csp",
                action="store_true",
                help="Updating cosponsor fields",
            )

    def handle(self, *args, **options):
        congress_key = os.getenv("CONGRESS_API_KEY")
        if not congress_key:
            raise CommandError("Congress API key is not provived")

        if options["cosponsor"]:
            bills = Bill.objects.all()

            for bill in bills:
                cosponsors = fetch_cosponsors(str(bill.congress), bill.bill_type, bill.bill_number)
                if not cosponsors:
                    continue

                for member in cosponsors:
                    try:
                        m, _ = Cosponsor.objects.get_or_create(
                                bioguide_id=member["bioguide_id"],
                                first_name=member["first_name"],
                                middle_name=member["middle_name"],
                                last_name=member["last_name"],
                                full_name=member["full_name"],
                                party=member["party"],
                                state=member["state"],
                                district=member["district"],
                                is_original_cosponsor=member["is_original_cosponsor"],
                                sponsorship_date=member["sponsorship_date"],
                                url=member["url"],
                                img_url=member["img_url"],
                                )

                        bill.cosponsors.add(m)
                    except Exception as e:
                        self.stdout.write(f"Error storing object: {e}")
