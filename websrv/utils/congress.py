from django.conf import os
from dotenv import load_dotenv
import requests

load_dotenv()

congress_url = "https://api.congress.gov/v3/"
def fetch_text_sources(congress: str, bill_type: str, bill_number: str):
    congress_key = os.getenv("CONGRESS_API_KEY")
    bill_type = bill_type.lower()

    params = {'api_key': congress_key}
    req = requests.get(congress_url + f"bill/{congress}/{bill_type}/{bill_number}" + "/text", params=params)

    data = req.json()
    if not data["textVersions"]:
        return None

    res = data["textVersions"][-1]
    return res


def fetch_text_htm(congress: str, bill_type: str, bill_number: str):
    src = fetch_text_sources(congress, bill_type, bill_number) 
    if not src:
        return None

    htm_url = src["formats"][0]["url"]
    htm = requests.get(htm_url)

    return htm.text
