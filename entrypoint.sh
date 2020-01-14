#!/bin/sh

python manage.py db upgrade
# All CMD if processed afterwards
exec "$@"