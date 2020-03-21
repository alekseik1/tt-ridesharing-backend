from main_app.views import api
from main_app.schemas import ReverseGeocodingSchema, \
    ForwardGeocodingSchema, OrganizationSchemaUserIDs
from flask import request, jsonify
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


def _parse_geocoding_results(response):
    return [dict(
        address=x['GeoObject']['metaDataProperty']['GeocoderMetaData']['Address']['formatted'],
        # NOTE: (latitude, longitude) are in reverse order
        gps=dict(zip(
            ('latitude', 'longitude'),
            x['GeoObject']['Point']['pos'].split(' ')[::-1]))
    ) for x in response['response']['GeoObjectCollection']['featureMember']]


def reverse_geocoding_blocking(latitude, longitude):
    yandex_response = requests.get(
        REVERSE_GEOCODING_URL.format(key=GEO_TOKEN, latitude=latitude, longitude=longitude)
    ).json()
    results = _parse_geocoding_results(yandex_response)
    # NOTE: we assume that first list element is nearest element
    return results[0]


def forward_geocoding_blocking(address):
    yandex_response = requests.get(
        FORWARD_GEOCODING_URL.format(key=GEO_TOKEN, address=address)
    ).json()
    results = _parse_geocoding_results(yandex_response)
    return results


def get_distance(coords1, coords2):
    return ((coords1[0] - coords2[0]) ** 2 + (coords1[1] - coords2[1]) ** 2) ** 0.5


@api.route('/decode_gps', methods=['POST'])
def decode_gps():
    data = ReverseGeocodingSchema().load(request.json)
    return jsonify(reverse_geocoding_blocking(**data))


@api.route('/encode_address', methods=['POST'])
def encode_address():
    data = ForwardGeocodingSchema().load(request.json)
    return jsonify(forward_geocoding_blocking(**data))


@api.route('/nearest_organizations', methods=['GET'])
@login_required
def get_nearest_organizations():
    data = ReverseGeocodingSchema().load(request.args)
    # TODO: what if organization does not have coordinates??
    result = sorted(
        current_user.organizations,
        key=lambda x: get_distance(
            (x.latitude, x.longitude),
            (float(data['latitude']), float(data['longitude']))
        )
    )
    dump_schema = OrganizationSchemaUserIDs(many=True)
    return jsonify(dump_schema.dump(result))
