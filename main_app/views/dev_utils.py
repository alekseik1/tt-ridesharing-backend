from main_app.views import api


@api.route('/debug-sentry')
def trigger_error():
    return 1 / 0
