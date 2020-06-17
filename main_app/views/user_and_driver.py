import requests
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from main_app.model import User, DriverSubscription
from main_app.schemas import OrganizationJsonSchema, UserJsonSchema, \
    PasswordChangeSchema, UploadFileSchema, UserChangeSchema, SearchSchema, \
    UpdateFirebaseIdSchema, SubscribeToDriverSchema
from main_app.exceptions.custom import InsufficientPermissions, InvalidCredentials, \
    SubscriptionError
from app import db
from main_app.views import api


@api.route('/user/organizations', methods=['GET'])
@login_required
def organizations():
    return jsonify(OrganizationJsonSchema(only=('id', 'name', 'address'), many=True).dump(
        current_user.organizations
    ))


@api.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    if request.method == 'GET':
        user = UserJsonSchema(only=('id', )).load(request.args)
        GENERAL_INFO = ['id', 'first_name', 'last_name', 'rating', 'photo_url', 'about']
        if user.id is None:
            return UserJsonSchema(
                only=GENERAL_INFO + ['email', 'phone_number']
            ).dump(current_user)
        if user.email is None:
            raise InsufficientPermissions()
        return UserJsonSchema(
            only=GENERAL_INFO
        ).dump(user)
    elif request.method == 'POST':
        updated_params = UserChangeSchema().load(request.json)
        for prop, new_value in updated_params.items():
            setattr(current_user, prop, new_value)
        db.session.commit()
        return 'ok'


@api.route('/user/password', methods=['POST'])
@login_required
def change_password():
    data = PasswordChangeSchema().load(request.json)
    old_password, new_password = data['old_password'], data['new_password']
    if not current_user.check_password(old_password):
        raise InvalidCredentials()
    current_user.password = new_password
    db.session.commit()
    return UserJsonSchema(only=('id', )).dump(current_user)


@api.route('/user/sign_s3', methods=['GET'])
@login_required
def user_avatar_sign_s3():
    data = UploadFileSchema().load(request.args)

    file_type = data.get('file_type')
    s3 = current_app.s3_client
    file_name = f'{current_user.id}.{file_type}'

    presigned_post = s3.generate_presigned_post(
        Bucket=current_app.config['S3_BUCKET'],
        Key=file_name,
        Fields={"acl": "public-read", "Content-Type": f'image/{file_type}'},
        Conditions=[
            {"acl": "public-read"},
            {"Content-Type": f'image/{file_type}'}
        ],
        ExpiresIn=3600
    )
    # https://sharemyride-avatars.s3.eu-north-1.amazonaws.com/53.png
    # Save avatar URL in database
    current_user.photo_url = f"https://{current_app.config.get('S3_BUCKET', '')}." \
                             f"{s3.meta.endpoint_url.split('://')[1]}/{file_name}"
    db.session.commit()
    return presigned_post


@api.route('/user/search', methods=['GET'])
@login_required
def search_users():
    query_string = SearchSchema().load(request.args)
    results, total = User.search(query_string['query'], 1, 10)
    return jsonify(UserJsonSchema(many=True, only=(
        'id', 'first_name', 'last_name', 'phone_number', 'email', 'photo_url'
    )).dump(results))


@api.route('/user/updateFirebaseRegistrationToken', methods=['POST'])
@login_required
def update_firebase_id():
    data = UpdateFirebaseIdSchema().load(request.json)
    response = requests.post(
        f"{current_app.config['FCM_BACKEND_URL']}/update_token/",
        data={'id': current_user.id, 'token': data['token']}
    )
    current_app.logger.info(f'response from FCM: {(response.content, response.status_code)}')
    return response.content, response.status_code


@api.route('/user/subscribe', methods=['POST'])
@login_required
def subscribe():
    data = SubscribeToDriverSchema().load(request.json)
    driver_id, action = data['id'], data['action']
    if action == 'SUBSCRIBE':
        try:
            db.session.add(DriverSubscription(
                subscriber=current_user, driver_id=driver_id))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise SubscriptionError()
    elif action == 'UNSUBSCRIBE':
        subscription_entry = db.session.query(DriverSubscription).filter_by(
            subscriber=current_user, driver_id=driver_id).first()
        if not subscription_entry:
            raise SubscriptionError(
                f'{current_user.id} is not subscribed to {driver_id}')
        db.session.delete(subscription_entry)
        db.session.commit()
    return 'ok'
