from app import db
from model import Ride, Organization
import operator
from geopy.distance import great_circle


# TODO: for now, `organizations` is ignored
# TODO: Optimization! Don't take all rides, use more filters
def find_best_rides(gps, organizations=[]):
    all_rides = db.session.query(Ride).filter_by(is_available=True).all()
    # For each ride, find distance to `gps`
    result_top = []
    for ride in all_rides:
        distance = great_circle(
            (ride.start_organization.latitude, ride.start_organization.longitude),
            gps
        ).kilometers
        result_top.append((ride, distance))
    result_top.sort(key=operator.itemgetter(1))
    return result_top
