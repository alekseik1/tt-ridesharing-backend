from werkzeug.exceptions import HTTPException


class InvalidCredentials(HTTPException):
    code = 400
    description = 'Invalid login or password'


class AlreadyLoggedIn(HTTPException):
    code = 200
    description = 'Already logged-in'


class EmailBusy(HTTPException):
    code = 400
    description = 'Email is already registered'


class IncorrectControlAnswer(HTTPException):
    code = 400
    description = 'Incorrect answer for control question'


class NotInOrganization(HTTPException):
    code = 403
    description = 'User is not in that organization'


class CreatorCannotLeave(HTTPException):
    code = 400
    description = 'The creator cannot leave his organization'


class InsufficientPermissions(HTTPException):
    code = 403
    description = 'You do not own this item or the item does not exist'


class NotCarOwner(HTTPException):
    code = 403
    description = 'You do not own this car or the car does not exist'


class RideNotActive(HTTPException):
    code = 403
    description = 'Ride is not active or not found'


class NoFreeSeats(HTTPException):
    code = 403
    description = 'No free seats available'


class CreatorCannotJoin(HTTPException):
    code = 403
    description = 'You cannot join if you are the creator'


class RequestAlreadySent(HTTPException):
    code = 400
    description = 'Request already sent'


class NotInRide(HTTPException):
    code = 403
    description = 'You did not take this ride'


class NotForOwner(HTTPException):
    code = 403
    description = 'Owner cannot do that'


class RideNotFinished(HTTPException):
    code = 403
    description = 'Ride has not finished yet'
