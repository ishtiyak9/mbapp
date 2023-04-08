from django.http import Http404
from geopy.geocoders import Bing
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from mbapp.settings import BING_MAPS_API_KEY
from .location_helpers import filter_by_distance, geocode_location
from .models import Business
from .serializers import BusinessSerializer


class BusinessDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """
            Helper method to get business object by primary key or raise 404 error if not found.
            :param pk: primary key of the business object to retrieve.
            :return: Business object for the given pk.
        """
        try:
            return Business.objects.get(pk=pk)
        except Business.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        """
            Retrieve a business object by primary key.
            :param request: Django request object.
            :param pk: primary key of the business object to retrieve.
            :return: Response object containing serialized business data.
        """
        business = self.get_object(pk)
        serializer = BusinessSerializer(business)
        return Response(serializer.data)

    def put(self, request, pk):
        """
            Update a business object with the given data.
            :param request: Django request object.
            :param pk: primary key of the business object to update.
            :return: Response object containing serialized updated business data.
        """
        business = self.get_object(pk)
        serializer = BusinessSerializer(business, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
            Delete a business object by primary key.
            :param request: Django request object.
            :param pk: primary key of the business object to delete.
            :return: Response object with no content and 204 status code.
        """
        business = self.get_object(pk)
        business.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BusinessList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
            Retrieves a list of businesses near a given location. The location is extracted
            from the request's query parameters. If a valid location is provided, the
            view will call an external API for geocoding and filter the Business model
            by distance. If no businesses are found, a 404 status response will be returned.
            If there is an issue with the location query or external API call, a 400 status
            response will be returned.

            Parameters: request (HttpRequest): The request object sent to the server.

            Returns:  Response: A response object containing a list of businesses within the specified distance of the location.

            Exceptions: Http404: If no Business objects are found with the provided primary key.

        """
        location_str = request.query_params.get('location')
        if location_str:
            try:
                geolocator = Bing(api_key=BING_MAPS_API_KEY)
                location = geolocator.geocode(location_str)
                if location is None:
                    return Response({'detail': 'Invalid location1.'}, status=status.HTTP_400_BAD_REQUEST)
                lat = location.latitude
                lon = location.longitude
            except:
                return Response({'detail': 'Invalid location2.'}, status=status.HTTP_400_BAD_REQUEST)
            nearby_businesses = filter_by_distance(lat, lon)
            if not nearby_businesses:
                return Response({'detail': 'No nearby businesses found.'}, status=status.HTTP_404_NOT_FOUND)
            serializer = BusinessSerializer(nearby_businesses, many=True)
            return Response(serializer.data)
        else:
            return Response({'detail': 'Missing location.'}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        """
            Creates a new Business object with the data provided in the request body.
            The location field is geocoded using an external API. If the location is invalid
            or cannot be geocoded, a 400 status response will be returned. If the object is
            successfully created, a 201 status response will be returned.

            Parameters: request (HttpRequest): The request object sent to the server.

            Returns: Response: A response object containing the created Business object.
            Exceptions: None

        """
        serializer = BusinessSerializer(data=request.data)
        if serializer.is_valid():
            location = serializer.validated_data['location']
            latitude, longitude = geocode_location(location)
            if not latitude or not longitude:
                return Response({'detail': 'Invalid location3.'}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(latitude=latitude, longitude=longitude)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
