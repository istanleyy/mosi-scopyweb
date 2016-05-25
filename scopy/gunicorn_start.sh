#!/bin/bash

NAME="scopy_app"
DJANGODIR=/home/mosidev/sandbox/scopyweb/scopy
SOCKFILE=/home/mosidev/sandbox/scopyweb/run/gunicorn.sock
USER=mosidev
NUM_WORKERS=1
DJANGO_SETTINGS_MODULE=scopy.settings
DJANGO_WSGI_MODULE=scopy.wsgi

echo "Starting $NAME as `whoami`"

# Activate virtual environment
cd $DJANGODIR
source ../venv/bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start Django Unicorn
# Programs meant to be run under Supervisor shouldn't be daemonized
exec ../venv/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --user=$USER \
    --bind=unix:$SOCKFILE \
    --log-level=debug \
    --log-file=-