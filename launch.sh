#!/bin/bash

echo "Running debug launch.sh ..."

echo "Checking for additional pip requirements in /extensions/pip-requirements ..."
for file in /extensions/pip-requirements/*; do
        [ -f "$file" ] && echo "Installing pip requirements in $file ..." && pip install -r "$file"
done

echo "Checking for pre-launch scripts in /extensions/pre-launch-scripts ..."
for file in /extensions/pre-launch-scripts/*; do
        [ -f "$file" ] && [ -x "$file" ] && echo "Running script $file ..." && "$file"
done

DATABASE_SLEEP_TIME=10

# Create the Django project if it doesn't exist
cd /django

if [ ! -d "$PROJECT_NAME" ]; then

        if [ -f "manage.py" ]; then
                rm manage.py
        fi

        echo "Creating Django project $PROJECT_NAME"
        django-admin.py startproject $PROJECT_NAME .

        # Create the Django app if it doesn't exist
        if [ ! -d "$APP_NAME" ]; then

                echo "Creating Django app $APP_NAME"
                python manage.py startapp $APP_NAME

                echo "Checking for Django post-startapp scripts in /extensions/django/post-startapp-scripts ..."
                for file in /extensions/django/post-startapp-scripts/*; do
                        [ -f "$file" ] && [ -x "$file" ] && echo "Running script $file ..." && "$file"
                done
        fi

        cd /django

        echo "Copying default settings.py ..."
        cp /config/django/default-settings.py $PROJECT_NAME/settings.py
fi

if [ $DATABASE_SLEEP_TIME -gt 0 ]; then

        echo "Giving database time to launch fully ..."
        sleep $DATABASE_SLEEP_TIME
        DATABASE_SLEEP_TIME=0
fi

echo "Checking for pre-migration scripts in /extensions/django/pre-migration-scripts ..."
for file in /extensions/django/pre-migration-scripts/*; do
        [ -f "$file" ] && [ -x "$file" ] && echo "Running script $file ..." && "$file"
done

echo "Making project migrations ..."
python manage.py makemigrations --no-input --verbosity 1
echo "Making $APP_NAME app migrations ..."
python manage.py makemigrations $APP_NAME --no-input --verbosity 1
echo "Performing default database migrations ..."
python manage.py migrate --no-input --verbosity 1

echo "Checking for post-migration scripts in /extensions/django/post-migration-scripts ..."
for file in /extensions/django/post-migration-scripts/*; do
        [ -f "$file" ] && [ -x "$file" ] && echo "Running script $file ..." && sleep 5 && "$file"
done

echo "Collecting static files ..."
python manage.py collectstatic --noinput

echo "Checking for post-launch scripts in /extensions/post-launch-scripts ..."
for file in /extensions/post-launch-scripts/*; do
        [ -f "$file" ] && [ -x "$file" ] && echo "Running script $file ..." && sleep 5 && "$file"
done

cd /django

echo "Adding debugpy..."
pip install debugpy

# Start the project app server via Gunicorn
echo "Starting Gunicorn ..."
echo "(don't forget to connect the debugger before opening a browser...)"
python -m debugpy --wait-for-client --listen 0.0.0.0:5678 -m gunicorn --config /config/django/gunicorn.conf.py --log-config /config/django/logging.conf $PROJECT_NAME.wsgi