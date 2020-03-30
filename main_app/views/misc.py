from main_app.misc import get_distance, reverse_geocoding_blocking, forward_geocoding_blocking
from main_app.views import api
from main_app.schemas import ReverseGeocodingSchema, \
    ForwardGeocodingSchema, OrganizationSchemaUserIDs
from flask import request, jsonify
from flask_login import login_required, current_user


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
