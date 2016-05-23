#!/bin/bash

NAME="scopy_app"
DJANGODIR=/scopyweb/scopy/scopy
USER=mosidev
GROUP=webapps
NUM_WORKERS=1
DJANGO_SETTINGS_MODULE=scopy.settings
DJANGO_WSGI_MODULE=scopy.wsgi

echo "Starting $NAME as `whoami`"

# Activate virtual environment
cd $DJANGODIR
source ../bin/activate
export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Create tun directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start Django Unicorn
# Programs meant to be run under Supervisor shouldn't be daemonized
exec ../bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
    --name $NAME \
    --workers $NUM_WORKERS \
    --user=$USER --group=$GROUP \
    --bind=unix:$SOCKFILE \
    --log-level=debug \
    --log-file=-