# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import urllib.parse
import urllib.request
from typing import Any


def geocode_address(address: str) -> dict[str, Any]:
    """Convert an address or city name into geographic latitude and longitude coordinates via Geocoding API.

    Args:
        address: The location, street address, or city name (e.g. '1600 Amphitheatre Pkwy, Mountain View, CA').

    Returns:
        dict containing formatted address, latitude, longitude, and place_id.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "GOOGLE_MAPS_API_KEY environment variable is missing.",
        }

    encoded_address = urllib.parse.quote(address.strip())
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data.get("status") == "OK" and data.get("results"):
                res = data["results"][0]
                loc = res.get("geometry", {}).get("location", {})
                return {
                    "status": "success",
                    "formatted_address": res.get("formatted_address"),
                    "location": {
                        "latitude": loc.get("lat"),
                        "longitude": loc.get("lng"),
                    },
                    "place_id": res.get("place_id"),
                }
            return {
                "status": "not_found",
                "message": f"Could not geocode address: {address}. API status: {data.get('status')}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to call Geocoding API: {str(e)}",
        }


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "gym",
    radius_meters: float = 5000.0,
) -> dict[str, Any]:
    """Find nearby places of a given type (such as 'gym', 'fitness_center', 'park') near coordinates using Places API (New).

    Args:
        latitude: Latitude of the center location.
        longitude: Longitude of the center location.
        place_type: Type of place to search for (default 'gym').
        radius_meters: Radius around coordinates in meters (default 5000.0).

    Returns:
        dict containing list of nearby places with name, address, location (latitude/longitude), and types.
    """
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "message": "GOOGLE_MAPS_API_KEY environment variable is missing.",
        }

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    body = {
        "includedTypes": [place_type.strip()],
        "maxResultCount": 5,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius_meters,
            }
        },
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                places_raw = data.get("places", [])
                places = []
                for p in places_raw:
                    places.append(
                        {
                            "name": p.get("displayName", {}).get("text", "Unknown"),
                            "address": p.get("formattedAddress", "N/A"),
                            "location": {
                                "latitude": p.get("location", {}).get("latitude"),
                                "longitude": p.get("location", {}).get("longitude"),
                            },
                            "types": p.get("types", []),
                        }
                    )
                return {
                    "status": "success",
                    "places_count": len(places),
                    "places": places,
                }
            return {
                "status": "error",
                "message": f"Places API returned HTTP status {response.status}",
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to call Places API (New): {str(e)}",
        }
