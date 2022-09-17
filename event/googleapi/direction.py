from urllib import response
import requests
from urllib.parse import urlencode
import json
from django.conf import settings


base_url = "https://maps.googleapis.com/maps/api/directions/json?"

def get_direction(origin, destination, mode="driving"):
    query_prams = urlencode({"origin":origin, "destination":destination, 
                    "mode":mode,"key":settings.GOOGLE_DIRECTION_SECRET_KEY})

    full_url = f"{base_url}{query_prams}"
    print(full_url)

    response = requests.post(full_url)

    return json.loads(response.content)

def get_direction_data(json_response):
    
    route_meta = json_response["routes"][0]["legs"][0]
    distance = route_meta["distance"].get("text")
    duration = route_meta["duration"].get("text")
    end_address = route_meta.get("start_address")
    start_adderss = route_meta.get("end_address")
    steps = route_meta["steps"]

    
    direction = []
    for step in steps:
        direction.append({
            "direction_instruction":step.get("html_instructions"),
            "duration":step["duration"].get("text"),
            "distance":step["distance"].get("text"),
            "maneuver":step.get("maneuver")
        })

    cleaned_direction = {
        "total_duration":duration,
        "total_distance":distance,
        "start_address":start_adderss,
        "end_address":end_address,
        "direction":direction
    }
    return cleaned_direction


        


    