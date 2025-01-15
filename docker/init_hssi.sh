
pushd $PWD

cd /django
python manage.py init_superuser
python manage.py import_website_database

popd
