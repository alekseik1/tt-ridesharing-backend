#!/bin/sh

python manage.py db upgrade

# For staging, fill database
if [ $STAGING -eq 1 ]
then
  python fill_db.py
fi
# All CMD if processed afterwards
exec "$@"