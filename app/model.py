from app import db, ma

MAX_NAME_LENGTH = 40
MAX_SURNAME_LENGTH = 40
MAX_EMAIL_LENGTH = 256
MAX_URL_LENGTH = 2000


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(MAX_NAME_LENGTH), nullable=False)
    surname = db.Column(db.String(MAX_SURNAME_LENGTH), nullable=False)
    email = db.Column(db.String(MAX_EMAIL_LENGTH), nullable=False)
    photo = db.Column(db.String(MAX_URL_LENGTH))
    is_trusful = db.Column(db.Boolean)

    # For some reason, `User` database creation happens twice.
    # I cannot locate with bug, so I'm just leaving a hack here :)
    __table_args__ = {'extend_existing': True}


class UserSchema(ma.ModelSchema):
    class Meta:
        model = User


class Driver(User):
    id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + '.id'), primary_key=True)
    passport_1 = db.Column(db.String(MAX_URL_LENGTH))
    passport_2 = db.Column(db.String(MAX_URL_LENGTH))
    passport_selfie = db.Column(db.String(MAX_URL_LENGTH))
    driver_license_1 = db.Column(db.String(MAX_URL_LENGTH))
    driver_license_2 = db.Column(db.String(MAX_URL_LENGTH))

    # For some reason, `Driver` database creation happens twice.
    # I cannot locate with bug, so I'm just leaving a hack here :)
    __table_args__ = {'extend_existing': True}


class DriverSchema(ma.ModelSchema):
    class Meta:
        model = Driver
