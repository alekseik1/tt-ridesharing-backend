from main_app.views import api
from main_app.controller import validate_params_with_schema
from main_app.schemas import ReverseGeocodingSchema, \
    ForwardGeocodingSchema, OrganizationSchemaUserIDs
from flask import request
from flask_login import login_required, current_user
import os
import requests

"""
Yandex geocoder.

Simply redirects to Yandex geocoding API
"""

REVERSE_GEOCODING_URL = 'https://geocode-maps.yandex.ru/1.x/?apikey={key}&' \
                        'format=json&geocode={longitude},{latitude}'
FORWARD_GEOCODING_URL = 'https://geocode-maps.yandex.ru/1.x/?apikey={key}&bbox=37.144775,' \
                        '55.561263~38.070374,56.059769&rspn=1&format=json&geocode={address}'
GEO_TOKEN = os.environ['GEOCODING_KEY']


def reverse_geocoding_blocking(latitude, longitude):
    return requests.get(
        REVERSE_GEOCODING_URL.format(key=GEO_TOKEN, latitude=latitude, longitude=longitude)
    ).json()


def forward_geocoding_blocking(address):
    return requests.get(
        FORWARD_GEOCODING_URL.format(key=GEO_TOKEN, address=address)
    ).json()


def get_distance(coords1, coords2):
    return ((coords1[0] - coords2[0]) ** 2 + (coords1[1] - coords2[1]) ** 2) ** 0.5


@api.route('/decode_gps', methods=['POST'])
def decode_gps():
    data = request.get_json()
    error = validate_params_with_schema(ReverseGeocodingSchema(), data)
    if error:
        return error
    return reverse_geocoding_blocking(**data)


@api.route('/encode_address', methods=['POST'])
def encode_address():
    data = request.get_json()
    error = validate_params_with_schema(ForwardGeocodingSchema(), data)
    if error:
        return error
    return forward_geocoding_blocking(**data)


@api.route('/nearest_organizations', methods=['GET'])
@login_required
def get_nearest_organizations():
    data = request.args
    error = validate_params_with_schema(ReverseGeocodingSchema(), data)
    if error:
        return error
    # TODO: what if organization does not have coordinates??
    result = sorted(
        current_user.organizations,
        key=lambda x: get_distance(
            (x.latitude, x.longitude),
            (float(data['latitude']), float(data['longitude']))
        )
    )
    dump_schema = OrganizationSchemaUserIDs(many=True)
    return dump_schema.dumps(result)
