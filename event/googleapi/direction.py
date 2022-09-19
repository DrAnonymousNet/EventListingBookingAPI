import json
from urllib.parse import urlencode

import requests
from django.conf import settings

base_url = "https://maps.googleapis.com/maps/api/directions/json?"


class DirectionClient:
    def __init__(self, origin, destination, mode) -> None:
        self.origin = origin
        self.destination = destination
        self.mode = mode
        self.secret_key = settings.GOOGLE_DIRECTION_SECRET_KEY

    def get_direction(self):
        query_prams = urlencode(
            {
                "origin": self.origin,
                "destination": self.destination,
                "mode": self.mode,
                "key": self.secret_key,
            }
        )

        full_url = f"{base_url}{query_prams}"
        response = requests.post(full_url)

        return json.loads(response.content)

    def get_direction_data(self, json_response):
        print(json_response)
        if json_response.get("status") == "OK":
            route_meta = json_response["routes"][0]["legs"][0]
            distance = route_meta["distance"].get("text")
            duration = route_meta["duration"].get("text")
            end_address = route_meta.get("start_address")
            start_adderss = route_meta.get("end_address")
            steps = route_meta["steps"]

            direction = []
            for step in steps:
                direction.append(
                    {
                        "direction_instruction": step.get("html_instructions"),
                        "duration": step["duration"].get("text"),
                        "distance": step["distance"].get("text"),
                        "maneuver": step.get("maneuver"),
                    }
                )

            cleaned_direction = {
                "total_duration": duration,
                "total_distance": distance,
                "start_address": start_adderss,
                "end_address": end_address,
                "direction": direction,
            }
            return cleaned_direction
        else:
            return None


def get_direction_cleaned_date(origin, destination, mode="driving"):
    client = DirectionClient(origin, destination, mode)
    response = client.get_direction()
    cleaned_data = client.get_direction_data(response)
    return cleaned_data
