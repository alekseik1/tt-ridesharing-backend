from werkzeug.exceptions import HTTPException


class InvalidCredentials(HTTPException):
    code = 400
    description = 'Invalid login or password'


class AlreadyLoggedIn(HTTPException):
    code = 400
    description = 'Already logged-in'


class EmailBusy(HTTPException):
    code = 400
    description = 'Email is already registered'


class IncorrectControlAnswer(HTTPException):
    code = 400
    description = 'Incorrect answer for control question'


class NotInOrganization(HTTPException):
    code = 400
    description = 'User is not in that organization'


class CreatorCannotLeave(HTTPException):
    code = 400
    description = 'The creator cannot leave his organization'


class NotCarOwner(HTTPException):
    code = 400
    description = 'You do not own this car or the car does not exist'
