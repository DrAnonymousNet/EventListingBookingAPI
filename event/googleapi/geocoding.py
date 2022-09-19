import json
import re
from urllib.parse import urlencode

import requests
from django.conf import settings

base_url = "https://maps.googleapis.com/maps/api/geocode/json"


class GeoEncodingClient:
    def __init__(self) -> None:
        self.key = settings.GOOGLE_DIRECTION_SECRET_KEY

    def clean_address(self, address) -> str:
        cleaned_address = re.sub(r"[^a-zA-Z0-9 ]", "")
        return cleaned_address

    def geoencode(self, address) -> tuple:
        # cleaned_address = self.clean_address(address)
        query_params = urlencode({"address": address, "key": self.key})
        full_path = f"{base_url}?{query_params}"
        response = requests.post(full_path)
        return json.loads(response.content), response.status_code

    def get_lat_and_long(self, address) -> dict:
        geoencode_data, geoencode_res_code = self.geoencode(address)
        if geoencode_res_code == 200:
            lat_n_long = geoencode_data["results"][0].get("geometry").get("location")
            return lat_n_long
        else:
            return geoencode_res_code.get("error_message")

    def reverse_geoencode(self, latlng: dict):
        query_params = urlencode(
            {"key": self.key, "latlng": f"{latlng['lat']},{latlng['lng']}"}
        )
        full_path = f"{base_url}?{query_params}"

        response = requests.post(full_path)
        return json.loads(response.content), response.status_code

    def get_full_address(self, latlng: dict):
        reversed_geoencode_data, reversed_geoencode_status = self.reverse_geoencode(
            latlng
        )
        if reversed_geoencode_status == 200:
            full_address = reversed_geoencode_data.get("formatted_address")
            return full_address
        else:
            return None


def geoencodeaddress(address):
    client = GeoEncodingClient()
    lat_and_long = client.get_lat_and_long(address)
    return lat_and_long
