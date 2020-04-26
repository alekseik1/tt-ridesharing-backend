#!/bin/sh

python manage.py db upgrade
if [ "$STAGING" = 1 ]
then
  python fill_db.py
fi
exec "$@"

