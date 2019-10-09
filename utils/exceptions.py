class ResponseExamples:

    INCORRECT_LOGIN = {'name': 'Invalid login or password', 'value': ''}
    USER_ID = {'user_id': 36}
    EMAIL_IS_BUSY = {'name': 'Email is already registered', 'value': 'm.smith@mail.ru'}

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
