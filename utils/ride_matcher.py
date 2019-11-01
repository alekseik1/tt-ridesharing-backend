from app import db
from main_app.model import Ride, User
from main_app.schemas import RideSchema, UserSchema
import operator
from geopy.distance import great_circle
from utils.misc import format_time


def _get_user_info(user_id):
    user_schema = UserSchema()
    user = db.session.query(User).filter_by(id=user_id).first()
    return user_schema.dump(user)


# TODO: for now, `organizations` is ignored
# TODO: Optimization! Don't take all rides, use more filters
def _find_best_rides(start_organization_id, destination_gps):
    # Get all rides starting from exact organization and are available
    ride_schema = RideSchema()
    all_rides = db.session.query(Ride)\
        .filter_by(start_organization_id=start_organization_id)\
        .filter_by(is_available=True).all()
    # For each ride, find distance to `gps`
    # We make top based on  destination point
    result_top = []
    for ride in all_rides:
        distance = great_circle(
            (ride.stop_latitude, ride.stop_longitude),
            destination_gps
        ).kilometers
        ride_info = ride_schema.dump(ride)
        ride_info['host_driver_info'] = _get_user_info(ride.host_driver_id)
        ride_info = format_time([ride_info])[0]
        result_top.append((ride_info, distance))
    result_top.sort(key=operator.itemgetter(1))
    return result_top
