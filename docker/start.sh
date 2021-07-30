#!/bin/bash
set -e
# Start Nginx, uwsgi and alembic migrations
service nginx start
(cd /app/src && flask db upgrade)
uwsgi -c /app/src/uwsgi.ini
