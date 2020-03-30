from main_app.misc import reverse_geocoding_blocking, forward_geocoding_blocking
from main_app.views import api
from main_app.schemas import ReverseGeocodingSchema, \
    ForwardGeocodingSchema
from flask import request, jsonify


@api.route('/decode_gps', methods=['POST'])
def decode_gps():
    data = ReverseGeocodingSchema().load(request.json)
    return jsonify(reverse_geocoding_blocking(**data))


@api.route('/encode_address', methods=['POST'])
def encode_address():
    data = ForwardGeocodingSchema().load(request.json)
    return jsonify(forward_geocoding_blocking(**data))
