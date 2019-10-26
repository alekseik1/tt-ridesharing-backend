from app import db
from model import Ride, Organization
import operator
from geopy.distance import great_circle


# TODO: for now, `organizations` is ignored
# TODO: Optimization! Don't take all rides, use more filters
def _find_best_rides(start_organization_id, destination_gps):
    # Get all rides starting from exact organization and are available
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
        result_top.append((ride, distance))
    result_top.sort(key=operator.itemgetter(1))
    return result_top
