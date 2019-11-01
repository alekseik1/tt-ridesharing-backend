class ResponseExamples:

    INCORRECT_LOGIN = {'name': 'Invalid login or password', 'value': ''}
    INVALID_ORGANIZATION_ID = {'name': 'Invalid organization with id', 'value': ''}
    USER_ID = {'user_id': 36}
    RIDE_ID = {'ride_id': 36}
    EMAIL_IS_BUSY = {'name': 'Email is already registered', 'value': 'm.smith@mail.ru'}
    ALREADY_LOGGED_IN = {'name': 'Already logged-in', 'value': ''}
    INVALID_USER_WITH_ID = {'name': 'Invalid user with id', 'value': 28}
    INVALID_USER_WITH_EMAIL = {'name': 'Email not found', 'value': 'm.mm@mm.ru'}
    NO_PERMISSION_FOR_USER = {'name': 'No permission for user', 'value': 28}
    UNHANDLED_ERROR = {'name': 'Unhandled error', 'value': ''}
    USER_INFO = {'user_id': 28, 'first_name': 'Martin', 'last_name': 'Smith',
                 'email': 'm.smith@gmail.com', 'photo_url': ''}

    IS_NOT_DRIVER = {'name': 'User with ID is not a driver', 'value': 0}

    RIDE_INFO = {'start_organization': None,
                 'stop_organization': None, 'start_time': '', 'host_driver_id': 36,
                 'estimated_time': '', 'passengers': []}
    INVALID_RIDE_WITH_ID = {'name': 'Invalid ride with id', 'value': 37}

    AUTHORIZATION_REQUIRED = {'name': 'Authorization required', 'value': ''}

    ORGANIZATION_LIMIT = {'name': 'Organization limit exceeded', 'value': ''}
    ERROR_NOT_IN_ORGANIZATION = {'name': 'Not in organization', 'value': 36}
    ERROR_ALREADY_IN_RIDE = {'name': 'User is already in drive with user_id', 'value': 36}
    ERROR_IS_RIDE_HOST = {'name': 'User is ride host with user_id', 'value': 36}
    ERROR_RIDE_UNAVAILABLE = {'name': 'Ride is unavailable with ride_id', 'value': 36}
    ORGANIZATION_ID = {'organization_id': 36}

    MATCHING_RESULTS = {'top': []}

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
