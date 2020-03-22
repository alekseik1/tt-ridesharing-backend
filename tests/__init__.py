from contextlib import contextmanager


@contextmanager
def login_as(client, user):
    from main_app.views.auth import login, logout
    from flask import url_for
    # Log in
    client.post(url_for(f'api.{login.__name__}'), json=dict(
        login=user.email,
        password='12345',
    ))
    yield user
    # Log out in the end
    client.post(url_for(f'api.{logout.__name__}'))