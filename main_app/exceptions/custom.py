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
