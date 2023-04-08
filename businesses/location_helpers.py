from geopy import distance
from geopy.geocoders import Bing
from rest_framework import status
from rest_framework.response import Response

from mbapp.settings import BING_MAPS_API_KEY
from .models import Business


def geocode_location(location):
    """
        Geocodes a given location using the Bing Maps API.

        Args:
            location (str): The location to be geocoded.

        Returns:
            tuple: A tuple containing the latitude and longitude of the geocoded location,
                   or (None, None) if the location could not be geocoded.
    """
    geolocator = Bing(api_key=BING_MAPS_API_KEY)
    location = geolocator.geocode(location)
    if location is not None:
        return location.latitude, location.longitude
    else:
        return None, None


def filter_by_distance(lat, lon):
    """
        Filters businesses by distance from a given location.

        Args:
            lat (float): The latitude of the location.
            lon (float): The longitude of the location.

        Returns:
            list: A list of businesses within 10km of the given location,
            or a Response with status 404 if no businesses are found.
    """
    location = (lat, lon)
    businesses = Business.objects.all()
    nearby_businesses = []
    for business in businesses:
        if business.latitude is not None and business.longitude is not None:
            business_location = (business.latitude, business.longitude)
            print(business_location)
            if distance.distance(location, business_location).km <= 10:
                nearby_businesses.append(business)
        else:
            return Response({'detail': 'No data found.'}, status=status.HTTP_404_NOT_FOUND)
    return nearby_businesses
