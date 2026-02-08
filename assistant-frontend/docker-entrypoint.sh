#!/bin/sh
set -e
export BACKEND_UPSTREAM="${BACKEND_UPSTREAM:-backend:8000}"
envsubst '${BACKEND_UPSTREAM}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf
exec nginx -g "daemon off;"
