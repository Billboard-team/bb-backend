from django.conf import os
from dotenv import load_dotenv
import requests

load_dotenv()

#this needs to be notated!
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


#helper function for retrieving cosponsor data
def fetch_cosponsors(congress: str, bill_type: str, bill_number: str) -> list[dict] | None:
    congress_key = os.getenv("CONGRESS_API_KEY")  
    bill_type = bill_type.lower()
    
    params = {"api_key": congress_key}
    req = requests.get(f"{congress_url}bill/{congress}/{bill_type}/{bill_number}/cosponsors", params=params)

    data = req.json()
    if "cosponsors" not in data or not data["cosponsors"]:
        return None  

    cosponsor_list = []
    for cosponsor in data["cosponsors"]:
        id = cosponsor["bioguideId"]
        req = requests.get(f"{congress_url}/member/{id}", params=params)

        data = req.json()
        img_url = ''
        if data["member"]["depiction"]["imageUrl"]:
            img_url = data["member"]["depiction"]["imageUrl"]

        cosponsor_list.append({
            "bioguide_id": cosponsor["bioguideId"],
            "first_name": cosponsor["firstName"],
            "middle_name": cosponsor.get("middleName", ""),
            "last_name": cosponsor["lastName"],
            "full_name": cosponsor["fullName"],
            "party": cosponsor["party"],
            "state": cosponsor["state"],
            "district": cosponsor.get("district", None),
            "is_original_cosponsor": cosponsor["isOriginalCosponsor"],
            "sponsorship_date": cosponsor["sponsorshipDate"],
            "url": cosponsor["url"],
            "img_url": img_url,
        })

    return cosponsor_list
