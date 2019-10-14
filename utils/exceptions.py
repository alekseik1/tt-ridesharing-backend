class ResponseExamples:

    INCORRECT_LOGIN = {'name': 'Invalid login or password', 'value': ''}
    USER_ID = {'user_id': 36}
    EMAIL_IS_BUSY = {'name': 'Email is already registered', 'value': 'm.smith@mail.ru'}
    ALREADY_LOGGED_IN = {'name': 'Already logged-in', 'value': ''}
    INVALID_USER_WITH_ID = {'name': 'Invalid user with id', 'value': 28}
    UNHANDLED_ERROR = {'name': 'Unhandled error', 'value': ''}

    @staticmethod
    def some_params_are_invalid(params):
        return {'name': 'Some of required fields are invalid', 'value': params}


class InvalidData(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv
