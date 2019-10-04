from app import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(40))
    surname = db.Column(db.String(40))
    email = db.Column(db.String(256))
    photo = db.Column(db.String(2000))
    is_trusful = db.Column(db.Boolean)

    # For some reason, `User` database creation happens twice.
    # I cannot locate with bug, so I'm just leaving a hack here :)
    __table_args__ = {'extend_existing': True}


class Driver(User):
    id = db.Column(db.Integer, db.ForeignKey(User.__tablename__ + '.id'), primary_key=True)
    passport_1 = db.Column(db.String(2000))
    passport_2 = db.Column(db.String(2000))
    passport_selfie = db.Column(db.String(2000))
    driver_license_1 = db.Column(db.String(2000))
    driver_license_2 = db.Column(db.String(2000))

    # For some reason, `Driver` database creation happens twice.
    # I cannot locate with bug, so I'm just leaving a hack here :)
    __table_args__ = {'extend_existing': True}
