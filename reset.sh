#!/usr/bin/env bash

if [ $# -lt 3 ]; then
    echo "Usage: $0 <superuser_email> <superuser_name> <superuser_password>"
    exit 1
fi

# exit on error
set -e

SUPERUSER_EMAIL=$1
SUPERUSER_USERNAME=$2
SUPERUSER_PASSWORD=$3

python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

# create super user
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(email='${SUPERUSER_EMAIL}').exists() or User.objects.create_superuser('${SUPERUSER_USERNAME}', '${SUPERUSER_EMAIL}', '${SUPERUSER_PASSWORD}')" | python manage.py shell

python manage.py update_permissions

python manage.py import_defaut

